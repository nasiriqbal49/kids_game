import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
VALID_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}
ROOT_NAME = "kidsgame"


def setup_logging(level="INFO", log_dir="logs", max_bytes=1_000_000, backup_count=5):
    """Set up console and file logging. Never raises: the game must start even if logs fail."""
    root = logging.getLogger(ROOT_NAME)
    root.handlers.clear()
    root.propagate = False

    level_name = str(level).upper()
    root.setLevel(VALID_LEVELS.get(level_name, logging.INFO))

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    if level_name not in VALID_LEVELS:
        root.warning("Unknown log level '%s', using INFO", level)

    try:
        folder = Path(log_dir)
        folder.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            folder / "kidsgame.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError as err:
        root.warning("Cannot write log file (%s). Logging to console only.", err)

    return root


def get_logger(name):
    """Get a logger for one module, for example get_logger('camera')."""
    return logging.getLogger(f"{ROOT_NAME}.{name}")