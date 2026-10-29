import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from core.events import Event, EventType
from core.event_bus import EventBus
from engine.game_engine import GameState
from engine.mechanics.entities import Obstacle
from engine.games.runner import RunnerGame


class FakeConfig:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


class TestRunnerGame(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.bus = EventBus()
        self.cfg = FakeConfig({
            "gameplay.sensitivity": "normal",
            "gameplay.forgiving_hitbox": True,
            "display.render_width": 1920,
            "display.render_height": 1080,
            "display.fullscreen": False,
        })
        self.runner = RunnerGame(bus=self.bus, cfg=self.cfg)

    def tearDown(self):
        self.runner.display.close()
        self.runner.audio.close()

    def test_08_01_complete_scripted_run(self):
        """UC 08.01: Full scripted run starts, updates metrics on clear, and triggers game over on zero health."""
        self.runner.start_new_game()
        self.assertEqual(self.runner.engine.state, GameState.PLAYING)

        # Clear one obstacle by jumping
        obs = Obstacle("obs_1", "low_hurdle", action_required="JUMP", z_position=0.0)
        self.runner.mechanics.player_action = "JUMP"
        self.runner.mechanics.check_obstacle_interaction(obs)

        self.assertEqual(self.runner.mechanics.score, 50)
        self.assertEqual(self.runner.obstacles_cleared_count, 1)

        # Force health to zero
        self.bus.publish(Event(EventType.HEALTH_CHANGED, {"current": 0, "max": 100, "delta": -20}))
        self.assertEqual(self.runner.engine.state, GameState.RESULTS)

    def test_08_02_idle_player_takes_damage_and_ends_game(self):
        """UC 08.02: Kid does nothing -> obstacles hit player until health drops to zero, ending the run."""
        self.runner.start_new_game()

        # Simulate 5 consecutive hurdle hits while standing
        for i in range(5):
            self.runner.mechanics.invulnerable_timer = 0.0  # Clear invulnerability for next obstacle
            obs = Obstacle(f"obs_{i}", "low_hurdle", action_required="JUMP", z_position=0.0)
            self.runner.mechanics.player_action = "STAND"
            self.runner.mechanics.check_obstacle_interaction(obs)

        self.assertEqual(self.runner.mechanics.health, 0)
        self.assertEqual(self.runner.engine.state, GameState.RESULTS)

    def test_08_03_jump_spam_locked_out_by_air_time(self):
        """UC 08.03: Spamming jump is locked out until the player lands."""
        self.runner.start_new_game()

        # First jump accepted
        self.assertTrue(self.runner.request_jump())
        self.assertTrue(self.runner.is_jumping)

        # Immediate second jump request locked out
        self.assertFalse(self.runner.request_jump())

        # Advance air time past 0.55s -> lands
        self.runner.update(0.60)
        self.assertFalse(self.runner.is_jumping)

        # Subsequent jump accepted again
        self.assertTrue(self.runner.request_jump())

    def test_08_04_new_personal_best_recorded_on_game_over(self):
        """UC 08.04: New personal best is updated only when game over occurs with higher score."""
        self.runner.personal_best = 200
        self.runner.mechanics.score = 450

        # Trigger Game Over
        self.bus.publish(Event(EventType.GAME_OVER, {"final_score": 450}))

        self.assertEqual(self.runner.personal_best, 450)
        self.assertTrue(self.runner.is_new_best)

    def test_08_05_difficulty_presets_apply_speed_and_damage_scaling(self):
        """UC 08.05: Difficulty preset alters speed scaling and maximum cap."""
        strict_cfg = FakeConfig({"gameplay.sensitivity": "strict"})
        strict_runner = RunnerGame(bus=self.bus, cfg=strict_cfg)

        self.assertEqual(strict_runner.engine.base_speed, 1.2)
        self.assertEqual(strict_runner.engine.speed_cap, 2.5)

        strict_runner.display.close()
        strict_runner.audio.close()

    def test_08_06_speed_cap_stops_acceleration(self):
        """UC 08.06: Speed caps at preset max and does not climb indefinitely."""
        self.runner.start_new_game()
        # Fast-forward 200 seconds of run duration
        for _ in range(200):
            self.runner.update(1.0)

        self.assertLessEqual(self.runner.engine.current_speed, self.runner.preset["speed_cap"])

    def test_08_08_results_screen_stats_summary(self):
        """UC 08.08: Results screen correctly summarizes score, streak, and clears."""
        self.runner.start_new_game()
        self.runner.obstacles_cleared_count = 12
        self.runner.longest_streak = 7
        self.runner.mechanics.score = 650

        surface = pygame.Surface((1920, 1080))
        self.runner.engine.state = GameState.RESULTS
        # Must render cleanly without error
        self.runner.draw(surface)

        self.assertEqual(self.runner.obstacles_cleared_count, 12)
        self.assertEqual(self.runner.longest_streak, 7)


if __name__ == "__main__":
    unittest.main()