import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from core.events import Event, EventType
from core.event_bus import EventBus
from engine.game_engine import GameState
from engine.games.spooky_red_light import SpookyRedLightGame, LightState


class FakeConfig:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


class TestSpookyRedLightGame(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.bus = EventBus()
        self.cfg = FakeConfig({
            "display.render_width": 1920,
            "display.render_height": 1080,
            "display.fullscreen": False,
        })
        self.game = SpookyRedLightGame(bus=self.bus, cfg=self.cfg)

    def tearDown(self):
        self.game.display.close()
        self.game.audio.close()

    def test_green_light_creeping_advances_distance(self):
        """Moving forward during GREEN light advances distance progress to TV."""
        self.game.start_new_game()
        self.assertEqual(self.game.light, LightState.GREEN)
        self.assertEqual(self.game.progress_distance, 0.0)

        # Baseline position at foot_y = 0.50
        self.game.evaluate_player_movement(foot_x=0.50, foot_y=0.50, dt=0.1)

        # Creep closer to TV (foot_y moves to 0.55)
        self.game.evaluate_player_movement(foot_x=0.50, foot_y=0.55, dt=0.1)

        self.assertGreater(self.game.progress_distance, 0.0)

    def test_red_light_movement_triggers_caught_jumpscare(self):
        """Moving during RED light triggers CAUGHT state and penalizes distance."""
        self.game.start_new_game()
        self.game.light = LightState.RED
        self.game.progress_distance = 0.50  # Halfway to TV

        # Baseline pose
        self.game.evaluate_player_movement(foot_x=0.50, foot_y=0.60, dt=0.1)

        # Movement during Red Light! (wobble > 0.030 tolerance)
        self.game.evaluate_player_movement(foot_x=0.58, foot_y=0.60, dt=0.1)

        self.assertEqual(self.game.light, LightState.CAUGHT)
        self.assertEqual(self.game.times_caught, 1)
        self.assertLess(self.game.progress_distance, 0.50)  # Sent backwards!

    def test_reaching_tv_triggers_victory_and_coins(self):
        """Reaching 100% distance triggers VICTORY, awards +200 points and +25 coins."""
        self.game.start_new_game()
        self.game.progress_distance = 0.95

        # Take final step to TV
        self.game.advance_manually(amount=0.10)

        self.assertEqual(self.game.light, LightState.VICTORY)
        self.assertEqual(self.game.score, 200)
        self.assertEqual(self.game.coins, 25)
        self.assertEqual(self.game.rounds_survived, 1)


if __name__ == "__main__":
    unittest.main()