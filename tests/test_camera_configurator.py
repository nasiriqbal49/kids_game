import unittest
from core.event_bus import EventBus
from tests.test_camera_manager import FakeVideoCapture
from vision.camera_configurator import CameraConfigurator, CameraRole


class FakeConfig:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value


class TestCameraConfigurator(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.cfg = FakeConfig()
        # Simulated 3-camera hardware setup: 0 = Laptop Webcam, 1 = Poco Front, 2 = Poco Side
        self.caps = {
            0: FakeVideoCapture(width=640, height=480, is_open=True),
            1: FakeVideoCapture(width=1280, height=720, is_open=True),
            2: FakeVideoCapture(width=1280, height=720, is_open=True),
            3: FakeVideoCapture(is_open=False),
        }
        self.configurator = CameraConfigurator(
            bus=self.bus,
            cfg=self.cfg,
            capture_factory=lambda idx: self.caps.get(idx)
        )

    def test_scan_devices_discovers_active_cameras(self):
        """Scans hardware indices and discovers all active cameras."""
        devices = self.configurator.scan_devices(max_to_test=4)
        self.assertEqual(len(devices), 3)  # Indices 0, 1, 2
        self.assertEqual(devices[0]["device_index"], 0)
        self.assertEqual(devices[1]["device_index"], 1)
        self.assertEqual(devices[2]["device_index"], 2)

    def test_assign_role_and_conflict_resolution(self):
        """Assigning a camera to a role resolves conflicts so one camera isn't used for two roles."""
        # Assign Camera 1 to FRONT
        self.configurator.assign_role(CameraRole.FRONT, device_index=1)
        self.assertEqual(self.configurator.get_assigned_device(CameraRole.FRONT), 1)

        # Assign Camera 2 to SIDE
        self.configurator.assign_role(CameraRole.SIDE, device_index=2)
        self.assertEqual(self.configurator.get_assigned_device(CameraRole.SIDE), 2)

        # Now re-assign Camera 1 to SIDE -> FRONT must be automatically unassigned (no conflict)
        self.configurator.assign_role(CameraRole.SIDE, device_index=1)
        self.assertEqual(self.configurator.get_assigned_device(CameraRole.SIDE), 1)
        self.assertIsNone(self.configurator.get_assigned_device(CameraRole.FRONT))

    def test_validate_setup_requires_front_camera(self):
        """Validation passes only when a FRONT tracker camera is assigned."""
        self.configurator.role_assignments[CameraRole.FRONT] = None
        valid, errors = self.configurator.validate_setup()
        self.assertFalse(valid)
        self.assertIn("FRONT", errors[0])

        # Assign FRONT
        self.configurator.assign_role(CameraRole.FRONT, device_index=1)
        valid, errors = self.configurator.validate_setup()
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_save_and_load_config_persistence(self):
        """Role bindings persist into configuration correctly."""
        self.configurator.assign_role(CameraRole.FRONT, device_index=1)
        self.configurator.assign_role(CameraRole.SIDE, device_index=2)
        self.configurator.assign_role(CameraRole.LAPTOP, device_index=0)

        self.configurator.save_to_config()

        # Create fresh configurator reading from same config
        new_conf = CameraConfigurator(bus=self.bus, cfg=self.cfg)
        self.assertEqual(new_conf.get_assigned_device(CameraRole.FRONT), 1)
        self.assertEqual(new_conf.get_assigned_device(CameraRole.SIDE), 2)
        self.assertEqual(new_conf.get_assigned_device(CameraRole.LAPTOP), 0)


if __name__ == "__main__":
    unittest.main()