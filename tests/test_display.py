import os
import unittest
import pygame

# Ensure tests run headless without opening a physical pop-up window
os.environ["SDL_VIDEODRIVER"] = "dummy"

from core.events import Event, EventType
from core.event_bus import EventBus
from core.config import Config
from engine.display import DisplayManager


class FakeConfig:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


class TestDisplayModule(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.cfg = FakeConfig({
            "display.display_index": 1,
            "display.render_width": 1920,
            "display.render_height": 1080,
            "display.fullscreen": False,
        })
        self.manager = DisplayManager(bus=self.bus, cfg=self.cfg)

    def tearDown(self):
        self.manager.close()

    def test_04_02_tv_not_detected_fallback_to_laptop(self):
        """UC 04.02: When TV (display index 1) is not found, fallback to laptop display 0 with warning."""
        # Simulate environment with only 1 screen connected (laptop display only)
        resolved = self.manager.resolve_display_index(num_displays=1)
        self.assertEqual(resolved, 0)
        self.assertFalse(self.manager.tv_found)

    def test_04_01_tv_detected_when_second_display_exists(self):
        """UC 04.01: When TV (display index 1) is present, it is selected."""
        # Simulate environment with 2 screens connected (laptop + TV)
        resolved = self.manager.resolve_display_index(num_displays=2)
        self.assertEqual(resolved, 1)
        self.assertTrue(self.manager.tv_found)

    def test_04_05_hud_state_updates_within_frame_on_events(self):
        """UC 04.05: HUD state updates immediately when events are received on the Event Bus."""
        # Publish health change
        self.bus.publish(Event(EventType.HEALTH_CHANGED, {"current": 75, "max": 100, "delta": -25}))
        self.assertEqual(self.manager.hud_state["health"], 75)

        # Publish score change
        self.bus.publish(Event(EventType.SCORE_CHANGED, {"score": 350, "delta": 50}))
        self.assertEqual(self.manager.hud_state["score"], 350)

        # Publish streak change
        self.bus.publish(Event(EventType.STREAK_CHANGED, {"streak": 4, "multiplier": 1.5}))
        self.assertEqual(self.manager.hud_state["streak"], 4)

        # Publish power-up collected and expired
        self.bus.publish(Event(EventType.POWERUP_COLLECTED, {"powerup_type": "shield", "duration_sec": 10.0}))
        self.assertIn("shield", self.manager.hud_state["active_powerups"])

        self.bus.publish(Event(EventType.POWERUP_EXPIRED, {"powerup_type": "shield"}))
        self.assertNotIn("shield", self.manager.hud_state["active_powerups"])

    def test_04_06_low_health_flag_triggered(self):
        """UC 04.06: Health at or below 25 triggers low health warning state."""
        self.bus.publish(Event(EventType.HEALTH_CHANGED, {"current": 20, "max": 100, "is_low": True}))
        self.assertTrue(self.manager.hud_state["health_is_low"])

        # Health restored
        self.bus.publish(Event(EventType.HEALTH_CHANGED, {"current": 80, "max": 100, "is_low": False}))
        self.assertFalse(self.manager.hud_state["health_is_low"])

    def test_04_04_headless_init_display(self):
        """UC 04.04: Display initializes cleanly with target 1080p resolution."""
        self.manager.init_display(headless=True)
        self.assertIsNotNone(self.manager.screen)
        self.assertEqual(self.manager.screen.get_width(), 1920)
        self.assertEqual(self.manager.screen.get_height(), 1080)


    def test_04_07_font_size_readability_rule(self):
        """UC 04.07: Minimum font size rules ensure text is readable from 10 feet."""
        from engine.display import MIN_TITLE_FONT_SIZE, MIN_STAT_FONT_SIZE
        self.assertGreaterEqual(MIN_TITLE_FONT_SIZE, 36)
        self.assertGreaterEqual(MIN_STAT_FONT_SIZE, 48)

    def test_04_10_low_fps_automatic_effects_reduction(self):
        """UC 04.10: FPS dropping under 45 triggers reduced_effects mode."""
        self.assertFalse(self.manager.reduced_effects)
        # Simulate severe stutter (e.g. 38 FPS)
        self.manager.check_fps(38.0)
        self.assertTrue(self.manager.reduced_effects)

        # Recovery back to 60 FPS
        self.manager.check_fps(59.0)
        self.assertFalse(self.manager.reduced_effects)

    def test_04_11_photosensitivity_rate_limiting(self):
        """UC 04.11: Hit flash is rate-limited to at most 3 per second with soft alpha."""
        from engine.display import MAX_FLASH_ALPHA
        # Max alpha must never be full-white strobe (255)
        self.assertLessEqual(MAX_FLASH_ALPHA, 100)

        t0 = 1000.0
        # First flash succeeds
        self.assertTrue(self.manager.trigger_hit_flash(now=t0))

        # Rapid second flash 100 ms later is blocked (violates 3/sec cap)
        self.assertFalse(self.manager.trigger_hit_flash(now=t0 + 0.10))

        # Flash after 350 ms succeeds (> 333 ms cooldown)
        self.assertTrue(self.manager.trigger_hit_flash(now=t0 + 0.35))

    def test_04_12_long_profile_name_clipped_with_ellipsis(self):
        """UC 04.12: Very long profile names are truncated with ellipsis to avoid overflow."""
        short_name = self.manager.format_display_name("Leo", max_chars=12)
        self.assertEqual(short_name, "Leo")

        long_name = self.manager.format_display_name("AlexanderTheGreat", max_chars=12)
        self.assertEqual(long_name, "Alexander...")
        self.assertLessEqual(len(long_name), 12)

    def test_04_13_focus_loss_dispatches_pause(self):
            """UC 04.13: Window focus loss emits GAME_PAUSE event."""
            if not pygame.get_init():
                pygame.init()

            paused_events = []
            self.bus.subscribe(EventType.GAME_PAUSE, lambda e: paused_events.append(e.payload.get("reason")))

            class FakeEvent:
                type = pygame.ACTIVEEVENT
                gain = 0
                state = 1

            import unittest.mock as mock
            with mock.patch("pygame.event.get", return_value=[FakeEvent()]):
                self.manager.process_window_events()

            self.assertEqual(paused_events, ["focus_loss"])

if __name__ == "__main__":
    unittest.main()