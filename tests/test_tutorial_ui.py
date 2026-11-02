import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from engine.tutorial_ui import TutorialAcademy, TUTORIAL_LESSONS, MASTER_CONTROL_MATRIX
from vision.pose_tracker import PoseResult, PoseLandmark


def make_test_pose(nose_y=0.20, ankle_y=0.85, is_partial=False):
    lms = {
        "nose": PoseLandmark(0, "nose", 0.50, nose_y, 0.0, 0.9),
        "left_wrist": PoseLandmark(15, "left_wrist", 0.48, 0.40, 0.0, 0.9),
        "right_wrist": PoseLandmark(16, "right_wrist", 0.52, 0.40, 0.0, 0.9),
        "left_ankle": PoseLandmark(27, "left_ankle", 0.46, ankle_y, 0.0, 0.9),
        "right_ankle": PoseLandmark(28, "right_ankle", 0.54, ankle_y, 0.0, 0.9),
    }
    return PoseResult(has_person=True, landmarks=lms, raw_landmarks=list(lms.values()), confidence=0.9, timestamp=10.0, is_partial=is_partial)


class TestTutorialAcademy(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.academy = TutorialAcademy()

    def tearDown(self):
        pygame.quit()

    def test_lesson_navigation(self):
        """Browses through tutorial lessons with wraparound."""
        initial_id = self.academy.get_current_lesson()["id"]
        self.assertEqual(self.academy.selected_lesson_idx, 0)

        self.academy.next_lesson()
        self.assertEqual(self.academy.selected_lesson_idx, 1)

        self.academy.prev_lesson()
        self.assertEqual(self.academy.selected_lesson_idx, 0)

    def test_camera_framing_evaluation_optimal_standing(self):
        """Evaluates optimal ~8.5 ft standing zone when head and feet are visible."""
        pose = make_test_pose(nose_y=0.20, ankle_y=0.85)
        tag, adv, col = self.academy.evaluate_camera_framing(pose, mode="STANDING (8 to 10 ft)")

        self.assertIn("PERFECT", tag)
        self.assertEqual(col, (46, 204, 113))

    def test_camera_framing_evaluation_feet_cut_off(self):
        """Warns when feet are cut off in standing mode."""
        pose = make_test_pose(is_partial=True)
        tag, adv, col = self.academy.evaluate_camera_framing(pose, mode="STANDING (8 to 10 ft)")

        self.assertIn("FEET", tag)

    def test_camera_framing_couch_mode(self):
        """Seated Couch Mode approves upper body even without feet."""
        pose = make_test_pose(nose_y=0.25, is_partial=True)
        tag, adv, col = self.academy.evaluate_camera_framing(pose, mode="COUCH / SEATED (4 to 6 ft)")

        self.assertIn("COUCH", tag)
        self.assertEqual(col, (52, 152, 219))

    def test_calculate_match_percentage_exact_action(self):
        """Exact gesture detected awards 100% match score."""
        pose = make_test_pose()
        score = self.academy.calculate_match_percentage("NERF_GUN", last_action="SHOOT", pose=pose)
        self.assertEqual(score, 100)

    def test_master_control_matrix_integrity(self):
        """Verifies Master Control Matrix contains all required gesture bindings and games."""
        self.assertGreaterEqual(len(MASTER_CONTROL_MATRIX), 10)
        gestures = [r[0] for r in MASTER_CONTROL_MATRIX]
        self.assertIn("Real Jump", gestures)
        self.assertIn("Steering Wheel", gestures)
        self.assertIn("Nerf Gun Recoil", gestures)
        self.assertIn("Boxing Punch", gestures)


if __name__ == "__main__":
    unittest.main()