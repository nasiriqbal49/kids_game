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

    # Close old handlers properly so log files are released (important on Windows)
    for handler in list(root.handlers):
        handler.close()
        root.removeHandler(handler)
    root.propagate = False

    level_name = str(level).upper()
    unknown_level = level_name not in VALID_LEVELS
    root.setLevel(VALID_LEVELS.get(level_name, logging.INFO))

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    file_error = None
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
        file_error = err

    # Warnings are emitted after all handlers exist, so they reach the file too
    if unknown_level:
        root.warning("Unknown log level '%s', using INFO", level)
    if file_error is not None:
        root.warning("Cannot write log file (%s). Logging to console only.", file_error)

    return root


def configure_from(cfg, log_dir="logs"):
    """Apply the 'logging' section of the config (level, max_bytes, backup_count)."""
    return setup_logging(
        level=cfg.get("logging.level", "INFO"),
        log_dir=log_dir,
        max_bytes=cfg.get("logging.max_bytes", 1_000_000),
        backup_count=cfg.get("logging.backup_count", 5),
    )


def get_logger(name):
    """Get a logger for one module, for example get_logger('camera')."""
    return logging.getLogger(f"{ROOT_NAME}.{name}")