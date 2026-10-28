from typing import Dict, List, Optional
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from engine.mechanics.entities import Obstacle, PowerUp

log = get_logger("mechanics")


class MechanicsManager:
    """
    Reusable gameplay mechanics library (Module 7):
    - Health, damage, and invulnerability window (UC 07.02, 07.03)
    - Score, streaks, and multipliers (UC 07.01, 07.11)
    - Collision verification against player posture/actions (UC 07.01, 07.05, 07.12, 07.14)
    - Power-ups lifecycle, duration, shield absorption, and slow-down (UC 07.06 - 07.09, 07.13)
    - Minimum spawn spacing and off-screen object pruning (UC 07.10, 07.15)
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        # Health & State
        self.health: int = 100
        self.max_health: int = 100
        self.invulnerable_timer: float = 0.0
        self.invulnerability_duration_sec: float = 1.0  # 1s invulnerability (UC 07.02)
        self.forgiving_hitbox: bool = self.config.get("gameplay.forgiving_hitbox", True)

        # Score & Streak (UC 07.01, 07.11)
        self.score: int = 0
        self.streak: int = 0
        self.base_points_per_clear: int = 50

        # Power-ups (UC 07.06 - 07.09, 07.13)
        self.active_powerups: Dict[str, float] = {}  # {powerup_type: duration_remaining}

        # Player Posture Tracking
        self.player_action: str = "STAND"
        self.player_lane: int = 1  # 0 = Left, 1 = Center, 2 = Right

        # Obstacles & Power-ups tracked in world
        self.obstacles: List[Obstacle] = []
        self.powerups: List[PowerUp] = []

        self._subscribe_events()

    def _subscribe_events(self) -> None:
        """Subscribe to player input actions from EventBus."""
        self.bus.subscribe(EventType.JUMP, lambda e: self._set_action("JUMP"))
        self.bus.subscribe(EventType.LAND, lambda e: self._set_action("STAND"))
        self.bus.subscribe(EventType.DUCK, lambda e: self._set_action("DUCK"))
        self.bus.subscribe(EventType.STAND, lambda e: self._set_action("STAND"))
        self.bus.subscribe(EventType.LEAN_LEFT, lambda e: self._set_lane(0, "LEAN_LEFT"))
        self.bus.subscribe(EventType.LEAN_CENTER, lambda e: self._set_lane(1, "STAND"))
        self.bus.subscribe(EventType.LEAN_RIGHT, lambda e: self._set_lane(2, "LEAN_RIGHT"))

    def _set_action(self, action: str) -> None:
        self.player_action = action

    def _set_lane(self, lane: int, action: str) -> None:
        self.player_lane = lane
        self.player_action = action

    @property
    def multiplier(self) -> float:
        """Calculates current streak & power-up score multiplier (UC 07.01, 07.06)."""
        mult = 1.0 + (self.streak // 5) * 0.5
        if "double_points" in self.active_powerups:
            mult *= 2.0
        return mult

    def get_effective_speed(self, base_speed: float) -> float:
        """Applies power-up multipliers (e.g. slow_down) on top of difficulty speed (UC 07.13)."""
        if "slow_down" in self.active_powerups:
            return round(base_speed * 0.6, 2)
        return base_speed

    def compute_min_spacing(self, speed: float, jump_air_time: float = 0.5, reaction_sec: float = 0.5) -> float:
        """Calculates minimum safe spawn distance so obstacles are always physically clearable (UC 07.10)."""
        speed_units = speed * 500.0
        return speed_units * (jump_air_time + reaction_sec)

    def can_spawn_obstacle(self, z_pos: float, speed: float) -> bool:
        """Checks that the candidate spawn position satisfies minimum spacing from the nearest obstacle (UC 07.10)."""
        min_gap = self.compute_min_spacing(speed)
        for obs in self.obstacles:
            if abs(obs.z_position - z_pos) < min_gap:
                return False
        return True

    def spawn_obstacle(self, obstacle_id: str, obstacle_type: str, action_required: str,
                       lane: int = 1, z_pos: float = 1000.0) -> Obstacle:
        obs = Obstacle(obstacle_id, obstacle_type, action_required=action_required, lane=lane, z_position=z_pos)
        self.obstacles.append(obs)
        return obs

    def spawn_powerup(self, powerup_id: str, powerup_type: str, duration_sec: float = 10.0,
                      lane: int = 1, z_pos: float = 1000.0) -> PowerUp:
        pup = PowerUp(powerup_id, powerup_type, duration_sec=duration_sec, lane=lane, z_position=z_pos)
        self.powerups.append(pup)
        return pup

    def advance_world(self, distance: float) -> None:
        """Moves obstacles and powerups along the track and purges off-screen entities (UC 07.15)."""
        for obs in self.obstacles:
            obs.z_position -= distance
        for pup in self.powerups:
            pup.z_position -= distance

        # Prune off-screen entities (passed z = -100) to keep memory flat (UC 07.15)
        self.obstacles = [o for o in self.obstacles if o.z_position >= -100.0]
        self.powerups = [p for p in self.powerups if p.z_position >= -100.0]

    def check_obstacle_interaction(self, obstacle: Obstacle) -> str:
        """
        Evaluates player interaction with an obstacle reaching the player plane
        (UC 07.01, 07.02, 07.04, 07.05, 07.08, 07.12, 07.14).
        Returns: 'CLEARED', 'HIT', or 'IGNORED_INVULNERABLE'
        """
        if obstacle.cleared or obstacle.hit:
            return "ALREADY_RESOLVED"

        # 1. Check if player's action clears the obstacle
        is_cleared = False
        if obstacle.obstacle_type == "lane_barrier":
            is_cleared = (self.player_lane != obstacle.lane)
        elif obstacle.action_required == "JUMP":
            if self.player_action == "JUMP":
                is_cleared = True
            else:
                obstacle.timing_feedback = "too_late"
        elif obstacle.action_required == "DUCK":
            if self.player_action == "DUCK":
                is_cleared = True
            elif self.player_action == "JUMP":
                # Airborne player collides with overhead bar (UC 07.12)
                obstacle.timing_feedback = "jumped_into_bar"
            else:
                obstacle.timing_feedback = "standing_hit"

        if is_cleared:
            obstacle.cleared = True
            points = int(self.base_points_per_clear * self.multiplier)
            self.score += points
            self.streak += 1

            self.bus.publish(Event(EventType.OBSTACLE_CLEARED, {
                "obstacle_type": obstacle.obstacle_type,
                "points": points
            }))
            self.bus.publish(Event(EventType.SCORE_CHANGED, {
                "score": self.score,
                "delta": points
            }))
            self.bus.publish(Event(EventType.STREAK_CHANGED, {
                "streak": self.streak,
                "multiplier": self.multiplier
            }))
            return "CLEARED"

        # 2. Collision occurred
        obstacle.hit = True

        # Check invulnerability window (UC 07.02, 07.03)
        if self.invulnerable_timer > 0.0:
            return "IGNORED_INVULNERABLE"

        # Check Shield absorption (UC 07.08)
        if "shield" in self.active_powerups:
            del self.active_powerups["shield"]
            self.invulnerable_timer = 0.5  # Brief safety grace after shield pop
            log.info("Shield absorbed obstacle hit! (UC 07.08)")
            self.bus.publish(Event(EventType.POWERUP_EXPIRED, {"powerup_type": "shield"}))
            return "HIT"

        # Damage applied
        damage = 20
        self.health = max(0, self.health - damage)
        self.streak = 0
        self.invulnerable_timer = self.invulnerability_duration_sec

        self.bus.publish(Event(EventType.OBSTACLE_HIT, {
            "obstacle_type": obstacle.obstacle_type
        }))
        self.bus.publish(Event(EventType.HEALTH_CHANGED, {
            "current": self.health,
            "max": self.max_health,
            "delta": -damage,
            "is_low": self.health <= 25
        }))
        self.bus.publish(Event(EventType.STREAK_CHANGED, {
            "streak": 0,
            "multiplier": 1.0
        }))
        return "HIT"

    def collect_powerup(self, powerup: PowerUp) -> None:
        """Collects a power-up and applies its effect (UC 07.06 - 07.09)."""
        if powerup.collected:
            return

        powerup.collected = True

        # Instant effect: Health Refill (UC 07.09)
        if powerup.powerup_type == "health_refill":
            if self.health >= self.max_health:
                bonus = 100
                self.score += bonus
                self.bus.publish(Event(EventType.SCORE_CHANGED, {"score": self.score, "delta": bonus}))
            else:
                heal = 30
                self.health = min(self.max_health, self.health + heal)
                self.bus.publish(Event(EventType.HEALTH_CHANGED, {
                    "current": self.health,
                    "max": self.max_health,
                    "delta": heal,
                    "is_low": self.health <= 25
                }))
            self.bus.publish(Event(EventType.POWERUP_COLLECTED, {
                "powerup_type": "health_refill",
                "duration_sec": 0.0
            }))
            return

        # Timed effects (shield, slow_down, double_points)
        self.active_powerups[powerup.powerup_type] = powerup.duration_sec

        self.bus.publish(Event(EventType.POWERUP_COLLECTED, {
            "powerup_type": powerup.powerup_type,
            "duration_sec": powerup.duration_sec
        }))

    def update(self, dt: float) -> None:
        """Advances active timers and expires power-ups (UC 07.06)."""
        # Invulnerability cooldown (UC 07.02)
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)

        # Power-up durations
        expired = []
        for p_type, remaining in self.active_powerups.items():
            new_remaining = remaining - dt
            if new_remaining <= 0.0:
                expired.append(p_type)
            else:
                self.active_powerups[p_type] = new_remaining

        for p_type in expired:
            del self.active_powerups[p_type]
            self.bus.publish(Event(EventType.POWERUP_EXPIRED, {"powerup_type": p_type}))