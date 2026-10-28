import unittest
import tempfile
import json
from pathlib import Path
from core.config import Config


class TestConfigModule(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for safe testing
        self.test_dir = tempfile.TemporaryDirectory()
        self.cfg_file = Path(self.test_dir.name) / "config.json"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_01_01_creates_defaults_if_missing(self):
        """UC 01.01: When no file exists, defaults are created and loaded."""
        self.assertFalse(self.cfg_file.exists())
        cfg = Config(file_path=self.cfg_file)
        self.assertTrue(self.cfg_file.exists())
        self.assertEqual(cfg.get("audio.volume"), 80)

    def test_01_02_fills_missing_keys_with_defaults(self):
        """UC 01.02: If a key is missing in the file, default is used."""
        partial = {"audio": {"mute": True}}  # volume is missing
        with open(self.cfg_file, "w", encoding="utf-8") as f:
            json.dump(partial, f)

        cfg = Config(file_path=self.cfg_file)
        self.assertTrue(cfg.get("audio.mute"))
        self.assertEqual(cfg.get("audio.volume"), 80)  # Default applied

    def test_01_03_clamps_out_of_range_values(self):
        """UC 01.03: Values beyond allowed ranges are clamped safely."""
        bad_range = {"audio": {"volume": 350}}  # Max is 100
        with open(self.cfg_file, "w", encoding="utf-8") as f:
            json.dump(bad_range, f)

        cfg = Config(file_path=self.cfg_file)
        self.assertEqual(cfg.get("audio.volume"), 100)  # Clamped to max

    def test_01_04_handles_malformed_json_with_bad_backup(self):
        """UC 01.04: Broken JSON creates a .bad backup and loads defaults without crashing."""
        with open(self.cfg_file, "w", encoding="utf-8") as f:
            f.write("{ broken json line :")

        cfg = Config(file_path=self.cfg_file)
        # Should not crash and should load default values
        self.assertEqual(cfg.get("audio.volume"), 80)
        # .bad backup should exist
        bad_backup = self.cfg_file.with_suffix(".json.bad")
        self.assertTrue(bad_backup.exists())

    def test_01_03_bool_is_not_accepted_as_a_number(self):
        """UC 01.03: true/false in a number setting is rejected and the default is used."""
        with open(self.cfg_file, "w", encoding="utf-8") as f:
            json.dump({"audio": {"volume": True}}, f)
        cfg = Config(file_path=self.cfg_file)
        self.assertEqual(cfg.get("audio.volume"), 80)

    def test_01_03_volume_cannot_exceed_volume_cap(self):
        """UC 01.03 / 05.06: volume above max_volume_cap is lowered to the cap."""
        with open(self.cfg_file, "w", encoding="utf-8") as f:
            json.dump({"audio": {"volume": 90, "max_volume_cap": 60}}, f)
        cfg = Config(file_path=self.cfg_file)
        self.assertEqual(cfg.get("audio.volume"), 60)

    def test_01_04_json_that_is_not_an_object_is_treated_as_malformed(self):
        """UC 01.04: A valid JSON file that is not an object (a list) is backed up and defaults load."""
        with open(self.cfg_file, "w", encoding="utf-8") as f:
            f.write("[1, 2, 3]")
        cfg = Config(file_path=self.cfg_file)
        self.assertEqual(cfg.get("audio.volume"), 80)
        self.assertTrue(self.cfg_file.with_suffix(".json.bad").exists())

    def test_01_06_cli_override_still_applies_after_malformed_file(self):
        """UC 01.06: Command-line overrides apply even when the file was broken."""
        with open(self.cfg_file, "w", encoding="utf-8") as f:
            f.write("{ broken")
        cfg = Config(file_path=self.cfg_file)
        cfg.load(cli_args=["--audio.volume=30"])
        self.assertEqual(cfg.get("audio.volume"), 30)

    def test_01_06_invalid_bool_override_is_rejected(self):
        """UC 01.06: A typo such as --display.fullscreen=flase is rejected, not read as False."""
        cfg = Config(file_path=self.cfg_file)
        cfg.load(cli_args=["--display.fullscreen=flase"])
        self.assertEqual(cfg.get("display.fullscreen"), True)

    def test_01_06_cli_override(self):
        """UC 01.06: Command-line arguments can override config settings."""
        cfg = Config(file_path=self.cfg_file)
        cfg.load(cli_args=["--audio.volume=45", "--display.fullscreen=false"])
        self.assertEqual(cfg.get("audio.volume"), 45)
        self.assertEqual(cfg.get("display.fullscreen"), False)

    def test_01_05_unknown_key_is_reported_with_suggestion(self):
        """UC 01.05: A typo in a key is reported with the closest valid key name."""
        with open(self.cfg_file, "w", encoding="utf-8") as f:
            json.dump({"audio": {"volum": 50}}, f)

        with self.assertLogs("kidsgame.config", level="WARNING") as logs:
            cfg = Config(file_path=self.cfg_file)

        output = "\n".join(logs.output)
        self.assertIn("Unknown configuration key 'audio.volum'", output)
        self.assertIn("Did you mean 'audio.volume'?", output)
        self.assertEqual(cfg.get("audio.volume"), 80)  # typo ignored, default applies

if __name__ == "__main__":
    unittest.main()