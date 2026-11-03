import os
import time
from enum import Enum
from typing import Dict, Optional, Callable, Any
import cv2
import numpy as np

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from vision.camera_manager import CameraDevice, Frame

log = get_logger("camera_supervisor")


class ActiveSource(str, Enum):
    PHONE = "phone"      # Iriun Phone Webcam
    LAPTOP = "laptop"    # ThinkPad Built-in Webcam (Index 0)
    KEYBOARD = "keyboard"


class CameraSupervisor:
    """
    Supervises a single active camera stream with automatic priority:
    1. Iriun Phone Webcam (Auto-detected on Index 1, 2, or 3)
    2. Laptop Webcam (Fallback on Index 0)
    3. Keyboard Mode (If no cameras open)
    Only ONE camera stream is ever open in memory to prevent USB bus choke.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 capture_factory: Optional[Callable[[int], Any]] = None,
                 phone_index: Optional[int] = None, laptop_index: int = 0):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.capture_factory = capture_factory or (
            lambda idx: cv2.VideoCapture(idx, cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY)
        )

        self.laptop_index = laptop_index
        self.preferred_phone_index = phone_index if phone_index is not None else self.config.get("camera.camera_index", 2)
        self.rotation_degrees: int = self.config.get("camera.rotation", 0)

        self.active_source: ActiveSource = ActiveSource.KEYBOARD
        self.active_device: Optional[CameraDevice] = None
        self.active_index: Optional[int] = None

        self.stale_timeout_sec: float = 1.0
        self.measured_latency_ms: float = 0.0
        self.last_discovery_time: float = 0.0

        self.discover_and_connect()

    def discover_and_connect(self) -> ActiveSource:
        """
        Scans devices and connects to the highest priority camera available.
        Only keeps ONE active camera open.
        """
        previous_source = self.active_source

        # Probe for Iriun Phone Camera (preferred index, then indices 1 to 4)
        indices_to_test = [self.preferred_phone_index] + [i for i in (1, 2, 3, 4) if i != self.preferred_phone_index]
        found_phone_idx = None

        for idx in indices_to_test:
            if idx == self.laptop_index:
                continue
            try:
                cap = self.capture_factory(idx)
                if cap is not None and cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None:
                        found_phone_idx = idx
                        break
            except Exception:
                pass

        # Priority 1: Connect to Iriun Phone
        if found_phone_idx is not None:
            if self.active_index != found_phone_idx or self.active_source != ActiveSource.PHONE:
                self._switch_to_device(ActiveSource.PHONE, found_phone_idx)
            return self.active_source

        # Priority 2: Fallback to Laptop Webcam (Index 0)
        try:
            cap = self.capture_factory(self.laptop_index)
            if cap is not None and cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    if self.active_index != self.laptop_index or self.active_source != ActiveSource.LAPTOP:
                        self._switch_to_device(ActiveSource.LAPTOP, self.laptop_index)
                    return self.active_source
        except Exception:
            pass

        # Priority 3: Keyboard Fallback
        if self.active_source != ActiveSource.KEYBOARD:
            self._close_active()
            self.active_source = ActiveSource.KEYBOARD
            self._emit_switch(previous_source, ActiveSource.KEYBOARD)

        return self.active_source

    def evaluate_fallback_chain(self) -> ActiveSource:
        """Alias for discover_and_connect to maintain 100% test compatibility."""
        return self.discover_and_connect()



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

    def get_frame(self) -> Optional[Frame]:
        now = time.time()
        if (self.active_source != ActiveSource.PHONE) and (now - self.last_discovery_time > 2.5):
            self.last_discovery_time = now
            self.discover_and_connect()

        if self.active_source == ActiveSource.KEYBOARD or not self.active_device:
            return None

        if self.active_device.is_stale():
            log.warning("Active camera stream lost. Triggering fallback failover...")
            self.discover_and_connect()
            if not self.active_device:
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
        self._close_active()
        self.active_source = ActiveSource.KEYBOARD