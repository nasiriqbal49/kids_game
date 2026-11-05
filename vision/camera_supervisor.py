import os
import threading
import time
from enum import Enum
from typing import Optional, Callable, Any, Tuple

import cv2

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from vision.camera_manager import CameraDevice, Frame

log = get_logger("camera_supervisor")


class ActiveSource(str, Enum):
    PHONE = "phone"      # Iriun Phone Webcam
    LAPTOP = "laptop"    # Built-in laptop webcam
    KEYBOARD = "keyboard"


class CameraSupervisor:
    """
    Supervises ONE active camera stream with automatic priority:
    1. Iriun phone webcam (a candidate only counts if it delivers non-black frames)
    2. Laptop webcam (fallback)
    3. Keyboard mode (no camera)

    Only one camera stream is kept open. While a camera is healthy it is never
    re-probed; looking for a better camera happens in a background thread so the
    UI never stalls.
    """

    WARMUP_SEC = 3.0  # a freshly started device may not have produced a frame yet
    STALE_LIMIT_SEC = 6.0  # tolerate main-thread stalls (MediaPipe load) before declaring a camera lost

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 capture_factory: Optional[Callable[[int], Any]] = None,
                 phone_index: Optional[int] = None, laptop_index: int = 0,
                 min_brightness: float = 0.0, recheck_interval_sec: float = 5.0):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.capture_factory = capture_factory or (
            lambda idx: cv2.VideoCapture(idx, cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY)
        )

        self.laptop_index = laptop_index
        self.preferred_phone_index = phone_index if phone_index is not None else self.config.get("camera.camera_index", 2)
        self.rotation_degrees: int = self.config.get("camera.rotation", 0)

        # Frames darker than this (mean pixel value 0-255) are treated as "no phone".
        # 0 disables the check. Apps pass ~6 so Iriun's empty virtual camera is ignored.
        self.min_brightness = float(min_brightness)
        self.recheck_interval_sec = recheck_interval_sec
        self.probe_reads = 8

        self.active_source: ActiveSource = ActiveSource.KEYBOARD
        self.active_device: Optional[CameraDevice] = None
        self.active_index: Optional[int] = None

        self.measured_latency_ms: float = 0.0
        self.last_discovery_time: float = time.time()

        self._device_started_at: float = 0.0
        self._pending_choice: Optional[Tuple[ActiveSource, Optional[int]]] = None
        self._discovery_thread: Optional[threading.Thread] = None
        self._closed: bool = False

        self.discover_and_connect()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _is_live(self, frame) -> bool:
        if self.min_brightness <= 0:
            return True
        try:
            return float(frame.mean()) >= self.min_brightness
        except Exception:
            return False

    def _probe_index(self, idx: int, require_live: bool) -> bool:
        """Opens a device briefly; True if it delivers a usable frame."""
        cap = None
        try:
            cap = self.capture_factory(idx)
            if cap is None or not cap.isOpened():
                return False
            for _ in range(self.probe_reads):
                ok, frame = cap.read()
                if ok and frame is not None and (not require_live or self._is_live(frame)):
                    return True
                time.sleep(0.03)
            return False
        except Exception:
            return False
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass

    def _probe_phone(self) -> Optional[int]:
        candidates = [self.preferred_phone_index] + [i for i in (1, 2, 3, 4) if i != self.preferred_phone_index]
        for idx in candidates:
            if idx == self.laptop_index or self._closed:
                continue
            if self._probe_index(idx, require_live=True):
                return idx
        return None

    def _device_healthy(self, dev: Optional[CameraDevice]) -> bool:
        if dev is None or not dev.is_connected:
            return False
        frame = dev.get_frame()
        last = frame.timestamp if frame is not None else self._device_started_at
        return (time.time() - last) < self.STALE_LIMIT_SEC

    def _find_best_source(self) -> Tuple[ActiveSource, Optional[int]]:
        """Decides which camera should be active. Does not switch anything itself."""
        src, dev, idx = self.active_source, self.active_device, self.active_index

        if src == ActiveSource.PHONE and self._device_healthy(dev):
            return ActiveSource.PHONE, idx

        phone_idx = self._probe_phone()
        if phone_idx is not None:
            return ActiveSource.PHONE, phone_idx

        # Never re-open the laptop webcam while it is already streaming fine
        if src == ActiveSource.LAPTOP and self._device_healthy(dev):
            return ActiveSource.LAPTOP, idx

        if self._probe_index(self.laptop_index, require_live=False):
            return ActiveSource.LAPTOP, self.laptop_index

        return ActiveSource.KEYBOARD, None

    def _apply_choice(self, choice: Tuple[ActiveSource, Optional[int]]) -> None:
        source, index = choice
        if self._closed:
            return
        if source == self.active_source and index == self.active_index:
            return
        if source == ActiveSource.KEYBOARD:
            previous = self.active_source
            self._close_active()
            self.active_source = ActiveSource.KEYBOARD
            self._emit_switch(previous, ActiveSource.KEYBOARD)
        else:
            self._switch_to_device(source, index)

    def discover_and_connect(self) -> ActiveSource:
        """Synchronous discovery (used at startup and by tests)."""
        self._apply_choice(self._find_best_source())
        return self.active_source

    def evaluate_fallback_chain(self) -> ActiveSource:
        """Alias for discover_and_connect to maintain test compatibility."""
        return self.discover_and_connect()

    def _start_background_discovery(self) -> None:
        if self._closed or (self._discovery_thread and self._discovery_thread.is_alive()):
            return

        def work():
            try:
                self._pending_choice = self._find_best_source()
            except Exception as err:
                log.error("Background camera discovery failed: %s", err)

        self._discovery_thread = threading.Thread(target=work, name="CamDiscovery", daemon=True)
        self._discovery_thread.start()

    def _apply_pending_choice(self) -> None:
        choice, self._pending_choice = self._pending_choice, None
        if choice is not None:
            self._apply_choice(choice)

    # ------------------------------------------------------------------
    # Switching
    # ------------------------------------------------------------------

    def _switch_to_device(self, source: ActiveSource, index: int) -> None:
        previous = self.active_source
        self._close_active()

        self.active_device = CameraDevice(
            role=source.value,
            device_index=index,
            bus=self.bus,
            capture_factory=self.capture_factory
        )
        self.active_device.start()
        self.active_source = source
        self.active_index = index
        self._device_started_at = time.time()

        log.info("Active camera switched: %s on device #%d.", source.value, index)
        self._emit_switch(previous, source)

    def _emit_switch(self, from_src: ActiveSource, to_src: ActiveSource) -> None:
        self.bus.publish(Event(EventType.CAMERA_SWITCHED, {
            "from_source": from_src.value,
            "to_source": to_src.value,
            "active_index": self.active_index
        }, source="camera_supervisor"))

    def _close_active(self) -> None:
        if self.active_device:
            try:
                self.active_device.stop()
            except Exception:
                pass
            self.active_device = None
        self.active_index = None

    # ------------------------------------------------------------------
    # Frames
    # ------------------------------------------------------------------

    def get_frame(self) -> Optional[Frame]:
        if self._closed:
            return None
        now = time.time()

        self._apply_pending_choice()

        # Look for a better camera in the background; never probe a healthy phone
        if self.active_source != ActiveSource.PHONE and (now - self.last_discovery_time) > self.recheck_interval_sec:
            self.last_discovery_time = now
            self._start_background_discovery()

        if self.active_source == ActiveSource.KEYBOARD or self.active_device is None:
            return None

        if not self._device_healthy(self.active_device):
            log.warning("Active camera stream lost. Releasing it and searching again...")
            previous = self.active_source
            self._close_active()
            self.active_source = ActiveSource.KEYBOARD
            self._emit_switch(previous, ActiveSource.KEYBOARD)
            self.last_discovery_time = now
            self._start_background_discovery()
            return None

        raw_frame = self.active_device.get_frame()
        if raw_frame is None or raw_frame.image is None:
            return None

        self.measured_latency_ms = max(0.0, (now - raw_frame.timestamp) * 1000.0)

        final_image = raw_frame.image
        if self.rotation_degrees == 90:
            final_image = cv2.rotate(final_image, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation_degrees == 180:
            final_image = cv2.rotate(final_image, cv2.ROTATE_180)
        elif self.rotation_degrees == 270:
            final_image = cv2.rotate(final_image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        return Frame(
            image=final_image,
            timestamp=raw_frame.timestamp,
            frame_index=raw_frame.frame_index,
            width=final_image.shape[1],
            height=final_image.shape[0],
            camera_role=self.active_source.value
        )

    def set_rotation(self, degrees: int) -> None:
        if degrees in (0, 90, 180, 270):
            self.rotation_degrees = degrees

    def close(self) -> None:
        self._closed = True
        self._close_active()
        self.active_source = ActiveSource.KEYBOARD