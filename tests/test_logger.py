import logging
import tempfile
import unittest
from pathlib import Path

from core.logger import setup_logging, configure_from, get_logger, ROOT_NAME


class FakeConfig:
    """Minimal stand-in for Config, so these tests never touch the real config.json."""
    def __init__(self, values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


class TestLoggerModule(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log_dir = Path(self.tmp.name) / "logs"

    def tearDown(self):
        root = logging.getLogger(ROOT_NAME)
        for handler in list(root.handlers):
            handler.close()
            root.removeHandler(handler)
        self.tmp.cleanup()

    def _read_log(self):
        return (self.log_dir / "kidsgame.log").read_text(encoding="utf-8")

    def test_01_07_log_line_has_time_level_module_message(self):
        """UC 01.07: A log line has time, level, module name and message."""
        setup_logging(level="INFO", log_dir=self.log_dir)
        get_logger("demo").info("hello world")
        text = self._read_log()
        self.assertIn("| INFO    | kidsgame.demo | hello world", text)
        self.assertRegex(text, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \|")

    def test_01_07_unwritable_log_folder_falls_back_to_console(self):
        """UC 01.07: If the log file cannot be written, logging continues on the console."""
        blocker = Path(self.tmp.name) / "blocker.txt"
        blocker.write_text("not a folder", encoding="utf-8")
        root = setup_logging(level="INFO", log_dir=blocker / "logs")
        self.assertEqual(len(root.handlers), 1)  # console only, no crash
        get_logger("demo").info("still works")

    def test_01_07_unknown_level_falls_back_to_info(self):
        """UC 01.07: An unknown log level uses INFO and records a warning."""
        root = setup_logging(level="LOUD", log_dir=self.log_dir)
        self.assertEqual(root.level, logging.INFO)
        self.assertIn("Unknown log level", self._read_log())

    def test_01_07_configure_from_applies_config_values(self):
        """UC 01.07: Level, size and backup count come from the config."""
        cfg = FakeConfig({"logging.level": "WARNING",
                          "logging.max_bytes": 5000,
                          "logging.backup_count": 3})
        root = configure_from(cfg, log_dir=self.log_dir)
        self.assertEqual(root.level, logging.WARNING)
        file_handlers = [h for h in root.handlers if hasattr(h, "maxBytes")]
        self.assertEqual(file_handlers[0].maxBytes, 5000)
        self.assertEqual(file_handlers[0].backupCount, 3)

    def test_01_08_rotation_keeps_only_backup_count_files(self):
        """UC 01.08: Old logs are rotated and only the last N files are kept."""
        root = setup_logging(level="INFO", log_dir=self.log_dir, max_bytes=2000, backup_count=2)
        # Keep test output quiet: remove the console handler, keep the file handler
        for handler in list(root.handlers):
            if not hasattr(handler, "maxBytes"):
                root.removeHandler(handler)
        log = get_logger("demo")
        for i in range(300):
            log.info("line %03d %s", i, "x" * 40)
        files = sorted(p.name for p in self.log_dir.glob("kidsgame.log*"))
        self.assertEqual(files, ["kidsgame.log", "kidsgame.log.1", "kidsgame.log.2"])


if __name__ == "__main__":
    unittest.main()