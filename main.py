from core.logger import setup_logging, get_logger
from core.config import get_config

# Setup logging
setup_logging(level="DEBUG")
log = get_logger("main")

log.info("--- Testing Kids Motion Game: Module 1 (Config & Logging) ---")

# Load config
cfg = get_config()

# Display current settings
log.info("Display target: %sx%s (Display index: %s)",
         cfg.get("display.render_width"),
         cfg.get("display.render_height"),
         cfg.get("display.display_index"))
log.info("Audio volume: %s (Mute: %s)", cfg.get("audio.volume"), cfg.get("audio.mute"))
log.info("Primary Camera index: %s at %sx%s @ %s FPS",
         cfg.get("camera.camera_index"),
         cfg.get("camera.width"),
         cfg.get("camera.height"),
         cfg.get("camera.target_fps"))
log.info("Gameplay sensitivity: %s", cfg.get("gameplay.sensitivity"))

log.info("--- Module 1 Initial Check Complete ---")