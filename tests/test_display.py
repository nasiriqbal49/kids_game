import os
import unittest

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


if __name__ == "__main__":
    unittest.main()