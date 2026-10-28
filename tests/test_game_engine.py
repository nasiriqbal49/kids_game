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


if __name__ == "__main__":
    unittest.main()