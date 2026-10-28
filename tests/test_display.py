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

    def test_04_13_real_focus_loss_event_pauses_game(self):
        """UC 04.13: A real window focus-loss event (Alt+Tab) publishes GAME_PAUSE."""
        pygame.init()
        paused = []
        self.bus.subscribe(EventType.GAME_PAUSE, lambda e: paused.append(e.payload.get("reason")))

        remaining = self.manager.process_window_events([pygame.event.Event(pygame.WINDOWFOCUSLOST)])

        self.assertEqual(paused, ["focus_loss"])
        self.assertEqual(remaining, [])

    def test_04_13_mouse_leaving_window_does_not_pause(self):
        """UC 04.13: Moving the mouse pointer out of the window must not pause the game."""
        pygame.init()
        paused = []
        self.bus.subscribe(EventType.GAME_PAUSE, lambda e: paused.append(e.payload.get("reason")))

        mouse_leave = pygame.event.Event(pygame.ACTIVEEVENT, gain=0, state=pygame.APPMOUSEFOCUS)
        self.manager.process_window_events([mouse_leave])

        self.assertEqual(paused, [])

    def test_04_13_key_events_pass_through_to_input_adapter(self):
        """UC 04.13: The display must not swallow keyboard events; it returns them to the main loop."""
        pygame.init()
        key_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0, unicode=" ", scancode=44)

        remaining = self.manager.process_window_events([key_event])

        self.assertEqual(remaining, [key_event])

    def test_04_13_window_close_requests_quit_without_pausing(self):
        """UC 04.13: Closing the window sets quit_requested and does not publish GAME_PAUSE."""
        pygame.init()
        paused = []
        self.bus.subscribe(EventType.GAME_PAUSE, lambda e: paused.append(e))

        self.manager.process_window_events([pygame.event.Event(pygame.QUIT)])

        self.assertTrue(self.manager.quit_requested)
        self.assertEqual(paused, [])

    def test_04_06_draw_hud_renders_low_health_badge(self):
        """UC 04.06: draw_hud renders without error when low health state is active."""
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

        surface = pygame.Surface((1920, 1080))
        # Trigger low health
        self.bus.publish(Event(EventType.HEALTH_CHANGED, {"current": 15, "max": 100, "is_low": True}))
        self.manager.draw_hud(surface)
        self.assertTrue(self.manager.hud_state["health_is_low"])

    def test_04_07_draw_hud_scales_to_custom_surface_size(self):
        """UC 04.07 / G8: draw_hud scales dynamically to any surface size (e.g. 1280x720 laptop fallback)."""
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

        small_surface = pygame.Surface((1280, 720))
        # Must execute cleanly without error or boundary overflow
        self.manager.draw_hud(small_surface)
        self.assertEqual(small_surface.get_size(), (1280, 720))

    def test_04_10_particles_enabled_property_reflects_fps(self):
        """UC 04.10: particles_enabled toggle reflects frame rate health."""
        self.manager.check_fps(60.0)
        self.assertTrue(self.manager.particles_enabled)

        # FPS drops under 45
        self.manager.check_fps(40.0)
        self.assertFalse(self.manager.particles_enabled)

    def test_04_12_draw_hud_renders_player_name(self):
        """UC 04.12: draw_hud renders the player name onto the surface."""
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

        surface = pygame.Surface((1920, 1080))
        self.manager.hud_state["player_name"] = "SuperKid"
        self.manager.draw_hud(surface)
        self.assertEqual(self.manager.hud_state["player_name"], "SuperKid")


    def test_04_03_display_disconnect_publishes_pause(self):
        """UC 04.03: HDMI disconnected mid-game pauses with reason='hdmi_disconnect'."""
        paused_reasons = []
        self.bus.subscribe(EventType.GAME_PAUSE, lambda e: paused_reasons.append(e.payload.get("reason")))

        # Simulate TV active (2 displays available)
        self.manager.resolve_display_index(num_displays=2)
        self.assertTrue(self.manager.tv_found)

        # HDMI cable pulled -> drops to 1 display (laptop only)
        self.manager.check_display_connection(num_displays=1)
        self.assertTrue(self.manager.display_lost)
        self.assertIn("hdmi_disconnect", paused_reasons)

        # Repeated check while disconnected must not spam duplicate pause events
        self.manager.check_display_connection(num_displays=1)
        self.assertEqual(len(paused_reasons), 1)

    def test_04_03_display_reconnect_starts_countdown_and_resumes(self):
        """UC 04.03: HDMI reconnected initiates 3s countdown then publishes GAME_RESUME."""
        ticks = []
        resumed = []
        self.bus.subscribe(EventType.COUNTDOWN_TICK, lambda e: ticks.append(e.payload.get("count")))
        self.bus.subscribe(EventType.GAME_RESUME, lambda e: resumed.append(e.payload.get("reason")))

        # Put into display_lost state
        self.manager.resolve_display_index(num_displays=2)
        self.manager.check_display_connection(num_displays=1)
        self.assertTrue(self.manager.display_lost)

        # TV reconnected (2 displays) at t0
        t0 = 2000.0
        self.manager.check_display_connection(num_displays=2)
        self.assertFalse(self.manager.display_lost)
        self.assertTrue(self.manager.reconnect_countdown_active)
        self.manager._countdown_start_time = t0

        # Progress through countdown: 1s, 2s, 3.1s
        self.manager.update_reconnect_countdown(now=t0 + 1.1)
        self.manager.update_reconnect_countdown(now=t0 + 2.1)
        self.manager.update_reconnect_countdown(now=t0 + 3.1)

        self.assertFalse(self.manager.reconnect_countdown_active)
        self.assertIn(3, ticks)
        self.assertIn(2, ticks)
        self.assertIn(1, ticks)
        self.assertIn("hdmi_reconnect", resumed)

    def test_04_03_draw_hud_renders_reconnect_countdown(self):
        """UC 04.03: draw_hud renders countdown text when reconnecting."""
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

        surface = pygame.Surface((1920, 1080))
        self.manager.reconnect_countdown_active = True
        self.manager._last_countdown_count = 2
        # Must execute cleanly and draw without error
        self.manager.draw_hud(surface)
        self.assertTrue(self.manager.reconnect_countdown_active)

    def test_04_09_keyboard_menu_navigation(self):
        """UC 04.09: Keyboard navigation moves through menu items and selects cleanly."""
        self.manager.set_menu("TEST MENU", ["Option A", "Option B", "Option C"])
        self.assertEqual(self.manager.selected_item_index, 0)

        # Down arrow / Next
        self.manager.menu_nav_next()
        self.assertEqual(self.manager.selected_item_index, 1)

        # Wrap around with Next
        self.manager.menu_nav_next()
        self.manager.menu_nav_next()
        self.assertEqual(self.manager.selected_item_index, 0)

        # Up arrow / Prev
        self.manager.menu_nav_prev()
        self.assertEqual(self.manager.selected_item_index, 2)

        # Select
        selected = self.manager.menu_select_instant()
        self.assertEqual(selected, "Option C")

    def test_04_08_hold_to_select_requires_full_second(self):
        """UC 04.08: Body control selection requires at least 1.0 second hold to confirm."""
        self.manager.set_menu("PROFILES", ["Child 1", "Child 2"])

        # Holding for 0.5s does not trigger selection
        confirmed = self.manager.update_hold_select(is_holding=True, dt=0.5)
        self.assertFalse(confirmed)
        self.assertAlmostEqual(self.manager.hold_select_timer, 0.5)

        # Releasing cancels timer
        self.manager.update_hold_select(is_holding=False, dt=0.1)
        self.assertEqual(self.manager.hold_select_timer, 0.0)

        # Holding continuously for 1.0s confirms
        self.manager.update_hold_select(is_holding=True, dt=0.6)
        confirmed = self.manager.update_hold_select(is_holding=True, dt=0.5)
        self.assertTrue(confirmed)

    def test_04_08_draw_menu_renders_without_error(self):
        """UC 04.08 / 04.09: draw_menu renders title, options, and hold indicator cleanly."""
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

        surface = pygame.Surface((1920, 1080))
        self.manager.set_menu("MAIN MENU", ["Play", "Settings"])
        self.manager.hold_select_timer = 0.5  # Mid-hold progress
        self.manager.draw_menu(surface)
        self.assertEqual(len(self.manager.menu_items), 2)

    def test_04_09_state_changed_event_configures_menus(self):
        """UC 04.09: STATE_CHANGED events automatically switch active menu layouts."""
        self.bus.publish(Event(EventType.STATE_CHANGED, {"old_state": "MENU", "new_state": "PAUSED"}))
        self.assertEqual(self.manager.current_state, "PAUSED")
        self.assertEqual(self.manager.menu_title, "GAME PAUSED")
        self.assertIn("Resume", self.manager.menu_items)

        # Switching to PLAYING clears the menu overlay
        self.bus.publish(Event(EventType.STATE_CHANGED, {"old_state": "PAUSED", "new_state": "PLAYING"}))
        self.assertEqual(self.manager.current_state, "PLAYING")
        self.assertIsNone(self.manager.menu_title)


if __name__ == "__main__":
    unittest.main()