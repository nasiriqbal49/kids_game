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
from engine.games.runner import RunnerGame
from engine.game_engine import GameState

# Vision Pipeline (Phase C)
from vision.camera_manager import CameraManager
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

log.info("--- Starting Kids Motion Game (Milestones M1 + M2 + M3 Live System) ---")


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
    active_player = profile_mgr.find_by_name("Champion")
    if not active_player:
        active_player = profile_mgr.create_profile("Champion")
    profile_mgr.select_profile(active_player.profile_id)
    display.hud_state["player_name"] = active_player.name

    # Initialize Vision Pipeline
    log.info("Starting Vision Tracking Pipeline (Webcam + MediaPipe)...")
    camera_mgr = CameraManager(bus=bus, cfg=cfg)
    pose_tracker = PoseTracker(bus=bus, cfg=cfg)
    zone_calibrator = ZoneCalibrator(bus=bus, cfg=cfg)
    zone_calibrator.load_calibration("front")
    player_lock = PlayerLock(bus=bus, cfg=cfg)
    action_detector = ActionDetector(bus=bus, cfg=cfg)
    debug_overlay = DebugOverlay(bus=bus, cfg=cfg)

    # Instantiate Runner Game
    runner = RunnerGame(bus=bus, cfg=cfg, display=display, audio=audio)
    runner.start_new_game()

    log.info("==================================================================")
    log.info(" GAME IS READY FOR YOUR CHILD!")
    log.info(" Body Controls:")
    log.info("   [JUMP]       - Jump up in the air over hurdles")
    log.info("   [DUCK]       - Crouch / duck down under high bars")
    log.info("   [LEAN]       - Lean your upper body Left or Right to switch lanes")
    log.info(" Keyboard Shortcuts (for Dad):")
    log.info("   [Space]      - Jump (keyboard fallback)")
    log.info("   [Down Arrow] - Duck (keyboard fallback)")
    log.info("   [Left/Right] - Lean (keyboard fallback)")
    log.info("   [Ctrl + F3]  - Toggle Debug Diagnostics")
    log.info("   [Ctrl + P]   - Pause Game")
    log.info("   [Esc]        - Quit Game")
    log.info("==================================================================")

    running = True
    latest_skeleton_pts = []

    while running and not display.quit_requested:
        dt = clock.tick(60) / 1000.0  # Lock at 60 FPS

        events = pygame.event.get()
        pump_events = []

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                # 1. Results Screen Navigation
                elif runner.engine.state == GameState.RESULTS:
                    if event.key == pygame.K_UP:
                        runner.results_nav_prev()
                    elif event.key == pygame.K_DOWN:
                        runner.results_nav_next()
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        choice = runner.results_select()
                        log.info("Results choice: %s", choice)
                        if choice == "Play Again":
                            runner.start_new_game()
                        elif choice == "Main Menu":
                            runner.engine.transition_to(GameState.MENU)

                # 2. Menu Navigation
                elif runner.engine.state in (GameState.MENU, GameState.PAUSED):
                    if event.key == pygame.K_UP:
                        display.menu_nav_prev()
                    elif event.key == pygame.K_DOWN:
                        display.menu_nav_next()
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        selected = display.menu_select_instant()
                        if selected in ("Start Game", "Play Again", "Restart"):
                            runner.start_new_game()
                        elif selected == "Resume":
                            runner.engine.transition_to(GameState.PLAYING)
                        elif selected in ("Quit", "Quit to Menu"):
                            if runner.engine.state == GameState.PAUSED:
                                runner.engine.transition_to(GameState.MENU)
                            else:
                                running = False

                # 3. Active Gameplay Keyboard Jump
                elif event.key == pygame.K_SPACE and runner.engine.state == GameState.PLAYING:
                    runner.request_jump()
                else:
                    pump_events.append(event)
            else:
                pump_events.append(event)

        # Feed non-intercepted events into EventPump
        pump.pump(pump_events)

        # -----------------------------------------------------------------
        # Vision Frame Processing (Camera -> Pose -> PlayerLock -> Actions)
        # -----------------------------------------------------------------
        cam_frame = camera_mgr.get_frame("front")
        cam_preview_surf = None

        if cam_frame is not None and cam_frame.image is not None:
            # 1. Run MediaPipe Pose Tracker
            pose_result = pose_tracker.process_frame(cam_frame.image, cam_frame.timestamp)

            # 2. Filter candidates through Player Lock
            candidates = [pose_result] if pose_result.has_person else []
            locked_pose = player_lock.update(candidates, zone_calibrator, dt)

            # 3. Detect Body Actions (JUMP, DUCK, LEAN)
            if locked_pose is not None and locked_pose.has_person:
                action_detector.process_pose(locked_pose, cam_frame.timestamp)
                zone_calibrator.evaluate_player_zone(locked_pose, is_jumping=runner.is_jumping)

                # Anchor skeleton dots directly to the corner camera preview box
                sh = screen.get_height()
                box_x, box_y = 30, sh - 180
                latest_skeleton_pts = [
                    (box_x + int(lm.x * 200), box_y + int(lm.y * 150))
                    for lm in locked_pose.raw_landmarks
                    if lm.visibility > 0.5
                ]
            else:
                latest_skeleton_pts = []

            # 4. Prepare Small Corner Webcam Preview (Picture-in-Picture)
            try:
                small_bgr = cv2.resize(cam_frame.image, (200, 150))
                small_rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)
                cam_preview_surf = pygame.image.frombuffer(small_rgb.tobytes(), (200, 150), "RGB")
            except Exception:
                cam_preview_surf = None

        # Drain vision events immediately into the game on the exact same frame!
        bus.drain()

        # Display monitoring
        display.check_display_connection()
        display.check_fps(clock.get_fps())

        # Update Runner World & Mechanics
        runner.update(dt)

        # Render 3D Perspective Track, Obstacles, Player Avatar, and HUD
        runner.draw(screen)

        # Draw Small Webcam Corner Preview (Bottom-Left) with Live Action Badge
        if cam_preview_surf is not None:
            sh = screen.get_height()
            box_x, box_y = 30, sh - 180
            screen.blit(cam_preview_surf, (box_x, box_y))
            pygame.draw.rect(screen, (52, 152, 219), (box_x, box_y, 200, 150), 2)

            # Draw green tracking dots directly on child's body inside preview
            for pt in latest_skeleton_pts:
                pygame.draw.circle(screen, (46, 204, 113), pt, 3)

            # Live Action Indicator Badge directly above camera box
            badge_font = pygame.font.Font(None, 24)
            action_text = f"ACTION: {action_detector.debug_last_action}"
            rise_text = f"Rise: {action_detector.debug_vertical_rise:+.2f}"
            badge_color = (46, 204, 113) if action_detector.is_airborne else ((241, 196, 15) if action_detector.is_ducking else (200, 220, 240))

            badge_surf = badge_font.render(f"{action_text} | {rise_text}", True, badge_color)
            screen.blit(badge_surf, (box_x, box_y - 25))

        # Draw Menu Overlay if active
        if display.menu_title and runner.engine.state in (GameState.MENU, GameState.PAUSED):
            display.draw_menu(screen)

        pygame.display.flip()

    # Clean shutdown
    log.info("Shutting down game and releasing camera devices...")
    camera_mgr.close()
    pose_tracker.close()
    display.close()
    audio.close()
    log.info("--- Game finished cleanly ---")


if __name__ == "__main__":
    run()