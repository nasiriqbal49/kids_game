import unittest
from core.events import EventType
from core.event_bus import EventBus
from vision.pose_tracker import PoseResult, PoseLandmark
from vision.zone_calibration import ZoneCalibrator
from vision.player_lock import PlayerLock


def make_candidate_pose(foot_x=0.50, foot_y=0.85, shoulder_w=0.20, torso_h=0.35):
    """Creates synthetic candidate PoseResult with defined position and body proportions."""
    lms = {
        "nose": PoseLandmark(0, "nose", foot_x, 0.20, 0.0, 0.9),
        "left_shoulder": PoseLandmark(11, "left_shoulder", foot_x - shoulder_w / 2, 0.35, 0.0, 0.9),
        "right_shoulder": PoseLandmark(12, "right_shoulder", foot_x + shoulder_w / 2, 0.35, 0.0, 0.9),
        "left_hip": PoseLandmark(23, "left_hip", foot_x - 0.05, 0.35 + torso_h, 0.0, 0.9),
        "right_hip": PoseLandmark(24, "right_hip", foot_x + 0.05, 0.35 + torso_h, 0.0, 0.9),
        "left_ankle": PoseLandmark(27, "left_ankle", foot_x - 0.02, foot_y, 0.0, 0.9),
        "right_ankle": PoseLandmark(28, "right_ankle", foot_x + 0.02, foot_y, 0.0, 0.9),
    }
    return PoseResult(has_person=True, landmarks=lms, raw_landmarks=list(lms.values()),
                      confidence=0.9, timestamp=100.0)


class TestPlayerLock(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.lock = PlayerLock(bus=self.bus)
        self.calibrator = ZoneCalibrator(bus=self.bus)
        self.calibrator.set_zone(min_x=0.25, max_x=0.75, min_y=0.50, max_y=0.98)

        self.locked_events = []
        self.multi_events = []
        self.lost_events = []
        self.bus.subscribe(EventType.PLAYER_LOCKED, lambda e: self.locked_events.append(e))
        self.bus.subscribe(EventType.MULTIPLE_PEOPLE, lambda e: self.multi_events.append(e))
        self.bus.subscribe(EventType.PLAYER_LOST, lambda e: self.lost_events.append(e))

    def test_13_01_stable_presence_acquires_lock_after_half_second(self):
        """UC 13.01: Person standing in zone acquires lock after 0.5s stable presence."""
        child = make_candidate_pose(foot_x=0.50, foot_y=0.80)

        # 0.3s elapsed -> not locked yet
        res = self.lock.update([child], self.calibrator, dt=0.3)
        self.assertFalse(self.lock.is_locked)
        self.assertIsNone(res)

        # Another 0.3s elapsed (total 0.6s > 0.5s threshold) -> locked!
        res_locked = self.lock.update([child], self.calibrator, dt=0.3)
        self.assertTrue(self.lock.is_locked)
        self.assertIsNotNone(res_locked)

        self.bus.drain()
        self.assertEqual(len(self.locked_events), 1)

    def test_13_02_multiple_people_in_zone_locks_nearest_and_emits_event(self):
        """UC 13.02: Two people in zone emits MULTIPLE_PEOPLE and locks onto the center child."""
        child_center = make_candidate_pose(foot_x=0.50, foot_y=0.80)  # On center tile
        sibling_side = make_candidate_pose(foot_x=0.70, foot_y=0.80)  # Near edge

        # Advance past 0.5s with both candidates
        res = self.lock.update([sibling_side, child_center], self.calibrator, dt=0.6)

        self.assertTrue(self.lock.is_locked)
        self.assertAlmostEqual(self.lock.last_known_x, 0.50, places=1)  # Locked center child

        self.bus.drain()
        self.assertEqual(len(self.multi_events), 1)

    def test_13_03_passing_person_ignored_while_locked(self):
        """UC 13.03: Bystander/parent walking through frame does not steal active lock."""
        child = make_candidate_pose(foot_x=0.50, foot_y=0.80)
        self.lock.update([child], self.calibrator, dt=0.6)
        self.assertTrue(self.lock.is_locked)

        # Parent walks through outside the zone at x=0.10
        parent = make_candidate_pose(foot_x=0.10, foot_y=0.80, shoulder_w=0.40)
        active = self.lock.update([child, parent], self.calibrator, dt=0.1)

        # Still locked to child
        self.assertEqual(active, child)
        self.assertAlmostEqual(self.lock.last_known_x, 0.50, places=1)

    def test_13_04_brief_occlusion_holds_lock_for_two_seconds(self):
        """UC 13.04: Sibling blocking camera holds lock during 2.0s occlusion grace period."""
        child = make_candidate_pose(foot_x=0.50, foot_y=0.80)
        self.lock.update([child], self.calibrator, dt=0.6)
        self.assertTrue(self.lock.is_locked)

        # 1.0 second of complete occlusion (0 candidates)
        held = self.lock.update([], self.calibrator, dt=1.0)
        self.assertTrue(self.lock.is_locked)  # Held!
        self.assertIsNotNone(held)

        # Another 1.2s of occlusion (total 2.2s > 2.0s) -> lock released (UC 13.05)
        released = self.lock.update([], self.calibrator, dt=1.2)
        self.assertFalse(self.lock.is_locked)
        self.assertIsNone(released)

        self.bus.drain()
        self.assertEqual(len(self.lost_events), 1)

    def test_13_06_jump_out_of_frame_retains_lock(self):
        """UC 13.06: Player jumping high out of frame holds lock during air time."""
        child = make_candidate_pose(foot_x=0.50, foot_y=0.80)
        self.lock.update([child], self.calibrator, dt=0.6)

        # Jump air time: 0.5s of no landmarks
        airborne = self.lock.update([], self.calibrator, dt=0.5)
        self.assertTrue(self.lock.is_locked)
        self.assertIsNotNone(airborne)

    def test_13_08_proportions_tracking_prevents_swapping(self):
        """UC 13.08: Candidate matching prioritizes body proportions over raw position swaps."""
        # Child: shoulder_w = 0.16, torso_h = 0.32 (ratio = 0.5)
        child = make_candidate_pose(foot_x=0.48, shoulder_w=0.16, torso_h=0.32)
        self.lock.update([child], self.calibrator, dt=0.6)
        self.assertTrue(self.lock.is_locked)

        # Taller adult steps in at x=0.49: shoulder_w = 0.35, torso_h = 0.50 (ratio = 0.7)
        adult = make_candidate_pose(foot_x=0.49, shoulder_w=0.35, torso_h=0.50)
        child_shifted = make_candidate_pose(foot_x=0.53, shoulder_w=0.16, torso_h=0.32)

        # Tracker must match child_shifted, NOT the adult who is closer in x
        matched = self.lock.update([adult, child_shifted], self.calibrator, dt=0.1)
        self.assertEqual(matched, child_shifted)


if __name__ == "__main__":
    unittest.main()