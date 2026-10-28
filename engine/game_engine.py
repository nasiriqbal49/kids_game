from typing import Dict, Set, Optional, Any
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("game_engine")


class GameState:
    """The 8 formal states of the Kids Motion Game (UC 06.01)."""
    MENU = "MENU"
    PROFILE_SELECT = "PROFILE_SELECT"
    CALIBRATION = "CALIBRATION"
    COUNTDOWN = "COUNTDOWN"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"
    RESULTS = "RESULTS"


# Strict legal transition table (UC 06.01, 06.02)
# Any state can safely transition to MENU (failsafe rule)
LEGAL_TRANSITIONS: Dict[str, Set[str]] = {
    GameState.MENU: {GameState.PROFILE_SELECT, GameState.CALIBRATION, GameState.COUNTDOWN, GameState.PLAYING},
    GameState.PROFILE_SELECT: {GameState.MENU, GameState.CALIBRATION, GameState.COUNTDOWN, GameState.PLAYING},
    GameState.CALIBRATION: {GameState.MENU, GameState.COUNTDOWN, GameState.PLAYING},
    GameState.COUNTDOWN: {GameState.MENU, GameState.PLAYING, GameState.PAUSED},
    GameState.PLAYING: {GameState.PAUSED, GameState.GAME_OVER, GameState.MENU},
    GameState.PAUSED: {GameState.PLAYING, GameState.MENU, GameState.COUNTDOWN},
    GameState.GAME_OVER: {GameState.RESULTS, GameState.MENU},
    GameState.RESULTS: {GameState.MENU, GameState.COUNTDOWN, GameState.PLAYING},
}


class GameEngine:
    """
    The reusable heart of every game: state machine, game clock,
    difficulty ramp, and lifecycle management (Module 6).
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        self.state: str = GameState.MENU

        # Game session metrics
        self.score: int = 0
        self.health: int = 100
        self.max_health: int = 100
        self.speed: float = 1.0
        self.streak: int = 0
        self.run_duration_sec: float = 0.0

        # Subscribe to lifecycle and input events
        self._subscribe_events()

    def _subscribe_events(self) -> None:
        """Subscribe to events that drive state changes and gameplay checks."""
        self.bus.subscribe(EventType.GAME_PAUSE, self._on_game_pause)
        self.bus.subscribe(EventType.GAME_RESUME, self._on_game_resume)
        self.bus.subscribe(EventType.HEALTH_CHANGED, self._on_health_changed)

    # -------------------------------------------------------------------------
    # State Machine (UC 06.01, 06.02)
    # -------------------------------------------------------------------------

    def transition_to(self, new_state: str) -> bool:
        """
        Transitions game to a new state if legal (UC 06.01).
        Rejects illegal transitions and logs an error (UC 06.02).
        Returns True on success, False if rejected.
        """
        if new_state == self.state:
            return True

        allowed_destinations = LEGAL_TRANSITIONS.get(self.state, set())

        # Always allow returning to MENU as a safe route (UC 06.02)
        if new_state != GameState.MENU and new_state not in allowed_destinations:
            log.error("Illegal state transition rejected: cannot transition from %s to %s (UC 06.02).",
                      self.state, new_state)
            return False

        old_state = self.state
        self.state = new_state
        log.info("State changed: %s -> %s (UC 06.01)", old_state, new_state)

        # Broadcast state change across the Event Bus
        self.bus.publish(Event(EventType.STATE_CHANGED, {
            "old_state": old_state,
            "new_state": new_state
        }))
        return True

    # -------------------------------------------------------------------------
    # Pause & Resume Handlers (UC 06.03)
    # -------------------------------------------------------------------------

    def _on_game_pause(self, event: Event) -> None:
        """Handles pause request (Ctrl+P, window focus loss, HDMI disconnect) (UC 06.03)."""
        if self.state == GameState.PLAYING:
            self.transition_to(GameState.PAUSED)
        elif self.state == GameState.PAUSED and event.payload.get("action") == "toggle":
            # Parent toggle key can unpause
            self.transition_to(GameState.PLAYING)

    def _on_game_resume(self, event: Event) -> None:
        """Resumes game from paused state (UC 06.03)."""
        if self.state == GameState.PAUSED:
            self.transition_to(GameState.PLAYING)

    # -------------------------------------------------------------------------
    # Health & Game Over Checkpoint (UC 06.05)
    # -------------------------------------------------------------------------

    def _on_health_changed(self, event: Event) -> None:
        """Single check point: when health reaches zero during play, trigger GAME_OVER (UC 06.05)."""
        current_hp = event.payload.get("current", self.health)
        self.health = current_hp

        if current_hp <= 0 and self.state == GameState.PLAYING:
            log.info("Health reached zero. Triggering GAME_OVER (UC 06.05).")
            # 1. Transition to GAME_OVER state
            self.transition_to(GameState.GAME_OVER)

            # 2. Publish critical GAME_OVER event with run statistics
            self.bus.publish(Event(EventType.GAME_OVER, {
                "final_score": self.score,
                "obstacles_cleared": self.score // 50,
                "longest_streak": self.streak,
                "run_duration_sec": self.run_duration_sec
            }))

            # 3. Transition to RESULTS screen
            self.transition_to(GameState.RESULTS)

    # -------------------------------------------------------------------------
    # Game Reset (UC 06.11)
    # -------------------------------------------------------------------------

    def reset_game(self) -> None:
        """Resets all metrics for a fresh new run (UC 06.11)."""
        self.score = 0
        self.health = 100
        self.max_health = 100
        self.speed = 1.0
        self.streak = 0
        self.run_duration_sec = 0.0
        log.info("Game engine reset to initial state (UC 06.11).")