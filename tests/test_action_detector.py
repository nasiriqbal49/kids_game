import unittest
from core.events import EventType, Event
from core.event_bus import EventBus
from vision.pose_tracker import PoseResult, PoseLandmark
from vision.action_detector import ActionDetector


def make_pose_at(hip_y=0.60, shoulder_x=0.50, hip_x=0.50, wrists_up=False,
                 l_elbow_y=0.45, r_elbow_y=0.45, l_ankle_y=0.90, r_ankle_y=0.90,
                 wrist_x=0.50, ankle_x=None):
    """Creates synthetic PoseResult with customizable joints for testing all gestures."""
    nose_y = hip_y - 0.35
    wrist_y = (nose_y - 0.10) if wrists_up else (hip_y - 0.10)
    ank_x = ankle_x if ankle_x is not None else hip_x

    lms = {
        "nose": PoseLandmark(0, "nose", shoulder_x, nose_y, 0.0, 0.9),
        "left_shoulder": PoseLandmark(11, "left_shoulder", shoulder_x - 0.08, hip_y - 0.20, 0.0, 0.9),
        "right_shoulder": PoseLandmark(12, "right_shoulder", shoulder_x + 0.08, hip_y - 0.20, 0.0, 0.9),
        "left_elbow": PoseLandmark(13, "left_elbow", shoulder_x - 0.15, l_elbow_y, 0.0, 0.9),
        "right_elbow": PoseLandmark(14, "right_elbow", shoulder_x + 0.15, r_elbow_y, 0.0, 0.9),
        "left_hip": PoseLandmark(23, "left_hip", hip_x - 0.05, hip_y, 0.0, 0.9),
        "right_hip": PoseLandmark(24, "right_hip", hip_x + 0.05, hip_y, 0.0, 0.9),
        "left_ankle": PoseLandmark(27, "left_ankle", ank_x - 0.03, l_ankle_y, 0.0, 0.9),
        "right_ankle": PoseLandmark(28, "right_ankle", ank_x + 0.03, r_ankle_y, 0.0, 0.9),
        "left_wrist": PoseLandmark(15, "left_wrist", wrist_x - 0.08, wrist_y, 0.0, 0.9),
        "right_wrist": PoseLandmark(16, "right_wrist", wrist_x + 0.08, wrist_y, 0.0, 0.9),
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
                    EventType.HANDS_UP, EventType.CHICKEN_FLAP, EventType.FART_BLAST,
                    EventType.FLAMINGO_BALANCE, EventType.TICKLE_SWAT):
            self.bus.subscribe(evt, lambda e: self.events_received.append(e.name))

    def test_14_01_real_jump_emits_jump_then_land(self):
        """UC 14.01: Fast vertical rise emits JUMP, followed by LAND on return to baseline."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_y=0.45), timestamp=10.08)
        self.bus.drain()
        self.assertIn(EventType.JUMP, self.events_received)
        self.assertTrue(self.detector.is_airborne)

        self.detector.process_pose(make_pose_at(hip_y=0.59), timestamp=10.60)
        self.bus.drain()
        self.assertIn(EventType.LAND, self.events_received)
        self.assertFalse(self.detector.is_airborne)

    def test_14_02_small_hop_below_threshold_ignored(self):
        """UC 14.02: Tiny vertical bounce below jump threshold does not trigger JUMP."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_y=0.588), timestamp=10.05)
        self.bus.drain()
        self.assertNotIn(EventType.JUMP, self.events_received)

    def test_14_03_slow_weight_shift_does_not_jump(self):
        """UC 14.03: Slow weight shifting over 2s does not trigger false jump."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_y=0.50), timestamp=12.00)
        self.bus.drain()
        self.assertNotIn(EventType.JUMP, self.events_received)

    def test_14_05_two_quick_jumps_require_land_between(self):
        """UC 14.05: Jump while already airborne is ignored until LAND occurs."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_y=0.45), timestamp=10.05)
        self.bus.drain()
        self.assertEqual(self.events_received.count(EventType.JUMP), 1)

        self.detector.process_pose(make_pose_at(hip_y=0.42), timestamp=10.15)
        self.bus.drain()
        self.assertEqual(self.events_received.count(EventType.JUMP), 1)

    def test_14_06_duck_and_stand_on_rise(self):
        """UC 14.06: Lowering body emits DUCK; rising back up emits STAND."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_y=0.72), timestamp=10.10)
        self.bus.drain()
        self.assertIn(EventType.DUCK, self.events_received)
        self.assertTrue(self.detector.is_ducking)

        self.detector.process_pose(make_pose_at(hip_y=0.62), timestamp=10.50)
        self.bus.drain()
        self.assertIn(EventType.STAND, self.events_received)
        self.assertFalse(self.detector.is_ducking)

    def test_14_07_lean_left_right_center_with_hysteresis(self):
        """UC 14.07: Torso tilt enters lean and exits with hysteresis."""
        self.detector.process_pose(make_pose_at(hip_x=0.50, shoulder_x=0.50), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_x=0.50, shoulder_x=0.44), timestamp=10.05)
        self.bus.drain()
        self.assertIn(EventType.LEAN_LEFT, self.events_received)

        self.detector.process_pose(make_pose_at(hip_x=0.50, shoulder_x=0.49), timestamp=10.15)
        self.bus.drain()
        self.assertIn(EventType.LEAN_CENTER, self.events_received)

    def test_14_08_player_lost_resets_neutral_posture(self):
        """UC 14.08: PLAYER_LOST event immediately resets duck and lean to neutral."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_y=0.72), timestamp=10.05)
        self.bus.drain()
        self.assertTrue(self.detector.is_ducking)

        self.bus.publish(Event(EventType.PLAYER_LOST))
        self.bus.drain()
        self.assertFalse(self.detector.is_ducking)
        self.assertIn(EventType.STAND, self.events_received)

    def test_14_13_hands_up_does_not_trigger_jump(self):
        """UC 14.13: Raising arms emits HANDS_UP and never triggers JUMP."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        pose_hands_up = make_pose_at(hip_y=0.60, wrists_up=True)
        self.detector.process_pose(pose_hands_up, timestamp=10.05)
        self.bus.drain()
        self.assertIn(EventType.HANDS_UP, self.events_received)
        self.assertNotIn(EventType.JUMP, self.events_received)

    def test_14_14_stuck_duck_auto_resets_after_five_seconds(self):
        """UC 14.14: Remaining in duck state for 5 seconds automatically resets to STAND."""
        self.detector.process_pose(make_pose_at(hip_y=0.60), timestamp=10.00)
        self.detector.process_pose(make_pose_at(hip_y=0.72), timestamp=10.05)
        self.bus.drain()
        self.assertTrue(self.detector.is_ducking)

        self.detector.process_pose(make_pose_at(hip_y=0.72), timestamp=15.50)
        self.bus.drain()
        self.assertFalse(self.detector.is_ducking)
        self.assertIn(EventType.STAND, self.events_received)

    # -------------------------------------------------------------
    # COMEDIC GESTURE UNIT TESTS
    # -------------------------------------------------------------

    def test_comedic_chicken_flap_detected(self):
        """Flapping elbows up and down emits CHICKEN_FLAP (wing glide flight)."""
        # Baseline establishment
        self.detector.process_pose(make_pose_at(l_elbow_y=0.50, r_elbow_y=0.50), timestamp=10.00)
        # Flap 1: Up then Down
        self.detector.process_pose(make_pose_at(l_elbow_y=0.40, r_elbow_y=0.40), timestamp=10.15)
        self.detector.process_pose(make_pose_at(l_elbow_y=0.50, r_elbow_y=0.50), timestamp=10.25)
        # Flap 2: Up
        self.detector.process_pose(make_pose_at(l_elbow_y=0.40, r_elbow_y=0.40), timestamp=10.40)
        self.bus.drain()
        self.assertIn(EventType.CHICKEN_FLAP, self.events_received)

    def test_comedic_fart_blast_detected(self):
        """Sideways hip-shift combined with crouch emits FART_BLAST."""
        self.detector.process_pose(make_pose_at(hip_y=0.60, hip_x=0.50, ankle_x=0.50), timestamp=10.00)
        fart_pose = make_pose_at(hip_y=0.66, hip_x=0.60, ankle_x=0.50)
        self.detector.process_pose(fart_pose, timestamp=10.10)
        self.bus.drain()
        self.assertIn(EventType.FART_BLAST, self.events_received)

    def test_comedic_flamingo_balance_detected(self):
        """Lifting one ankle up while standing on one leg for 1.0s emits FLAMINGO_BALANCE."""
        self.detector.process_pose(make_pose_at(), timestamp=10.00)
        flamingo_pose = make_pose_at(l_ankle_y=0.75, r_ankle_y=0.90)

        self.detector.process_pose(flamingo_pose, timestamp=10.50)
        self.bus.drain()
        self.assertNotIn(EventType.FLAMINGO_BALANCE, self.events_received)

        self.detector.process_pose(flamingo_pose, timestamp=11.20)
        self.bus.drain()
        self.assertIn(EventType.FLAMINGO_BALANCE, self.events_received)

    def test_comedic_tickle_swat_detected(self):
        """Waving wrists horizontally back and forth emits TICKLE_SWAT."""
        self.detector.process_pose(make_pose_at(wrist_x=0.50), timestamp=10.00)
        # 3 side-to-side wrist sweeps
        self.detector.process_pose(make_pose_at(wrist_x=0.40), timestamp=10.10)
        self.detector.process_pose(make_pose_at(wrist_x=0.55), timestamp=10.20)
        self.detector.process_pose(make_pose_at(wrist_x=0.40), timestamp=10.30)
        self.bus.drain()
        self.assertIn(EventType.TICKLE_SWAT, self.events_received)


if __name__ == "__main__":
    unittest.main()