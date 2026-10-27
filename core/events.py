import time
from dataclasses import dataclass, field
from typing import Any, Dict


# Complete Event Catalogue defined in Section 3.3 of the Game Plan
class EventType:
    # Player actions
    JUMP = "JUMP"
    LAND = "LAND"
    DUCK = "DUCK"
    STAND = "STAND"
    LEAN_LEFT = "LEAN_LEFT"
    LEAN_RIGHT = "LEAN_RIGHT"
    LEAN_CENTER = "LEAN_CENTER"
    HANDS_UP = "HANDS_UP"
    STEP_LEFT = "STEP_LEFT"
    STEP_RIGHT = "STEP_RIGHT"
    POSE_MATCHED = "POSE_MATCHED"

    # Player state
    PLAYER_DETECTED = "PLAYER_DETECTED"
    PLAYER_LOST = "PLAYER_LOST"
    PLAYER_LOCKED = "PLAYER_LOCKED"
    PLAYER_IN_ZONE = "PLAYER_IN_ZONE"
    PLAYER_OUT_OF_ZONE = "PLAYER_OUT_OF_ZONE"
    MULTIPLE_PEOPLE = "MULTIPLE_PEOPLE"

    # Camera
    CAMERA_CONNECTED = "CAMERA_CONNECTED"
    CAMERA_LOST = "CAMERA_LOST"
    CAMERA_LOW_FPS = "CAMERA_LOW_FPS"
    CAMERA_SWITCHED = "CAMERA_SWITCHED"

    # Game flow
    GAME_START = "GAME_START"
    GAME_PAUSE = "GAME_PAUSE"
    GAME_RESUME = "GAME_RESUME"
    GAME_OVER = "GAME_OVER"
    STATE_CHANGED = "STATE_CHANGED"
    COUNTDOWN_TICK = "COUNTDOWN_TICK"

    # Gameplay
    OBSTACLE_CLEARED = "OBSTACLE_CLEARED"
    OBSTACLE_HIT = "OBSTACLE_HIT"
    POWERUP_COLLECTED = "POWERUP_COLLECTED"
    POWERUP_EXPIRED = "POWERUP_EXPIRED"
    HEALTH_CHANGED = "HEALTH_CHANGED"
    SCORE_CHANGED = "SCORE_CHANGED"
    SPEED_CHANGED = "SPEED_CHANGED"
    STREAK_CHANGED = "STREAK_CHANGED"

    # Profile
    PROFILE_SELECTED = "PROFILE_SELECTED"
    PROFILE_CREATED = "PROFILE_CREATED"
    PROFILE_UPDATED = "PROFILE_UPDATED"
    MEASUREMENT_STARTED = "MEASUREMENT_STARTED"
    MEASUREMENT_DONE = "MEASUREMENT_DONE"
    MEASUREMENT_FAILED = "MEASUREMENT_FAILED"

    # System
    CONFIG_LOADED = "CONFIG_LOADED"
    ERROR = "ERROR"
    WARNING = "WARNING"
    DEBUG_TOGGLED = "DEBUG_TOGGLED"


# All permitted event names set for fast O(1) lookup
VALID_EVENT_NAMES = {
    v for k, v in EventType.__dict__.items()
    if not k.startswith("_") and isinstance(v, str)
}


@dataclass(frozen=True)
class Event:
    """
    Immutable event contract passed across the Event Bus.
    Every event carries its type name, timestamp, origin source, and payload.
    """
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if self.name not in VALID_EVENT_NAMES:
            raise ValueError(f"Unknown event name '{self.name}'. Event must be in Event Catalogue (UC 02.05).")