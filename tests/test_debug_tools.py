import os
import json
import tempfile
import unittest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from core.events import Event, EventType
from core.event_bus import EventBus
from vision.debug_tools import DebugOverlay, SessionRecorder, SessionReplayer


class TestDebugTools(unittest.TestCase):

    def setUp(self):
        pygame.init()
        pygame.font.init()
        self.bus = EventBus()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()
        pygame.quit()

    def test_10_01_debug_overlay_toggles_and_renders_only_when_enabled(self):
        """UC 10.01: DebugOverlay toggles via DEBUG_TOGGLED and renders with zero cost when off."""
        overlay = DebugOverlay(bus=self.bus)
        self.assertFalse(overlay.enabled)

        surface = pygame.Surface((640, 480))

        # When disabled, calling render executes with zero draw overhead
        overlay.render(surface, fps=60.0)

        # Toggle on
        self.bus.publish(Event(EventType.DEBUG_TOGGLED))
        self.assertTrue(overlay.enabled)

        # Overlay renders without error when enabled
        overlay.render(surface, fps=59.5, camera_fps=30.0, latency_ms=18.5,
                       landmarks=[(100, 100), (100, 150)], zone_rect=(50, 50, 200, 300))

        # Toggle off again
        self.bus.publish(Event(EventType.DEBUG_TOGGLED))
        self.assertFalse(overlay.enabled)

    def test_10_02_record_landmark_session_creates_valid_json_with_metadata(self):
        """UC 10.02: SessionRecorder creates structured JSON file with metadata header."""
        recorder = SessionRecorder(output_dir=self.temp_dir.name)

        cam_info = {"width": 640, "height": 480, "fps": 30}
        self.assertTrue(recorder.start_recording(camera_info=cam_info, profile_name="Leo"))

        # Record 3 sample landmark frames
        for i in range(3):
            recorder.record_frame(frame_index=i, timestamp=float(i) * 0.033,
                                  landmarks=[{"x": 0.5, "y": 0.4 + i * 0.01}])

        saved_path = recorder.stop_recording()
        self.assertIsNotNone(saved_path)
        self.assertTrue(saved_path.exists())

        # Verify file structure & metadata
        with open(saved_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["metadata"]["profile_name"], "Leo")
        self.assertEqual(data["metadata"]["camera_info"]["width"], 640)
        self.assertEqual(len(data["frames"]), 3)

    def test_10_03_replay_session_delivers_deterministic_frames(self):
        """UC 10.03: SessionReplayer steps through recorded frames deterministically."""
        # Create a sample session file
        sample_path = Path(self.temp_dir.name) / "test_session.json"
        session_data = {
            "metadata": {
                "version": "1.0",
                "recorded_at": "2026-10-29 12:00:00",
                "camera_info": {"width": 640, "height": 480, "fps": 30}
            },
            "frames": [
                {"frame_index": 0, "timestamp": 0.0, "landmarks": [{"x": 10, "y": 20}]},
                {"frame_index": 1, "timestamp": 0.033, "landmarks": [{"x": 12, "y": 22}]},
            ]
        }
        with open(sample_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f)

        replayer = SessionReplayer()
        self.assertTrue(replayer.load_recording(sample_path))

        f0 = replayer.step_frame()
        f1 = replayer.step_frame()
        f2 = replayer.step_frame()

        self.assertEqual(f0["frame_index"], 0)
        self.assertEqual(f1["frame_index"], 1)
        self.assertIsNone(f2)  # End of recording

    def test_10_07_corrupt_recording_file_rejected_safely(self):
        """UC 10.07: Corrupted or incomplete recording files are rejected without crashing."""
        replayer = SessionReplayer()

        # Case 1: Corrupted malformed JSON syntax
        bad_json = Path(self.temp_dir.name) / "corrupt_syntax.json"
        bad_json.write_text("{ incomplete json...", encoding="utf-8")
        self.assertFalse(replayer.load_recording(bad_json))

        # Case 2: Missing required header metadata
        missing_header = Path(self.temp_dir.name) / "missing_header.json"
        missing_header.write_text(json.dumps({"frames": []}), encoding="utf-8")
        self.assertFalse(replayer.load_recording(missing_header))

    def test_10_05_ground_truth_marking_and_accuracy_evaluation(self):
        """UC 10.05: Replayer evaluates detection accuracy against ground-truth jump markers."""
        sample_path = Path(self.temp_dir.name) / "session_gt.json"
        session_data = {
            "metadata": {
                "version": "1.0",
                "recorded_at": "2026-10-29 12:00:00",
                "camera_info": {"width": 640, "height": 480},
                "ground_truth_events": [
                    {"frame_index": 10, "event": EventType.JUMP},
                    {"frame_index": 40, "event": EventType.JUMP},
                ]
            },
            "frames": []
        }
        with open(sample_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f)

        replayer = SessionReplayer()
        replayer.load_recording(sample_path)

        # Detector detected frame 11 (near 10) and frame 41 (near 40), plus a false jump at 80
        report = replayer.calculate_accuracy(detected_jump_frames=[11, 41, 80], tolerance_frames=3)

        self.assertEqual(report["ground_truth_total"], 2)
        self.assertEqual(report["detected_true_jumps"], 2)
        self.assertEqual(report["missed_jumps"], 0)
        self.assertEqual(report["false_jumps"], 1)
        self.assertEqual(report["accuracy_pct"], 100.0)

    def test_10_04_replay_with_changed_thresholds_side_by_side_summary(self):
        """UC 10.04: Replayer runs session with different thresholds and returns summary."""
        sample_path = Path(self.temp_dir.name) / "thresh_session.json"
        sample_data = {
            "metadata": {"version": "1.0", "camera_info": {"width": 640, "height": 480}},
            "frames": [
                {"frame_index": 0, "landmarks": [{"y": 100}]},
                {"frame_index": 1, "landmarks": [{"y": 130}]},
                {"frame_index": 2, "landmarks": [{"y": 160}]},
            ]
        }
        with open(sample_path, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)

        replayer = SessionReplayer()
        replayer.load_recording(sample_path)

        def mock_detector(frames, threshold):
            detected = []
            for i in range(1, len(frames)):
                diff = frames[i]["landmarks"][0]["y"] - frames[i-1]["landmarks"][0]["y"]
                if diff >= threshold:
                    detected.append(i)
            return detected

        # Run with threshold 20 (detects 2 jumps) vs threshold 50 (detects 0 jumps)
        summary = replayer.compare_thresholds(mock_detector, threshold_variants=[20.0, 50.0])
        self.assertEqual(summary[20.0], 2)
        self.assertEqual(summary[50.0], 0)

    def test_10_06_low_disk_space_aborts_recording(self):
        """UC 10.06: Recording aborts when free disk space is below min_disk_mb threshold."""
        # Set min_disk_mb to a huge value so the free disk check triggers
        recorder = SessionRecorder(output_dir=self.temp_dir.name, min_disk_mb=999_999_999.0)
        started = recorder.start_recording(camera_info={"width": 640, "height": 480})
        self.assertFalse(started)
        self.assertFalse(recorder.is_recording)

    def test_10_09_delete_all_recordings(self):
        """UC 10.09: delete_all_recordings removes session files and reports count."""
        recorder = SessionRecorder(output_dir=self.temp_dir.name)
        (Path(self.temp_dir.name) / "session_1.json").write_text("{}", encoding="utf-8")
        (Path(self.temp_dir.name) / "session_2.json").write_text("{}", encoding="utf-8")

        deleted = recorder.delete_all_recordings()
        self.assertEqual(deleted, 2)
        self.assertEqual(len(list(Path(self.temp_dir.name).glob("session_*.json"))), 0)


if __name__ == "__main__":
    unittest.main()