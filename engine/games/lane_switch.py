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

log = get_logger("lane_switch")


class LaneSwitchGame:
    """
    Game 2: Coin Slalom & Lane Switch (Module 18 - Milestone M5).
    A high-speed slalom game focusing on upper-body leaning, coin trail gathering,
    and obstacle dodging.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 display: Optional[DisplayManager] = None, audio: Optional[AudioManager] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.display = display or DisplayManager(bus=self.bus, cfg=self.config)
        self.audio = audio or AudioManager(bus=self.bus, cfg=self.config)

        self.engine = GameEngine(bus=self.bus, cfg=self.config)
        self.mechanics = MechanicsManager(bus=self.bus, cfg=self.config)

        # Fast baseline pace for slalom excitement
        self.engine.base_speed = 1.1
        self.engine.speed_cap = 2.4
        self.engine.speed_ramp_rate = 0.015

        # 3 Lanes: 0 = Left, 1 = Center, 2 = Right
        self.current_lane: int = 1
        self.target_lane: int = 1
        self.visual_lane_x: float = 1.0  # Smooth interpolated lane position

        # Stats & High Scores (UC 18.08)
        self.game_id = "lane_switch"
        self.coins_collected: int = 0
        self.crates_smashed: int = 0
        self.personal_best: int = 0
        self.is_new_best: bool = False
        self.longest_streak: int = 0

        # Spawning parameters
        self.spawn_timer: float = 0.0
        self.spawn_interval: float = 1.4  # Fast frequency
        self.next_obstacle_id: int = 1
        self.next_powerup_id: int = 1
        self.road_scroll_offset: float = 0.0

        # Results navigation
        self.results_options = ["Play Again", "Main Menu"]
        self.results_selected_index: int = 0

        self._subscribe_events()

    def _subscribe_events(self) -> None:
        """Subscribe to lean actions, punch gestures, and game lifecycle."""
        self.bus.subscribe(EventType.LEAN_LEFT, lambda e: self.set_lane(0))
        self.bus.subscribe(EventType.LEAN_CENTER, lambda e: self.set_lane(1))
        self.bus.subscribe(EventType.LEAN_RIGHT, lambda e: self.set_lane(2))
        self.bus.subscribe(EventType.HANDS_UP, lambda e: self.smash_crate())
        self.bus.subscribe(EventType.PUNCH, lambda e: self.smash_crate())
        self.bus.subscribe(EventType.KICK, lambda e: self.smash_crate())
        self.bus.subscribe(EventType.GAME_OVER, self._on_game_over)
        self.bus.subscribe(EventType.STREAK_CHANGED, self._on_streak_changed)

    def set_lane(self, lane: int) -> None:
        """
        Shifts active player lane with boundary clamping (UC 18.01, 18.02).
        Leaning left at Lane 0 stays safely in Lane 0 (never leaves the track).
        """
        clamped_lane = max(0, min(2, lane))
        self.current_lane = clamped_lane
        self.mechanics.player_lane = clamped_lane

    def shift_lane_relative(self, delta: int) -> None:
        """Keyboard navigation fallback for lane changes (UC 18.01, 18.02)."""
        self.set_lane(self.current_lane + delta)

    def smash_crate(self) -> bool:
        """
        Comedic Punch & Kick Mechanic:
        If a smashable wooden crate is in the player's active lane, smash it for coins!
        """
        for obs in self.mechanics.obstacles:
            if obs.obstacle_type == "smashable_crate" and obs.lane == self.current_lane:
                if -40.0 <= obs.z_position <= 50.0 and not obs.cleared and not obs.hit:
                    obs.cleared = True
                    self.crates_smashed += 1
                    bonus_points = 150
                    self.mechanics.score += bonus_points
                    self.coins_collected += 5
                    log.info("SMASHED wooden crate! +%d points, +5 coins!", bonus_points)
                    self.audio.play_sound("hit", priority=True)
                    self.bus.publish(Event(EventType.SCORE_CHANGED, {"score": self.mechanics.score, "delta": bonus_points}))
                    return True
        return False

    def _on_game_over(self, event: Event) -> None:
        """Records personal best for Game 2 (UC 18.08)."""
        score = self.mechanics.score
        if score > self.personal_best:
            self.personal_best = score
            self.is_new_best = True
        else:
            self.is_new_best = False
        self.results_selected_index = 0

    def _on_streak_changed(self, event: Event) -> None:
        current_streak = event.payload.get("streak", 0)
        if current_streak > self.longest_streak:
            self.longest_streak = current_streak

    def start_new_game(self) -> None:
        """Starts a fresh Coin Slalom run (UC 18.07)."""
        self.mechanics.health = 100
        self.mechanics.score = 0
        self.mechanics.streak = 0
        self.current_lane = 1
        self.visual_lane_x = 1.0
        self.mechanics.player_lane = 1
        self.mechanics.player_action = "STAND"
        self.mechanics.obstacles.clear()
        self.mechanics.powerups.clear()
        self.mechanics.active_powerups.clear()

        self.coins_collected = 0
        self.crates_smashed = 0
        self.is_new_best = False
        self.longest_streak = 0
        self.results_selected_index = 0
        self.spawn_timer = self.spawn_interval

        self.engine.reset_game()
        self.display.clear_menu()
        self.engine.transition_to(GameState.PLAYING)

    def results_nav_next(self) -> None:
        self.results_selected_index = (self.results_selected_index + 1) % len(self.results_options)

    def results_nav_prev(self) -> None:
        self.results_selected_index = (self.results_selected_index - 1) % len(self.results_options)

    def results_select(self) -> str:
        return self.results_options[self.results_selected_index]

    def update(self, dt: float) -> None:
        """Main game update step for Coin Slalom (UC 18.01, 18.02)."""
        self.engine.tick(dt)

        if self.engine.state != GameState.PLAYING:
            return

        # Smooth horizontal avatar sliding between lanes
        self.visual_lane_x += (self.current_lane - self.visual_lane_x) * min(1.0, dt * 14.0)

        effective_speed = self.mechanics.get_effective_speed(self.engine.current_speed)
        scroll_distance = effective_speed * 500.0 * dt
        self.road_scroll_offset = (self.road_scroll_offset + scroll_distance) % 100.0

        self.mechanics.advance_world(scroll_distance)
        self.mechanics.update(dt)

        # 1. Collision & Collection at Player Plane
        for obs in list(self.mechanics.obstacles):
            if -30.0 <= obs.z_position <= 30.0:
                self.mechanics.check_obstacle_interaction(obs)

        for pup in list(self.mechanics.powerups):
            if -30.0 <= pup.z_position <= 30.0:
                if pup.lane == self.current_lane:
                    self.mechanics.collect_powerup(pup)
                    if pup.powerup_type in ("coin", "double_points"):
                        self.coins_collected += 1
                        self.audio.play_sound("powerup")

        # 2. Spawning Slalom Waves (Barriers & Coin Trails)
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0.0

            # Randomize wave pattern:
            # 50% chance: Barrier wave with open safe lane
            # 30% chance: Smashable wooden crate
            # 20% chance: Rainbow coin trail
            pattern = random.random()

            if pattern < 0.50:
                # Block 1 or 2 lanes, leaving at least 1 lane open to slalom through
                blocked_lanes = random.sample([0, 1, 2], k=random.choice([1, 2]))
                for b_lane in blocked_lanes:
                    self.mechanics.spawn_obstacle(f"barrier_{self.next_obstacle_id}", "lane_barrier", "LEAN", lane=b_lane, z_pos=1200.0)
                    self.next_obstacle_id += 1

                # Place a coin in the open safe lane
                safe_lane = [l for l in [0, 1, 2] if l not in blocked_lanes][0]
                self.mechanics.spawn_powerup(f"coin_{self.next_powerup_id}", "double_points", duration_sec=5.0, lane=safe_lane, z_pos=1200.0)
                self.next_powerup_id += 1

            elif pattern < 0.80:
                # Spawn smashable crate in a random lane
                crate_lane = random.choice([0, 1, 2])
                obs = self.mechanics.spawn_obstacle(f"crate_{self.next_obstacle_id}", "smashable_crate", "LEAN", lane=crate_lane, z_pos=1200.0)
                self.next_obstacle_id += 1

            else:
                # Snake a coin trail across lanes
                for i in range(3):
                    c_lane = (self.current_lane + i) % 3
                    self.mechanics.spawn_powerup(f"coin_trail_{self.next_powerup_id}", "double_points", duration_sec=4.0, lane=c_lane, z_pos=1100.0 + i * 80.0)
                    self.next_powerup_id += 1

    def draw(self, surface: pygame.Surface) -> None:
        """Renders 3D Slalom track with neon visuals and floating coins."""
        sw = surface.get_width()
        sh = surface.get_height()

        # 1. Vibrant Cyber Slalom Road
        horizon_y = int(sh * 0.14)
        surface.fill((12, 16, 28))
        pygame.draw.rect(surface, (20, 26, 42), (0, horizon_y, sw, sh - horizon_y))

        road_top_w = int(sw * 0.22)
        road_bot_w = int(sw * 0.86)
        top_left = (sw // 2 - road_top_w // 2, horizon_y)
        top_right = (sw // 2 + road_top_w // 2, horizon_y)
        bot_right = (sw // 2 + road_bot_w // 2, sh)
        bot_left = (sw // 2 - road_bot_w // 2, sh)

        # Neon Cyan / Magenta borders for Slalom aesthetic
        pygame.draw.polygon(surface, (36, 44, 66), [top_left, top_right, bot_right, bot_left])
        pygame.draw.line(surface, (0, 255, 200), top_left, bot_left, 5)
        pygame.draw.line(surface, (0, 255, 200), top_right, bot_right, 5)

        for l_idx in (1, 2):
            tx = top_left[0] + (road_top_w * l_idx // 3)
            bx = bot_left[0] + (road_bot_w * l_idx // 3)
            pygame.draw.line(surface, (100, 120, 160), (tx, horizon_y), (bx, sh), 3)

        # 2. Draw Approaching Obstacles & Crates
        for obs in self.mechanics.obstacles:
            if obs.z_position < 0:
                continue
            pct = max(0.0, min(1.0, 1.0 - (obs.z_position / 1200.0)))
            cur_y = horizon_y + int((sh - horizon_y) * (pct ** 1.8))
            cur_w = road_top_w + int((road_bot_w - road_top_w) * pct)
            cur_left = sw // 2 - cur_w // 2
            lane_w = cur_w // 3
            lane_cx = cur_left + lane_w * obs.lane + lane_w // 2

            box_size = max(16, int(70 * pct))
            if obs.obstacle_type == "smashable_crate":
                # Brown wooden crate with smash X
                pygame.draw.rect(surface, (160, 90, 44), (lane_cx - box_size // 2, cur_y - box_size, box_size, box_size), border_radius=4)
                pygame.draw.line(surface, (230, 160, 100), (lane_cx - box_size // 2, cur_y - box_size), (lane_cx + box_size // 2, cur_y), 2)
            else:
                # Glowing red/orange slalom barrier
                pygame.draw.rect(surface, (231, 76, 60), (lane_cx - box_size // 2, cur_y - box_size, box_size, box_size), border_radius=4)

        # 3. Draw Approaching Golden Coins & Stars
        for pup in self.mechanics.powerups:
            if pup.z_position < 0 or pup.collected:
                continue
            pct = max(0.0, min(1.0, 1.0 - (pup.z_position / 1200.0)))
            cur_y = horizon_y + int((sh - horizon_y) * (pct ** 1.8))
            cur_w = road_top_w + int((road_bot_w - road_top_w) * pct)
            cur_left = sw // 2 - cur_w // 2
            lane_w = cur_w // 3
            lane_cx = cur_left + lane_w * pup.lane + lane_w // 2

            radius = max(10, int(24 * pct))
            # Glowing gold star/coin
            pygame.draw.circle(surface, (241, 196, 15), (lane_cx, cur_y - radius), radius)
            pygame.draw.circle(surface, (255, 255, 255), (lane_cx, cur_y - radius), max(2, radius // 2), 2)

        # 4. Draw Player Avatar (Smoothly slides between lanes)
        player_lane_w = road_bot_w // 3
        player_cx = int(bot_left[0] + player_lane_w * self.visual_lane_x + player_lane_w // 2)
        player_y = sh - 150

        # Avatar with speed trail
        avatar_color = (0, 230, 255)
        if self.mechanics.invulnerable_timer > 0 and int(pygame.time.get_ticks() / 100) % 2 == 0:
            avatar_color = (255, 255, 255)

        pygame.draw.rect(surface, avatar_color, (player_cx - 25, player_y, 50, 90), border_radius=12)
        pygame.draw.rect(surface, (255, 255, 255), (player_cx - 25, player_y, 50, 90), 3, border_radius=12)

        # 5. Draw HUD with Coin Wallet
        self.display.draw_hud(surface)
        coin_font = pygame.font.Font(None, 34)
        coin_surf = coin_font.render(f"COINS: {self.coins_collected}", True, (241, 196, 15))
        surface.blit(coin_surf, (sw // 2 - coin_surf.get_width() // 2, 20))

        # 6. Results Screen Overlay
        if self.engine.state == GameState.RESULTS:
            self._draw_results_screen(surface)

    def _draw_results_screen(self, surface: pygame.Surface) -> None:
        sw = surface.get_width()
        sh = surface.get_height()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 235))
        surface.blit(overlay, (0, 0))

        font_title = pygame.font.Font(None, 64)
        font_stat = pygame.font.Font(None, 42)
        font_option = pygame.font.Font(None, 48)

        title = font_title.render("COIN SLALOM - RUN OVER", True, (0, 255, 200))
        surface.blit(title, (sw // 2 - title.get_width() // 2, int(sh * 0.16)))

        if self.is_new_best:
            best_surf = font_stat.render("[ ! ] NEW SLALOM BEST! [ ! ]", True, (241, 196, 15))
            surface.blit(best_surf, (sw // 2 - best_surf.get_width() // 2, int(sh * 0.26)))

        stats = [
            f"Final Score: {self.mechanics.score}",
            f"Personal Best: {self.personal_best}",
            f"Coins Collected: {self.coins_collected}",
            f"Crates Smashed: {self.crates_smashed}",
            f"Longest Streak: {self.longest_streak}x",
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