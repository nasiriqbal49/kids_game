import os
import tempfile
import unittest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from core.events import EventType
from core.event_bus import EventBus
from projection.projector_manager import ProjectorManager, ProjectionMode


class TestProjectorManager(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.bus = EventBus()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mgr = ProjectorManager(bus=self.bus, calibration_dir=Path(self.temp_dir.name))

        self.events_received = []
        self.bus.subscribe(EventType.GAME_PAUSE, lambda e: self.events_received.append(e))

    def tearDown(self):
        self.temp_dir.cleanup()
        pygame.quit()

    def test_19_01_projector_connection_check(self):
        """UC 19.01: Checks if display index 2 (projector) is present."""
        # 2 displays (TV + Laptop) -> Projector not connected
        self.assertFalse(self.mgr.check_projector_connection(num_displays=2))

        # 3 displays (Laptop + TV + Projector) -> Projector connected!
        self.assertTrue(self.mgr.check_projector_connection(num_displays=3))

    def test_19_02_keystone_calibration_and_warping(self):
        """UC 19.02: 4-corner keystone calibration computes homography matrix."""
        self.mgr.set_keystone_corners(
            tl=(50, 50),
            tr=(750, 50),
            br=(800, 550),
            bl=(0, 550)
        )

        self.assertIsNotNone(self.mgr.homography_matrix)
        self.assertEqual(self.mgr.homography_matrix.shape, (3, 3))

        # Warp a surface without error
        surf = pygame.Surface((800, 600))
        warped = self.mgr.warp_for_floor(surf)
        self.assertEqual(warped.get_size(), (800, 600))

    def test_19_07_projector_disconnect_in_hybrid_mode_triggers_pause(self):
        """UC 19.07: Pulling projector cable in Hybrid mode pauses game safely."""
        self.mgr.mode = ProjectionMode.HYBRID
        # Connected with 3 screens
        self.mgr.check_projector_connection(num_displays=3)
        self.assertTrue(self.mgr.is_projector_connected)

        # Cable pulled -> drops to 2 screens
        self.mgr.check_projector_connection(num_displays=2)
        self.assertFalse(self.mgr.is_projector_connected)

        # Dispatches GAME_PAUSE
        pause_events = [e for e in self.events_received if e.name == EventType.GAME_PAUSE]
        self.assertEqual(len(pause_events), 1)
        self.assertEqual(pause_events[0].payload["reason"], "projector_disconnect")

    def test_19_11_save_and_load_calibration(self):
        """UC 19.11: Projector settings and corner coordinates persist to JSON."""
        self.mgr.mode = ProjectionMode.HYBRID
        self.mgr.set_keystone_corners(tl=(80, 80), tr=(720, 80), br=(780, 520), bl=(20, 520))

        # Load fresh instance
        new_mgr = ProjectorManager(bus=self.bus, calibration_dir=Path(self.temp_dir.name))
        self.assertEqual(new_mgr.keystone.top_left, (80, 80))
        self.assertEqual(new_mgr.mode, ProjectionMode.HYBRID)


if __name__ == "__main__":
    unittest.main()