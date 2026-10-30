import math
import random
import pygame
from typing import Dict, List, Optional
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from engine.game_engine import GameEngine, GameState
from engine.mechanics.entities import Obstacle, PowerUp
from engine.mechanics.manager import MechanicsManager
from engine.display import DisplayManager
from engine.audio import AudioManager

log = get_logger("runner")

# Difficulty Presets (UC 08.05, 08.06)
DIFFICULTY_PRESETS = {
    "easy": {
        "base_speed": 0.6,
        "speed_cap": 1.2,
        "speed_ramp_rate": 0.008,
        "damage_per_hit": 10,
        "spawn_interval": 2.5,
        "powerup_chance": 0.35,
    },
    "normal": {
        "base_speed": 1.0,
        "speed_cap": 2.0,
        "speed_ramp_rate": 0.02,
        "damage_per_hit": 20,
        "spawn_interval": 2.0,
        "powerup_chance": 0.25,
    },
    "strict": {
        "base_speed": 1.2,
        "speed_cap": 2.5,
        "speed_ramp_rate": 0.03,
        "damage_per_hit": 25,
        "spawn_interval": 1.5,
        "powerup_chance": 0.15,
    },
}


class RunnerGame:
    """
    Game 1: Runner (Module 8 - Milestone M1)
    Coordinates GameEngine, MechanicsManager, DisplayManager, and AudioManager
    into a complete, playable 3-lane runner.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 display: Optional[DisplayManager] = None, audio: Optional[AudioManager] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.display = display or DisplayManager(bus=self.bus, cfg=self.config)
        self.audio = audio or AudioManager(bus=self.bus, cfg=self.config)

        self.engine = GameEngine(bus=self.bus, cfg=self.config)
        self.mechanics = MechanicsManager(bus=self.bus, cfg=self.config)

        # Apply Difficulty Preset (UC 08.05)
        sensitivity = self.config.get("gameplay.sensitivity", "easy").lower()
        self.preset = DIFFICULTY_PRESETS.get(sensitivity, DIFFICULTY_PRESETS["easy"])
        self.engine.base_speed = self.preset["base_speed"]
        self.engine.speed_cap = self.preset["speed_cap"]
        self.engine.speed_ramp_rate = self.preset["speed_ramp_rate"]
        self.mechanics.damage_per_hit = self.preset["damage_per_hit"]
        self.spawn_interval = self.preset["spawn_interval"]
        self.powerup_chance = self.preset["powerup_chance"]

        # Jump air-time lockout (UC 08.03)
        self.is_jumping: bool = False
        self.jump_timer: float = 0.0
        self.jump_duration: float = 0.55  # 550 ms air-time

        # High Score / Personal Best tracking (UC 08.04)
        self.personal_best: int = 0
        self.is_new_best: bool = False

        # Run Statistics Summary (UC 08.08)
        self.obstacles_cleared_count: int = 0
        self.longest_streak: int = 0

        # Results Screen navigation options
        self.results_options = ["Play Again", "Main Menu"]
        self.results_selected_index: int = 0

        # Spawning parameters
        self.spawn_timer: float = 0.0
        self.next_obstacle_id: int = 1
        self.next_powerup_id: int = 1

        # Track scroll visual phase
        self.road_scroll_offset: float = 0.0

        self._subscribe_events()

    def _subscribe_events(self) -> None:
        """Subscribe to game events to keep state synced."""
        self.bus.subscribe(EventType.JUMP, self._on_jump_action)
        self.bus.subscribe(EventType.GAME_OVER, self._on_game_over)
        self.bus.subscribe(EventType.OBSTACLE_CLEARED, self._on_obstacle_cleared)
        self.bus.subscribe(EventType.STREAK_CHANGED, self._on_streak_changed)

    def _on_jump_action(self, event: Event) -> None:
        """Triggers the avatar jump arc when JUMP fires from camera or keyboard."""
        if not self.is_jumping and self.engine.state == GameState.PLAYING:
            self.is_jumping = True
            self.jump_timer = 0.0

    def _on_game_over(self, event: Event) -> None:
        """Records personal best and saves summary stats on Game Over (UC 08.04, 08.08)."""
        score = self.mechanics.score
        if score > self.personal_best:
            self.personal_best = score
            self.is_new_best = True
            log.info("New personal best achieved: %d! (UC 08.04)", score)
        else:
            self.is_new_best = False
        self.results_selected_index = 0

    def _on_obstacle_cleared(self, event: Event) -> None:
        self.obstacles_cleared_count += 1

    def _on_streak_changed(self, event: Event) -> None:
        current_streak = event.payload.get("streak", 0)
        if current_streak > self.longest_streak:
            self.longest_streak = current_streak

    def request_jump(self) -> bool:
        """Processes jump command with air-time lockout (UC 08.03)."""
        if self.is_jumping or self.engine.state != GameState.PLAYING:
            return False

        self.is_jumping = True
        self.jump_timer = 0.0
        self.bus.publish(Event(EventType.JUMP))
        return True

    def start_new_game(self) -> None:
        """Starts a fresh game session (UC 08.01)."""
        self.mechanics.health = 100
        self.mechanics.score = 0
        self.mechanics.streak = 0
        self.mechanics.player_lane = 1
        self.mechanics.player_action = "STAND"
        self.mechanics.obstacles.clear()
        self.mechanics.powerups.clear()
        self.mechanics.active_powerups.clear()

        self.obstacles_cleared_count = 0
        self.longest_streak = 0
        self.is_new_best = False
        self.is_jumping = False
        self.jump_timer = 0.0
        self.results_selected_index = 0

        self.spawn_timer = self.spawn_interval

        self.engine.reset_game()
        self.display.clear_menu()
        self.engine.transition_to(GameState.PLAYING)

    def results_nav_next(self) -> None:
        """Navigates to next option on Results screen."""
        self.results_selected_index = (self.results_selected_index + 1) % len(self.results_options)

    def results_nav_prev(self) -> None:
        """Navigates to previous option on Results screen."""
        self.results_selected_index = (self.results_selected_index - 1) % len(self.results_options)

    def results_select(self) -> str:
        """Selects current option on Results screen."""
        return self.results_options[self.results_selected_index]

    def update(self, dt: float) -> None:
        """Main game update step (UC 08.01, 08.02, 08.03, 08.06)."""
        self.engine.tick(dt)

        if self.engine.state != GameState.PLAYING:
            return

        # 1. Update jump air-time
        if self.is_jumping:
            self.jump_timer += dt
            if self.jump_timer >= self.jump_duration:
                self.is_jumping = False
                self.jump_timer = 0.0
                self.bus.publish(Event(EventType.LAND))

        # 2. Scroll world
        effective_speed = self.mechanics.get_effective_speed(self.engine.current_speed)
        scroll_distance = effective_speed * 450.0 * dt
        self.road_scroll_offset = (self.road_scroll_offset + scroll_distance) % 100.0

        self.mechanics.advance_world(scroll_distance)
        self.mechanics.update(dt)

        # 3. Collision checks at player plane (z between -30 and 30)
        for obs in list(self.mechanics.obstacles):
            if -30.0 <= obs.z_position <= 30.0:
                self.mechanics.check_obstacle_interaction(obs)

        for pup in list(self.mechanics.powerups):
            if -30.0 <= pup.z_position <= 30.0:
                if pup.lane == self.mechanics.player_lane:
                    self.mechanics.collect_powerup(pup)

        # 4. Spawner with relaxed spacing
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0
            if self.mechanics.can_spawn_obstacle(z_pos=1200.0, speed=effective_speed):
                obs_types = [
                    ("low_hurdle", "JUMP"),
                    ("high_bar", "DUCK"),
                    ("lane_barrier", "LEAN"),
                ]
                otype, req_act = random.choice(obs_types)
                lane = random.choice([0, 1, 2])
                self.mechanics.spawn_obstacle(f"obs_{self.next_obstacle_id}", otype, req_act, lane=lane, z_pos=1200.0)
                self.next_obstacle_id += 1

                # Spawn powerup with configured chance
                if random.random() < self.powerup_chance:
                    ptype = random.choice(["shield", "slow_down", "double_points", "health_refill"])
                    plane = (lane + 1) % 3
                    self.mechanics.spawn_powerup(f"pup_{self.next_powerup_id}", ptype, duration_sec=8.0, lane=plane, z_pos=1300.0)
                    self.next_powerup_id += 1

    def draw(self, surface: pygame.Surface) -> None:
        """Renders 3-lane perspective road, obstacles, player, and UI (UC 08.01)."""
        sw = surface.get_width()
        sh = surface.get_height()

        # 1. Sleek Horizon at Top 14% (Expands game world to 86% of TV!)
        horizon_y = int(sh * 0.14)
        surface.fill((16, 20, 32))
        pygame.draw.rect(surface, (28, 34, 48), (0, horizon_y, sw, sh - horizon_y))

        # 2. 3-Lane Perspective Road (Wider & Full-Screen)
        road_top_w = int(sw * 0.22)
        road_bot_w = int(sw * 0.84)
        top_left = (sw // 2 - road_top_w // 2, horizon_y)
        top_right = (sw // 2 + road_top_w // 2, horizon_y)
        bot_right = (sw // 2 + road_bot_w // 2, sh)
        bot_left = (sw // 2 - road_bot_w // 2, sh)

        pygame.draw.polygon(surface, (45, 52, 70), [top_left, top_right, bot_right, bot_left])
        pygame.draw.line(surface, (241, 196, 15), top_left, bot_left, 5)
        pygame.draw.line(surface, (241, 196, 15), top_right, bot_right, 5)

        # Lane dividers
        for l_idx in (1, 2):
            tx = top_left[0] + (road_top_w * l_idx // 3)
            bx = bot_left[0] + (road_bot_w * l_idx // 3)
            pygame.draw.line(surface, (130, 142, 165), (tx, horizon_y), (bx, sh), 3)

        # Sleek semi-transparent HUD banner across top
        hud_bar = pygame.Surface((sw, horizon_y + 10), pygame.SRCALPHA)
        hud_bar.fill((10, 14, 22, 190))
        surface.blit(hud_bar, (0, 0))

        # 3. Draw Approaching Obstacles
        for obs in self.mechanics.obstacles:
            if obs.z_position < 0:
                continue
            pct = max(0.0, min(1.0, 1.0 - (obs.z_position / 1200.0)))
            cur_y = horizon_y + int((sh - horizon_y) * (pct ** 1.8))
            cur_w = road_top_w + int((road_bot_w - road_top_w) * pct)
            cur_left = sw // 2 - cur_w // 2
            lane_w = cur_w // 3
            lane_cx = cur_left + lane_w * obs.lane + lane_w // 2

            box_size = max(14, int(65 * pct))
            if obs.obstacle_type == "low_hurdle":
                color = (230, 126, 34)
                pygame.draw.rect(surface, color, (lane_cx - box_size // 2, cur_y - box_size // 2, box_size, box_size // 2), border_radius=4)
            elif obs.obstacle_type == "high_bar":
                color = (155, 89, 182)
                pygame.draw.rect(surface, color, (lane_cx - box_size // 2, cur_y - box_size, box_size, box_size // 3), border_radius=4)
            else:
                color = (231, 76, 60)
                pygame.draw.rect(surface, color, (lane_cx - box_size // 2, cur_y - box_size, box_size, box_size), border_radius=4)

        # 4. Draw Approaching Power-Ups
        for pup in self.mechanics.powerups:
            if pup.z_position < 0 or pup.collected:
                continue
            pct = max(0.0, min(1.0, 1.0 - (pup.z_position / 1200.0)))
            cur_y = horizon_y + int((sh - horizon_y) * (pct ** 1.8))
            cur_w = road_top_w + int((road_bot_w - road_top_w) * pct)
            cur_left = sw // 2 - cur_w // 2
            lane_w = cur_w // 3
            lane_cx = cur_left + lane_w * pup.lane + lane_w // 2

            radius = max(9, int(22 * pct))
            pygame.draw.circle(surface, (46, 204, 113), (lane_cx, cur_y - radius), radius)

        # 5. Draw Player Avatar
        player_lane_w = road_bot_w // 3
        player_cx = bot_left[0] + player_lane_w * self.mechanics.player_lane + player_lane_w // 2
        player_base_y = sh - 60

        jump_offset = 0
        if self.is_jumping:
            progress = self.jump_timer / self.jump_duration
            jump_offset = int(math.sin(progress * math.pi) * 140)

        player_h = 45 if self.mechanics.player_action == "DUCK" else 90
        player_y = player_base_y - player_h - jump_offset

        if "shield" in self.mechanics.active_powerups:
            pygame.draw.ellipse(surface, (52, 152, 219), (player_cx - 45, player_y - 15, 90, player_h + 30), 4)

        avatar_color = (241, 196, 15) if self.is_jumping else (52, 152, 219)
        if self.mechanics.invulnerable_timer > 0 and int(pygame.time.get_ticks() / 100) % 2 == 0:
            avatar_color = (255, 255, 255)

        pygame.draw.rect(surface, avatar_color, (player_cx - 25, player_y, 50, player_h), border_radius=10)

        # 6. Draw HUD
        self.display.draw_hud(surface)

        # 7. Results Screen Overlay (UC 08.08)
        if self.engine.state == GameState.RESULTS:
            self._draw_results_screen(surface)

    def _draw_results_screen(self, surface: pygame.Surface) -> None:
        """Renders interactive results screen with navigable options (UC 08.08)."""
        sw = surface.get_width()
        sh = surface.get_height()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 230))
        surface.blit(overlay, (0, 0))

        font_title = pygame.font.Font(None, 64)
        font_stat = pygame.font.Font(None, 42)
        font_option = pygame.font.Font(None, 48)

        title = font_title.render("RUN RESULTS", True, (255, 255, 255))
        surface.blit(title, (sw // 2 - title.get_width() // 2, int(sh * 0.16)))

        if self.is_new_best:
            best_surf = font_stat.render("[ ! ] NEW PERSONAL BEST! [ ! ]", True, (241, 196, 15))
            surface.blit(best_surf, (sw // 2 - best_surf.get_width() // 2, int(sh * 0.26)))

        stats = [
            f"Final Score: {self.mechanics.score}",
            f"Personal Best: {self.personal_best}",
            f"Obstacles Cleared: {self.obstacles_cleared_count}",
            f"Longest Streak: {self.longest_streak}x",
        ]

        start_y = int(sh * 0.35)
        for i, text in enumerate(stats):
            stat_surf = font_stat.render(text, True, (200, 210, 220))
            surface.blit(stat_surf, (sw // 2 - stat_surf.get_width() // 2, start_y + i * 50))

        menu_y = int(sh * 0.68)
        for i, opt in enumerate(self.results_options):
            is_sel = (i == self.results_selected_index)
            color = (241, 196, 15) if is_sel else (160, 160, 160)
            prefix = "> " if is_sel else "  "
            opt_surf = font_option.render(f"{prefix}{opt}", True, color)
            opt_x = sw // 2 - opt_surf.get_width() // 2
            opt_y = menu_y + i * 60

            if is_sel:
                box_w = opt_surf.get_width() + 50
                box_h = opt_surf.get_height() + 12
                pygame.draw.rect(surface, (241, 196, 15), (sw // 2 - box_w // 2, opt_y - 6, box_w, box_h), 3)

            surface.blit(opt_surf, (opt_x, opt_y))