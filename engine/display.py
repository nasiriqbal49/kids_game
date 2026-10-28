import os
import pygame
from typing import Dict, Any, Optional
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("display")


class DisplayManager:
    """
    Manages game window, multi-display targeting (TV vs laptop fallback),
    and HUD state driven entirely by Event Bus events (Module 4).
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        # HUD State: updated purely from events (UC 04.05, 04.06)
        self.hud_state: Dict[str, Any] = {
            "score": 0,
            "health": 100,
            "max_health": 100,
            "health_is_low": False,
            "speed": 1.0,
            "streak": 0,
            "active_powerups": {},  # {powerup_type: time_remaining}
        }

        # Display status
        self.tv_found: bool = False
        self.selected_display_index: int = 0
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None

        # Subscribe to gameplay and state events
        self._subscribe_events()

    def _subscribe_events(self) -> None:
        """Subscribe to events that drive HUD state and visual feedback."""
        self.bus.subscribe(EventType.HEALTH_CHANGED, self._on_health_changed)
        self.bus.subscribe(EventType.SCORE_CHANGED, self._on_score_changed)
        self.bus.subscribe(EventType.SPEED_CHANGED, self._on_speed_changed)
        self.bus.subscribe(EventType.STREAK_CHANGED, self._on_streak_changed)
        self.bus.subscribe(EventType.POWERUP_COLLECTED, self._on_powerup_collected)
        self.bus.subscribe(EventType.POWERUP_EXPIRED, self._on_powerup_expired)

    # -------------------------------------------------------------------------
    # Event Handlers (HUD State Updates within 1 frame - UC 04.05, 04.06)
    # -------------------------------------------------------------------------

    def _on_health_changed(self, event: Event) -> None:
        current = event.payload.get("current", self.hud_state["health"])
        max_hp = event.payload.get("max", self.hud_state["max_health"])
        self.hud_state["health"] = current
        self.hud_state["max_health"] = max_hp
        # UC 04.06: Low health warning threshold (<= 25% or explicit flag)
        self.hud_state["health_is_low"] = event.payload.get("is_low", current <= 25)

    def _on_score_changed(self, event: Event) -> None:
        self.hud_state["score"] = event.payload.get("score", self.hud_state["score"])

    def _on_speed_changed(self, event: Event) -> None:
        self.hud_state["speed"] = event.payload.get("current_speed", self.hud_state["speed"])

    def _on_streak_changed(self, event: Event) -> None:
        self.hud_state["streak"] = event.payload.get("streak", self.hud_state["streak"])

    def _on_powerup_collected(self, event: Event) -> None:
        p_type = event.payload.get("powerup_type")
        duration = event.payload.get("duration_sec", 0.0)
        if p_type:
            self.hud_state["active_powerups"][p_type] = duration

    def _on_powerup_expired(self, event: Event) -> None:
        p_type = event.payload.get("powerup_type")
        if p_type in self.hud_state["active_powerups"]:
            del self.hud_state["active_powerups"][p_type]

    # -------------------------------------------------------------------------
    # Display Setup & Target Selection (UC 04.01, 04.02, 04.04)
    # -------------------------------------------------------------------------

    def resolve_display_index(self, num_displays: int) -> int:
        """
        Picks the display index. Target is the TV (index 1).
        If TV is not connected, falls back safely to laptop screen (index 0) (UC 04.02).
        """
        requested_index = self.config.get("display.display_index", 1)

        if num_displays > requested_index:
            self.tv_found = True
            self.selected_display_index = requested_index
            log.info("Target display %d (TV) detected. (UC 04.01)", requested_index)
        else:
            self.tv_found = False
            self.selected_display_index = 0
            log.warning("Display %d not detected (found %d display(s)). Falling back to screen 0 (UC 04.02).",
                        requested_index, num_displays)

        return self.selected_display_index

    def init_display(self, headless: bool = False) -> None:
        """Initializes Pygame video and opens the window."""
        if headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        if not pygame.get_init():
            pygame.init()

        num_displays = pygame.display.get_num_displays()
        target_display = self.resolve_display_index(num_displays)

        width = self.config.get("display.render_width", 1920)
        height = self.config.get("display.render_height", 1080)
        fullscreen = self.config.get("display.fullscreen", True) and not headless

        flags = pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN

        try:
            self.screen = pygame.display.set_mode(
                (width, height),
                flags=flags,
                display=target_display
            )
            pygame.display.set_caption("Kids Motion Game")
            self.clock = pygame.time.Clock()
            log.info("Display initialized at %dx%d on display %d (fullscreen=%s). (UC 04.04)",
                     width, height, target_display, fullscreen)
        except Exception as err:
            log.error("Failed to initialize display on index %d: %s. Falling back to default.", target_display, err)
            self.screen = pygame.display.set_mode((width, height))
            self.clock = pygame.time.Clock()

    def close(self) -> None:
        """Cleanly releases video resources."""
        if pygame.get_init():
            pygame.quit()