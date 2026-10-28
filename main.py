from core.logger import setup_logging, configure_from, get_logger
from core.config import get_config

# 1) Start logging with safe defaults, so the config loader can report problems
setup_logging()

# 2) Load config
cfg = get_config()

# 3) Re-apply logging using the settings from config.json (or --logging.level=...)
configure_from(cfg)
log = get_logger("main")

log.info("--- Kids Motion Game: startup check ---")
log.info("Logging level: %s", cfg.get("logging.level"))
log.info("Display target: %sx%s (Display index: %s)",
         cfg.get("display.render_width"),
         cfg.get("display.render_height"),
         cfg.get("display.display_index"))
log.info("Audio volume: %s (Mute: %s)", cfg.get("audio.volume"), cfg.get("audio.mute"))
log.info("Camera index: %s at %sx%s @ %s FPS",
         cfg.get("camera.camera_index"),
         cfg.get("camera.width"),
         cfg.get("camera.height"),
         cfg.get("camera.target_fps"))
log.info("Gameplay sensitivity: %s", cfg.get("gameplay.sensitivity"))
log.info("--- Startup check complete ---")