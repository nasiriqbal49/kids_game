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
FLASH_COOLDOWN_SEC = 1.0 / MAX_FLASH_RATE_PER_SEC
FLASH_DURATION_SEC = 0.20
MAX_FLASH_ALPHA = 100

# HUD Layout Constants for 1080p
COLOR_BG = (20, 24, 35)
COLOR_TEXT = (255, 255, 255)
COLOR_HEALTH_NORMAL = (46, 204, 113)
COLOR_HEALTH_LOW = (231, 76, 60)
COLOR_FLASH = (231, 76, 60)


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
            "active_powerups": {},
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

        # Menu state & navigation with Auto-Scroll (UC 04.08, 04.09)
        self.menu_title: Optional[str] = "KIDS MOTION GAME"
        self.menu_items: list = ["Start Game", "Quit"]
        self.selected_item_index: int = 0
        self.menu_scroll_offset: int = 0
        self.max_visible_menu_items: int = 5  # Keeps menu compact & centered
        self.hold_select_duration: float = 1.0
        self.hold_select_timer: float = 0.0
        self.current_state: str = "MENU"

        self._subscribe_events()

    def _subscribe_events(self) -> None:
        self.bus.subscribe(EventType.HEALTH_CHANGED, self._on_health_changed)
        self.bus.subscribe(EventType.SCORE_CHANGED, self._on_score_changed)
        self.bus.subscribe(EventType.SPEED_CHANGED, self._on_speed_changed)
        self.bus.subscribe(EventType.STREAK_CHANGED, self._on_streak_changed)
        self.bus.subscribe(EventType.POWERUP_COLLECTED, self._on_powerup_collected)
        self.bus.subscribe(EventType.POWERUP_EXPIRED, self._on_powerup_expired)
        self.bus.subscribe(EventType.OBSTACLE_HIT, self._on_obstacle_hit)
        self.bus.subscribe(EventType.STATE_CHANGED, self._on_state_changed)

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
        self.trigger_hit_flash()

    def trigger_hit_flash(self, now: Optional[float] = None) -> bool:
        current_time = now if now is not None else time.time()
        if (current_time - self._last_flash_time) < FLASH_COOLDOWN_SEC:
            return False

        self._last_flash_time = current_time
        self._flash_active_until = current_time + FLASH_DURATION_SEC
        return True

    @staticmethod
    def format_display_name(name: str, max_chars: int = 12) -> str:
        trimmed = name.strip()
        if len(trimmed) <= max_chars:
            return trimmed
        return trimmed[:max_chars - 3] + "..."

    def check_fps(self, current_fps: float) -> None:
        if current_fps < 45.0 and not self.reduced_effects:
            self.reduced_effects = True
            log.warning("Frame rate dropped to %.1f FPS (< 45). Reduced visual effects enabled (UC 04.10).", current_fps)
        elif current_fps >= 55.0 and self.reduced_effects:
            self.reduced_effects = False
            log.info("Frame rate recovered to %.1f FPS. Full effects restored.", current_fps)

    def check_display_connection(self, num_displays: Optional[int] = None) -> bool:
        if num_displays is None:
            if not pygame.get_init():
                return not self.display_lost
            num_displays = pygame.display.get_num_displays()

        target_index = self.config.get("display.display_index", 1)

        if self.tv_found and num_displays <= target_index:
            if not self.display_lost:
                self.display_lost = True
                self.tv_found = False
                log.warning("Target display disconnected! Auto-pausing (UC 04.03).")
                self.bus.publish(Event(EventType.GAME_PAUSE, {"reason": "hdmi_disconnect"}))
            return False

        if self.display_lost and num_displays > target_index:
            self.display_lost = False
            self.tv_found = True
            self.reconnect_countdown_active = True
            self._countdown_start_time = time.time()
            self._last_countdown_count = 3
            log.info("Target display reconnected. Starting 3s countdown (UC 04.03).")
            self.bus.publish(Event(EventType.COUNTDOWN_TICK, {"count": 3}))
            return True

        return not self.display_lost

    def update_reconnect_countdown(self, now: Optional[float] = None) -> Optional[int]:
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
            self.bus.publish(Event(EventType.GAME_RESUME, {"reason": "hdmi_reconnect"}))
            return 0

        return remaining

    def process_window_events(self, events: Optional[list] = None) -> list:
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
    # Menu Management & Auto-Scrolling (UC 04.08, 04.09)
    # -------------------------------------------------------------------------

    def _on_state_changed(self, event: Event) -> None:
        new_state = event.payload.get("new_state", "MENU")
        self.current_state = new_state
        if new_state == "MENU":
            self.set_menu("KIDS MOTION GAME", ["Start Game", "Quit"])
        elif new_state == "PAUSED":
            self.set_menu("GAME PAUSED", ["Resume", "Restart", "Quit to Menu"])
        elif new_state in ("PLAYING", "RESULTS", "GAME_OVER"):
            self.clear_menu()

    def set_menu(self, title: str, items: list) -> None:
        self.menu_title = title
        self.menu_items = items
        self.selected_item_index = 0
        self.menu_scroll_offset = 0
        self.hold_select_timer = 0.0

    def clear_menu(self) -> None:
        self.menu_title = None
        self.menu_items = []
        self.selected_item_index = 0
        self.menu_scroll_offset = 0
        self.hold_select_timer = 0.0

    def menu_nav_next(self) -> int:
        """Navigates to next menu item with smooth viewport scrolling."""
        if self.menu_items:
            self.selected_item_index = (self.selected_item_index + 1) % len(self.menu_items)
            self._update_scroll_bounds()
            self.hold_select_timer = 0.0
        return self.selected_item_index

    def menu_nav_prev(self) -> int:
        """Navigates to previous menu item with smooth viewport scrolling."""
        if self.menu_items:
            self.selected_item_index = (self.selected_item_index - 1) % len(self.menu_items)
            self._update_scroll_bounds()
            self.hold_select_timer = 0.0
        return self.selected_item_index

    def _update_scroll_bounds(self) -> None:
        """Keeps the selected item inside the visible window."""
        if self.selected_item_index < self.menu_scroll_offset:
            self.menu_scroll_offset = self.selected_item_index
        elif self.selected_item_index >= self.menu_scroll_offset + self.max_visible_menu_items:
            self.menu_scroll_offset = self.selected_item_index - self.max_visible_menu_items + 1

    def menu_select_instant(self) -> Optional[str]:
        if self.menu_items and 0 <= self.selected_item_index < len(self.menu_items):
            return self.menu_items[self.selected_item_index]
        return None

    def update_hold_select(self, is_holding: bool, dt: float) -> bool:
        if not is_holding:
            self.hold_select_timer = 0.0
            return False

        self.hold_select_timer += dt
        if self.hold_select_timer >= self.hold_select_duration:
            self.hold_select_timer = 0.0
            return True
        return False

    def draw_menu(self, surface: pygame.Surface) -> None:
        """
        Renders centered menu with Auto-Scrolling Viewport (UC 04.08, 04.09).
        Never gets cut off regardless of how many games or options are in the list!
        """
        if not self.menu_title or not self.menu_items:
            return

        sw = surface.get_width()
        sh = surface.get_height()
        scale_y = sh / 1080.0

        # Semi-transparent dark backdrop
        backdrop = pygame.Surface((sw, sh), pygame.SRCALPHA)
        backdrop.fill((10, 15, 25, 225))
        surface.blit(backdrop, (0, 0))

        # Title
        title_font = pygame.font.Font(None, max(46, int(64 * scale_y)))
        title_surf = title_font.render(self.menu_title, True, (255, 255, 255))
        surface.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, int(120 * scale_y)))

        # Subtitle instructions
        desc_font = pygame.font.Font(None, 24)
        desc_surf = desc_font.render("[Up / Down] Browse Games  |  [Enter / Space] Select", True, (160, 180, 205))
        surface.blit(desc_surf, (sw // 2 - desc_surf.get_width() // 2, int(185 * scale_y)))

        # Calculate visible viewport
        self._update_scroll_bounds()
        visible_indices = range(
            self.menu_scroll_offset,
            min(len(self.menu_items), self.menu_scroll_offset + self.max_visible_menu_items)
        )

        item_font = pygame.font.Font(None, max(32, int(46 * scale_y)))
        start_y = int(240 * scale_y)
        spacing = int(72 * scale_y)

        # Draw "▲ More Above" indicator if scrolled down
        if self.menu_scroll_offset > 0:
            arrow_up = desc_font.render("▲  MORE GAMES ABOVE  ▲", True, (241, 196, 15))
            surface.blit(arrow_up, (sw // 2 - arrow_up.get_width() // 2, start_y - 30))

        # Render visible items
        for slot_idx, actual_idx in enumerate(visible_indices):
            item_text = self.menu_items[actual_idx]
            is_selected = (actual_idx == self.selected_item_index)
            color = (241, 196, 15) if is_selected else (205, 215, 225)

            prefix = "> " if is_selected else "  "
            item_surf = item_font.render(f"{prefix}{item_text}", True, color)
            x_pos = sw // 2 - item_surf.get_width() // 2
            y_pos = start_y + slot_idx * spacing

            if is_selected:
                box_w = max(420, item_surf.get_width() + 60)
                box_h = item_surf.get_height() + 14
                pygame.draw.rect(surface, (24, 32, 48), (sw // 2 - box_w // 2, y_pos - 7, box_w, box_h), border_radius=6)
                pygame.draw.rect(surface, (241, 196, 15), (sw // 2 - box_w // 2, y_pos - 7, box_w, box_h), 2, border_radius=6)

                if self.hold_select_timer > 0.0:
                    pct = min(1.0, self.hold_select_timer / self.hold_select_duration)
                    prog_w = int(box_w * pct)
                    pygame.draw.rect(surface, (46, 204, 113), (sw // 2 - box_w // 2, y_pos + box_h - 9, prog_w, 5), border_radius=3)

            surface.blit(item_surf, (x_pos, y_pos))

        # Draw "▼ More Below" indicator if items remain below
        if self.menu_scroll_offset + self.max_visible_menu_items < len(self.menu_items):
            arrow_down = desc_font.render("▼  MORE GAMES BELOW  ▼", True, (241, 196, 15))
            surface.blit(arrow_down, (sw // 2 - arrow_down.get_width() // 2, start_y + len(visible_indices) * spacing + 10))

    # -------------------------------------------------------------------------
    # Display Setup & Drawing Routines
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
            log.warning("Display %d not detected. Falling back to screen 0 (UC 04.02).", requested_index)
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
            log.info("Display initialized at %dx%d on display %d. (UC 04.04)", width, height, target_display)
        except Exception as err:
            log.error("Failed to initialize display on index %d: %s. Falling back.", target_display, err)
            self.screen = pygame.display.set_mode((width, height))
            self.clock = pygame.time.Clock()

    @property
    def particles_enabled(self) -> bool:
        return not self.reduced_effects

    def draw_hud(self, surface: pygame.Surface) -> None:
        sw = surface.get_width()
        sh = surface.get_height()
        scale_x = sw / 1920.0
        scale_y = sh / 1080.0

        display_name = self.format_display_name(self.hud_state.get("player_name", "Player 1"), max_chars=12)
        name_font = pygame.font.Font(None, max(24, int(MIN_TITLE_FONT_SIZE * scale_y)))
        name_surf = name_font.render(display_name, True, COLOR_TEXT)
        surface.blit(name_surf, (int(60 * scale_x), int(15 * scale_y)))

        bar_x = int(60 * scale_x)
        bar_y = int(50 * scale_y)
        bar_w = int(350 * scale_x)
        bar_h = int(45 * scale_y)
        hp_pct = max(0.0, min(1.0, self.hud_state["health"] / max(1, self.hud_state["max_health"])))
        current_w = int(bar_w * hp_pct)

        color = COLOR_HEALTH_LOW if self.hud_state["health_is_low"] else COLOR_HEALTH_NORMAL

        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, color, (bar_x, bar_y, current_w, bar_h))
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), max(2, int(3 * scale_x)))

        if self.hud_state["health_is_low"]:
            alert_font = pygame.font.Font(None, max(22, int(MIN_TITLE_FONT_SIZE * scale_y)))
            alert_surf = alert_font.render("[ ! ] LOW HEALTH", True, COLOR_HEALTH_LOW)
            surface.blit(alert_surf, (bar_x + bar_w + int(15 * scale_x), bar_y + int(10 * scale_y)))

        stat_font_size = max(28, int(MIN_STAT_FONT_SIZE * scale_y))
        font = pygame.font.Font(None, stat_font_size)
        score_surf = font.render(f"SCORE: {self.hud_state['score']}", True, COLOR_TEXT)
        surface.blit(score_surf, (sw - score_surf.get_width() - int(60 * scale_x), int(40 * scale_y)))

        if self.hud_state["streak"] > 1:
            streak_font = pygame.font.Font(None, max(24, int(MIN_TITLE_FONT_SIZE * scale_y)))
            streak_surf = streak_font.render(f"STREAK: {self.hud_state['streak']}x", True, (241, 196, 15))
            surface.blit(streak_surf, (sw - streak_surf.get_width() - int(60 * scale_x), int(95 * scale_y)))

        now = time.time()
        if now < self._flash_active_until:
            flash_overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            flash_overlay.fill((*COLOR_FLASH, MAX_FLASH_ALPHA))
            surface.blit(flash_overlay, (0, 0))

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