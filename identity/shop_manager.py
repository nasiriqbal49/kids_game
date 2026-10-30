import json
import os
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from identity.profile_manager import ProfileManager, PlayerProfile

log = get_logger("shop_manager")

DEFAULT_USER_DATA_DIR = Path("user_data")
DEFAULT_CATALOG_FILE = DEFAULT_USER_DATA_DIR / "catalog.json"
CUSTOM_ASSETS_DIR = DEFAULT_USER_DATA_DIR / "custom_assets"


@dataclass
class ShopItem:
    item_id: str
    name: str
    category: str        # "powerup" or "accessory"
    price: int
    description: str
    icon_type: str = "builtin"   # "builtin" or "custom"
    custom_asset_path: Optional[str] = None


DEFAULT_CATALOG: List[Dict[str, Any]] = [
    {
        "item_id": "shield",
        "name": "Super Shield",
        "category": "powerup",
        "price": 30,
        "description": "Absorbs 1 obstacle hit with zero damage!"
    },
    {
        "item_id": "wings_glider",
        "name": "Turbo Wings",
        "category": "powerup",
        "price": 40,
        "description": "Flap elbows like a chicken to glide in mid-air!"
    },
    {
        "item_id": "double_points",
        "name": "Double Star Booster",
        "category": "powerup",
        "price": 25,
        "description": "Doubles all points scored during your run!"
    },
    {
        "item_id": "slow_down",
        "name": "Chill-Out Potion",
        "category": "powerup",
        "price": 20,
        "description": "Slows world speed down to a gentle breeze."
    },
    {
        "item_id": "sunglasses",
        "name": "Cool Sunglasses",
        "category": "accessory",
        "price": 50,
        "description": "Equips stylish sunglasses on your avatar."
    },
    {
        "item_id": "monster_horns",
        "name": "Monster Horns",
        "category": "accessory",
        "price": 60,
        "description": "Grow wacky cartoon horns on your head!"
    },
    {
        "item_id": "party_hat",
        "name": "Party Hat",
        "category": "accessory",
        "price": 35,
        "description": "A festive party hat for high scorers."
    }
]


class ShopManager:
    """
    Manages the virtual coin shop, parent workshop studio, and homemade asset directories.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 profile_manager: Optional[ProfileManager] = None,
                 storage_dir: Optional[Path] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.profile_mgr = profile_manager or ProfileManager(bus=self.bus, cfg=self.config)

        self.storage_dir = Path(storage_dir) if storage_dir else DEFAULT_USER_DATA_DIR
        self.catalog_path = self.storage_dir / "catalog.json"
        self.assets_dir = self.storage_dir / "custom_assets"

        self.catalog: Dict[str, ShopItem] = {}
        self.max_equipped_capacity: int = 3  # Kids can carry up to 3 items into a run

        self._init_folders()
        self.load_catalog()

    def _init_folders(self) -> None:
        """Creates protected user_data custom asset folders if they don't exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        for sub in ("powerups", "monsters", "actions", "photos"):
            (self.assets_dir / sub).mkdir(parents=True, exist_ok=True)

    def load_catalog(self) -> None:
        """Loads shop item catalog from user_data/catalog.json or saves defaults."""
        if not self.catalog_path.exists():
            self._save_default_catalog()
            return

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.catalog = {item["item_id"]: ShopItem(**item) for item in data.get("items", [])}
            log.info("Loaded %d shop items from catalog.json.", len(self.catalog))
        except Exception as err:
            log.error("Error loading catalog.json: %s. Loading in-memory defaults.", err)
            self._save_default_catalog()

    def _save_default_catalog(self) -> None:
        self.catalog = {item["item_id"]: ShopItem(**item) for item in DEFAULT_CATALOG}
        self.save_catalog()

    def save_catalog(self) -> bool:
        """Saves custom names, prices, and asset bindings to user_data/catalog.json."""
        payload = {
            "version": "1.0",
            "updated_at": time.time(),
            "items": [asdict(item) for item in self.catalog.values()]
        }
        try:
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            log.info("Catalog saved successfully.")
            return True
        except OSError as err:
            log.error("Failed saving catalog: %s", err)
            return False

    def list_items(self, category: Optional[str] = None) -> List[ShopItem]:
        """Returns shop items, optionally filtered by category ('powerup' or 'accessory')."""
        items = list(self.catalog.values())
        if category:
            items = [it for it in items if it.category == category]
        return items

    def buy_item(self, profile_id: str, item_id: str) -> Tuple[bool, str]:
        """
        Purchases an item using player's coins.
        - Power-ups add to consumable inventory count.
        - Accessories unlock permanently for the avatar.
        """
        profile = self.profile_mgr.get_profile(profile_id)
        if not profile:
            return False, "Player profile not found."

        item = self.catalog.get(item_id)
        if not item:
            return False, "Item not found in catalog."

        if profile.coins < item.price:
            log.warning("Purchase rejected: Not enough coins (%d < %d).", profile.coins, item.price)
            return False, f"Need {item.price} coins (You have {profile.coins})."

        # Deduct coins
        profile.coins -= item.price

        if item.category == "powerup":
            # Add to inventory
            current_count = profile.inventory.get(item_id, 0)
            profile.inventory[item_id] = current_count + 1
            log.info("Profile '%s' bought %s (Count: %d, Coins left: %d).",
                     profile.name, item.name, profile.inventory[item_id], profile.coins)
        else:
            # Accessory equip
            profile.avatar[item_id] = "equipped"
            log.info("Profile '%s' unlocked accessory %s.", profile.name, item.name)

        self.profile_mgr.save()
        return True, f"Bought {item.name}!"

    def get_equipped_powerups(self, profile_id: str) -> List[str]:
        """Returns list of active power-ups equipped for the next run (up to max capacity)."""
        profile = self.profile_mgr.get_profile(profile_id)
        if not profile:
            return []

        equipped = []
        for item_id, count in profile.inventory.items():
            if count > 0 and len(equipped) < self.max_equipped_capacity:
                equipped.append(item_id)
        return equipped

    def consume_equipped_item(self, profile_id: str, item_id: str) -> bool:
        """Consumes 1 item from inventory when activated during a run."""
        profile = self.profile_mgr.get_profile(profile_id)
        if profile and profile.inventory.get(item_id, 0) > 0:
            profile.inventory[item_id] -= 1
            if profile.inventory[item_id] == 0:
                del profile.inventory[item_id]
            self.profile_mgr.save()
            return True
        return False

    # -------------------------------------------------------------------------
    # Parent Workshop Studio Helpers
    # -------------------------------------------------------------------------

    def parent_grant_coins(self, profile_id: str, bonus_coins: int) -> int:
        """Allows parents to reward kids with bonus coins."""
        return self.profile_mgr.add_coins(profile_id, bonus_coins)

    def parent_edit_item(self, item_id: str, new_name: str, new_price: int,
                         custom_asset_path: Optional[str] = None) -> bool:
        """Allows parents to rename items, adjust coin prices, or bind custom child art."""
        item = self.catalog.get(item_id)
        if not item:
            return False

        item.name = new_name.strip()
        item.price = max(1, new_price)
        if custom_asset_path:
            item.custom_asset_path = custom_asset_path
            item.icon_type = "custom"

        self.save_catalog()
        log.info("Parent Workshop: Item '%s' updated (Name: %s, Price: %d).", item_id, item.name, item.price)
        return True

    def open_assets_folder_in_explorer(self) -> bool:
        """
        1-Click Button in Parent Workshop:
        Opens user_data/custom_assets/ in Windows File Explorer so parents can
        drag & drop child drawings and voice recordings directly!
        """
        try:
            folder_str = str(self.assets_dir.resolve())
            if os.name == "nt":  # Windows
                os.startfile(folder_str)
            else:
                subprocess.Popen(["xdg-open", folder_str])
            log.info("Opened custom assets folder in Windows Explorer: %s", folder_str)
            return True
        except Exception as err:
            log.error("Failed opening assets folder: %s", err)
            return False