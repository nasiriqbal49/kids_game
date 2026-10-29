import unittest
import numpy as np
from types import SimpleNamespace

from core.events import EventType
from core.event_bus import EventBus
from vision.pose_tracker import PoseTracker, LANDMARK_NAMES


def make_mock_landmarks(nose_y=0.2, nose_vis=0.9, ankle_y=0.8, ankle_vis=0.9, avg_vis=0.8):
    """Creates a synthetic MediaPipe landmark list for unit testing."""
    landmarks = []
    for i in range(33):
        vis = avg_vis
        y = 0.5
        if i == 0:  # Nose
            y = nose_y
            vis = nose_vis
        elif i in (27, 28):  # Ankles
            y = ankle_y
            vis = ankle_vis

        lm = SimpleNamespace(x=0.5, y=y, z=0.0, visibility=vis)
        landmarks.append(lm)

    return SimpleNamespace(pose_landmarks=SimpleNamespace(landmark=landmarks))


class TestPoseTracker(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.events_received = []
        self.bus.subscribe(EventType.PLAYER_LOST, lambda e: self.events_received.append(e))

    def test_11_01_person_detected_extracts_landmarks(self):
        """UC 11.01: Full person detected extracts 33 landmarks with names and confidence."""
        mock_backend = lambda img: make_mock_landmarks(nose_y=0.2, ankle_y=0.8)
        tracker = PoseTracker(bus=self.bus, backend=mock_backend)

        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = tracker.process_frame(dummy_img, timestamp=100.0)

        self.assertTrue(result.has_person)
        self.assertEqual(len(result.raw_landmarks), 33)
        self.assertIn("nose", result.landmarks)
        self.assertIn("left_shoulder", result.landmarks)
        self.assertIn("right_ankle", result.landmarks)
        self.assertGreater(result.confidence, 0.5)

    def test_11_02_nobody_in_view_dispatches_player_lost_after_consecutive_frames(self):
        """UC 11.02: Empty frames dispatch PLAYER_LOST after 5 consecutive frames."""
        mock_backend = lambda img: None
        tracker = PoseTracker(bus=self.bus, backend=mock_backend)

        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)

        # 4 empty frames -> not yet declared lost
        for i in range(4):
            res = tracker.process_frame(dummy_img, timestamp=float(i))
            self.assertFalse(res.has_person)

        self.bus.drain()
        self.assertEqual(len(self.events_received), 0)

        # 5th empty frame -> dispatches PLAYER_LOST
        tracker.process_frame(dummy_img, timestamp=5.0)
        self.bus.drain()
        self.assertEqual(len(self.events_received), 1)

    def test_11_03_head_or_feet_cut_off_flags_partial_body(self):
        """UC 11.03: Ankles out of frame (low visibility) flags is_partial = True."""
        # Ankles cut off (visibility 0.1)
        mock_backend = lambda img: make_mock_landmarks(ankle_vis=0.1)
        tracker = PoseTracker(bus=self.bus, backend=mock_backend)

        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = tracker.process_frame(dummy_img, timestamp=100.0)

        self.assertTrue(result.has_person)
        self.assertTrue(result.is_partial)

    def test_11_05_missing_mediapipe_falls_soft_without_crashing(self):
        """UC 11.05: If library fails to load, tracker flags unavailable and returns empty pose."""
        # Tracker with a failing backend
        failing_backend = lambda img: (_ for _ in ()).throw(RuntimeError("MediaPipe model missing"))
        tracker = PoseTracker(bus=self.bus, backend=failing_backend)

        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = tracker.process_frame(dummy_img, timestamp=10.0)

        self.assertFalse(result.has_person)

    def test_11_06_low_confidence_flags_low_light_warning(self):
        """UC 11.06: Average confidence below 0.40 triggers low_light_warning."""
        # Low visibility (0.3) simulating dim room
        mock_backend = lambda img: make_mock_landmarks(avg_vis=0.3)
        tracker = PoseTracker(bus=self.bus, backend=mock_backend)

        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = tracker.process_frame(dummy_img, timestamp=100.0)

        self.assertTrue(result.has_person)
        self.assertTrue(result.low_light_warning)

    def test_11_07_fast_motion_blur_holds_last_valid_pose_for_150ms(self):
        """UC 11.07: Single empty frame during jump blur holds last valid pose (is_held = True)."""
        valid_backend = lambda img: make_mock_landmarks(nose_y=0.2, ankle_y=0.8)
        tracker = PoseTracker(bus=self.bus, backend=valid_backend)

        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        t0 = 1000.0
        r1 = tracker.process_frame(dummy_img, timestamp=t0)
        self.assertTrue(r1.has_person)
        self.assertFalse(r1.is_held)

        # Immediate next frame has motion blur (backend returns None) 50 ms later
        tracker.backend = lambda img: None
        r2 = tracker.process_frame(dummy_img, timestamp=t0 + 0.05)

        # Held over!
        self.assertTrue(r2.has_person)
        self.assertTrue(r2.is_held)

        # Frame 250 ms later exceeds 150 ms threshold -> marked lost
        r3 = tracker.process_frame(dummy_img, timestamp=t0 + 0.25)
        self.assertFalse(r3.has_person)

    def test_11_08_small_body_in_frame_triggers_scale_warning(self):
        """UC 11.08: Body span under 25% of frame triggers child_scale_warning."""
        # Nose at 0.50, ankles at 0.65 -> span is only 0.15 (15% of frame)
        mock_backend = lambda img: make_mock_landmarks(nose_y=0.50, ankle_y=0.65)
        tracker = PoseTracker(bus=self.bus, backend=mock_backend)

        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = tracker.process_frame(dummy_img, timestamp=100.0)

        self.assertTrue(result.has_person)
        self.assertTrue(result.child_scale_warning)

    def test_11_11_landmark_names_map_joints_correctly(self):
        """UC 11.11: Joint names map correctly to standard indices."""
        self.assertEqual(LANDMARK_NAMES[0], "nose")
        self.assertEqual(LANDMARK_NAMES[11], "left_shoulder")
        self.assertEqual(LANDMARK_NAMES[12], "right_shoulder")
        self.assertEqual(LANDMARK_NAMES[23], "left_hip")
        self.assertEqual(LANDMARK_NAMES[24], "right_hip")
        self.assertEqual(LANDMARK_NAMES[27], "left_ankle")
        self.assertEqual(LANDMARK_NAMES[28], "right_ankle")


if __name__ == "__main__":
    unittest.main()