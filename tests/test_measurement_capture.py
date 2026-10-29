import tempfile
import unittest
from pathlib import Path

from core.events import EventType
from core.event_bus import EventBus
from vision.pose_tracker import PoseResult, PoseLandmark
from identity.profile_manager import ProfileManager
from identity.measurement_capture import MeasurementCapture, MeasurementState


def make_test_pose(nose_y=0.20, ankle_y=0.80, hip_y=0.55, is_partial=False, arms_pinned=False):
    """Creates synthetic PoseResult with customizable vertical landmarks and arm span."""
    wrist_offset = 0.05 if arms_pinned else 0.20
    lms = {
        "nose": PoseLandmark(0, "nose", 0.50, nose_y, 0.0, 0.9),
        "left_shoulder": PoseLandmark(11, "left_shoulder", 0.42, hip_y - 0.20, 0.0, 0.9),
        "right_shoulder": PoseLandmark(12, "right_shoulder", 0.58, hip_y - 0.20, 0.0, 0.9),
        "left_wrist": PoseLandmark(15, "left_wrist", 0.50 - wrist_offset, hip_y - 0.10, 0.0, 0.9),
        "right_wrist": PoseLandmark(16, "right_wrist", 0.50 + wrist_offset, hip_y - 0.10, 0.0, 0.9),
        "left_hip": PoseLandmark(23, "left_hip", 0.45, hip_y, 0.0, 0.9),
        "right_hip": PoseLandmark(24, "right_hip", 0.55, hip_y, 0.0, 0.9),
        "left_ankle": PoseLandmark(27, "left_ankle", 0.46, ankle_y, 0.0, 0.9),
        "right_ankle": PoseLandmark(28, "right_ankle", 0.54, ankle_y, 0.0, 0.9),
    }
    return PoseResult(
        has_person=True,
        landmarks=lms,
        raw_landmarks=list(lms.values()),
        confidence=0.9,
        timestamp=100.0,
        is_partial=is_partial
    )


class TestMeasurementCapture(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.profile_mgr = ProfileManager(bus=self.bus, storage_dir=Path(self.temp_dir.name))
        self.capture = MeasurementCapture(bus=self.bus, profile_manager=self.profile_mgr)

        self.events_received = []
        for evt in (EventType.MEASUREMENT_STARTED, EventType.MEASUREMENT_DONE, EventType.MEASUREMENT_FAILED):
            self.bus.subscribe(evt, lambda e: self.events_received.append(e))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_16_01_guided_measurement_succeeds_and_saves_to_profile(self):
        """UC 16.01: 2.0s of steady superhero pose captures measurements and saves to profile."""
        profile = self.profile_mgr.create_profile("Lucas")
        self.assertTrue(self.capture.start_session(profile.profile_id))

        # Check MEASUREMENT_STARTED event
        started = [e for e in self.events_received if e.name == EventType.MEASUREMENT_STARTED]
        self.assertEqual(len(started), 1)

        # Feed 2.0s of steady frames
        pose = make_test_pose(nose_y=0.20, ankle_y=0.80, hip_y=0.55)
        for _ in range(5):
            feedback = self.capture.process_pose(pose, dt=0.5)

        # Transitions to jump test
        self.assertEqual(feedback.state, MeasurementState.WAITING_FOR_JUMP)
        self.assertEqual(feedback.measured_height_cm, 120.0)

    def test_16_02_partial_body_instructs_to_step_back(self):
        """UC 16.02: When head or feet are cut off (is_partial=True), instructs child to step back."""
        profile = self.profile_mgr.create_profile("Emma")
        self.capture.start_session(profile.profile_id)

        cut_off_pose = make_test_pose(nose_y=0.20, ankle_y=0.80, is_partial=True)
        feedback = self.capture.process_pose(cut_off_pose, dt=0.5)

        self.assertEqual(feedback.state, MeasurementState.WAITING_FOR_PLAYER)
        self.assertIn("Step back", feedback.instruction)

    def test_16_03_child_movement_resets_hold_timer(self):
        """UC 16.03: Fidgeting or jumping during superhero pose resets 2.0s hold timer."""
        profile = self.profile_mgr.create_profile("Oliver")
        self.capture.start_session(profile.profile_id)

        steady_pose = make_test_pose(hip_y=0.55)
        self.capture.process_pose(steady_pose, dt=0.5)
        feedback = self.capture.process_pose(steady_pose, dt=0.5)
        self.assertAlmostEqual(feedback.progress_pct, 0.50, places=1)

        # Sudden movement resets timer
        moving_pose = make_test_pose(hip_y=0.65)
        feedback_moving = self.capture.process_pose(moving_pose, dt=0.1)
        self.assertEqual(feedback_moving.progress_pct, 0.0)

    def test_16_04_three_failed_attempts_triggers_manual_fallback(self):
        """UC 16.04: If child cannot hold still after 3 attempts, switches to MANUAL_FALLBACK."""
        profile = self.profile_mgr.create_profile("FidgetyKid")
        self.capture.start_session(profile.profile_id)

        # Trigger 3 movement failures
        for i in range(3):
            self.capture.process_pose(make_test_pose(hip_y=0.50), dt=0.5)
            feedback = self.capture.process_pose(make_test_pose(hip_y=0.60 + i * 0.02), dt=0.1)

        self.assertEqual(feedback.state, MeasurementState.MANUAL_FALLBACK)
        self.assertIn("manually", feedback.instruction.lower())

    def test_16_05_child_walks_off_cancels_and_saves_nothing(self):
        """UC 16.05: If child walks away for 3.0s, session cancels and profile remains untouched."""
        profile = self.profile_mgr.create_profile("Liam")
        self.capture.start_session(profile.profile_id)

        empty_pose = PoseResult(has_person=False, landmarks={}, raw_landmarks=[], confidence=0.0, timestamp=10.0)
        feedback = self.capture.process_pose(empty_pose, dt=3.5)

        self.assertEqual(feedback.state, MeasurementState.CANCELLED)
        reloaded = self.profile_mgr.get_profile(profile.profile_id)
        self.assertEqual(len(reloaded.measurements), 0)

    def test_16_06_implausible_height_rejected_and_retried(self):
        """UC 16.06: Unrealistic heights (< 80cm or > 190cm) are rejected with a retry instruction."""
        profile = self.profile_mgr.create_profile("GiantChild")
        self.capture.start_session(profile.profile_id)

        # Tiny figure (span = 0.10 -> height = 20 cm < 80 cm)
        tiny_pose = make_test_pose(nose_y=0.40, ankle_y=0.50, hip_y=0.45)

        # 4 steps of 0.5s = 2.0s (completes the hold on the 4th step)
        feedbacks = []
        for _ in range(4):
            feedbacks.append(self.capture.process_pose(tiny_pose, dt=0.5))

        self.assertIn("failed", feedbacks[-1].instruction.lower())
        self.assertEqual(self.capture.failed_attempts, 1)

    def test_16_07_wrong_pose_arms_pinned_prompts_to_spread_arms(self):
        """UC 16.07: Child with arms pinned to sides is prompted to spread arms wide."""
        profile = self.profile_mgr.create_profile("PinnedArms")
        self.capture.start_session(profile.profile_id)

        pinned_pose = make_test_pose(arms_pinned=True)
        feedback = self.capture.process_pose(pinned_pose, dt=0.5)

        self.assertIn("Spread your arms", feedback.instruction)
        self.assertEqual(self.capture.hold_timer, 0.0)

    def test_16_08_test_jump_captures_personal_peak_rise_and_threshold(self):
        """UC 16.08: Test jump stage tracks personal peak rise and configures jump threshold."""
        profile = self.profile_mgr.create_profile("JumpingJack")
        self.capture.start_session(profile.profile_id)

        # Complete still superhero pose
        pose = make_test_pose(hip_y=0.55)
        for _ in range(5):
            feedback = self.capture.process_pose(pose, dt=0.5)
        self.assertEqual(feedback.state, MeasurementState.WAITING_FOR_JUMP)

        # Perform jump: hips rise from 0.55 to 0.40 (rise = 0.15)
        jump_pose = make_test_pose(hip_y=0.40)
        self.capture.process_pose(jump_pose, dt=0.1)

        # Land: hips return to 0.54
        landing_pose = make_test_pose(hip_y=0.54)
        feedback_done = self.capture.process_pose(landing_pose, dt=0.1)

        self.assertEqual(feedback_done.state, MeasurementState.CONFIRMING)
        reloaded = self.profile_mgr.get_profile(profile.profile_id)
        self.assertAlmostEqual(reloaded.measurements["jump_peak_rise"], 0.15, places=2)
        self.assertAlmostEqual(reloaded.measurements["jump_threshold"], 0.09, places=2)

    def test_16_09_manual_real_height_entry_calibrates_scale(self):
        """UC 16.09: Parent typing child's real height stores manual measurements successfully."""
        profile = self.profile_mgr.create_profile("ManualChild")
        self.capture.start_session(profile.profile_id)

        # Parent enters 125.0 cm manually
        success = self.capture.set_manual_height(125.0, standing_baseline_y=0.58)

        self.assertTrue(success)
        reloaded = self.profile_mgr.get_profile(profile.profile_id)
        self.assertEqual(reloaded.measurements["height_cm"], 125.0)
        self.assertTrue(reloaded.measurements["calibrated_manually"])


if __name__ == "__main__":
    unittest.main()