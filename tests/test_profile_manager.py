import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.events import EventType
from core.event_bus import EventBus
from identity.profile_manager import ProfileManager, PlayerProfile


class TestProfileManager(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name)
        self.manager = ProfileManager(bus=self.bus, storage_dir=self.storage_path)

        self.events_received = []
        for evt in (EventType.PROFILE_CREATED, EventType.PROFILE_SELECTED, EventType.PROFILE_UPDATED):
            self.bus.subscribe(evt, lambda e: self.events_received.append(e))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_15_01_create_profile_validates_and_stores(self):
        """UC 15.01: Profile is created with trimmed name, unique ID, and persisted to disk."""
        profile = self.manager.create_profile("  Aiden  ")

        self.assertIsNotNone(profile)
        self.assertEqual(profile.name, "Aiden")
        self.assertTrue(profile.profile_id)
        self.assertEqual(profile.coins, 0)
        self.assertIn(profile.profile_id, self.manager.profiles)

        created_events = [e for e in self.events_received if e.name == EventType.PROFILE_CREATED]
        self.assertEqual(len(created_events), 1)
        self.assertEqual(created_events[0].payload["name"], "Aiden")

        self.assertIsNone(self.manager.create_profile("   "))
        self.assertIsNone(self.manager.create_profile("SuperLongNameExceedingLimit"))

    def test_15_02_duplicate_name_rejected_without_silent_overwrite(self):
        """UC 15.02: Case-insensitive duplicate name is rejected to prevent silent data loss."""
        first = self.manager.create_profile("Sarah")
        self.assertIsNotNone(first)

        dup1 = self.manager.create_profile("Sarah")
        dup2 = self.manager.create_profile("sarah")

        self.assertIsNone(dup1)
        self.assertIsNone(dup2)
        self.assertEqual(len(self.manager.profiles), 1)

    def test_15_03_select_profile_broadcasts_profile_selected_event(self):
        """UC 15.03: Selecting profile emits PROFILE_SELECTED with full payload for HUD and engine."""
        profile = self.manager.create_profile("Leo")
        selected = self.manager.select_profile("Leo")

        self.assertEqual(selected.profile_id, profile.profile_id)
        self.assertEqual(self.manager.active_profile.name, "Leo")

        selected_events = [e for e in self.events_received if e.name == EventType.PROFILE_SELECTED]
        self.assertEqual(len(selected_events), 1)
        self.assertEqual(selected_events[0].payload["name"], "Leo")
        self.assertIn("avatar", selected_events[0].payload)
        self.assertIn("high_scores", selected_events[0].payload)

    def test_15_04_corrupted_profiles_json_restores_from_rolling_backup(self):
        """UC 15.04: Damaged profiles.json automatically restores from profiles.json.bak."""
        self.manager.create_profile("Maya")
        self.manager.create_profile("Zack")
        self.manager.save()

        self.assertTrue(self.manager.profiles_path.exists())
        self.assertTrue(self.manager.backup_path.exists())

        with open(self.manager.profiles_path, "w", encoding="utf-8") as f:
            f.write("{ damaged json text : [")

        recovered_manager = ProfileManager(bus=self.bus, storage_dir=self.storage_path)

        self.assertEqual(len(recovered_manager.profiles), 2)
        self.assertIsNotNone(recovered_manager.find_by_name("Maya"))
        self.assertIsNotNone(recovered_manager.find_by_name("Zack"))

    def test_15_05_update_score_updates_specific_game_only_and_adds_coins(self):
        """UC 15.05: High score updates for the specific game without touching other games; coins credited."""
        profile = self.manager.create_profile("Omar")
        self.manager.select_profile("Omar")

        profile.high_scores["freeze_dance"] = 300
        is_new_best = self.manager.record_game_result("runner", score=450, coins_earned=25)

        self.assertTrue(is_new_best)
        self.assertEqual(profile.high_scores["runner"], 450)
        self.assertEqual(profile.high_scores["freeze_dance"], 300)
        self.assertEqual(profile.coins, 25)

        is_new_best_lower = self.manager.record_game_result("runner", score=380, coins_earned=10)
        self.assertFalse(is_new_best_lower)
        self.assertEqual(profile.high_scores["runner"], 450)
        self.assertEqual(profile.coins, 35)

    def test_15_06_rename_and_avatar_change_preserves_scores_and_coins(self):
        """UC 15.06: Renaming or changing avatar keeps permanent ID, scores, and wallet intact."""
        profile = self.manager.create_profile("OriginalName")
        pid = profile.profile_id
        self.manager.select_profile(pid)
        self.manager.record_game_result("runner", score=500, coins_earned=50)

        # Rename
        renamed = self.manager.rename_profile(pid, "NewName")
        self.assertTrue(renamed)
        self.assertEqual(profile.name, "NewName")
        self.assertEqual(profile.high_scores["runner"], 500)
        self.assertEqual(profile.coins, 50)

        # Update Avatar
        self.manager.update_avatar(pid, {"color": "gold", "hat": "cap"})
        self.assertEqual(profile.avatar["color"], "gold")
        self.assertEqual(profile.avatar["hat"], "cap")

    def test_15_07_delete_profile_requires_parent_confirmation(self):
        """UC 15.07: Deletion without parent confirmation is rejected; parent confirmation removes it."""
        profile = self.manager.create_profile("Sibling")
        pid = profile.profile_id

        # Accidental deletion without parent confirmation -> REJECTED
        deleted_unconfirmed = self.manager.delete_profile(pid, parent_confirmed=False)
        self.assertFalse(deleted_unconfirmed)
        self.assertIn(pid, self.manager.profiles)

        # Deletion with parent confirmation -> SUCCEEDS
        deleted_confirmed = self.manager.delete_profile(pid, parent_confirmed=True)
        self.assertTrue(deleted_confirmed)
        self.assertNotIn(pid, self.manager.profiles)

    def test_15_08_remeasure_updates_measurements_without_resetting_scores(self):
        """UC 15.08: Re-measuring updates heights and jump baseline; high scores and coins untouched."""
        profile = self.manager.create_profile("GrowingChild")
        pid = profile.profile_id
        self.manager.select_profile(pid)
        self.manager.record_game_result("runner", score=600, coins_earned=100)

        new_measurements = {"height_cm": 135, "jump_baseline": 0.68}
        self.manager.update_measurements(pid, new_measurements)

        self.assertEqual(profile.measurements["height_cm"], 135)
        self.assertEqual(profile.measurements["jump_baseline"], 0.68)
        self.assertEqual(profile.high_scores["runner"], 600)  # Preserved
        self.assertEqual(profile.coins, 100)                  # Preserved

    def test_15_09_guest_profile_temporary_and_not_saved_to_disk(self):
        """UC 15.09: Guest mode provides a valid profile without writing to disk."""
        initial_count = len(self.manager.profiles)
        guest = self.manager.get_guest_profile()

        self.assertEqual(guest.name, "Guest")
        self.assertEqual(guest.profile_id, "guest_player")
        self.assertEqual(len(self.manager.profiles), initial_count)  # Not added to permanent profiles

    def test_15_10_disk_write_failure_kept_in_memory_safely(self):
        """UC 15.10: Disk write failure retains modifications in memory and flags warning without crashing."""
        profile = self.manager.create_profile("InMemoryChild")
        pid = profile.profile_id

        # Simulate read-only or locked disk during save
        with patch("builtins.open", side_effect=OSError("Disk full / permission denied")):
            saved = self.manager.save()
            self.assertFalse(saved)
            self.assertTrue(self.manager.write_error_active)

        # Data still exists intact in memory
        self.assertIn(pid, self.manager.profiles)


if __name__ == "__main__":
    unittest.main()