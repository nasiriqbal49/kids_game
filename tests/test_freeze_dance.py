import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from core.events import Event, EventType
from core.event_bus import EventBus
from engine.game_engine import GameState
from engine.games.freeze_dance import FreezeDanceGame, DancePhase


class FakeConfig:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


class TestFreezeDanceGame(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.bus = EventBus()
        self.cfg = FakeConfig({
            "display.render_width": 1920,
            "display.render_height": 1080,
            "display.fullscreen": False,
        })
        self.game = FreezeDanceGame(bus=self.bus, cfg=self.cfg)

    def tearDown(self):
        self.game.display.close()
        self.game.audio.close()

    def test_18_03_successful_freeze_under_tolerance_awards_points(self):
        """UC 18.03: Holding still during FREEZE for 2.0s awards bonus points and coins."""
        self.game.start_new_game()
        self.game.phase = DancePhase.FREEZING
        self.game.freeze_hold_timer = 0.0

        # Feed 2.1s of perfectly still pose (jitter < 0.035)
        for _ in range(21):
            self.game.evaluate_body_pose(hip_x=0.50, hip_y=0.60, dt=0.1)

        self.assertEqual(self.game.freezes_mastered, 1)
        self.assertEqual(self.game.score, 100)
        self.assertEqual(self.game.coins, 5)
        self.assertEqual(self.game.phase, DancePhase.ROUND_SUCCESS)

    def test_18_04_movement_during_freeze_triggers_wobble_strike(self):
        """UC 18.04: Moving beyond tolerance during FREEZE inflicts a strike."""
        self.game.start_new_game()
        self.game.phase = DancePhase.FREEZING
        self.assertEqual(self.game.strikes, 0)

        # Baseline pose
        self.game.evaluate_body_pose(hip_x=0.50, hip_y=0.60, dt=0.1)

        # Sudden movement (hip shifts to 0.58 > 0.035 tolerance)
        self.game.evaluate_body_pose(hip_x=0.58, hip_y=0.60, dt=0.1)

        self.assertEqual(self.game.strikes, 1)

    def test_floor_is_lava_safe_during_jump_or_flamingo_balance(self):
        """Floor is Lava phase survives if jumping or holding 1-leg Flamingo balance."""
        self.game.start_new_game()
        self.game.phase = DancePhase.FLOOR_LAVA
        self.assertFalse(self.game.player_safe_from_lava)

        # Child does a Flamingo 1-leg balance
        self.bus.publish(Event(EventType.FLAMINGO_BALANCE))
        self.assertTrue(self.game.player_safe_from_lava)

        # Advance timer past 2.5s
        self.game.update(2.6)
        self.assertEqual(self.game.lava_survived, 1)
        self.assertEqual(self.game.score, 150)
        self.assertEqual(self.game.coins, 10)

    def test_three_strikes_triggers_game_over(self):
        """3 wobble strikes triggers GAME_OVER."""
        self.game.start_new_game()
        self.game.strikes = 2
        self.game.phase = DancePhase.FREEZING

        self.game.evaluate_body_pose(hip_x=0.50, hip_y=0.60, dt=0.1)
        self.game.evaluate_body_pose(hip_x=0.65, hip_y=0.60, dt=0.1)  # 3rd strike!

        self.assertEqual(self.game.strikes, 3)
        self.assertEqual(self.game.engine.state, GameState.RESULTS)


if __name__ == "__main__":
    unittest.main()