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

    def test_01_06_cli_override(self):
        """UC 01.06: Command-line arguments can override config settings."""
        cfg = Config(file_path=self.cfg_file)
        cfg.load(cli_args=["--audio.volume=45", "--display.fullscreen=false"])
        self.assertEqual(cfg.get("audio.volume"), 45)
        self.assertEqual(cfg.get("display.fullscreen"), False)


if __name__ == "__main__":
    unittest.main()