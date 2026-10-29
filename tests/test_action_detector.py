import unittest
from core.events import EventType, Event
from core.event_bus import EventBus
from vision.pose_tracker import PoseResult, PoseLandmark
from vision.action_detector import ActionDetector


def make_pose_at(hip_y=0.60, shoulder_x=0.50, hip_x=0.50, wrists_up=False):
    """Creates synthetic PoseResult at specified vertical hip position and lean offset."""
    nose_y = hip_y - 0.35
    wrist_y = (nose_y - 0.10) if wrists_up else (hip_y - 0.10)

    lms = {
        "nose": PoseLandmark(0, "nose", shoulder_x, nose_y, 0.0, 0.9),
        "left_shoulder": PoseLandmark(11, "left_shoulder", shoulder_x - 0.08, hip_y - 0.20, 0.0, 0.9),
        "right_shoulder": PoseLandmark(12, "right_shoulder", shoulder_x + 0.08, hip_y - 0.20, 0.0, 0.9),
        "left_hip": PoseLandmark(23, "left_hip", hip_x - 0.05, hip_y, 0.0, 0.9),
        "right_hip": PoseLandmark(24, "right_hip", hip_x + 0.05, hip_y, 0.0, 0.9),
        "left_ankle": PoseLandmark(27, "left_ankle", hip_x - 0.03, hip_y + 0.30, 0.0, 0.9),
        "right_ankle": PoseLandmark(28, "right_ankle", hip_x + 0.03, hip_y + 0.30, 0.0, 0.9),
        "left_wrist": PoseLandmark(15, "left_wrist", shoulder_x - 0.10, wrist_y, 0.0, 0.9),
        "right_wrist": PoseLandmark(16, "right_wrist", shoulder_x + 0.10, wrist_y, 0.0, 0.9),
    }
    return PoseResult(has_person=True, landmarks=lms, raw_landmarks=list(lms.values()),
                      confidence=0.9, timestamp=100.0)


class TestActionDetector(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.detector = ActionDetector(bus=self.bus)
        self.events_received = []

        for evt in (EventType.JUMP, EventType.LAND, EventType.DUCK, EventType.STAND,
                    EventType.LEAN_LEFT, EventType.LEAN_RIGHT, EventType.LEAN_CENTER,
                    EventType.HANDS_UP):
            self.bus.subscribe(evt, lambda e: self.events_received.append(e.name))

    def test_14_01_real_jump_emits_jump_then_land(self):
        """UC 14.01: Fast vertical rise emits JUMP, followed by LAND on return to baseline."""
        # 1. Establish baseline at hip_y = 0.60
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)

        # 2. Fast upward jump: hip_y rises from 0.60 to 0.45 in 0.08s (vel > 0.20)
        self.detector.process_pose(make_pose_at(hip_y=0.45), timestamp=10.08)
        self.bus.drain()
        self.assertIn(EventType.JUMP, self.events_received)
        self.assertTrue(self.detector.is_airborne)

        # 3. Landing: hip_y returns near baseline at 0.58
        self.detector.process_pose(make_pose_at(hip_y=0.58), timestamp=10.40)
        self.bus.drain()
        self.assertIn(EventType.LAND, self.events_received)
        self.assertFalse(self.detector.is_airborne)

    def test_14_02_small_hop_below_threshold_ignored(self):
        """UC 14.02: Tiny vertical bounce below jump threshold does not trigger JUMP."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)

        # Tiny rise of only 0.015 (threshold is ~0.055)
        self.detector.process_pose(make_pose_at(hip_y=0.585), timestamp=10.05)
        self.bus.drain()
        self.assertNotIn(EventType.JUMP, self.events_received)

    def test_14_03_slow_weight_shift_does_not_jump(self):
        """UC 14.03: Slow weight shifting or walking does not meet velocity threshold and avoids false jump."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)

        # Slow rise over 2 full seconds (velocity is tiny, 0.05 < 0.20)
        self.detector.process_pose(make_pose_at(hip_y=0.50), timestamp=12.00)
        self.bus.drain()
        self.assertNotIn(EventType.JUMP, self.events_received)

    def test_14_05_two_quick_jumps_require_land_between(self):
        """UC 14.05: Jump while already airborne is ignored until LAND occurs."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_y=0.45), timestamp=10.05)  # Jump 1
        self.bus.drain()
        self.assertEqual(self.events_received.count(EventType.JUMP), 1)

        # Second jump impulse while still in air
        self.detector.process_pose(make_pose_at(hip_y=0.42), timestamp=10.15)
        self.bus.drain()
        self.assertEqual(self.events_received.count(EventType.JUMP), 1)  # Still only 1 jump

    def test_14_06_duck_and_stand_on_rise(self):
        """UC 14.06: Lowering body emits DUCK; rising back up emits STAND."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)

        # Lower body downwards (hip_y drops to 0.72)
        self.detector.process_pose(make_pose_at(hip_y=0.72), timestamp=10.10)
        self.bus.drain()
        self.assertIn(EventType.DUCK, self.events_received)
        self.assertTrue(self.detector.is_ducking)

        # Rise back up to 0.62
        self.detector.process_pose(make_pose_at(hip_y=0.62), timestamp=10.50)
        self.bus.drain()
        self.assertIn(EventType.STAND, self.events_received)
        self.assertFalse(self.detector.is_ducking)

    def test_14_07_lean_left_right_center_with_hysteresis(self):
        """UC 14.07: Torso tilt enters lean at higher threshold and exits at lower hysteresis bound."""
        self.detector.process_pose(make_pose_at(hip_x=0.50, shoulder_x=0.50), timestamp=10.00)

        # Tilt Left past enter threshold (-0.07 < -0.055)
        self.detector.process_pose(make_pose_at(hip_x=0.50, shoulder_x=0.43), timestamp=10.05)
        self.bus.drain()
        self.assertIn(EventType.LEAN_LEFT, self.events_received)

        # Small return to -0.04 stays LEAN_LEFT (hysteresis bound is -0.025)
        self.detector.process_pose(make_pose_at(hip_x=0.50, shoulder_x=0.46), timestamp=10.10)
        self.bus.drain()
        self.assertEqual(self.detector.current_lean, EventType.LEAN_LEFT)

        # Return to center (dx = -0.01 > -0.025)
        self.detector.process_pose(make_pose_at(hip_x=0.50, shoulder_x=0.49), timestamp=10.15)
        self.bus.drain()
        self.assertIn(EventType.LEAN_CENTER, self.events_received)

    def test_14_08_player_lost_resets_neutral_posture(self):
        """UC 14.08: PLAYER_LOST event immediately resets duck and lean to neutral."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_y=0.72), timestamp=10.05)  # Ducking
        self.bus.drain()
        self.assertTrue(self.detector.is_ducking)

        # Player lost event emitted
        self.bus.publish(Event(EventType.PLAYER_LOST))
        self.bus.drain()

        self.assertFalse(self.detector.is_ducking)
        self.assertIn(EventType.STAND, self.events_received)

    def test_14_13_hands_up_does_not_trigger_jump(self):
        """UC 14.13: Raising arms emits HANDS_UP and never triggers a false JUMP."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)

        # Wrists above nose while hips stay firmly at 0.60
        pose_hands_up = make_pose_at(hip_y=0.60, wrists_up=True)
        self.detector.process_pose(pose_hands_up, timestamp=10.05)
        self.bus.drain()

        self.assertIn(EventType.HANDS_UP, self.events_received)
        self.assertNotIn(EventType.JUMP, self.events_received)

    def test_14_14_stuck_duck_auto_resets_after_five_seconds(self):
        """UC 14.14: Remaining in duck state for 5 seconds automatically resets to STAND."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_y=0.72), timestamp=10.05)  # Ducking
        self.bus.drain()
        self.assertTrue(self.detector.is_ducking)

        # Advance past 5 seconds while still ducking
        self.detector.process_pose(make_pose_at(hip_y=0.72), timestamp=15.50)
        self.bus.drain()

        self.assertFalse(self.detector.is_ducking)
        self.assertIn(EventType.STAND, self.events_received)


if __name__ == "__main__":
    unittest.main()