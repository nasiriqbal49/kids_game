import json
import tempfile
import unittest
from pathlib import Path

from core.event_bus import EventBus
from identity.profile_manager import ProfileManager
from identity.shop_manager import ShopManager, ShopItem


class TestShopManager(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name)
        self.profile_mgr = ProfileManager(bus=self.bus, storage_dir=self.storage_path)
        self.shop_mgr = ShopManager(bus=self.bus, profile_manager=self.profile_mgr, storage_dir=self.storage_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_catalog_loads_default_items(self):
        """Catalog initializes with default power-ups and accessories."""
        items = self.shop_mgr.list_items()
        self.assertGreaterEqual(len(items), 5)
        item_ids = [it.item_id for it in items]
        self.assertIn("shield", item_ids)
        self.assertIn("wings_glider", item_ids)
        self.assertIn("sunglasses", item_ids)

    def test_buy_item_with_sufficient_coins_succeeds(self):
        """Player with enough coins successfully buys item and inventory increments."""
        profile = self.profile_mgr.create_profile("ShopperKid")
        self.profile_mgr.add_coins(profile.profile_id, 100)  # Give 100 coins

        success, msg = self.shop_mgr.buy_item(profile.profile_id, "shield")  # Shield costs 30

        self.assertTrue(success)
        reloaded = self.profile_mgr.get_profile(profile.profile_id)
        self.assertEqual(reloaded.coins, 70)  # 100 - 30 = 70
        self.assertEqual(reloaded.inventory["shield"], 1)

    def test_buy_item_insufficient_coins_fails_safely(self):
        """Buying without enough coins rejects transaction without deducting wallet."""
        profile = self.profile_mgr.create_profile("BrokeKid")
        self.assertEqual(profile.coins, 0)

        success, msg = self.shop_mgr.buy_item(profile.profile_id, "wings_glider")  # Costs 40

        self.assertFalse(success)
        self.assertIn("Need 40 coins", msg)
        self.assertEqual(profile.coins, 0)

    def test_equipped_powerups_and_consumption(self):
        """Equipped items can be consumed during a run up to max carrying capacity."""
        profile = self.profile_mgr.create_profile("Hero")
        profile.inventory = {"shield": 2, "wings_glider": 1}
        self.profile_mgr.save()

        equipped = self.shop_mgr.get_equipped_powerups(profile.profile_id)
        self.assertIn("shield", equipped)
        self.assertIn("wings_glider", equipped)

        # Consume 1 shield during play
        consumed = self.shop_mgr.consume_equipped_item(profile.profile_id, "shield")
        self.assertTrue(consumed)
        self.assertEqual(profile.inventory["shield"], 1)

    def test_parent_workshop_grant_coins_and_rename_item(self):
        """Parents can grant bonus coins and customize shop catalog names/prices."""
        profile = self.profile_mgr.create_profile("GoodStudent")

        # Parent rewards 250 coins for doing homework
        new_balance = self.shop_mgr.parent_grant_coins(profile.profile_id, 250)
        self.assertEqual(new_balance, 250)

        # Parent customizes "wings_glider" to "Eagle Wings" for 15 coins
        edited = self.shop_mgr.parent_edit_item("wings_glider", new_name="Eagle Wings", new_price=15)
        self.assertTrue(edited)

        # Verify change persists in catalog
        reloaded_item = self.shop_mgr.catalog["wings_glider"]
        self.assertEqual(reloaded_item.name, "Eagle Wings")
        self.assertEqual(reloaded_item.price, 15)


if __name__ == "__main__":
    unittest.main()