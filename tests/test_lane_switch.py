import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from core.events import Event, EventType
from core.event_bus import EventBus
from engine.game_engine import GameState
from engine.games.lane_switch import LaneSwitchGame


class FakeConfig:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


class TestLaneSwitchGame(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.bus = EventBus()
        self.cfg = FakeConfig({
            "display.render_width": 1920,
            "display.render_height": 1080,
            "display.fullscreen": False,
        })
        self.game = LaneSwitchGame(bus=self.bus, cfg=self.cfg)

    def tearDown(self):
        self.game.display.close()
        self.game.audio.close()

    def test_18_01_lean_events_change_lanes(self):
        """UC 18.01: LEAN_LEFT, LEAN_RIGHT, and LEAN_CENTER events move player lane."""
        self.game.start_new_game()
        self.assertEqual(self.game.current_lane, 1)  # Starts in Center

        # Lean Left
        self.bus.publish(Event(EventType.LEAN_LEFT))
        self.assertEqual(self.game.current_lane, 0)  # Left lane

        # Lean Right
        self.bus.publish(Event(EventType.LEAN_RIGHT))
        self.assertEqual(self.game.current_lane, 2)  # Right lane

        # Lean Center
        self.bus.publish(Event(EventType.LEAN_CENTER))
        self.assertEqual(self.game.current_lane, 1)  # Center lane

    def test_18_02_edge_lanes_are_strictly_clamped(self):
        """UC 18.02: Leaning hard at the edge stays clamped in that lane (never leaves road)."""
        self.game.start_new_game()

        # At Left lane (0), leaning left again stays clamped at 0
        self.game.set_lane(0)
        self.game.shift_lane_relative(-1)
        self.assertEqual(self.game.current_lane, 0)

        # At Right lane (2), leaning right again stays clamped at 2
        self.game.set_lane(2)
        self.game.shift_lane_relative(1)
        self.assertEqual(self.game.current_lane, 2)

    def test_18_08_personal_best_recorded_for_lane_switch_on_game_over(self):
        """UC 18.08: Personal best is recorded separately under lane_switch on Game Over."""
        self.game.personal_best = 300
        self.game.mechanics.score = 750

        # Trigger Game Over
        self.bus.publish(Event(EventType.GAME_OVER, {"final_score": 750}))

        self.assertEqual(self.game.personal_best, 750)
        self.assertTrue(self.game.is_new_best)

    def test_smashable_crate_mechanic(self):
        """Punch gesture smashes soft wooden crates for bonus points and coins."""
        self.game.start_new_game()
        self.game.set_lane(1)

        # Spawn crate in Lane 1 at player plane
        crate = self.game.mechanics.spawn_obstacle("crate_1", "smashable_crate", "LEAN", lane=1, z_pos=0.0)

        # Player punches (HANDS_UP)
        smashed = self.game.smash_crate()
        self.assertTrue(smashed)
        self.assertTrue(crate.cleared)
        self.assertEqual(self.game.crates_smashed, 1)
        self.assertEqual(self.game.coins_collected, 5)
        self.assertEqual(self.game.mechanics.score, 150)


if __name__ == "__main__":
    unittest.main()