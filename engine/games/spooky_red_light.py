import math
import random
import time
import pygame
from typing import Dict, List, Optional
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from engine.game_engine import GameEngine, GameState
from engine.display import DisplayManager
from engine.audio import AudioManager

log = get_logger("spooky_red_light")


class LightState:
    GREEN = "GREEN"           # Sneaking forward allowed
    WARNING = "WARNING"       # Monster is turning around!
    RED = "RED"               # Freeze! Power outage effect active
    CAUGHT = "CAUGHT"         # Jumpscare! Kid moved!
    VICTORY = "VICTORY"       # Kid reached the TV!


class SpookyRedLightGame:
    """
    Game 4: Spooky Red Light, Green Light with Monster Power-Outage (Module 18).
    Tracks player creeping towards the TV and detects movement during blackout red lights.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 display: Optional[DisplayManager] = None, audio: Optional[AudioManager] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.display = display or DisplayManager(bus=self.bus, cfg=self.config)
        self.audio = audio or AudioManager(bus=self.bus, cfg=self.config)

        self.engine = GameEngine(bus=self.bus, cfg=self.config)
        self.game_id = "spooky_red_light"

        # Game state & timing
        self.light: str = LightState.GREEN
        self.light_timer: float = 0.0
        self.green_duration: float = 4.5
        self.red_duration: float = 3.0

        # Motion & Sneaking Evaluation
        # Distance: 0.0 (at the back of room) to 1.0 (reached the TV)
        self.progress_distance: float = 0.0
        self.start_foot_y: Optional[float] = None
        self.last_foot_y: Optional[float] = None
        self.last_foot_x: Optional[float] = None
        self.freeze_tolerance: float = 0.030

        # Horror / Power-Outage visual effects
        self.blackout_flicker: bool = False
        self.jumpscare_active_until: float = 0.0

        # Stats & Profile
        self.score: int = 0
        self.coins: int = 0
        self.rounds_survived: int = 0
        self.times_caught: int = 0
        self.personal_best: int = 0
        self.is_new_best: bool = False

        # Results navigation
        self.results_options = ["Play Again", "Main Menu"]
        self.results_selected_index: int = 0

        self._subscribe_events()

    def _subscribe_events(self) -> None:
        self.bus.subscribe(EventType.GAME_OVER, self._on_game_over)

    def _on_game_over(self, event: Event) -> None:
        if self.score > self.personal_best:
            self.personal_best = self.score
            self.is_new_best = True
        else:
            self.is_new_best = False
        self.results_selected_index = 0

    def start_new_game(self) -> None:
        """Starts a fresh Red Light, Green Light session."""
        self.score = 0
        self.coins = 0
        self.progress_distance = 0.0
        self.start_foot_y = None
        self.last_foot_y = None
        self.last_foot_x = None
        self.rounds_survived = 0
        self.times_caught = 0
        self.is_new_best = False
        self.jumpscare_active_until = 0.0

        self._start_green_light()
        self.engine.reset_game()
        self.display.clear_menu()
        self.engine.transition_to(GameState.PLAYING)

    def _start_green_light(self) -> None:
        """Green light starts: safe to sneak forward."""
        self.light = LightState.GREEN
        self.light_timer = 0.0
        self.green_duration = random.uniform(3.5, 6.0)
        self.blackout_flicker = False
        self.audio.start_loop("running_loop")
        log.info("GREEN LIGHT: Sneak forward (duration: %.1fs).", self.green_duration)

    def _trigger_red_light(self) -> None:
        """Red light & power-outage effect triggered!"""
        self.light = LightState.RED
        self.light_timer = 0.0
        self.red_duration = random.uniform(2.5, 3.8)
        self.blackout_flicker = True
        self.audio.stop_loop()
        self.audio.play_sound("countdown")
        log.info("RED LIGHT: Freeze! Power-outage blackout active!")

    def evaluate_player_movement(self, foot_x: float, foot_y: float, dt: float) -> None:
        """
        Processes body position:
        1. When Green: Detects creeping forward towards TV (increases distance progress).
        2. When Red: Detects movement $\to$ triggers jumpscare & sends back to start!
        """
        # Baseline start position (when child starts at back of room)
        if self.start_foot_y is None:
            self.start_foot_y = foot_y
            self.last_foot_y = foot_y
            self.last_foot_x = foot_x
            return

        delta_x = abs(foot_x - self.last_foot_x) if self.last_foot_x else 0.0
        delta_y = (foot_y - self.last_foot_y) if self.last_foot_y else 0.0
        total_motion = math.hypot(delta_x, delta_y)

        # -------------------------------------------------------------
        # 1. GREEN LIGHT: Creeping Forward towards TV
        # -------------------------------------------------------------
        if self.light == LightState.GREEN:
            # In camera: moving closer to TV moves foot_y downwards (towards 1.0)
            if delta_y > 0.005:
                # Advancing forward!
                step_progress = delta_y * 1.8
                self.progress_distance = min(1.0, self.progress_distance + step_progress)

                # Check Victory (reached the TV!)
                if self.progress_distance >= 1.0:
                    self._trigger_victory()
                    return

        # -------------------------------------------------------------
        # 2. RED LIGHT: Movement Detection during Blackout
        # -------------------------------------------------------------
        elif self.light == LightState.RED:
            if total_motion > self.freeze_tolerance:
                # CAUGHT MOVING! Jumpscare!
                self._trigger_jumpscare()
                return

        self.last_foot_x = foot_x
        self.last_foot_y = foot_y

    def advance_manually(self, amount: float = 0.08) -> None:
        """Keyboard fallback: Up Arrow sneaks forward."""
        if self.light == LightState.GREEN:
            self.progress_distance = min(1.0, self.progress_distance + amount)
            if self.progress_distance >= 1.0:
                self._trigger_victory()
        elif self.light == LightState.RED:
            self._trigger_jumpscare()

    def _trigger_jumpscare(self) -> None:
        """Kid moved during Red Light! Monster roars and zaps them back to start."""
        self.light = LightState.CAUGHT
        self.times_caught += 1
        self.jumpscare_active_until = time.time() + 1.8
        self.progress_distance = max(0.0, self.progress_distance - 0.40)  # Sent back!
        self.audio.play_sound("hit", priority=True)
        log.warning("PLAYER CAUGHT MOVING! Jumpscare triggered! Sent back to start.")

    def _trigger_victory(self) -> None:
        """Player reached the TV without getting caught!"""
        self.light = LightState.VICTORY
        self.score += 200
        self.coins += 25
        self.rounds_survived += 1
        self.audio.play_sound("powerup")
        self.bus.publish(Event(EventType.SCORE_CHANGED, {"score": self.score, "delta": 200}))
        log.info("VICTORY! Child reached the TV! +200 pts, +25 coins!")

    def results_nav_next(self) -> None:
        self.results_selected_index = (self.results_selected_index + 1) % len(self.results_options)

    def results_nav_prev(self) -> None:
        self.results_selected_index = (self.results_selected_index - 1) % len(self.results_options)

    def results_select(self) -> str:
        return self.results_options[self.results_selected_index]

    def update(self, dt: float) -> None:
        """Main game loop update for Red Light, Green Light."""
        self.engine.tick(dt)

        if self.engine.state != GameState.PLAYING:
            return

        self.light_timer += dt

        # Green Light Phase
        if self.light == LightState.GREEN:
            if self.light_timer >= self.green_duration:
                # Warning before turning
                self.light = LightState.WARNING
                self.light_timer = 0.0

        # Warning Phase (0.8s)
        elif self.light == LightState.WARNING:
            if self.light_timer >= 0.8:
                self._trigger_red_light()

        # Red Light Phase
        elif self.light == LightState.RED:
            if self.light_timer >= self.red_duration:
                # Survived the freeze! Resume Green light
                self.rounds_survived += 1
                self.score += 50
                self.coins += 5
                log.info("Freeze survived! +50 pts, +5 coins.")
                self._start_green_light()

        # Caught Phase (Jumpscare pause for 1.8s)
        elif self.light == LightState.CAUGHT:
            if time.time() >= self.jumpscare_active_until:
                self._start_green_light()

        # Victory Phase (Celebration for 3.0s then game over / results)
        elif self.light == LightState.VICTORY:
            if self.light_timer >= 3.0:
                self.engine.transition_to(GameState.GAME_OVER)
                self.bus.publish(Event(EventType.GAME_OVER, {
                    "final_score": self.score,
                    "coins": self.coins,
                    "rounds_survived": self.rounds_survived
                }))
                self.engine.transition_to(GameState.RESULTS)

    def draw(self, surface: pygame.Surface) -> None:
        """Renders haunted hall, funny monster animations, power-cut flickers, and jumpscares."""
        sw = surface.get_width()
        sh = surface.get_height()

        # 1. Haunted Hallway / Spooky Castle Backdrop
        surface.fill((16, 12, 24))
        pygame.draw.rect(surface, (25, 20, 36), (sw // 2 - 350, 100, 700, sh - 100))
        pygame.draw.line(surface, (80, 60, 110), (sw // 2 - 350, 100), (sw // 2 - 350, sh), 4)
        pygame.draw.line(surface, (80, 60, 110), (sw // 2 + 350, 100), (sw // 2 + 350, sh), 4)

        # 2. Power-Outage / Blackout Lighting Flicker (UC Horror Effect)
        if self.light == LightState.RED and (int(pygame.time.get_ticks() / 120) % 5 == 0):
            blackout = pygame.Surface((sw, sh), pygame.SRCALPHA)
            blackout.fill((0, 0, 0, 220))
            surface.blit(blackout, (0, 0))

        # 3. Draw The Funny Cartoon Monster in Center
        monster_cx, monster_cy = sw // 2, 280

        if self.light == LightState.GREEN:
            # Monster facing AWAY (fluffy purple back with funny ears)
            pygame.draw.circle(surface, (120, 60, 180), (monster_cx, monster_cy), 85)
            # Two pointy monster ears
            pygame.draw.polygon(surface, (90, 40, 150), [(monster_cx - 60, monster_cy - 70), (monster_cx - 40, monster_cy - 120), (monster_cx - 20, monster_cy - 65)])
            pygame.draw.polygon(surface, (90, 40, 150), [(monster_cx + 20, monster_cy - 65), (monster_cx + 40, monster_cy - 120), (monster_cx + 60, monster_cy - 70)])

        elif self.light in (LightState.WARNING, LightState.RED):
            # Monster TURNED AROUND with Giant Glowing Eyes!
            pygame.draw.circle(surface, (140, 70, 200), (monster_cx, monster_cy), 85)
            # Glowing Red / Yellow Eyes staring at the child
            eye_color = (255, 40, 40) if self.light == LightState.RED else (241, 196, 15)
            pygame.draw.circle(surface, (255, 255, 255), (monster_cx - 30, monster_cy - 15), 24)
            pygame.draw.circle(surface, (255, 255, 255), (monster_cx + 30, monster_cy - 15), 24)
            pygame.draw.circle(surface, eye_color, (monster_cx - 30, monster_cy - 15), 14)
            pygame.draw.circle(surface, eye_color, (monster_cx + 30, monster_cy - 15), 14)
            # Silly toothy grin
            pygame.draw.arc(surface, (255, 255, 255), (monster_cx - 35, monster_cy + 10, 70, 40), math.pi, 2 * math.pi, 5)

        # 4. JUMPSCARE OVERLAY (When caught moving!)
        if self.light == LightState.CAUGHT:
            # Giant roaring monster face right in camera!
            jumpscare_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            jumpscare_surf.fill((200, 20, 20, 160))
            surface.blit(jumpscare_surf, (0, 0))

            # Monster roaring giant face
            pygame.draw.circle(surface, (160, 60, 220), (sw // 2, sh // 2), 220)
            # Giant glowing eyes
            pygame.draw.circle(surface, (255, 255, 255), (sw // 2 - 80, sh // 2 - 40), 60)
            pygame.draw.circle(surface, (255, 255, 255), (sw // 2 + 80, sh // 2 - 40), 60)
            pygame.draw.circle(surface, (255, 0, 0), (sw // 2 - 80, sh // 2 - 40), 30)
            pygame.draw.circle(surface, (255, 0, 0), (sw // 2 + 80, sh // 2 - 40), 30)
            # Roaring mouth
            pygame.draw.ellipse(surface, (20, 0, 0), (sw // 2 - 100, sh // 2 + 50, 200, 120))

            font_roar = pygame.font.Font(None, 84)
            roar_surf = font_roar.render("I SAW YOU MOVE! BZZZZT!", True, (255, 255, 0))
            surface.blit(roar_surf, (sw // 2 - roar_surf.get_width() // 2, sh // 2 - 180))

        # 5. Massive Status Banners
        font_banner = pygame.font.Font(None, 62)
        font_sub = pygame.font.Font(None, 34)

        if self.light == LightState.GREEN:
            banner = font_banner.render("🟢 GREEN LIGHT! SNEAK FORWARD! 🟢", True, (46, 204, 113))
            sub = font_sub.render("Creep closer to the TV... shhh!", True, (200, 230, 200))
        elif self.light == LightState.WARNING:
            banner = font_banner.render("⚠️ HE IS TURNING! GET READY TO FREEZE! ⚠️", True, (241, 196, 15))
            sub = font_sub.render("3... 2... 1...", True, (241, 196, 15))
        elif self.light == LightState.RED:
            banner = font_banner.render("🔴 RED LIGHT! FREEZE! DON'T BREATHE! 🔴", True, (255, 50, 50))
            sub = font_sub.render("Hold completely still... he is watching!", True, (255, 180, 180))
        elif self.light == LightState.VICTORY:
            banner = font_banner.render("🏆 VICTORY! YOU REACHED THE TV! 🏆", True, (241, 196, 15))
            sub = font_sub.render("+200 Points & 25 Coins!", True, (255, 255, 255))
        else:
            banner = font_banner.render("CAUGHT! SENT BACK TO START!", True, (255, 60, 60))
            sub = font_sub.render("Try again... stay statue-still next time!", True, (255, 255, 255))

        if self.light != LightState.CAUGHT:
            surface.blit(banner, (sw // 2 - banner.get_width() // 2, 45))
            surface.blit(sub, (sw // 2 - sub.get_width() // 2, 105))

        # 6. Distance Progress Bar to the TV (Bottom Center)
        bar_w, bar_h = 600, 34
        bar_x = sw // 2 - bar_w // 2
        bar_y = sh - 75

        pygame.draw.rect(surface, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        fill_w = int(bar_w * self.progress_distance)
        pygame.draw.rect(surface, (46, 204, 113), (bar_x, bar_y, fill_w, bar_h), border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)

        font_dist = pygame.font.Font(None, 26)
        dist_txt = font_dist.render(f"DISTANCE TO TV: {int(self.progress_distance * 100)}%", True, (255, 255, 255))
        surface.blit(dist_txt, (sw // 2 - dist_txt.get_width() // 2, bar_y + 8))

        # Score & Coins HUD
        font_hud = pygame.font.Font(None, 34)
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

        title = font_title.render("SPOOKY SNEAK - RESULTS", True, (241, 196, 15))
        surface.blit(title, (sw // 2 - title.get_width() // 2, int(sh * 0.16)))

        stats = [
            f"Final Score: {self.score}",
            f"Personal Best: {self.personal_best}",
            f"Rounds Survived: {self.rounds_survived}",
            f"Times Caught: {self.times_caught}",
            f"Total Coins: {self.coins}",
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