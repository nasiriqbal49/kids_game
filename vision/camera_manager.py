import time
import threading
import cv2
import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("camera")


@dataclass(frozen=True)
class Frame:
    """Immutable timestamped video frame produced by a camera device."""
    image: np.ndarray
    timestamp: float
    frame_index: int
    width: int
    height: int
    camera_role: str


class CameraDevice:
    """
    Manages a single physical video capture device in a dedicated background
    acquisition thread (UC 09.01, 09.09).
    Never blocks the 60 FPS main game loop.
    """

    def __init__(self, role: str, device_index: int, width: int = 640, height: int = 480,
                 target_fps: int = 30, mirror: bool = True, bus: Optional[EventBus] = None,
                 capture_factory: Optional[Callable[[int], Any]] = None):
        self.role = role
        self.device_index = device_index
        self.target_width = width
        self.target_height = height
        self.target_fps = target_fps
        self.mirror = mirror
        self.bus = bus or get_event_bus()
        self.capture_factory = capture_factory or (lambda idx: cv2.VideoCapture(idx))

        # Capture instance and thread state
        self.cap: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._lock = threading.Lock()

        # Frame data
        self.latest_frame: Optional[Frame] = None
        self.frame_count: int = 0
        self.actual_width: int = width
        self.actual_height: int = height
        self.actual_fps: float = float(target_fps)

        # FPS monitoring & degradation control (UC 09.08)
        self.recent_frame_times = deque(maxlen=30)
        self.measured_fps: float = float(target_fps)
        self.low_fps_warned: bool = False

        # Connection health & stale frame detection (UC 09.03, 09.06)
        self.is_connected: bool = False
        self.stale_threshold_sec: float = 1.0
        self._reconnect_interval_sec: float = 2.0
        self._last_reconnect_attempt: float = 0.0

    def start(self) -> bool:
        """Opens capture and starts background capture worker (UC 09.01)."""
        self._running = True
        self._open_capture()

        self._thread = threading.Thread(target=self._capture_loop, name=f"CamThread_{self.role}", daemon=True)
        self._thread.start()
        return self.is_connected

    def _open_capture(self) -> bool:
        """Attempts to open physical or fake camera source (UC 09.01, 09.02, 09.05)."""
        try:
            self.cap = self.capture_factory(self.device_index)
            if self.cap is not None and self.cap.isOpened():
                # Configure resolution
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)

                # Read back actual capabilities (UC 09.01)
                self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or self.target_width
                self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or self.target_height
                self.actual_fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or float(self.target_fps)

                self.is_connected = True
                log.info("Camera [%s] opened on index %d: %dx%d @ %.1f FPS (mirror=%s) (UC 09.01).",
                         self.role, self.device_index, self.actual_width, self.actual_height,
                         self.actual_fps, self.mirror)

                self.bus.post(Event(EventType.CAMERA_CONNECTED, {
                    "camera_role": self.role,
                    "device_index": self.device_index,
                    "width": self.actual_width,
                    "height": self.actual_height,
                }, source="camera"))
                return True
            else:
                self.is_connected = False
                log.warning("Camera [%s] not found or busy in another app (UC 09.02, 09.05).", self.role)
                self.bus.post(Event(EventType.CAMERA_LOST, {
                    "camera_role": self.role,
                    "device_index": self.device_index,
                    "reason": "camera_busy_or_unavailable"
                }, source="camera"))
                return False
        except Exception as err:
            self.is_connected = False
            log.error("Failed opening camera [%s]: %s (UC 09.02, 09.05).", self.role, err)
            self.bus.post(Event(EventType.CAMERA_LOST, {
                "camera_role": self.role,
                "device_index": self.device_index,
                "reason": str(err)
            }, source="camera"))
            return False

    def _capture_loop(self) -> None:
        """Background acquisition loop running at target FPS."""
        frame_interval = 1.0 / max(10, self.target_fps)

        while self._running:
            start_t = time.time()

            if not self.is_connected or self.cap is None:
                # Retry loop if disconnected (UC 09.04)
                if (start_t - self._last_reconnect_attempt) >= self._reconnect_interval_sec:
                    self._last_reconnect_attempt = start_t
                    log.info("Attempting reconnect for camera [%s]...", self.role)
                    self._open_capture()
                time.sleep(0.1)
                continue

            # Read frame
            ret, raw_frame = self.cap.read()
            if not ret or raw_frame is None:
                log.warning("Camera [%s] lost stream / read failed (UC 09.03).", self.role)
                self.is_connected = False
                if self.cap:
                    self.cap.release()
                    self.cap = None
                self.bus.post(Event(EventType.CAMERA_LOST, {
                    "camera_role": self.role,
                    "device_index": self.device_index,
                    "reason": "stream_read_failed"
                }, source="camera"))
                continue

            # Mirror horizontally if requested (UC 09.12)
            if self.mirror:
                raw_frame = cv2.flip(raw_frame, 1)

            now = time.time()
            self.frame_count += 1
            self.recent_frame_times.append(now)

            # Update FPS measurement (UC 09.08)
            if len(self.recent_frame_times) >= 15:
                elapsed = self.recent_frame_times[-1] - self.recent_frame_times[0]
                if elapsed > 0:
                    self.measured_fps = len(self.recent_frame_times) / elapsed
                    self.check_fps_health()

            frame_obj = Frame(
                image=raw_frame,
                timestamp=now,
                frame_index=self.frame_count,
                width=raw_frame.shape[1],
                height=raw_frame.shape[0],
                camera_role=self.role
            )

            with self._lock:
                self.latest_frame = frame_obj

            elapsed_step = time.time() - start_t
            sleep_time = max(0.001, frame_interval - elapsed_step)
            time.sleep(sleep_time)

    def check_fps_health(self) -> None:
        """Low FPS degradation and automatic downscaling (UC 09.08)."""
        if self.measured_fps < (self.target_fps * 0.6) and not self.low_fps_warned:
            self.low_fps_warned = True
            log.warning("Camera [%s] FPS dropped to %.1f (< 60%% target). Triggering CAMERA_LOW_FPS (UC 09.08).",
                        self.role, self.measured_fps)
            self.bus.post(Event(EventType.CAMERA_LOW_FPS, {
                "camera_role": self.role,
                "actual_fps": round(self.measured_fps, 1),
                "target_fps": self.target_fps,
            }, source="camera"))

            # Step down resolution to reduce CPU / USB bandwidth pressure (UC 09.08)
            if self.target_width > 320:
                self.target_width = self.target_width // 2
                self.target_height = self.target_height // 2
                if self.cap:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                log.info("Auto-downscaled camera [%s] resolution to %dx%d (UC 09.08).",
                         self.role, self.target_width, self.target_height)

    def get_frame(self) -> Optional[Frame]:
        """Returns the most recent frame thread-safely."""
        with self._lock:
            return self.latest_frame

    def is_stale(self) -> bool:
        """Returns True if the frame stream has frozen (UC 09.06)."""
        frame = self.get_frame()
        if frame is None or not self.is_connected:
            return True
        return (time.time() - frame.timestamp) > self.stale_threshold_sec

    def stop(self) -> None:
        """Stops thread and releases hardware (UC 09.14)."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.is_connected = False
        log.info("Camera [%s] released cleanly (UC 09.14).", self.role)


class CameraManager:
    """
    Supervises video cameras, role mapping (front, side, laptop),
    bandwidth prioritization, and safe fallback to keyboard mode (Module 9).
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 capture_factory: Optional[Callable[[int], Any]] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.capture_factory = capture_factory

        self.devices: Dict[str, CameraDevice] = {}
        self._init_primary_camera()

    def _init_primary_camera(self) -> None:
        """Initializes primary front camera from config."""
        dev_idx = self.config.get("camera.camera_index", 0)
        width = self.config.get("camera.width", 640)
        height = self.config.get("camera.height", 480)
        fps = self.config.get("camera.target_fps", 30)
        mirror = self.config.get("camera.mirror", True)

        self.add_camera(role="front", device_index=dev_idx, width=width,
                        height=height, target_fps=fps, mirror=mirror)

    def add_camera(self, role: str, device_index: int, width: int = 640, height: int = 480,
                   target_fps: int = 30, mirror: bool = True) -> CameraDevice:
        """Registers and starts a camera device for a specific role (UC 09.01, 09.09)."""
        if role in self.devices:
            self.devices[role].stop()

        device = CameraDevice(
            role=role,
            device_index=device_index,
            width=width,
            height=height,
            target_fps=target_fps,
            mirror=mirror,
            bus=self.bus,
            capture_factory=self.capture_factory
        )
        self.devices[role] = device
        device.start()
        return device

    def prioritize_primary_camera(self) -> None:
        """
        USB bandwidth shortage protection (UC 09.10).
        If both front and side cameras are active, side camera resolution is
        stepped down to preserve primary tracking stability.
        """
        if "side" in self.devices:
            side_dev = self.devices["side"]
            log.warning("Prioritizing primary camera: lowering secondary side camera resolution (UC 09.10).")
            side_dev.target_width = 320
            side_dev.target_height = 240
            if side_dev.cap:
                side_dev.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                side_dev.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    @staticmethod
    def list_available_cameras(max_to_test: int = 4,
                               capture_factory: Optional[Callable[[int], Any]] = None) -> List[Dict[str, Any]]:
        """
        Discovers connected cameras across device indices (UC 09.07).
        Used by the Room & Camera Setup Configurator to list choices for user assignment.
        """
        found = []
        factory = capture_factory or (lambda idx: cv2.VideoCapture(idx))

        for idx in range(max_to_test):
            try:
                cap = factory(idx)
                if cap is not None and cap.isOpened():
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
                    found.append({
                        "device_index": idx,
                        "name": f"Camera {idx}",
                        "width": w,
                        "height": h
                    })
                    cap.release()
            except Exception:
                pass
        return found

    def get_frame(self, role: str = "front") -> Optional[Frame]:
        """Retrieves latest frame from a camera role."""
        device = self.devices.get(role)
        if device is not None:
            return device.get_frame()
        return None

    def is_available(self, role: str = "front") -> bool:
        """Returns True if the camera is connected and producing fresh frames."""
        device = self.devices.get(role)
        if device is not None:
            return device.is_connected and not device.is_stale()
        return False

    def close(self) -> None:
        """Shuts down all cameras cleanly (UC 09.14)."""
        for device in self.devices.values():
            device.stop()
        self.devices.clear()