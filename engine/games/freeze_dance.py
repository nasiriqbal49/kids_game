import math
import random
import pygame
from typing import Dict, List, Optional
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from engine.game_engine import GameEngine, GameState
from engine.display import DisplayManager
from engine.audio import AudioManager

log = get_logger("freeze_dance")


class DancePhase:
    DANCING = "DANCING"               # Music playing, kids dancing & popping bubbles
    FREEZING = "FREEZING"             # Music stopped, player must freeze for 2 seconds
    FLOOR_LAVA = "FLOOR_LAVA"         # Floor is lava! Must jump or balance
    ROUND_SUCCESS = "ROUND_SUCCESS"   # Freeze succeeded! Cheers & points


class Bubble:
    """Floating musical bubble that kids pop by waving hands."""
    def __init__(self, bubble_id: int, x: float, y: float, radius: float = 30.0):
        self.bubble_id = bubble_id
        self.x = x
        self.y = y
        self.radius = radius
        self.popped: bool = False


class FreezeDanceGame:
    """
    Game 3: Freeze Dance & Floor is Lava (Module 18 - Milestone M5).
    Evaluates body stillness when music stops (UC 18.03, 18.04) and detects
    jumping/balance when the floor turns to lava.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 display: Optional[DisplayManager] = None, audio: Optional[AudioManager] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.display = display or DisplayManager(bus=self.bus, cfg=self.config)
        self.audio = audio or AudioManager(bus=self.bus, cfg=self.config)

        self.engine = GameEngine(bus=self.bus, cfg=self.config)
        self.game_id = "freeze_dance"

        # Game state & phase timing
        self.phase: str = DancePhase.DANCING
        self.phase_timer: float = 0.0
        self.dance_duration: float = 5.0
        self.freeze_required_sec: float = 2.0
        self.freeze_hold_timer: float = 0.0

        # Motion & Stillness Evaluation (UC 18.03, 18.04)
        self.freeze_tolerance: float = 0.035
        self.last_hip_y: Optional[float] = None
        self.last_hip_x: Optional[float] = None
        self.current_jitter: float = 0.0

        # Lava & Gestures
        self.round_counter: int = 0
        self.is_lava_active: bool = False
        self.player_safe_from_lava: bool = False

        # Score, Strikes & Coins
        self.score: int = 0
        self.coins: int = 0
        self.freezes_mastered: int = 0
        self.lava_survived: int = 0
        self.strikes: int = 0
        self.max_strikes: int = 3
        self.personal_best: int = 0
        self.is_new_best: bool = False

        # Floating Bubbles
        self.bubbles: List[Bubble] = []
        self.next_bubble_id: int = 1
        self.bubble_spawn_timer: float = 0.0

        # Results navigation
        self.results_options = ["Play Again", "Main Menu"]
        self.results_selected_index: int = 0

        self._subscribe_events()

    def _subscribe_events(self) -> None:
        """Subscribe to jumps, gestures, and game lifecycle."""
        self.bus.subscribe(EventType.JUMP, lambda e: self._on_safe_gesture("JUMP"))
        self.bus.subscribe(EventType.FLAMINGO_BALANCE, lambda e: self._on_safe_gesture("FLAMINGO"))
        self.bus.subscribe(EventType.CHICKEN_FLAP, lambda e: self._on_safe_gesture("FLAP"))
        self.bus.subscribe(EventType.TICKLE_SWAT, lambda e: self.pop_bubbles())
        self.bus.subscribe(EventType.HANDS_UP, lambda e: self.pop_bubbles())
        self.bus.subscribe(EventType.PUNCH, lambda e: self.pop_bubbles())
        self.bus.subscribe(EventType.GAME_OVER, self._on_game_over)

    def _on_safe_gesture(self, gesture_name: str) -> None:
        """Survives Floor is Lava if jumping, flying, or balancing!"""
        if self.phase == DancePhase.FLOOR_LAVA:
            self.player_safe_from_lava = True
            log.info("Lava survived via %s gesture!", gesture_name)

    def _on_game_over(self, event: Event) -> None:
        if self.score > self.personal_best:
            self.personal_best = self.score
            self.is_new_best = True
        else:
            self.is_new_best = False
        self.results_selected_index = 0

    def start_new_game(self) -> None:
        """Starts a fresh Freeze Dance session."""
        self.score = 0
        self.coins = 0
        self.freezes_mastered = 0
        self.lava_survived = 0
        self.strikes = 0
        self.round_counter = 0
        self.is_new_best = False
        self.bubbles.clear()

        self._start_dancing_phase()
        self.engine.reset_game()
        self.display.clear_menu()
        self.engine.transition_to(GameState.PLAYING)

    def _start_dancing_phase(self) -> None:
        """Starts active dance interval and loops music."""
        self.phase = DancePhase.DANCING
        self.phase_timer = 0.0
        self.dance_duration = random.uniform(4.0, 6.5)
        self.is_lava_active = False
        self.player_safe_from_lava = False
        self.audio.start_loop("running_loop")
        log.info("Dance phase started (duration: %.1fs).", self.dance_duration)

    def _trigger_freeze(self) -> None:
        """Music abruptly stops! Triggers Freeze check (UC 18.03)."""
        self.audio.stop_loop()
        self.round_counter += 1

        if self.round_counter % 3 == 0:
            self.phase = DancePhase.FLOOR_LAVA
            self.phase_timer = 0.0
            self.player_safe_from_lava = False
            log.info("FLOOR IS LAVA triggered!")
        else:
            self.phase = DancePhase.FREEZING
            self.phase_timer = 0.0
            self.freeze_hold_timer = 0.0
            self.current_jitter = 0.0
            log.info("FREEZE triggered! Player must freeze for 2.0s (UC 18.03).")

    def evaluate_body_pose(self, hip_x: float, hip_y: float, dt: float) -> None:
        """
        Evaluates body stillness during freeze (UC 18.03, 18.04).
        If child stays still for 2.0s -> Success!
        If child moves beyond tolerance -> Wobble strike!
        """
        if self.last_hip_x is not None and self.last_hip_y is not None:
            movement = math.hypot(hip_x - self.last_hip_x, hip_y - self.last_hip_y)
            self.current_jitter = movement

            if self.phase == DancePhase.FREEZING:
                if movement > self.freeze_tolerance:
                    self.strikes += 1
                    self.audio.play_sound("hit", priority=True)
                    log.warning("Player wobbled during freeze! Strikes: %d/%d (UC 18.04)", self.strikes, self.max_strikes)
                    if self.strikes >= self.max_strikes:
                        self.trigger_game_over()
                    else:
                        self._start_dancing_phase()
                    return

                self.freeze_hold_timer += dt
                if self.freeze_hold_timer >= self.freeze_required_sec:
                    self.freezes_mastered += 1
                    bonus = 100
                    self.score += bonus
                    self.coins += 5
                    self.audio.play_sound("powerup")
                    self.bus.publish(Event(EventType.SCORE_CHANGED, {"score": self.score, "delta": bonus}))
                    log.info("Freeze mastered! +%d pts, +5 coins (UC 18.03).", bonus)
                    self.phase = DancePhase.ROUND_SUCCESS
                    self.phase_timer = 0.0

        self.last_hip_x = hip_x
        self.last_hip_y = hip_y

    def pop_bubbles(self) -> int:
        """Pops floating bubbles with arm gestures for points."""
        popped_count = 0
        for b in self.bubbles:
            if not b.popped:
                b.popped = True
                popped_count += 1
                self.score += 25
        if popped_count > 0:
            self.audio.play_sound("powerup")
        return popped_count

    def trigger_game_over(self) -> None:
        """Ends round after 3 strikes."""
        self.audio.stop_loop()
        self.engine.transition_to(GameState.GAME_OVER)
        self.bus.publish(Event(EventType.GAME_OVER, {
            "final_score": self.score,
            "freezes_mastered": self.freezes_mastered,
            "coins": self.coins
        }))
        self.engine.transition_to(GameState.RESULTS)

    def results_nav_next(self) -> None:
        self.results_selected_index = (self.results_selected_index + 1) % len(self.results_options)

    def results_nav_prev(self) -> None:
        self.results_selected_index = (self.results_selected_index - 1) % len(self.results_options)

    def results_select(self) -> str:
        return self.results_options[self.results_selected_index]

    def update(self, dt: float) -> None:
        """Main game loop update for Freeze Dance."""
        self.engine.tick(dt)

        if self.engine.state != GameState.PLAYING:
            return

        self.phase_timer += dt

        # 1. Active Dancing Phase
        if self.phase == DancePhase.DANCING:
            self.bubble_spawn_timer += dt
            if self.bubble_spawn_timer >= 1.0:
                self.bubble_spawn_timer = 0.0
                sw = self.display.screen.get_width() if self.display.screen else 1920
                b = Bubble(self.next_bubble_id, x=random.randint(200, sw - 200), y=150)
                self.bubbles.append(b)
                self.next_bubble_id += 1

            for b in self.bubbles:
                b.y += 120.0 * dt

            self.bubbles = [b for b in self.bubbles if b.y < 900 and not b.popped]

            if self.phase_timer >= self.dance_duration:
                self._trigger_freeze()

        # 2. Floor is Lava Phase
        elif self.phase == DancePhase.FLOOR_LAVA:
            if self.phase_timer >= 2.5:
                if self.player_safe_from_lava:
                    self.lava_survived += 1
                    bonus = 150
                    self.score += bonus
                    self.coins += 10
                    self.audio.play_sound("powerup")
                    log.info("Survived Floor is Lava! +%d pts, +10 coins!", bonus)
                    self.phase = DancePhase.ROUND_SUCCESS
                    self.phase_timer = 0.0
                else:
                    self.strikes += 1
                    self.audio.play_sound("hit", priority=True)
                    log.warning("Burned in Lava! Strikes: %d/%d", self.strikes, self.max_strikes)
                    if self.strikes >= self.max_strikes:
                        self.trigger_game_over()
                    else:
                        self._start_dancing_phase()

        # 3. Round Success Pause
        elif self.phase == DancePhase.ROUND_SUCCESS:
            if self.phase_timer >= 1.2:
                self._start_dancing_phase()

    def draw(self, surface: pygame.Surface) -> None:
        """Renders disco dance floor, lava effects, bubbles, and status banners."""
        sw = surface.get_width()
        sh = surface.get_height()

        if self.phase == DancePhase.FLOOR_LAVA:
            surface.fill((120, 20, 10))
            for i in range(12):
                bx = (i * 160 + int(pygame.time.get_ticks() / 20)) % sw
                by = sh - 180 + int(math.sin((pygame.time.get_ticks() / 200) + i) * 20)
                pygame.draw.circle(surface, (230, 80, 20), (bx, by), 50)
        else:
            surface.fill((18, 14, 32))
            tile_w, tile_h = sw // 6, (sh - 200) // 4
            for r in range(4):
                for c in range(6):
                    tx = c * tile_w
                    ty = 200 + r * tile_h
                    pulse = (r + c + int(pygame.time.get_ticks() / 300)) % 3
                    tile_color = (40, 25, 65) if pulse == 0 else ((25, 45, 75) if pulse == 1 else (50, 30, 60))
                    pygame.draw.rect(surface, tile_color, (tx + 4, ty + 4, tile_w - 8, tile_h - 8), border_radius=6)

        for b in self.bubbles:
            if not b.popped:
                pygame.draw.circle(surface, (0, 230, 255), (int(b.x), int(b.y)), int(b.radius), 3)
                pygame.draw.circle(surface, (255, 255, 255), (int(b.x) - 6, int(b.y) - 6), 6)

        font_banner = pygame.font.Font(None, 68)
        font_sub = pygame.font.Font(None, 36)

        if self.phase == DancePhase.DANCING:
            banner_surf = font_banner.render("🎵 DANCE & JUMP! POP BUBBLES! 🎵", True, (46, 204, 113))
            sub_surf = font_sub.render("Music is playing... get ready to freeze!", True, (200, 220, 240))
        elif self.phase == DancePhase.FREEZING:
            banner_surf = font_banner.render("❄️ FREEZE! DON'T MOVE! ❄️", True, (0, 255, 255))
            pct = min(1.0, self.freeze_hold_timer / self.freeze_required_sec)
            sub_surf = font_sub.render(f"Hold still... {int(pct * 100)}%", True, (241, 196, 15))
            pygame.draw.circle(surface, (0, 255, 255), (sw // 2, sh // 2 + 100), 40, 4)
            pygame.draw.arc(surface, (46, 204, 113), (sw // 2 - 40, sh // 2 + 60, 80, 80), 0, pct * 2 * math.pi, 6)
        elif self.phase == DancePhase.FLOOR_LAVA:
            banner_surf = font_banner.render("🔥 THE FLOOR IS LAVA! JUMP OR BALANCE! 🔥", True, (255, 60, 20))
            status_txt = "SAFE IN THE AIR!" if self.player_safe_from_lava else "JUMP OFF THE FLOOR!"
            sub_surf = font_sub.render(status_txt, True, (255, 220, 0))
        else:
            banner_surf = font_banner.render("⭐ GREAT FREEZE! +100 POINTS! ⭐", True, (241, 196, 15))
            sub_surf = font_sub.render("Next dance starting...", True, (255, 255, 255))

        surface.blit(banner_surf, (sw // 2 - banner_surf.get_width() // 2, 80))
        surface.blit(sub_surf, (sw // 2 - sub_surf.get_width() // 2, 145))

        font_hud = pygame.font.Font(None, 38)
        strike_text = "X " * self.strikes + "- " * (self.max_strikes - self.strikes)
        strike_surf = font_hud.render(f"STRIKES: [ {strike_text.strip()} ]", True, (231, 76, 60) if self.strikes > 0 else (150, 160, 170))
        surface.blit(strike_surf, (sw - strike_surf.get_width() - 40, 25))

        score_surf = font_hud.render(f"SCORE: {self.score}  |  COINS: {self.coins}", True, (241, 196, 15))
        surface.blit(score_surf, (40, 25))

        if self.engine.state == GameState.RESULTS:
            self._draw_results_screen(surface)

    def _draw_results_screen(self, surface: pygame.Surface) -> None:
        sw = surface.get_width()
        sh = surface.get_height()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 240))
        surface.blit(overlay, (0, 0))

        font_title = pygame.font.Font(None, 64)
        font_stat = pygame.font.Font(None, 42)
        font_option = pygame.font.Font(None, 48)

        title = font_title.render("DANCE-OFF OVER!", True, (0, 255, 255))
        surface.blit(title, (sw // 2 - title.get_width() // 2, int(sh * 0.16)))

        if self.is_new_best:
            best_surf = font_stat.render("[ ! ] NEW DANCE RECORD! [ ! ]", True, (241, 196, 15))
            surface.blit(best_surf, (sw // 2 - best_surf.get_width() // 2, int(sh * 0.26)))

        stats = [
            f"Final Score: {self.score}",
            f"Personal Best: {self.personal_best}",
            f"Freezes Mastered: {self.freezes_mastered}",
            f"Lava Survived: {self.lava_survived}",
            f"Coins Earned: {self.coins}",
        ]

        start_y = int(sh * 0.35)
        for i, text in enumerate(stats):
            stat_surf = font_stat.render(text, True, (210, 225, 240))
            surface.blit(stat_surf, (sw // 2 - stat_surf.get_width() // 2, start_y + i * 48))

        menu_y = int(sh * 0.70)
        for i, opt in enumerate(self.results_options):
            is_sel = (i == self.results_selected_index)
            color = (241, 196, 15) if is_sel else (150, 160, 170)
            prefix = "> " if is_sel else "  "
            opt_surf = font_option.render(f"{prefix}{opt}", True, color)
            opt_x = sw // 2 - opt_surf.get_width() // 2
            opt_y = menu_y + i * 55

            if is_sel:
                box_w = opt_surf.get_width() + 50
                box_h = opt_surf.get_height() + 10
                pygame.draw.rect(surface, (241, 196, 15), (sw // 2 - box_w // 2, opt_y - 5, box_w, box_h), 3)

            surface.blit(opt_surf, (opt_x, opt_y))