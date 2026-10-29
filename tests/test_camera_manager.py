import time
import unittest
import numpy as np
import cv2

from core.events import EventType
from core.event_bus import EventBus
from vision.camera_manager import CameraManager, CameraDevice


class FakeConfig:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


class FakeVideoCapture:
    """Simulates OpenCV VideoCapture device in memory (testability rule)."""

    def __init__(self, width=640, height=480, fps=30, is_open=True):
        self.width = width
        self.height = height
        self.fps = fps
        self._is_open = is_open
        self.fail_reads = False
        self.release_called = False

    def isOpened(self):
        return self._is_open

    def read(self):
        if not self._is_open or self.fail_reads:
            return False, None
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img[10:30, 10:30] = [255, 255, 255]
        return True, img

    def get(self, prop_id):
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            return float(self.width)
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return float(self.height)
        elif prop_id == cv2.CAP_PROP_FPS:
            return float(self.fps)
        return 0.0

    def set(self, prop_id, value):
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            self.width = int(value)
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            self.height = int(value)
        return True

    def release(self):
        self._is_open = False
        self.release_called = True


class TestCameraManager(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.cfg = FakeConfig({
            "camera.camera_index": 0,
            "camera.width": 640,
            "camera.height": 480,
            "camera.target_fps": 30,
            "camera.mirror": True,
        })
        self.events_received = []
        self.bus.subscribe(EventType.CAMERA_CONNECTED, lambda e: self.events_received.append(e))
        self.bus.subscribe(EventType.CAMERA_LOST, lambda e: self.events_received.append(e))
        self.bus.subscribe(EventType.CAMERA_LOW_FPS, lambda e: self.events_received.append(e))

    def test_09_01_camera_streams_timestamped_frames(self):
        """UC 09.01: Camera opens and produces timestamped frames in background thread."""
        fake_cap = FakeVideoCapture(width=640, height=480, fps=30)
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: fake_cap)

        time.sleep(0.08)
        self.bus.drain()

        frame = mgr.get_frame("front")
        self.assertIsNotNone(frame)
        self.assertEqual(frame.width, 640)
        self.assertEqual(frame.height, 480)
        self.assertGreater(frame.timestamp, 0.0)
        self.assertTrue(mgr.is_available("front"))

        mgr.close()

    def test_09_02_camera_not_found_publishes_camera_lost(self):
        """UC 09.02: Invalid camera index triggers CAMERA_LOST and flags unavailable."""
        fake_cap = FakeVideoCapture(is_open=False)
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: fake_cap)

        self.bus.drain()
        self.assertFalse(mgr.is_available("front"))
        lost_events = [e for e in self.events_received if e.name == EventType.CAMERA_LOST]
        self.assertGreaterEqual(len(lost_events), 1)

        mgr.close()

    def test_09_03_camera_unplugged_mid_stream_publishes_camera_lost(self):
        """UC 09.03: Camera read failure mid-stream dispatches CAMERA_LOST."""
        fake_cap = FakeVideoCapture(width=640, height=480, fps=30)
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: fake_cap)

        time.sleep(0.05)
        self.assertTrue(mgr.devices["front"].is_connected)

        fake_cap.fail_reads = True
        time.sleep(0.08)
        self.bus.drain()

        self.assertFalse(mgr.devices["front"].is_connected)
        lost_events = [e for e in self.events_received if e.name == EventType.CAMERA_LOST]
        self.assertGreaterEqual(len(lost_events), 1)

        mgr.close()

    def test_09_04_camera_reconnect_recovers_stream(self):
        """UC 09.04: Disconnected camera automatically reconnects when device becomes available."""
        fake_cap = FakeVideoCapture(width=640, height=480, fps=30)
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: fake_cap)

        device = mgr.devices["front"]
        device._reconnect_interval_sec = 0.05

        fake_cap.fail_reads = True
        time.sleep(0.06)
        self.assertFalse(device.is_connected)

        fake_cap.fail_reads = False
        fake_cap._is_open = True
        time.sleep(0.12)
        self.bus.drain()

        self.assertTrue(device.is_connected)
        mgr.close()

    def test_09_05_camera_busy_error_message(self):
        """UC 09.05: Camera in use / busy reports clear status."""
        fake_busy = FakeVideoCapture(is_open=False)
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: fake_busy)

        self.bus.drain()
        lost = [e for e in self.events_received if e.name == EventType.CAMERA_LOST]
        self.assertIn(lost[0].payload.get("reason"), ["camera_busy_or_unavailable", "device_not_found"])

        mgr.close()

    def test_09_06_stale_frame_detection(self):
        """UC 09.06: When a frame stops updating past threshold, it is flagged stale."""
        fake_cap = FakeVideoCapture(width=640, height=480, fps=30)
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: fake_cap)

        device = mgr.devices["front"]
        device.stale_threshold_sec = 0.05
        time.sleep(0.04)

        fake_cap.fail_reads = True
        time.sleep(0.08)

        self.assertTrue(device.is_stale())
        mgr.close()

    def test_09_07_list_available_cameras_probes_indices(self):
        """UC 09.07: list_available_cameras discovers connected hardware devices."""
        # Simulate camera 0 and camera 1 exist, camera 2 does not
        caps = {
            0: FakeVideoCapture(width=640, height=480, is_open=True),
            1: FakeVideoCapture(width=1280, height=720, is_open=True),
            2: FakeVideoCapture(is_open=False),
        }

        found = CameraManager.list_available_cameras(max_to_test=3, capture_factory=lambda idx: caps.get(idx))
        self.assertEqual(len(found), 2)
        self.assertEqual(found[0]["device_index"], 0)
        self.assertEqual(found[1]["device_index"], 1)
        self.assertEqual(found[1]["width"], 1280)

    def test_09_08_low_fps_dispatches_event_and_downscales(self):
        """UC 09.08: Measured FPS dropping below threshold fires CAMERA_LOW_FPS and downscales."""
        fake_cap = FakeVideoCapture(width=640, height=480, fps=30)
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: fake_cap)

        device = mgr.devices["front"]
        # Simulate slow measured FPS (12 FPS < 18 FPS threshold)
        device.measured_fps = 12.0
        device.check_fps_health()
        self.bus.drain()

        low_fps_events = [e for e in self.events_received if e.name == EventType.CAMERA_LOW_FPS]
        self.assertEqual(len(low_fps_events), 1)
        self.assertEqual(device.target_width, 320)  # Auto-downscaled from 640

        mgr.close()

    def test_09_09_two_cameras_running_concurrently(self):
        """UC 09.09: Multiple cameras (front and side) run concurrently in their own threads."""
        fake_front = FakeVideoCapture(width=640, height=480, fps=30)
        fake_side = FakeVideoCapture(width=1280, height=720, fps=30)

        caps = {0: fake_front, 1: fake_side}
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: caps[idx])
        mgr.add_camera(role="side", device_index=1, width=1280, height=720)

        time.sleep(0.08)
        self.bus.drain()

        frame_front = mgr.get_frame("front")
        frame_side = mgr.get_frame("side")

        self.assertIsNotNone(frame_front)
        self.assertIsNotNone(frame_side)
        self.assertEqual(frame_front.width, 640)
        self.assertEqual(frame_side.width, 1280)

        mgr.close()

    def test_09_10_secondary_camera_throttled_under_bandwidth_pressure(self):
        """UC 09.10: prioritize_primary_camera reduces secondary camera resolution."""
        fake_front = FakeVideoCapture(width=640, height=480)
        fake_side = FakeVideoCapture(width=1280, height=720)

        caps = {0: fake_front, 1: fake_side}
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: caps[idx])
        mgr.add_camera(role="side", device_index=1, width=1280, height=720)

        self.assertEqual(mgr.devices["side"].target_width, 1280)
        mgr.prioritize_primary_camera()
        self.assertEqual(mgr.devices["side"].target_width, 320)  # Downscaled

        mgr.close()

    def test_09_12_horizontal_mirroring(self):
        """UC 09.12: Mirror flag horizontally flips the frame."""
        fake_cap = FakeVideoCapture(width=640, height=480, fps=30)
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: fake_cap)

        time.sleep(0.08)
        frame = mgr.get_frame("front")
        self.assertIsNotNone(frame)

        # Original marker is at x=10:30. Horizontally flipped, it shifts to (width - 30):(width - 10).
        flipped_x_start = frame.width - 30
        flipped_x_end = frame.width - 10
        white_pixels_flipped = np.sum(frame.image[:, flipped_x_start:flipped_x_end])
        self.assertGreater(white_pixels_flipped, 0)

        # And the original left side (10:30) is now black (0)
        white_pixels_left = np.sum(frame.image[:, 10:30])
        self.assertEqual(white_pixels_left, 0)

        mgr.close()

    def test_09_14_clean_shutdown_releases_devices(self):
        """UC 09.14: close() stops background threads and releases video devices."""
        fake_cap = FakeVideoCapture()
        mgr = CameraManager(bus=self.bus, cfg=self.cfg, capture_factory=lambda idx: fake_cap)

        self.assertTrue(mgr.devices["front"]._thread.is_alive())
        mgr.close()

        self.assertFalse(mgr.devices.get("front", CameraDevice("front", 0)).is_connected)
        self.assertTrue(fake_cap.release_called)


if __name__ == "__main__":
    unittest.main()