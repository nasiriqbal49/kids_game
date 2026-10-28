from dataclasses import dataclass
from typing import Optional


@dataclass
class Obstacle:
    """
    Represents an obstacle on the track.
    Types:
      - 'low_hurdle': Cleared by JUMP (UC 07.01)
      - 'high_bar': Cleared by DUCK (UC 07.05)
      - 'lane_barrier': Cleared by changing lanes (LEAN) (UC 07.14)
    """
    obstacle_id: str
    obstacle_type: str
    action_required: str       # "JUMP", "DUCK", or "LEAN"
    lane: int = 1              # 0 = Left, 1 = Center, 2 = Right
    z_position: float = 1000.0 # Distance along track (counts down to 0 at player)
    depth: float = 60.0        # Collision window depth
    cleared: bool = False
    hit: bool = False
    timing_feedback: Optional[str] = None  # "too_early", "too_late", "jumped_into_bar" (UC 07.04)


@dataclass
class PowerUp:
    """
    Represents a collectible power-up item.
    Types:
      - 'shield': Absorbs 1 hit without health loss (UC 07.08)
      - 'slow_down': Reduces track speed (UC 07.13)
      - 'double_points': Doubles score points (UC 07.06)
      - 'health_refill': Restores health or converts to bonus points if full (UC 07.09)
    """
    powerup_id: str
    powerup_type: str
    duration_sec: float = 10.0
    lane: int = 1
    z_position: float = 1000.0
    collected: bool = False