import unittest
from core.events import Event, EventType
from core.event_bus import EventBus
from engine.game_engine import GameEngine, GameState


class TestGameEngine(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.engine = GameEngine(bus=self.bus)
        self.state_changes = []
        self.bus.subscribe(EventType.STATE_CHANGED, lambda e: self.state_changes.append(e.payload))

    def test_06_01_normal_state_progression(self):
        """UC 06.01: Normal game progression moves legally through states."""
        self.assertEqual(self.engine.state, GameState.MENU)

        # MENU -> PROFILE_SELECT -> COUNTDOWN -> PLAYING
        self.assertTrue(self.engine.transition_to(GameState.PROFILE_SELECT))
        self.assertTrue(self.engine.transition_to(GameState.COUNTDOWN))
        self.assertTrue(self.engine.transition_to(GameState.PLAYING))

        self.assertEqual(self.engine.state, GameState.PLAYING)
        self.assertEqual(len(self.state_changes), 3)

    def test_06_02_illegal_transition_rejected_with_safe_route_to_menu(self):
        """UC 06.02: Illegal transitions are rejected, but route back to MENU is always permitted."""
        self.assertEqual(self.engine.state, GameState.MENU)

        # Illegal: Cannot transition directly from MENU to RESULTS
        self.assertFalse(self.engine.transition_to(GameState.RESULTS))
        self.assertEqual(self.engine.state, GameState.MENU)

        # Move to PLAYING
        self.engine.transition_to(GameState.PLAYING)

        # Safe route: PLAYING can always safely transition back to MENU
        self.assertTrue(self.engine.transition_to(GameState.MENU))
        self.assertEqual(self.engine.state, GameState.MENU)

    def test_06_03_pause_and_resume_events(self):
        """UC 06.03: GAME_PAUSE transitions PLAYING to PAUSED; GAME_RESUME resumes to PLAYING."""
        self.engine.transition_to(GameState.PLAYING)

        # Parent key or focus loss sends GAME_PAUSE
        self.bus.publish(Event(EventType.GAME_PAUSE, {"reason": "parent_key"}))
        self.assertEqual(self.engine.state, GameState.PAUSED)

        # GAME_RESUME returns to PLAYING
        self.bus.publish(Event(EventType.GAME_RESUME, {"reason": "parent_key"}))
        self.assertEqual(self.engine.state, GameState.PLAYING)

    def test_06_05_health_zero_triggers_game_over_and_results(self):
        """UC 06.05: Health reaching zero triggers GAME_OVER event and moves to RESULTS."""
        game_over_events = []
        self.bus.subscribe(EventType.GAME_OVER, lambda e: game_over_events.append(e.payload))

        self.engine.transition_to(GameState.PLAYING)
        self.engine.score = 500
        self.engine.streak = 6

        # Health drops to 0
        self.bus.publish(Event(EventType.HEALTH_CHANGED, {"current": 0, "max": 100, "delta": -20}))

        # Must have fired GAME_OVER with statistics
        self.assertEqual(len(game_over_events), 1)
        self.assertEqual(game_over_events[0]["final_score"], 500)
        self.assertEqual(game_over_events[0]["longest_streak"], 6)

        # Engine ends in RESULTS state
        self.assertEqual(self.engine.state, GameState.RESULTS)

    def test_06_11_reset_game_clears_metrics(self):
        """UC 06.11: reset_game resets score, streak, and health to defaults."""
        self.engine.score = 1200
        self.engine.streak = 15
        self.engine.health = 20

        self.engine.reset_game()

        self.assertEqual(self.engine.score, 0)
        self.assertEqual(self.engine.streak, 0)
        self.assertEqual(self.engine.health, 100)

    def test_06_04_out_of_zone_grace_period_and_autopause(self):
        """UC 06.04: Stepping out of zone auto-pauses after 1.0s grace period."""
        paused_reasons = []
        self.bus.subscribe(EventType.GAME_PAUSE, lambda e: paused_reasons.append(e.payload.get("reason")))

        self.engine.transition_to(GameState.PLAYING)

        # Player steps out of zone
        self.bus.publish(Event(EventType.PLAYER_OUT_OF_ZONE))
        self.assertFalse(self.engine.player_in_zone)

        # 0.5s elapsed (within grace period) -> no pause
        self.engine.tick(0.5)
        self.assertEqual(len(paused_reasons), 0)

        # Another 0.6s elapsed (total 1.1s > 1.0s grace) -> triggers auto-pause
        self.engine.tick(0.6)
        self.assertIn("out_of_zone", paused_reasons)

    def test_06_06_difficulty_speed_ramps_smoothly_to_cap(self):
        """UC 06.06: Speed rises smoothly with distance/time up to speed_cap."""
        self.engine.transition_to(GameState.PLAYING)
        self.engine.speed_ramp_rate = 0.1  # Fast ramp for testing
        self.engine.speed_cap = 1.5

        # Advance 2 seconds
        for _ in range(120):
            self.engine.tick(1.0 / 60.0)

        self.assertGreater(self.engine.current_speed, 1.1)

        # Advance another 10 seconds -> must be capped at 1.5
        for _ in range(600):
            self.engine.tick(1.0 / 60.0)

        self.assertEqual(self.engine.current_speed, 1.5)

    def test_06_07_frame_spike_accumulator_clamp(self):
        """UC 06.07: Huge frame time spikes are clamped to max_catch_up_steps."""
        self.engine.transition_to(GameState.PLAYING)

        # Simulate a 1.0 second lag spike (60 missed frames)
        steps_executed = self.engine.tick(1.0)

        # Must not execute 60 steps (prevents death spiral), clamped to max 5
        self.assertEqual(steps_executed, self.engine.max_catch_up_steps)
        self.assertEqual(self.engine._accumulator, 0.0)

    def test_06_09_idle_timeout_returns_to_menu(self):
        """UC 06.09: Idle paused game returns to MENU after idle_timeout_sec."""
        self.engine.transition_to(GameState.PLAYING)
        self.engine.transition_to(GameState.PAUSED)
        self.engine.idle_timeout_sec = 10.0  # Set short for test

        # 5 seconds elapsed -> still paused
        self.engine.tick(5.0)
        self.assertEqual(self.engine.state, GameState.PAUSED)

        # Total 11 seconds elapsed -> returns to MENU
        self.engine.tick(6.0)
        self.assertEqual(self.engine.state, GameState.MENU)

if __name__ == "__main__":
    unittest.main()