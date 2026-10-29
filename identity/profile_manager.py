import json
import re
import shutil
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("profile_manager")

DEFAULT_USER_DATA_DIR = Path("user_data")
DEFAULT_PROFILES_FILE = DEFAULT_USER_DATA_DIR / "profiles.json"
MAX_NAME_LENGTH = 16


@dataclass
class PlayerProfile:
    """Universal player profile shared across all games (UC 15.01, 15.05, 15.06)."""
    profile_id: str
    name: str
    coins: int = 0
    inventory: Dict[str, int] = field(default_factory=dict)
    high_scores: Dict[str, int] = field(default_factory=dict)
    avatar: Dict[str, Any] = field(default_factory=lambda: {
        "color": "blue",
        "hat": "none",
        "accessory": "none"
    })
    measurements: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_played_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerProfile":
        valid_fields = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class ProfileManager:
    """
    Manages player identity, coin economy, and profile storage (Module 15).
    Safeguards user content in user_data/ with rolling backups (UC 15.01 - 15.10).
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 storage_dir: Optional[Path] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        self.storage_dir = Path(storage_dir) if storage_dir else DEFAULT_USER_DATA_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_path = self.storage_dir / "profiles.json"
        self.backup_path = self.storage_dir / "profiles.json.bak"

        self.profiles: Dict[str, PlayerProfile] = {}  # Keyed by profile_id
        self.active_profile: Optional[PlayerProfile] = None
        self.write_error_active: bool = False

        self.load()

    # -------------------------------------------------------------------------
    # Validation & Lookup Helpers (UC 15.01, 15.02)
    # -------------------------------------------------------------------------

    @staticmethod
    def validate_name(name: str) -> Optional[str]:
        """Validates and sanitizes a profile name (UC 15.01)."""
        trimmed = name.strip()
        if not trimmed:
            log.warning("Profile creation rejected: empty name (UC 15.01).")
            return None
        if len(trimmed) > MAX_NAME_LENGTH:
            log.warning("Profile creation rejected: name exceeds %d characters (UC 15.01).", MAX_NAME_LENGTH)
            return None
        if not re.match(r"^[\w\s-]+$", trimmed, re.UNICODE):
            log.warning("Profile creation rejected: name '%s' contains invalid characters (UC 15.01).", trimmed)
            return None
        return trimmed

    def find_by_name(self, name: str) -> Optional[PlayerProfile]:
        """Case-insensitive search for a profile by name."""
        target = name.strip().lower()
        for p in self.profiles.values():
            if p.name.lower() == target:
                return p
        return None

    def get_profile(self, profile_id_or_name: str) -> Optional[PlayerProfile]:
        """Look up by unique profile_id, or by display name."""
        if profile_id_or_name in self.profiles:
            return self.profiles[profile_id_or_name]
        return self.find_by_name(profile_id_or_name)

    def list_profiles(self) -> List[PlayerProfile]:
        """Returns all profiles sorted by last played time (newest first)."""
        return sorted(self.profiles.values(), key=lambda p: p.last_played_at, reverse=True)

    # -------------------------------------------------------------------------
    # Profile Lifecycle (UC 15.01, 15.02, 15.03, 15.05)
    # -------------------------------------------------------------------------

    def create_profile(self, name: str, avatar: Optional[Dict[str, Any]] = None) -> Optional[PlayerProfile]:
        """Creates a new profile with duplicate check (UC 15.01, 15.02)."""
        valid_name = self.validate_name(name)
        if not valid_name:
            return None

        if self.find_by_name(valid_name) is not None:
            log.warning("Profile creation rejected: name '%s' already exists (UC 15.02).", valid_name)
            return None

        new_id = str(uuid.uuid4())
        profile = PlayerProfile(
            profile_id=new_id,
            name=valid_name,
            avatar=avatar or {"color": "blue", "hat": "none", "accessory": "none"}
        )

        self.profiles[new_id] = profile
        self.save()
        log.info("Profile created: '%s' (ID: %s) (UC 15.01).", valid_name, new_id)

        self.bus.publish(Event(EventType.PROFILE_CREATED, {
            "profile_id": new_id,
            "name": valid_name
        }))
        return profile

    def select_profile(self, profile_id_or_name: str) -> Optional[PlayerProfile]:
        """Selects active profile and broadcasts PROFILE_SELECTED (UC 15.03)."""
        profile = self.get_profile(profile_id_or_name)
        if not profile:
            log.error("Cannot select profile '%s': not found (UC 15.03).", profile_id_or_name)
            return None

        profile.last_played_at = time.time()
        self.active_profile = profile
        self.save()

        log.info("Active profile selected: '%s' (UC 15.03).", profile.name)
        self.bus.publish(Event(EventType.PROFILE_SELECTED, {
            "profile_id": profile.profile_id,
            "name": profile.name,
            "coins": profile.coins,
            "avatar": profile.avatar,
            "measurements": profile.measurements,
            "high_scores": profile.high_scores
        }))
        return profile

    def record_game_result(self, game_id: str, score: int, coins_earned: int = 0) -> bool:
        """Updates game high score and deposits coins (UC 15.05)."""
        if not self.active_profile:
            log.warning("No active profile to record game result for.")
            return False

        profile = self.active_profile
        old_best = profile.high_scores.get(game_id, 0)
        is_new_best = score > old_best

        if is_new_best:
            profile.high_scores[game_id] = score
            log.info("Profile '%s' achieved new high score in '%s': %d (UC 15.05).",
                     profile.name, game_id, score)

        if coins_earned > 0:
            profile.coins += coins_earned
            log.info("Profile '%s' earned %d coins (total: %d).", profile.name, coins_earned, profile.coins)

        profile.last_played_at = time.time()
        self.save()

        self.bus.publish(Event(EventType.PROFILE_UPDATED, {
            "profile_id": profile.profile_id,
            "game_id": game_id,
            "score": score,
            "is_new_best": is_new_best,
            "total_coins": profile.coins
        }))
        return is_new_best

    # -------------------------------------------------------------------------
    # Updates, Deletion, Re-measurement & Guest (UC 15.06 - 15.09)
    # -------------------------------------------------------------------------

    def rename_profile(self, profile_id: str, new_name: str) -> bool:
        """
        Renames a profile while preserving ID, high scores, coins, and avatar (UC 15.06).
        """
        profile = self.profiles.get(profile_id)
        if not profile:
            return False

        valid = self.validate_name(new_name)
        if not valid:
            return False

        # If name is already taken by someone else
        existing = self.find_by_name(valid)
        if existing and existing.profile_id != profile_id:
            log.warning("Cannot rename: '%s' is already in use (UC 15.06).", valid)
            return False

        profile.name = valid
        self.save()
        log.info("Profile %s renamed to '%s' (UC 15.06).", profile_id, valid)
        return True

    def update_avatar(self, profile_id: str, avatar_data: Dict[str, Any]) -> bool:
        """Updates avatar choices (color, hat, accessory) without touching scores (UC 15.06)."""
        profile = self.profiles.get(profile_id)
        if not profile:
            return False

        profile.avatar.update(avatar_data)
        self.save()
        log.info("Profile %s avatar updated (UC 15.06).", profile_id)
        return True

    def delete_profile(self, profile_id: str, parent_confirmed: bool = False) -> bool:
        """
        Deletes a profile with mandatory parent confirmation (UC 15.07).
        Prevents siblings from accidentally deleting each other's profiles.
        """
        if not parent_confirmed:
            log.warning("Profile deletion rejected: parent confirmation required (UC 15.07).")
            return False

        if profile_id in self.profiles:
            deleted_name = self.profiles[profile_id].name
            del self.profiles[profile_id]

            if self.active_profile and self.active_profile.profile_id == profile_id:
                self.active_profile = None

            self.save()
            log.info("Profile '%s' deleted with parent confirmation (UC 15.07).", deleted_name)
            return True
        return False

    def update_measurements(self, profile_id: str, measurements: Dict[str, Any]) -> bool:
        """
        Updates physical measurements (height, jump baseline) from camera calibration
        while keeping scores, coins, and avatar intact (UC 15.08).
        """
        profile = self.profiles.get(profile_id)
        if not profile:
            return False

        profile.measurements.update(measurements)
        self.save()
        log.info("Profile '%s' measurements updated (UC 15.08).", profile.name)
        return True

    def get_guest_profile(self) -> PlayerProfile:
        """
        Generates a temporary guest profile (UC 15.09).
        Never saved to disk; scores and coins remain in-memory for this run only.
        """
        return PlayerProfile(
            profile_id="guest_player",
            name="Guest",
            avatar={"color": "green", "hat": "none", "accessory": "none"},
            measurements={"height_cm": 120, "jump_baseline": 0.60}
        )

    # -------------------------------------------------------------------------
    # Virtual Coin Shop Wallet Helpers
    # -------------------------------------------------------------------------

    def add_coins(self, profile_id: str, amount: int) -> int:
        """Adds coins to a player's wallet balance."""
        profile = self.get_profile(profile_id)
        if profile and amount > 0:
            profile.coins += amount
            self.save()
            return profile.coins
        return 0

    def spend_coins(self, profile_id: str, amount: int) -> bool:
        """Deducts coins if the player has sufficient balance."""
        profile = self.get_profile(profile_id)
        if profile and 0 < amount <= profile.coins:
            profile.coins -= amount
            self.save()
            return True
        return False

    # -------------------------------------------------------------------------
    # Storage & Rolling Backup Engine (UC 15.04, 15.10)
    # -------------------------------------------------------------------------

    def save(self) -> bool:
        """
        Atomically saves profiles to user_data/profiles.json.
        Preserves previous valid state in profiles.json.bak (UC 15.04, 15.10).
        """
        tmp_path = self.profiles_path.with_suffix(".json.tmp")
        payload = {
            "version": "1.0",
            "saved_at": time.time(),
            "profiles": [p.to_dict() for p in self.profiles.values()]
        }

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

            if self.profiles_path.exists():
                shutil.copyfile(self.profiles_path, self.backup_path)

            tmp_path.replace(self.profiles_path)
            self.write_error_active = False
            return True
        except (OSError, PermissionError) as err:
            self.write_error_active = True
            log.error("Failed to save profiles to disk: %s. Data retained in memory (UC 15.10).", err)
            return False

    def load(self) -> bool:
        """Loads profiles with automatic rolling backup fallback on corruption (UC 15.04)."""
        if not self.profiles_path.exists():
            if self.backup_path.exists():
                log.warning("profiles.json missing, restoring from rolling backup (UC 15.04).")
                return self._load_file(self.backup_path)
            self.profiles = {}
            return True

        success = self._load_file(self.profiles_path)
        if not success:
            log.warning("profiles.json corrupted. Attempting recovery from backup (UC 15.04)...")
            if self.backup_path.exists() and self._load_file(self.backup_path):
                log.info("Successfully recovered player profiles from rolling backup! (UC 15.04)")
                shutil.copyfile(self.backup_path, self.profiles_path)
                return True
            else:
                log.error("Both primary and backup profile files are damaged or missing.")
                self.profiles = {}
                return False
        return True

    def _load_file(self, target_path: Path) -> bool:
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict) or "profiles" not in data:
                return False

            loaded = {}
            for raw_p in data["profiles"]:
                if isinstance(raw_p, dict) and "profile_id" in raw_p and "name" in raw_p:
                    p = PlayerProfile.from_dict(raw_p)
                    loaded[p.profile_id] = p

            self.profiles = loaded
            return True
        except (json.JSONDecodeError, OSError, ValueError) as err:
            log.error("Could not parse profile file %s: %s (UC 15.04)", target_path, err)
            return False