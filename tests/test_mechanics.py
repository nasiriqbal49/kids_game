import unittest
from core.events import Event, EventType
from core.event_bus import EventBus
from engine.mechanics.entities import Obstacle, PowerUp
from engine.mechanics.manager import MechanicsManager


class FakeConfig:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


class TestMechanicsModule(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.cfg = FakeConfig({"gameplay.forgiving_hitbox": True})
        self.mechanics = MechanicsManager(bus=self.bus, cfg=self.cfg)
        self.cleared_events = []
        self.hit_events = []
        self.expired_events = []
        self.bus.subscribe(EventType.OBSTACLE_CLEARED, lambda e: self.cleared_events.append(e.payload))
        self.bus.subscribe(EventType.OBSTACLE_HIT, lambda e: self.hit_events.append(e.payload))
        self.bus.subscribe(EventType.POWERUP_EXPIRED, lambda e: self.expired_events.append(e.payload))

    def test_07_01_jump_clears_low_obstacle(self):
        """UC 07.01: JUMP action clears low_hurdle, adds points and increments streak."""
        obstacle = Obstacle("obs_1", "low_hurdle", action_required="JUMP")

        # Player jumps
        self.bus.publish(Event(EventType.JUMP))
        result = self.mechanics.check_obstacle_interaction(obstacle)

        self.assertEqual(result, "CLEARED")
        self.assertTrue(obstacle.cleared)
        self.assertEqual(self.mechanics.score, 50)
        self.assertEqual(self.mechanics.streak, 1)
        self.assertEqual(len(self.cleared_events), 1)

    def test_07_02_obstacle_hit_damages_and_triggers_invulnerability(self):
        """UC 07.02: Standing into a low_hurdle deals damage and triggers 1.0s invulnerability."""
        obstacle = Obstacle("obs_1", "low_hurdle", action_required="JUMP")

        # Player is standing
        self.mechanics.player_action = "STAND"
        result = self.mechanics.check_obstacle_interaction(obstacle)

        self.assertEqual(result, "HIT")
        self.assertEqual(self.mechanics.health, 80)
        self.assertEqual(self.mechanics.streak, 0)
        self.assertEqual(self.mechanics.invulnerable_timer, 1.0)
        self.assertEqual(len(self.hit_events), 1)

    def test_07_03_two_collisions_in_one_frame_only_hit_once(self):
        """UC 07.03: Rapid collisions within invulnerability window deal damage only once."""
        obs1 = Obstacle("obs_1", "low_hurdle", action_required="JUMP")
        obs2 = Obstacle("obs_2", "low_hurdle", action_required="JUMP")

        self.mechanics.player_action = "STAND"
        res1 = self.mechanics.check_obstacle_interaction(obs1)
        res2 = self.mechanics.check_obstacle_interaction(obs2)

        self.assertEqual(res1, "HIT")
        self.assertEqual(res2, "IGNORED_INVULNERABLE")
        self.assertEqual(self.mechanics.health, 80)
        self.assertEqual(len(self.hit_events), 1)

    def test_07_04_timing_feedback_recorded_on_collision(self):
        """UC 07.04: Standing into an obstacle records timing feedback 'too_late'."""
        obstacle = Obstacle("obs_1", "low_hurdle", action_required="JUMP")
        self.mechanics.player_action = "STAND"
        self.mechanics.check_obstacle_interaction(obstacle)

        self.assertEqual(obstacle.timing_feedback, "too_late")

    def test_07_05_duck_clears_high_bar(self):
        """UC 07.05: DUCK action clears high_bar; standing or jumping collides."""
        obstacle = Obstacle("bar_1", "high_bar", action_required="DUCK")

        self.bus.publish(Event(EventType.DUCK))
        res = self.mechanics.check_obstacle_interaction(obstacle)

        self.assertEqual(res, "CLEARED")
        self.assertTrue(obstacle.cleared)

    def test_07_06_powerup_expiration_event_fired(self):
        """UC 07.06: Expired power-ups trigger POWERUP_EXPIRED event and are removed."""
        pup = PowerUp("p_shield", "shield", duration_sec=1.5)
        self.mechanics.collect_powerup(pup)
        self.assertIn("shield", self.mechanics.active_powerups)

        self.mechanics.update(2.0)  # Exceeds duration
        self.assertNotIn("shield", self.mechanics.active_powerups)
        self.assertEqual(len(self.expired_events), 1)
        self.assertEqual(self.expired_events[0]["powerup_type"], "shield")

    def test_07_07_powerup_timer_refreshes_on_duplicate(self):
        """UC 07.07: Collecting the same power-up type refreshes its duration timer."""
        p1 = PowerUp("p_1", "double_points", duration_sec=5.0)
        p2 = PowerUp("p_2", "double_points", duration_sec=10.0)

        self.mechanics.collect_powerup(p1)
        self.mechanics.update(2.0)
        self.assertAlmostEqual(self.mechanics.active_powerups["double_points"], 3.0)

        self.mechanics.collect_powerup(p2)
        self.assertAlmostEqual(self.mechanics.active_powerups["double_points"], 10.0)

    def test_07_08_shield_absorbs_hit_without_health_loss(self):
        """UC 07.08: Shield absorbs collision: shield is consumed, health is not lost."""
        shield = PowerUp("p_1", "shield", duration_sec=5.0)
        obstacle = Obstacle("obs_1", "low_hurdle", action_required="JUMP")

        self.mechanics.collect_powerup(shield)
        self.mechanics.player_action = "STAND"
        res = self.mechanics.check_obstacle_interaction(obstacle)

        self.assertEqual(res, "HIT")
        self.assertEqual(self.mechanics.health, 100)
        self.assertNotIn("shield", self.mechanics.active_powerups)

    def test_07_09_health_refill_at_full_health_awards_bonus_points(self):
        """UC 07.09: Health refill at 100% health does not overflow; awards bonus points."""
        refill = PowerUp("p_heal", "health_refill", duration_sec=0.0)

        self.mechanics.score = 500
        self.mechanics.health = 100
        self.mechanics.collect_powerup(refill)

        self.assertEqual(self.mechanics.health, 100)
        self.assertEqual(self.mechanics.score, 600)

    def test_07_10_spawner_enforces_minimum_clearable_gap(self):
        """UC 07.10: Spawner enforces minimum gap to prevent impossible obstacle sequences."""
        self.mechanics.spawn_obstacle("obs_1", "low_hurdle", "JUMP", z_pos=1000.0)

        # Gap is only 100 units at speed 1.0 (minimum is 500) -> rejected
        can_spawn_too_close = self.mechanics.can_spawn_obstacle(z_pos=1100.0, speed=1.0)
        self.assertFalse(can_spawn_too_close)

        # Gap is 600 units -> accepted
        can_spawn_safe = self.mechanics.can_spawn_obstacle(z_pos=1600.0, speed=1.0)
        self.assertTrue(can_spawn_safe)

    def test_07_11_streak_resets_on_hit(self):
        """UC 07.11: Streak resets to 0 and multiplier drops to 1.0 on obstacle hit."""
        self.mechanics.streak = 8
        obstacle = Obstacle("obs_1", "low_hurdle", action_required="JUMP")

        self.mechanics.player_action = "STAND"
        self.mechanics.check_obstacle_interaction(obstacle)

        self.assertEqual(self.mechanics.streak, 0)
        self.assertEqual(self.mechanics.multiplier, 1.0)

    def test_07_12_airborne_player_hits_high_bar(self):
        """UC 07.12: Jumping into an overhead high bar counts as a collision."""
        bar = Obstacle("bar_1", "high_bar", action_required="DUCK")

        # Player is jumping (airborne)
        self.mechanics.player_action = "JUMP"
        res = self.mechanics.check_obstacle_interaction(bar)

        self.assertEqual(res, "HIT")
        self.assertEqual(bar.timing_feedback, "jumped_into_bar")

    def test_07_13_slow_down_powerup_scales_speed(self):
        """UC 07.13: Active slow_down power-up reduces effective speed."""
        base_speed = 1.5
        self.assertEqual(self.mechanics.get_effective_speed(base_speed), 1.5)

        slow_pup = PowerUp("p_slow", "slow_down", duration_sec=5.0)
        self.mechanics.collect_powerup(slow_pup)

        effective = self.mechanics.get_effective_speed(base_speed)
        self.assertAlmostEqual(effective, 0.9)  # 1.5 * 0.6 = 0.9

    def test_07_14_lane_barrier_avoided_by_changing_lane(self):
        """UC 07.14: Lane barrier collides if player is in the barrier lane, clears if player changed lanes."""
        barrier = Obstacle("b_1", "lane_barrier", action_required="LEAN", lane=1)

        # Player is in Lane 0 (Left lane) -> avoided and cleared
        self.mechanics.player_lane = 0
        res = self.mechanics.check_obstacle_interaction(barrier)
        self.assertEqual(res, "CLEARED")

        # Second barrier at Lane 0, player still in Lane 0 -> collision
        barrier2 = Obstacle("b_2", "lane_barrier", action_required="LEAN", lane=0)
        self.mechanics.invulnerable_timer = 0.0  # Clear invulnerability for test
        res2 = self.mechanics.check_obstacle_interaction(barrier2)
        self.assertEqual(res2, "HIT")

    def test_07_15_offscreen_obstacles_pruned_flat_memory(self):
        """UC 07.15: Obstacles scrolled past the player (z < -100) are purged to keep memory flat."""
        self.mechanics.spawn_obstacle("obs_1", "low_hurdle", "JUMP", z_pos=50.0)
        self.mechanics.spawn_obstacle("obs_2", "low_hurdle", "JUMP", z_pos=500.0)
        self.assertEqual(len(self.mechanics.obstacles), 2)

        # World scrolls forward by 200 units -> obs_1 moves to -150 and is purged
        self.mechanics.advance_world(200.0)

        self.assertEqual(len(self.mechanics.obstacles), 1)
        self.assertEqual(self.mechanics.obstacles[0].obstacle_id, "obs_2")


if __name__ == "__main__":
    unittest.main()