import sys
import json
import shutil
import difflib
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Tuple
from core.logger import get_logger

log = get_logger("config")

DEFAULT_CONFIG_PATH = Path("config.json")

# Default settings tailored for the ThinkPad + 43" TV setup
DEFAULT_CONFIG: Dict[str, Any] = {
    "display": {
        "fullscreen": True,
        "display_index": 1,        # 0 = Laptop screen, 1 = TV (extended display)
        "render_width": 1920,
        "render_height": 1080,
        "target_fps": 60,
    },
    "audio": {
        "volume": 80,              # 0 to 100
        "mute": False,
        "max_volume_cap": 100,
        "sfx_enabled": True,
        "music_enabled": True,
    },
    "camera": {
        "camera_index": 0,         # Laptop webcam to start; phone webcam later
        "width": 640,
        "height": 480,
        "target_fps": 30,
        "mirror": True,
    },
    "gameplay": {
        "sensitivity": "normal",   # "easy", "normal", "strict"
        "idle_timeout_sec": 300,
        "forgiving_hitbox": True,
    },
    "logging": {
        "level": "INFO",
        "max_bytes": 1_000_000,
        "backup_count": 5,
    },
    "keyboard": {
        "jump": "space",
        "duck": "down",
        "lean_left": "left",
        "lean_right": "right",
        "pause": "p",
        "debug": "f3",
    }
}

# Validation rules: (expected_type, min_val, max_val, allowed_choices)
VALIDATION_RULES: Dict[str, Tuple[type, Any, Any, Any]] = {
    "display.fullscreen": (bool, None, None, None),
    "display.display_index": (int, 0, 10, None),
    "display.render_width": (int, 640, 3840, None),
    "display.render_height": (int, 480, 2160, None),
    "display.target_fps": (int, 15, 120, None),

    "audio.volume": (int, 0, 100, None),
    "audio.mute": (bool, None, None, None),
    "audio.max_volume_cap": (int, 0, 100, None),
    "audio.sfx_enabled": (bool, None, None, None),
    "audio.music_enabled": (bool, None, None, None),

    "camera.camera_index": (int, 0, 10, None),
    "camera.width": (int, 320, 1920, None),
    "camera.height": (int, 240, 1080, None),
    "camera.target_fps": (int, 10, 60, None),
    "camera.mirror": (bool, None, None, None),

    "gameplay.sensitivity": (str, None, None, ["easy", "normal", "strict"]),
    "gameplay.idle_timeout_sec": (int, 10, 3600, None),
    "gameplay.forgiving_hitbox": (bool, None, None, None),

    "logging.level": (str, None, None, ["DEBUG", "INFO", "WARNING", "ERROR"]),
    "logging.max_bytes": (int, 10_000, 50_000_000, None),
    "logging.backup_count": (int, 1, 20, None),
}


def _flatten_dict(d: dict, parent_key: str = "") -> dict:
    """Flatten nested dict to dot-notation keys: {'audio': {'volume': 80}} -> {'audio.volume': 80}"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _unflatten_dict(d: dict) -> dict:
    """Unflatten dot-notation keys back to nested dict."""
    result: dict = {}
    for key, value in d.items():
        parts = key.split(".")
        current = result
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
    return result


class Config:
    def __init__(self, file_path: Path = DEFAULT_CONFIG_PATH):
        self.file_path = Path(file_path)
        self._data: Dict[str, Any] = deepcopy(DEFAULT_CONFIG)
        self._cli_overrides: Dict[str, Any] = {}   # settings forced from the command line
        self._pending: Dict[str, Any] = {}         # changes waiting for a safe moment (UC 01.09)
        self.load()

    def get(self, dot_key: str, default: Any = None) -> Any:
        """Get setting using dot notation, e.g. get('audio.volume')"""
        parts = dot_key.split(".")
        curr = self._data
        for part in parts:
            if not isinstance(curr, dict) or part not in curr:
                return default
            curr = curr[part]
        return curr

    def set(self, dot_key: str, value: Any) -> None:
        """Set setting using dot notation."""
        parts = dot_key.split(".")
        curr = self._data
        for part in parts[:-1]:
            curr = curr.setdefault(part, {})
        curr[parts[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        return deepcopy(self._data)

    def load(self, cli_args: list = None) -> None:
        """Loads config, validates, applies CLI overrides, and saves defaults if needed."""
        self._cli_overrides = {}
        self._pending = {}

        if not self.file_path.exists():
            log.info("No config file found at %s. Creating with defaults. (UC 01.01)", self.file_path)
            self._save_defaults()
            self._data = deepcopy(DEFAULT_CONFIG)
        else:
            loaded_raw = self._read_json_or_backup()
            if loaded_raw is None:
                log.warning("Loading fallback in-memory defaults.")
                self._data = deepcopy(DEFAULT_CONFIG)
            else:
                self._data = self._validate_and_merge(loaded_raw)

        # Command-line overrides always apply, even after a broken file (UC 01.06)
        args_to_check = cli_args if cli_args is not None else sys.argv[1:]
        self._apply_cli_overrides(args_to_check)

        # Checks that involve more than one setting
        self._apply_cross_checks()

    def _read_json_or_backup(self):
        """Read the settings file as a JSON object.
        On any problem (bad JSON, not an object, unreadable) the file is copied to
        .json.bad and None is returned (UC 01.04)."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if not isinstance(raw, dict):
                raise ValueError(f"top level must be a JSON object, got {type(raw).__name__}")
            return raw
        except (ValueError, OSError) as err:  # JSONDecodeError is a ValueError
            log.error("Config file %s is malformed: %s (UC 01.04)", self.file_path, err)
            backup_path = self.file_path.with_suffix(".json.bad")
            try:
                shutil.copyfile(self.file_path, backup_path)
                log.warning("Corrupted config backed up to %s", backup_path)
            except OSError as copy_err:
                log.error("Failed to create backup: %s", copy_err)
            return None

    def _apply_cross_checks(self) -> None:
        """Checks that involve more than one setting."""
        volume = self.get("audio.volume")
        cap = self.get("audio.max_volume_cap")
        if isinstance(volume, int) and isinstance(cap, int) and volume > cap:
            log.warning("audio.volume (%d) is above audio.max_volume_cap (%d). Lowering volume. (UC 05.06)",
                        volume, cap)
            self._data["audio"]["volume"] = cap

    def _save_defaults(self) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        except OSError as err:
            log.warning("Cannot write default config to %s (%s). Running on in-memory defaults.", self.file_path, err)

    def _validate_and_merge(self, raw_data: dict) -> dict:
        flat_default = _flatten_dict(DEFAULT_CONFIG)
        flat_incoming = _flatten_dict(raw_data)
        validated_flat = deepcopy(flat_default)

        # Check for unknown keys / typos (UC 01.05)
        for in_key in flat_incoming.keys():
            if in_key not in flat_default:
                close = difflib.get_close_matches(in_key, flat_default.keys(), n=1, cutoff=0.6)
                suggestion = f" Did you mean '{close[0]}'?" if close else ""
                log.warning("Unknown configuration key '%s'.%s (UC 01.05)", in_key, suggestion)

        # Validate each expected key
        for key, def_val in flat_default.items():
            if key not in flat_incoming:
                # Missing key (UC 01.02)
                log.warning("Missing key '%s' in config file. Using default '%s'. (UC 01.02)", key, def_val)
                continue

            val = flat_incoming[key]
            rule = VALIDATION_RULES.get(key)

            if rule is None:
                validated_flat[key] = val
                continue

            expected_type, min_v, max_v, choices = rule

            # Type check (a bool is not accepted where a number is expected)
            if not isinstance(val, expected_type) or (isinstance(val, bool) and expected_type is not bool):
                log.warning("Key '%s' expected type %s, got %s (%r). Using default %r.",
                            key, expected_type.__name__, type(val).__name__, val, def_val)
                continue

            # Range check for numbers (UC 01.03)
            if expected_type in (int, float):
                if min_v is not None and val < min_v:
                    log.warning("Key '%s' value %r below min allowed %r. Clamping. (UC 01.03)", key, val, min_v)
                    val = min_v
                elif max_v is not None and val > max_v:
                    log.warning("Key '%s' value %r exceeds max allowed %r. Clamping. (UC 01.03)", key, val, max_v)
                    val = max_v

            # Choices check
            if choices is not None and val not in choices:
                log.warning("Key '%s' value %r not in allowed %r. Using default %r.", key, val, choices, def_val)
                continue

            validated_flat[key] = val

        return _unflatten_dict(validated_flat)

    def _apply_cli_overrides(self, args: list) -> None:
        """Parses arguments like --audio.volume=50 or --display.fullscreen=false"""
        flat_default = _flatten_dict(DEFAULT_CONFIG)

        for arg in args:
            if not arg.startswith("--") or "=" not in arg:
                continue
            pair = arg[2:].split("=", 1)
            raw_key, raw_val = pair[0].strip(), pair[1].strip()

            if raw_key not in flat_default:
                log.warning("CLI override rejected: unknown key '%s'.", raw_key)
                continue

            rule = VALIDATION_RULES.get(raw_key)
            if not rule:
                continue

            exp_type, min_v, max_v, choices = rule
            parsed_val = None

            try:
                if exp_type is bool:
                    lowered = raw_val.lower()
                    if lowered in ("true", "1", "yes", "on"):
                        parsed_val = True
                    elif lowered in ("false", "0", "no", "off"):
                        parsed_val = False
                    else:
                        raise ValueError(raw_val)
                elif exp_type is int:
                    parsed_val = int(raw_val)
                elif exp_type is float:
                    parsed_val = float(raw_val)
                else:
                    parsed_val = raw_val
            except ValueError:
                log.warning("CLI override rejected: cannot parse %r as %s for '%s'. (UC 01.06)",
                            raw_val, exp_type.__name__, raw_key)
                continue

            # Check range / choices
            if exp_type in (int, float):
                if (min_v is not None and parsed_val < min_v) or (max_v is not None and parsed_val > max_v):
                    log.warning("CLI override rejected: %r out of range [%s, %s] for '%s'. (UC 01.06)",
                                parsed_val, min_v, max_v, raw_key)
                    continue

            if choices and parsed_val not in choices:
                log.warning("CLI override rejected: %r not in %r for '%s'. (UC 01.06)", parsed_val, choices, raw_key)
                continue

            log.info("CLI override applied: %s = %r (UC 01.06)", raw_key, parsed_val)
            self.set(raw_key, parsed_val)
            self._cli_overrides[raw_key] = parsed_val


# Global singleton helper
_config_instance = None

def get_config(reload: bool = False) -> Config:
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = Config()
    return _config_instance