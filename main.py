import sys
import time
import cv2
import pygame

from core.logger import setup_logging, configure_from, get_logger
from core.config import get_config
from core.events import Event, EventType
from core.event_bus import get_event_bus
from core.input_keyboard import KeyboardInputAdapter
from engine.display import DisplayManager
from engine.event_pump import EventPump
from engine.audio import AudioManager
from engine.games import RunnerGame, LaneSwitchGame
from engine.game_engine import GameState

# Vision Pipeline (Phase C & E)
from vision.camera_manager import CameraManager
from vision.camera_supervisor import CameraSupervisor
from vision.camera_configurator import CameraConfigurator, CameraRole
from vision.pose_tracker import PoseTracker
from vision.zone_calibration import ZoneCalibrator
from vision.player_lock import PlayerLock
from vision.action_detector import ActionDetector
from vision.debug_tools import DebugOverlay

# Identity Pipeline (Phase D)
from identity.profile_manager import ProfileManager

# 1. Setup Logging and Config
setup_logging()
cfg = get_config()
configure_from(cfg)
log = get_logger("main")

log.info("--- Starting Kids Motion Game (Milestones M1 to M5 Live System) ---")


def run():
    bus = get_event_bus()
    keyboard = KeyboardInputAdapter(bus=bus, cfg=cfg)
    display = DisplayManager(bus=bus, cfg=cfg)
    audio = AudioManager(bus=bus, cfg=cfg)
    pump = EventPump(display=display, keyboard=keyboard)

    # Initialize display window (auto-targets TV at index 1 or laptop screen at 0)
    display.init_display(headless=False)
    screen = display.screen
    clock = display.clock

    # Initialize Player Profile Manager
    profile_mgr = ProfileManager(bus=bus, cfg=cfg)
    all_profiles = profile_mgr.list_profiles()
    active_player = all_profiles[0] if all_profiles else profile_mgr.create_profile("Champion")
    profile_mgr.select_profile(active_player.profile_id)
    display.hud_state["player_name"] = active_player.name

    # Initialize Camera Configurator & Supervisor
    configurator = CameraConfigurator(bus=bus, cfg=cfg)

    def create_supervisor():
        f_idx = configurator.get_assigned_device(CameraRole.FRONT)
        if f_idx is None:
            f_idx = cfg.get("camera.camera_index", 0)
        l_idx = configurator.get_assigned_device(CameraRole.LAPTOP) or 0
        return CameraSupervisor(bus=bus, cfg=cfg, phone_index=f_idx, laptop_index=l_idx)

    camera_supervisor = create_supervisor()

    # Initialize Vision Tracking
    pose_tracker = PoseTracker(bus=bus, cfg=cfg)
    zone_calibrator = ZoneCalibrator(bus=bus, cfg=cfg)
    zone_calibrator.load_calibration("front")
    player_lock = PlayerLock(bus=bus, cfg=cfg)
    action_detector = ActionDetector(bus=bus, cfg=cfg)
    debug_overlay = DebugOverlay(bus=bus, cfg=cfg)

    # Instantiate Both Games (Module 8 & Module 18)
    runner_game = RunnerGame(bus=bus, cfg=cfg, display=display, audio=audio)
    slalom_game = LaneSwitchGame(bus=bus, cfg=cfg, display=display, audio=audio)

    # Active game pointer
    active_game = runner_game
    active_game.engine.transition_to(GameState.MENU)

    def refresh_menu():
        p_name = profile_mgr.active_profile.name if profile_mgr.active_profile else "None"
        display.set_menu("KIDS MOTION GAME", [
            "Game 1: 3D Hurdle Runner (Jump & Duck)",
            "Game 2: Coin Slalom (Lean & Smash)",
            "Camera Setup (3-Camera Wizard)",
            f"Active Player: {p_name} (Click to Change)",
            "Quit"
        ])

    refresh_menu()

    running = True
    show_camera_setup = False
    latest_skeleton_pts = []

    while running and not display.quit_requested:
        dt = clock.tick(60) / 1000.0  # Lock at 60 FPS

        events = pygame.event.get()
        pump_events = []

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if show_camera_setup:
                        configurator.release_caps()
                        show_camera_setup = False
                        camera_supervisor = create_supervisor()
                    elif active_game.engine.state == GameState.PLAYING:
                        active_game.engine.transition_to(GameState.PAUSED)
                    else:
                        running = False

                # Quick Key [C] to open Camera Setup
                elif event.key == pygame.K_c and not show_camera_setup:
                    show_camera_setup = True
                    camera_supervisor.close()
                    configurator.scan_devices(max_to_test=8)

                # Camera Setup Navigation
                elif show_camera_setup:
                    if event.key == pygame.K_LEFT:
                        configurator.selected_device_idx = max(0, configurator.selected_device_idx - 1)
                    elif event.key == pygame.K_RIGHT:
                        configurator.selected_device_idx = min(len(configurator.detected_devices) - 1, configurator.selected_device_idx + 1)
                    elif event.key == pygame.K_1:
                        if configurator.detected_devices:
                            dev_idx = configurator.detected_devices[configurator.selected_device_idx]["device_index"]
                            configurator.assign_role(CameraRole.FRONT, dev_idx)
                    elif event.key == pygame.K_2:
                        if configurator.detected_devices:
                            dev_idx = configurator.detected_devices[configurator.selected_device_idx]["device_index"]
                            configurator.assign_role(CameraRole.SIDE, dev_idx)
                    elif event.key == pygame.K_3:
                        if configurator.detected_devices:
                            dev_idx = configurator.detected_devices[configurator.selected_device_idx]["device_index"]
                            configurator.assign_role(CameraRole.LAPTOP, dev_idx)
                    elif event.key == pygame.K_r:
                        configurator.scan_devices(max_to_test=8)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        valid, _ = configurator.validate_setup()
                        if valid:
                            configurator.save_to_config()
                            configurator.release_caps()
                            show_camera_setup = False
                            camera_supervisor = create_supervisor()
                            log.info("Cameras configured successfully!")

                # Results Screen Navigation (Per-Game)
                elif active_game.engine.state == GameState.RESULTS:
                    if event.key == pygame.K_UP:
                        active_game.results_nav_prev()
                    elif event.key == pygame.K_DOWN:
                        active_game.results_nav_next()
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        choice = active_game.results_select()
                        if choice == "Play Again":
                            active_game.start_new_game()
                        elif choice == "Main Menu":
                            # Record game result into profile (UC 18.08)
                            if active_game == runner_game:
                                profile_mgr.record_game_result("runner", runner_game.mechanics.score, coins_earned=runner_game.mechanics.score // 50)
                            else:
                                profile_mgr.record_game_result("lane_switch", slalom_game.mechanics.score, coins_earned=slalom_game.coins_collected)

                            active_game.engine.transition_to(GameState.MENU)
                            refresh_menu()

                # Main Menu & Pause Navigation
                elif active_game.engine.state in (GameState.MENU, GameState.PAUSED):
                    if event.key == pygame.K_UP:
                        display.menu_nav_prev()
                    elif event.key == pygame.K_DOWN:
                        display.menu_nav_next()
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        selected = display.menu_select_instant()

                        if selected and "Game 1:" in selected:
                            active_game = runner_game
                            active_game.start_new_game()
                        elif selected and "Game 2:" in selected:
                            active_game = slalom_game
                            active_game.start_new_game()
                        elif selected in ("Start Game", "Play Again", "Restart"):
                            active_game.start_new_game()
                        elif selected == "Resume":
                            active_game.engine.transition_to(GameState.PLAYING)
                        elif selected and "Camera Setup" in selected:
                            show_camera_setup = True
                            camera_supervisor.close()
                            configurator.scan_devices(max_to_test=8)
                        elif selected and "Active Player:" in selected:
                            profiles = profile_mgr.list_profiles()
                            if len(profiles) <= 1:
                                profile_mgr.create_profile("Player 2")
                                profiles = profile_mgr.list_profiles()

                            curr_idx = 0
                            for i, p in enumerate(profiles):
                                if profile_mgr.active_profile and p.profile_id == profile_mgr.active_profile.profile_id:
                                    curr_idx = i
                                    break
                            next_p = profiles[(curr_idx + 1) % len(profiles)]
                            profile_mgr.select_profile(next_p.profile_id)
                            display.hud_state["player_name"] = next_p.name
                            refresh_menu()
                        elif selected in ("Quit", "Quit to Menu"):
                            if active_game.engine.state == GameState.PAUSED:
                                active_game.engine.transition_to(GameState.MENU)
                                refresh_menu()
                            else:
                                running = False

                # Active Gameplay Keyboard Fallback
                elif active_game.engine.state == GameState.PLAYING:
                    if event.key == pygame.K_SPACE and hasattr(active_game, "request_jump"):
                        active_game.request_jump()
                    elif event.key == pygame.K_LEFT and hasattr(active_game, "shift_lane_relative"):
                        active_game.shift_lane_relative(-1)
                    elif event.key == pygame.K_RIGHT and hasattr(active_game, "shift_lane_relative"):
                        active_game.shift_lane_relative(1)
                    else:
                        pump_events.append(event)
                else:
                    pump_events.append(event)
            else:
                pump_events.append(event)

        pump.pump(pump_events)

        # -----------------------------------------------------------------
        # Vision Frame Processing (CameraSupervisor -> Pose -> Actions)
        # -----------------------------------------------------------------
        cam_frame = None if show_camera_setup else camera_supervisor.get_frame()
        cam_preview_surf = None

        if cam_frame is not None and cam_frame.image is not None:
            pose_result = pose_tracker.process_frame(cam_frame.image, cam_frame.timestamp)
            candidates = [pose_result] if pose_result.has_person else []
            locked_pose = player_lock.update(candidates, zone_calibrator, dt)

            if locked_pose is not None and locked_pose.has_person:
                if active_game.engine.state == GameState.PLAYING:
                    action_detector.process_pose(locked_pose, cam_frame.timestamp)
                    is_jumping_flag = getattr(active_game, "is_jumping", False)
                    zone_calibrator.evaluate_player_zone(locked_pose, is_jumping=is_jumping_flag)

                sh = screen.get_height()
                box_x, box_y = 30, sh - 180
                latest_skeleton_pts = [
                    (box_x + int(lm.x * 200), box_y + int(lm.y * 150))
                    for lm in locked_pose.raw_landmarks
                    if lm.visibility > 0.5
                ]
            else:
                latest_skeleton_pts = []

            try:
                small_bgr = cv2.resize(cam_frame.image, (200, 150))
                small_rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)
                cam_preview_surf = pygame.image.frombuffer(small_rgb.tobytes(), (200, 150), "RGB")
            except Exception:
                cam_preview_surf = None

        bus.drain()

        display.check_display_connection()
        display.check_fps(clock.get_fps())

        if active_game.engine.state == GameState.PLAYING and not show_camera_setup:
            active_game.update(dt)

        # Render Active Game World (Runner or Slalom)
        active_game.draw(screen)

        # Draw Corner Camera Preview when in game
        if cam_preview_surf is not None and not show_camera_setup:
            sh = screen.get_height()
            box_x, box_y = 30, sh - 180
            screen.blit(cam_preview_surf, (box_x, box_y))
            pygame.draw.rect(screen, (52, 152, 219), (box_x, box_y, 200, 150), 2)

            for pt in latest_skeleton_pts:
                pygame.draw.circle(screen, (46, 204, 113), pt, 3)

            badge_font = pygame.font.Font(None, 24)
            action_text = f"ACTION: {action_detector.debug_last_action}"
            rise_text = f"Rise: {action_detector.debug_vertical_rise:+.2f}"
            src_text = f"[{camera_supervisor.active_source.value.upper()}]"
            badge_color = (46, 204, 113) if action_detector.is_airborne else ((241, 196, 15) if action_detector.is_ducking else (200, 220, 240))

            badge_surf = badge_font.render(f"{src_text} {action_text} | {rise_text}", True, badge_color)
            screen.blit(badge_surf, (box_x, box_y - 25))

        # Render Camera Configurator Screen if open
        if show_camera_setup:
            configurator.draw(screen)

        # Draw Menu Overlay
        if display.menu_title and active_game.engine.state in (GameState.MENU, GameState.PAUSED) and not show_camera_setup:
            display.draw_menu(screen)

        pygame.display.flip()

    log.info("Shutting down cleanly...")
    configurator.release_caps()
    camera_supervisor.close()
    pose_tracker.close()
    display.close()
    audio.close()


if __name__ == "__main__":
    run()