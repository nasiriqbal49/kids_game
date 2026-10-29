import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from core.events import EventType
from core.event_bus import EventBus
from vision.pose_tracker import PoseResult, PoseLandmark
from vision.zone_calibration import ZoneCalibrator, ZoneGeometry


def make_test_pose(foot_x=0.50, foot_y=0.85, nose_x=0.50, nose_y=0.20):
    """Creates synthetic PoseResult with specified foot and nose coordinates."""
    lms = {
        "nose": PoseLandmark(0, "nose", nose_x, nose_y, 0.0, 0.9),
        "left_ankle": PoseLandmark(27, "left_ankle", foot_x - 0.02, foot_y, 0.0, 0.9),
        "right_ankle": PoseLandmark(28, "right_ankle", foot_x + 0.02, foot_y, 0.0, 0.9),
        "left_hip": PoseLandmark(23, "left_hip", foot_x - 0.05, foot_y - 0.35, 0.0, 0.9),
        "right_hip": PoseLandmark(24, "right_hip", foot_x + 0.05, foot_y - 0.35, 0.0, 0.9),
    }
    return PoseResult(has_person=True, landmarks=lms, raw_landmarks=list(lms.values()),
                      confidence=0.9, timestamp=100.0)


class TestZoneCalibration(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.calibrator = ZoneCalibrator(bus=self.bus, calibration_dir=self.temp_dir.name)
        # Standard zone: x in [0.25, 0.75], y in [0.50, 0.98]
        self.calibrator.set_zone(min_x=0.25, max_x=0.75, min_y=0.50, max_y=0.98)

        self.events_received = []
        self.bus.subscribe(EventType.PLAYER_IN_ZONE, lambda e: self.events_received.append(e.name))
        self.bus.subscribe(EventType.PLAYER_OUT_OF_ZONE, lambda e: self.events_received.append(e.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_12_03_player_inside_zone(self):
        """UC 12.03: Player with feet in center of zone is evaluated as INSIDE."""
        pose = make_test_pose(foot_x=0.50, foot_y=0.75)
        state = self.calibrator.evaluate_player_zone(pose)
        self.assertEqual(state, "INSIDE")

    def test_12_04_player_at_edge_warning(self):
        """UC 12.04: Player feet within edge margin is evaluated as EDGE warning."""
        # Zone min_x is 0.25, edge_margin is 0.08. foot_x at 0.28 is near the edge.
        pose = make_test_pose(foot_x=0.28, foot_y=0.75)
        state = self.calibrator.evaluate_player_zone(pose)
        self.assertEqual(state, "EDGE")

    def test_12_05_player_outside_zone_dispatches_out_of_zone(self):
        """UC 12.05: Player feet outside boundaries dispatches PLAYER_OUT_OF_ZONE."""
        # foot_x at 0.15 is outside left boundary (0.25)
        pose_outside = make_test_pose(foot_x=0.15, foot_y=0.75)
        state = self.calibrator.evaluate_player_zone(pose_outside)

        self.assertEqual(state, "OUTSIDE")
        self.bus.drain()
        self.assertIn(EventType.PLAYER_OUT_OF_ZONE, self.events_received)

        # Player steps back inside -> dispatches PLAYER_IN_ZONE (UC 12.03)
        pose_inside = make_test_pose(foot_x=0.50, foot_y=0.75)
        state_in = self.calibrator.evaluate_player_zone(pose_inside)

        self.assertEqual(state_in, "INSIDE")
        self.bus.drain()
        self.assertIn(EventType.PLAYER_IN_ZONE, self.events_received)

    def test_12_08_jump_ignores_vertical_motion(self):
        """UC 12.08: Jumping up in the air does not falsely trigger leaving the zone."""
        pose_ground = make_test_pose(foot_x=0.50, foot_y=0.85)
        self.calibrator.evaluate_player_zone(pose_ground, is_jumping=False)

        # Airborne pose: feet y rose to 0.45 (above min_y 0.50), but is_jumping=True
        pose_airborne = make_test_pose(foot_x=0.50, foot_y=0.45)
        state = self.calibrator.evaluate_player_zone(pose_airborne, is_jumping=True)

        # Retains floor position, stays INSIDE
        self.assertEqual(state, "INSIDE")
        self.bus.drain()
        self.assertNotIn(EventType.PLAYER_OUT_OF_ZONE, self.events_received)

    def test_12_09_strong_lean_evaluates_feet_not_head(self):
        """UC 12.09: Strong upper body lean with feet planted in center stays INSIDE."""
        # Nose leaned far to x=0.10 (outside boundary), but feet are at x=0.50 (center)
        pose_lean = make_test_pose(foot_x=0.50, foot_y=0.75, nose_x=0.10, nose_y=0.30)
        state = self.calibrator.evaluate_player_zone(pose_lean)

        # Foot position decides: still INSIDE!
        self.assertEqual(state, "INSIDE")

    def test_12_01_save_and_load_calibration(self):
        """UC 12.01 / 12.10: Zone calibration persists to JSON keyed by camera role."""
        self.calibrator.set_zone(min_x=0.30, max_x=0.70, min_y=0.45, max_y=0.95, pixels_per_meter=340.0)
        saved_file = self.calibrator.save_calibration(camera_role="front")
        self.assertTrue(saved_file.exists())

        # Fresh calibrator loads saved values
        new_calibrator = ZoneCalibrator(bus=self.bus, calibration_dir=self.temp_dir.name)
        loaded = new_calibrator.load_calibration(camera_role="front")
        self.assertTrue(loaded)
        self.assertEqual(new_calibrator.zone.min_x, 0.30)
        self.assertEqual(new_calibrator.zone.max_x, 0.70)
        self.assertEqual(new_calibrator.zone.pixels_per_meter, 340.0)


if __name__ == "__main__":
    unittest.main()