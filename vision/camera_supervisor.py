import time
from enum import Enum
from typing import Dict, Optional, Callable, Any, Tuple
import cv2
import numpy as np

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from vision.camera_manager import CameraManager, CameraDevice, Frame

log = get_logger("camera_supervisor")


class ActiveSource(str, Enum):
    PHONE = "phone"
    LAPTOP = "laptop"
    KEYBOARD = "keyboard"


class CameraSupervisor:
    """
    Supervises multi-camera hierarchy, orientation locking, and the automatic
    fallback chain: Phone -> Laptop Webcam -> Keyboard (Module 17 - Milestone M4).
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 capture_factory: Optional[Callable[[int], Any]] = None,
                 phone_index: Optional[int] = None, laptop_index: int = 0):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.capture_factory = capture_factory

        # Indices
        self.phone_index = phone_index if phone_index is not None else self.config.get("camera.camera_index", 1)
        self.laptop_index = laptop_index

        # Rotation configuration: 0, 90, 180, 270 degrees (UC 17.09)
        self.rotation_degrees: int = self.config.get("camera.rotation", 0)

        # Active Source State
        self.active_source: ActiveSource = ActiveSource.KEYBOARD
        self.devices: Dict[str, CameraDevice] = {}

        # Latency & Health Tracking (UC 17.07)
        self.stale_timeout_sec: float = 0.80
        self.last_frame_timestamp: float = 0.0
        self.measured_latency_ms: float = 0.0

        self._init_devices()

    def _init_devices(self) -> None:
        """Initializes both phone and laptop devices (UC 17.01, 17.05)."""
        # 1. Primary Phone Camera
        if self.phone_index is not None and self.phone_index != self.laptop_index:
            self.devices["phone"] = CameraDevice(
                role="phone",
                device_index=self.phone_index,
                bus=self.bus,
                capture_factory=self.capture_factory
            )
            self.devices["phone"].start()

        # 2. Secondary Laptop Webcam (Standby / Backup)
        self.devices["laptop"] = CameraDevice(
            role="laptop",
            device_index=self.laptop_index,
            bus=self.bus,
            capture_factory=self.capture_factory
        )
        self.devices["laptop"].start()

        self.evaluate_fallback_chain()

    def evaluate_fallback_chain(self) -> ActiveSource:
        """
        Evaluates camera health and enforces the Fallback Chain:
        Phone -> Laptop -> Keyboard (UC 17.05).
        """
        previous_source = self.active_source
        new_source = ActiveSource.KEYBOARD

        # Priority 1: Phone Camera
        phone = self.devices.get("phone")
        if phone and phone.is_connected and not phone.is_stale():
            new_source = ActiveSource.PHONE

        # Priority 2: Laptop Webcam
        elif self.devices.get("laptop") and self.devices["laptop"].is_connected and not self.devices["laptop"].is_stale():
            new_source = ActiveSource.LAPTOP

        # Priority 3: Keyboard Fallback
        else:
            new_source = ActiveSource.KEYBOARD

        if new_source != previous_source:
            log.warning("Camera fallback chain transition: %s -> %s (UC 17.05).",
                        previous_source.value, new_source.value)
            self.active_source = new_source
            self.bus.publish(Event(EventType.CAMERA_SWITCHED, {
                "from_source": previous_source.value,
                "to_source": new_source.value,
                "phone_connected": phone.is_connected if phone else False,
                "laptop_connected": self.devices["laptop"].is_connected if "laptop" in self.devices else False
            }, source="camera_supervisor"))

        return self.active_source

    def get_frame(self) -> Optional[Frame]:
        """
        Retrieves frame from the highest-priority active camera source,
        applies orientation locking, and checks for stale stream failover (UC 17.03, 17.09).
        """
        self.evaluate_fallback_chain()

        if self.active_source == ActiveSource.KEYBOARD:
            return None

        device = self.devices.get(self.active_source.value)
        if not device:
            return None

        raw_frame = device.get_frame()
        if raw_frame is None or raw_frame.image is None:
            return None

        now = time.time()
        self.measured_latency_ms = max(0.0, (now - raw_frame.timestamp) * 1000.0)

        # Apply Orientation Lock (UC 17.09)
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
        """Sets fixed orientation lock (0, 90, 180, 270) (UC 17.09)."""
        if degrees in (0, 90, 180, 270):
            self.rotation_degrees = degrees
            log.info("Camera orientation locked to %d degrees (UC 17.09).", degrees)

    def close(self) -> None:
        """Stops all supervised cameras cleanly."""
        for dev in self.devices.values():
            dev.stop()
        self.devices.clear()
        self.active_source = ActiveSource.KEYBOARD