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
        # Fixed-timestep loop & lag spike protection (UC 06.07)
        self.fixed_dt: float = 1.0 / 60.0  # 60 Hz fixed physics tick
        self._accumulator: float = 0.0
        self.max_catch_up_steps: int = 5

        # Difficulty curve (UC 06.06)
        self.base_speed: float = 1.0
        self.speed_cap: float = 2.0
        self.speed_ramp_rate: float = 0.02  # Speed increase per second
        self.current_speed: float = 1.0

        # Safety & Zone Tracking (UC 06.04)
        self.player_in_zone: bool = True
        self.zone_grace_period_sec: float = 1.0
        self._out_of_zone_timer: float = 0.0

        # Idle Timeout (UC 06.09)
        self.idle_timeout_sec: float = float(self.config.get("gameplay.idle_timeout_sec", 300))
        self._idle_timer: float = 0.0

        # Subscribe to lifecycle and input events
        self._subscribe_events()

    def _subscribe_events(self) -> None:
        """Subscribe to events that drive state changes and gameplay checks."""
        self.bus.subscribe(EventType.GAME_PAUSE, self._on_game_pause)
        self.bus.subscribe(EventType.GAME_RESUME, self._on_game_resume)
        self.bus.subscribe(EventType.HEALTH_CHANGED, self._on_health_changed)
        self.bus.subscribe(EventType.PLAYER_IN_ZONE, self._on_player_in_zone)
        self.bus.subscribe(EventType.PLAYER_OUT_OF_ZONE, self._on_player_out_of_zone)

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

        # -------------------------------------------------------------------------
    # Zone Safety & Auto-Pause (UC 06.04)
    # -------------------------------------------------------------------------

    def _on_player_in_zone(self, event: Event) -> None:
        """Player returned to play zone (UC 06.04)."""
        self.player_in_zone = True
        self._out_of_zone_timer = 0.0
        if self.state == GameState.PAUSED:
            log.info("Player returned to zone. Resuming game with countdown (UC 06.04).")
            self.transition_to(GameState.PLAYING)

    def _on_player_out_of_zone(self, event: Event) -> None:
        """Player stepped off floor tiles (UC 06.04)."""
        self.player_in_zone = False

    # -------------------------------------------------------------------------
    # Fixed-Timestep Loop & Timing Updates (UC 06.06, 06.07, 06.09)
    # -------------------------------------------------------------------------

    def tick(self, frame_time_sec: float) -> int:
        """
        Fixed-timestep accumulator loop (UC 06.07).
        Guarantees physics and timers advance consistently regardless of frame rate.
        Caps catch-up steps at max_catch_up_steps to prevent lag death spiral.
        Returns the number of fixed steps executed.
        """
        # Idle timeout tracking (UC 06.09)
        if self.state in (GameState.PAUSED, GameState.MENU):
            self._idle_timer += frame_time_sec
            if self._idle_timer >= self.idle_timeout_sec and self.state != GameState.MENU:
                log.info("Idle timeout (%.0fs) reached. Returning to MENU (UC 06.09).", self.idle_timeout_sec)
                self.transition_to(GameState.MENU)
                self._idle_timer = 0.0
        else:
            self._idle_timer = 0.0

        # Zone grace period countdown during active play (UC 06.04)
        if self.state == GameState.PLAYING and not self.player_in_zone:
            self._out_of_zone_timer += frame_time_sec
            if self._out_of_zone_timer >= self.zone_grace_period_sec:
                log.warning("Player out of zone past grace period. Auto-pausing (UC 06.04).")
                self.bus.publish(Event(EventType.GAME_PAUSE, {"reason": "out_of_zone"}))
                return 0

        if self.state != GameState.PLAYING:
            return 0

        # Accumulate elapsed time for fixed steps
        self._accumulator += frame_time_sec
        steps = 0

        while self._accumulator >= self.fixed_dt and steps < self.max_catch_up_steps:
            self._update_fixed_step(self.fixed_dt)
            self._accumulator -= self.fixed_dt
            steps += 1

        # Discard excess lag spike accumulation (UC 06.07)
        if self._accumulator > self.fixed_dt:
            self._accumulator = 0.0

        return steps

    def _update_fixed_step(self, dt: float) -> None:
        """Single fixed-timestep physics and difficulty update."""
        self.run_duration_sec += dt

        # Smooth progressive difficulty speed ramping (UC 06.06)
        old_speed = self.current_speed
        self.current_speed = min(self.speed_cap, self.base_speed + (self.run_duration_sec * self.speed_ramp_rate))

        # Broadcast speed updates when speed changes measurably
        if abs(self.current_speed - old_speed) >= 0.05:
            self.bus.publish(Event(EventType.SPEED_CHANGED, {
                "current_speed": round(self.current_speed, 2),
                "is_capped": self.current_speed >= self.speed_cap
            }))