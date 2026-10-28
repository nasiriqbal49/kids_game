import os
import time
import pygame
from typing import Dict, Any, Optional
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("display")

# Visual & Safety Constants (UC 04.07, 04.11)
MIN_TITLE_FONT_SIZE = 36
MIN_STAT_FONT_SIZE = 48
MAX_FLASH_RATE_PER_SEC = 3
FLASH_COOLDOWN_SEC = 1.0 / MAX_FLASH_RATE_PER_SEC  # ~333 ms minimum between flashes
FLASH_DURATION_SEC = 0.20
MAX_FLASH_ALPHA = 100  # Soft flash (never 255 pure white strobe)

# HUD Layout Constants for 1080p
COLOR_BG = (20, 24, 35)
COLOR_TEXT = (255, 255, 255)
COLOR_HEALTH_NORMAL = (46, 204, 113)
COLOR_HEALTH_LOW = (231, 76, 60)
COLOR_FLASH = (231, 76, 60)  # Soft red tint for damage


class DisplayManager:
    """
    Manages game window, multi-display targeting (TV vs laptop fallback),
    HUD rendering at 1080p, and photosensitivity/focus safety rules.
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
            "player_name": "Player 1",
        }

        # Display status
        self.tv_found: bool = False
        self.selected_display_index: int = 0
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None

        # Safety & Performance Controls (UC 04.10, 04.11)
        self.reduced_effects: bool = False
        self.quit_requested: bool = False
        self._last_flash_time: float = -1.0
        self._flash_active_until: float = -1.0

        # Display connection monitoring (UC 04.03)
        self.display_lost: bool = False
        self.reconnect_countdown_active: bool = False
        self._countdown_start_time: float = 0.0
        self._last_countdown_count: int = -1

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
        self.bus.subscribe(EventType.OBSTACLE_HIT, self._on_obstacle_hit)

    # -------------------------------------------------------------------------
    # Event Handlers (HUD State Updates within 1 frame - UC 04.05, 04.06, 04.11)
    # -------------------------------------------------------------------------

    def _on_health_changed(self, event: Event) -> None:
        current = event.payload.get("current", self.hud_state["health"])
        max_hp = event.payload.get("max", self.hud_state["max_health"])
        self.hud_state["health"] = current
        self.hud_state["max_health"] = max_hp
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

    def _on_obstacle_hit(self, event: Event) -> None:
        """Trigger photosensitive-safe hit flash on damage (UC 04.11)."""
        self.trigger_hit_flash()

    # -------------------------------------------------------------------------
    # Photosensitivity & Safety Rules (UC 04.11, 04.12, 04.13)
    # -------------------------------------------------------------------------

    def trigger_hit_flash(self, now: Optional[float] = None) -> bool:
        """
        Triggers a damage flash. Enforces photosensitivity safety:
        - Max 3 flashes per second.
        - Soft tint (max alpha 100), never full white strobe.
        """
        current_time = now if now is not None else time.time()
        if (current_time - self._last_flash_time) < FLASH_COOLDOWN_SEC:
            # Suppress rapid flashing (UC 04.11)
            return False

        self._last_flash_time = current_time
        self._flash_active_until = current_time + FLASH_DURATION_SEC
        return True

    @staticmethod
    def format_display_name(name: str, max_chars: int = 12) -> str:
        """Truncates long profile names with an ellipsis (UC 04.12)."""
        trimmed = name.strip()
        if len(trimmed) <= max_chars:
            return trimmed
        return trimmed[:max_chars - 3] + "..."

    def check_fps(self, current_fps: float) -> None:
        """Low FPS degradation (UC 04.10). Automatically simplifies effects if under 45 FPS."""
        if current_fps < 45.0 and not self.reduced_effects:
            self.reduced_effects = True
            log.warning("Frame rate dropped to %.1f FPS (< 45). Reduced visual effects enabled (UC 04.10).",
                        current_fps)
        elif current_fps >= 55.0 and self.reduced_effects:
            self.reduced_effects = False
            log.info("Frame rate recovered to %.1f FPS. Full effects restored.", current_fps)

    def check_display_connection(self, num_displays: Optional[int] = None) -> bool:
        """
        Monitors HDMI / target display connection state (UC 04.03).
        - If target display is unplugged mid-game, auto-pauses with reason='hdmi_disconnect'.
        - When reconnected, starts a 3-second countdown before resuming.
        """
        if num_displays is None:
            if not pygame.get_init():
                return not self.display_lost
            num_displays = pygame.display.get_num_displays()

        target_index = self.config.get("display.display_index", 1)

        # 1. Target display was active but is now missing (HDMI pulled)
        if self.tv_found and num_displays <= target_index:
            if not self.display_lost:
                self.display_lost = True
                self.tv_found = False
                log.warning("Target display disconnected (HDMI pulled)! Auto-pausing game (UC 04.03).")
                self.bus.publish(Event(EventType.GAME_PAUSE, {"reason": "hdmi_disconnect"}))
            return False

        # 2. Target display was lost but has now reconnected
        if self.display_lost and num_displays > target_index:
            self.display_lost = False
            self.tv_found = True
            self.reconnect_countdown_active = True
            self._countdown_start_time = time.time()
            self._last_countdown_count = 3
            log.info("Target display reconnected. Starting 3-second countdown before resume (UC 04.03).")
            self.bus.publish(Event(EventType.COUNTDOWN_TICK, {"count": 3}))
            return True

        return not self.display_lost

    def update_reconnect_countdown(self, now: Optional[float] = None) -> Optional[int]:
        """
        Advances the 3-second resume countdown after HDMI reconnection (UC 04.03).
        Publishes COUNTDOWN_TICK on second boundaries and GAME_RESUME when complete.
        """
        if not self.reconnect_countdown_active:
            return None

        current_time = now if now is not None else time.time()
        elapsed = current_time - self._countdown_start_time
        remaining = max(0, 3 - int(elapsed))

        if remaining != self._last_countdown_count:
            self._last_countdown_count = remaining
            self.bus.publish(Event(EventType.COUNTDOWN_TICK, {"count": remaining}))

        if elapsed >= 3.0:
            self.reconnect_countdown_active = False
            log.info("Reconnect countdown finished. Resuming game (UC 04.03).")
            self.bus.publish(Event(EventType.GAME_RESUME, {"reason": "hdmi_reconnect"}))
            return 0

        return remaining



    def process_window_events(self, events: Optional[list] = None) -> list:
        """
        Handles window-level events and returns every other event untouched, so the
        main loop can pass keyboard events on to the input adapter.
        - Real focus loss (Alt+Tab, another window on top) pauses the game (UC 04.13).
        - Closing the window sets quit_requested; it does NOT pause (the game loop decides).
        Pass the list from pygame.event.get() once per frame, or leave it empty to read it here.
        """
        if events is None:
            if not pygame.get_init():
                return []
            events = pygame.event.get()

        remaining = []
        for event in events:
            if event.type == pygame.QUIT:
                self.quit_requested = True
            elif event.type == pygame.WINDOWFOCUSLOST:
                log.info("Window focus lost. Pausing game (UC 04.13).")
                self.bus.publish(Event(EventType.GAME_PAUSE, {"reason": "focus_loss"}))
            else:
                remaining.append(event)
        return remaining

    # -------------------------------------------------------------------------
    # Display Setup & Drawing Routines (UC 04.01, 04.04, 04.07)
    # -------------------------------------------------------------------------

    def resolve_display_index(self, num_displays: int) -> int:
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
        if headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

        num_displays = pygame.display.get_num_displays()
        target_display = self.resolve_display_index(num_displays)

        width = self.config.get("display.render_width", 1920)
        height = self.config.get("display.render_height", 1080)
        fullscreen = self.config.get("display.fullscreen", True) and not headless

        flags = pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN

        try:
            self.screen = pygame.display.set_mode((width, height), flags=flags, display=target_display)
            pygame.display.set_caption("Kids Motion Game")
            self.clock = pygame.time.Clock()
            log.info("Display initialized at %dx%d on display %d (fullscreen=%s). (UC 04.04)",
                     width, height, target_display, fullscreen)
        except Exception as err:
            log.error("Failed to initialize display on index %d: %s. Falling back to default.", target_display, err)
            self.screen = pygame.display.set_mode((width, height))
            self.clock = pygame.time.Clock()

    @property
    def particles_enabled(self) -> bool:
        """Visual effects toggle: disabled automatically when FPS drops under 45 (UC 04.10)."""
        return not self.reduced_effects

    def draw_hud(self, surface: pygame.Surface) -> None:
        """
        Draws HUD scaled dynamically to surface dimensions (Gap G8):
        - Player Name (UC 04.12: clipped with ellipsis if long).
        - Health Bar (UC 04.06: turns red + draws '[ ! ] LOW HEALTH' alert badge when is_low).
        - Score and Streak with 10-ft readable font sizes (UC 04.07).
        - Soft Hit Flash Overlay (UC 04.11).
        - Respects reduced_effects by skipping decorative accents (UC 04.10).
        """
        sw = surface.get_width()
        sh = surface.get_height()
        scale_x = sw / 1920.0
        scale_y = sh / 1080.0

        # 1. Player Name (UC 04.12)
        display_name = self.format_display_name(self.hud_state.get("player_name", "Player 1"), max_chars=12)
        name_font = pygame.font.Font(None, max(24, int(MIN_TITLE_FONT_SIZE * scale_y)))
        name_surf = name_font.render(display_name, True, COLOR_TEXT)
        surface.blit(name_surf, (int(60 * scale_x), int(15 * scale_y)))

        # 2. Health Bar & Warning Badge (UC 04.06)
        bar_x = int(60 * scale_x)
        bar_y = int(50 * scale_y)
        bar_w = int(350 * scale_x)
        bar_h = int(45 * scale_y)
        hp_pct = max(0.0, min(1.0, self.hud_state["health"] / max(1, self.hud_state["max_health"])))
        current_w = int(bar_w * hp_pct)

        color = COLOR_HEALTH_LOW if self.hud_state["health_is_low"] else COLOR_HEALTH_NORMAL

        # Background + Current HP + Border
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, color, (bar_x, bar_y, current_w, bar_h))
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), max(2, int(3 * scale_x)))

        # Low-Health Alert Badge (UC 04.06)
        if self.hud_state["health_is_low"]:
            alert_font = pygame.font.Font(None, max(22, int(MIN_TITLE_FONT_SIZE * scale_y)))
            alert_surf = alert_font.render("[ ! ] LOW HEALTH", True, COLOR_HEALTH_LOW)
            surface.blit(alert_surf, (bar_x + bar_w + int(15 * scale_x), bar_y + int(10 * scale_y)))

        # 3. Score & Streak (Large fonts for 10-ft readability - UC 04.07)
        stat_font_size = max(28, int(MIN_STAT_FONT_SIZE * scale_y))
        font = pygame.font.Font(None, stat_font_size)
        score_surf = font.render(f"SCORE: {self.hud_state['score']}", True, COLOR_TEXT)
        surface.blit(score_surf, (sw - score_surf.get_width() - int(60 * scale_x), int(40 * scale_y)))

        if self.hud_state["streak"] > 1:
            streak_font = pygame.font.Font(None, max(24, int(MIN_TITLE_FONT_SIZE * scale_y)))
            streak_surf = streak_font.render(f"STREAK: {self.hud_state['streak']}x", True, (241, 196, 15))
            surface.blit(streak_surf, (sw - streak_surf.get_width() - int(60 * scale_x), int(95 * scale_y)))

        # 4. Soft Hit Flash Overlay (UC 04.11)
        now = time.time()
        if now < self._flash_active_until:
            flash_overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            flash_overlay.fill((*COLOR_FLASH, MAX_FLASH_ALPHA))
            surface.blit(flash_overlay, (0, 0))

        # 5. Display Disconnect / Reconnect Countdown Overlay (UC 04.03)
        if self.display_lost:
            banner_font = pygame.font.Font(None, max(36, int(MIN_STAT_FONT_SIZE * scale_y)))
            banner_surf = banner_font.render("TV DISCONNECTED - GAME PAUSED", True, COLOR_HEALTH_LOW)
            surface.blit(banner_surf, (sw // 2 - banner_surf.get_width() // 2, sh // 2 - 30))
        elif self.reconnect_countdown_active:
            count_font = pygame.font.Font(None, max(48, int(72 * scale_y)))
            count_surf = count_font.render(f"RESUMING IN {self._last_countdown_count}...", True, (241, 196, 15))
            surface.blit(count_surf, (sw // 2 - count_surf.get_width() // 2, sh // 2 - 30))    

    def close(self) -> None:
        if pygame.get_init():
            pygame.quit()