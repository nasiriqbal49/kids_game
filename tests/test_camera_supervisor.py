import time
import unittest
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
        """When phone camera is healthy, it is assigned as ActiveSource.PHONE."""
        def factory(idx):
            if idx == 1:
                return FakeVideoCapture(width=1280, height=720, fps=30, is_open=True)
            elif idx == 0:
                return FakeVideoCapture(width=640, height=480, fps=30, is_open=True)
            return None

        supervisor = CameraSupervisor(
            bus=self.bus,
            capture_factory=factory,
            phone_index=1,
            laptop_index=0
        )

        time.sleep(0.08)
        self.assertEqual(supervisor.active_source, ActiveSource.PHONE)
        frame = supervisor.get_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.camera_role, "phone")
        supervisor.close()

    def test_17_02_phone_lost_falls_back_to_laptop_webcam(self):
        """Phone camera absent -> falls back cleanly to laptop webcam (Index 0)."""
        def factory(idx):
            if idx == 1:
                return FakeVideoCapture(is_open=False)
            elif idx == 0:
                return FakeVideoCapture(width=640, height=480, fps=30, is_open=True)
            return None

        supervisor = CameraSupervisor(
            bus=self.bus,
            capture_factory=factory,
            phone_index=1,
            laptop_index=0
        )

        time.sleep(0.08)
        self.assertEqual(supervisor.active_source, ActiveSource.LAPTOP)
        frame = supervisor.get_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.camera_role, "laptop")
        supervisor.close()

    def test_17_05_both_cameras_lost_falls_back_to_keyboard(self):
        """When both phone and laptop cameras fail, system falls back to KEYBOARD."""
        def factory(idx):
            return FakeVideoCapture(is_open=False)

        supervisor = CameraSupervisor(
            bus=self.bus,
            capture_factory=factory,
            phone_index=1,
            laptop_index=0
        )

        self.assertEqual(supervisor.active_source, ActiveSource.KEYBOARD)
        self.assertIsNone(supervisor.get_frame())
        supervisor.close()

    def test_17_05_phone_reconnect_promotes_back_to_primary(self):
        """Reconnecting phone promotes it back to ActiveSource.PHONE."""
        phone_online = [False]

        def factory(idx):
            if idx == 1:
                return FakeVideoCapture(width=1280, height=720, is_open=phone_online[0])
            elif idx == 0:
                return FakeVideoCapture(width=640, height=480, is_open=True)
            return None

        supervisor = CameraSupervisor(
            bus=self.bus,
            capture_factory=factory,
            phone_index=1,
            laptop_index=0
        )
        time.sleep(0.08)
        self.assertEqual(supervisor.active_source, ActiveSource.LAPTOP)

        # Phone plugged back in
        phone_online[0] = True
        supervisor.preferred_phone_index = 1
        supervisor.discover_and_connect()
        time.sleep(0.08)

        self.assertEqual(supervisor.active_source, ActiveSource.PHONE)
        supervisor.close()

    def test_17_09_orientation_lock_rotates_frame_90_degrees(self):
        """Orientation lock setting rotates frame 90 degrees."""
        def factory(idx):
            if idx == 1:
                return FakeVideoCapture(width=640, height=480, is_open=True)
            return FakeVideoCapture(is_open=False)

        supervisor = CameraSupervisor(
            bus=self.bus,
            capture_factory=factory,
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