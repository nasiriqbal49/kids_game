import time
import unittest
import numpy as np

from core.events import EventType
from core.event_bus import EventBus
from tests.test_camera_manager import FakeVideoCapture
from vision.camera_supervisor import CameraSupervisor, ActiveSource


class TestCameraSupervisor(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.events_received = []
        self.bus.subscribe(EventType.CAMERA_SWITCHED, lambda e: self.events_received.append(e))

    def test_17_01_phone_primary_selected_when_available(self):
        """UC 17.01: When phone camera is healthy, it is assigned as ActiveSource.PHONE."""
        caps = {
            1: FakeVideoCapture(width=1280, height=720, fps=30, is_open=True),
            0: FakeVideoCapture(width=640, height=480, fps=30, is_open=True),
        }

        supervisor = CameraSupervisor(
            bus=self.bus,
            capture_factory=lambda idx: caps.get(idx),
            phone_index=1,
            laptop_index=0
        )

        time.sleep(0.08)
        source = supervisor.evaluate_fallback_chain()

        self.assertEqual(source, ActiveSource.PHONE)
        frame = supervisor.get_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.camera_role, "phone")
        supervisor.close()

    def test_17_02_phone_lost_falls_back_to_laptop_webcam(self):
        """UC 17.02 / 17.05: Phone disconnects -> falls back cleanly to laptop webcam."""
        phone_cap = FakeVideoCapture(width=1280, height=720, is_open=True)
        laptop_cap = FakeVideoCapture(width=640, height=480, is_open=True)
        caps = {1: phone_cap, 0: laptop_cap}

        supervisor = CameraSupervisor(
            bus=self.bus,
            capture_factory=lambda idx: caps.get(idx),
            phone_index=1,
            laptop_index=0
        )

        time.sleep(0.08)
        self.assertEqual(supervisor.evaluate_fallback_chain(), ActiveSource.PHONE)

        # Simulate phone unplugged / app closed
        phone_cap.fail_reads = True
        supervisor.devices["phone"].is_connected = False

        # Evaluate fallback chain -> falls back to laptop!
        source = supervisor.evaluate_fallback_chain()
        self.assertEqual(source, ActiveSource.LAPTOP)

        frame = supervisor.get_frame()
        self.assertEqual(frame.camera_role, "laptop")

        # Check CAMERA_SWITCHED event was published
        self.bus.drain()
        switched = [e for e in self.events_received if e.name == EventType.CAMERA_SWITCHED]
        self.assertGreaterEqual(len(switched), 1)
        self.assertEqual(switched[-1].payload["to_source"], "laptop")

        supervisor.close()

    def test_17_05_both_cameras_lost_falls_back_to_keyboard(self):
        """UC 17.05: When both phone and laptop cameras fail, system falls back to KEYBOARD."""
        phone_cap = FakeVideoCapture(is_open=False)
        laptop_cap = FakeVideoCapture(is_open=False)
        caps = {1: phone_cap, 0: laptop_cap}

        supervisor = CameraSupervisor(
            bus=self.bus,
            capture_factory=lambda idx: caps.get(idx),
            phone_index=1,
            laptop_index=0
        )

        source = supervisor.evaluate_fallback_chain()
        self.assertEqual(source, ActiveSource.KEYBOARD)
        self.assertIsNone(supervisor.get_frame())

        supervisor.close()

    def test_17_05_phone_reconnect_promotes_back_to_primary(self):
        """UC 17.05: Reconnecting phone promotes it back to ActiveSource.PHONE."""
        phone_cap = FakeVideoCapture(is_open=False)
        laptop_cap = FakeVideoCapture(is_open=True)
        caps = {1: phone_cap, 0: laptop_cap}

        supervisor = CameraSupervisor(
            bus=self.bus,
            capture_factory=lambda idx: caps.get(idx),
            phone_index=1,
            laptop_index=0
        )

        time.sleep(0.08)
        # Starts on laptop
        self.assertEqual(supervisor.evaluate_fallback_chain(), ActiveSource.LAPTOP)

        # Phone plugged back in
        phone_cap._is_open = True
        phone_cap.fail_reads = False
        supervisor.devices["phone"].is_connected = True
        time.sleep(0.08)

        # Re-evaluates -> promoted back to phone!
        source = supervisor.evaluate_fallback_chain()
        self.assertEqual(source, ActiveSource.PHONE)

        supervisor.close()

    def test_17_09_orientation_lock_rotates_frame_90_degrees(self):
        """UC 17.09: Orientation setting rotates frame 90 degrees cleanly."""
        cap = FakeVideoCapture(width=640, height=480, is_open=True)
        caps = {1: cap, 0: FakeVideoCapture(is_open=False)}

        supervisor = CameraSupervisor(
            bus=self.bus,
            capture_factory=lambda idx: caps.get(idx),
            phone_index=1,
            laptop_index=0
        )

        time.sleep(0.08)
        supervisor.set_rotation(90)

        frame = supervisor.get_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.width, 480)
        self.assertEqual(frame.height, 640)

        supervisor.close()


if __name__ == "__main__":
    unittest.main()