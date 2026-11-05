import os
import sys
import time
import cv2
import pygame

from core.logger import setup_logging, get_logger
from core.config import get_config
from core.event_bus import get_event_bus
from engine.motion_bridge import MotionControllerBridge
from engine.tutorial_ui import TutorialAcademy
from vision.camera_supervisor import CameraSupervisor
from vision.pose_tracker import PoseTracker
from vision.player_lock import PlayerLock
from vision.zone_calibration import ZoneCalibrator
from vision.action_detector import ActionDetector

setup_logging()
cfg = get_config()
log = get_logger("main")


def run():
    pygame.init()
    pygame.font.init()

    sw, sh = 1280, 720
    screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
    pygame.display.set_caption("Universal Motion Game Controller")
    clock = pygame.time.Clock()

    bus = get_event_bus()
    motion_bridge = MotionControllerBridge(bus=bus, cfg=cfg)
    pose_tracker = PoseTracker(bus=bus, cfg=cfg)

    # Supervisor automatically chooses Iriun Phone -> Laptop Webcam -> Keyboard
    camera_supervisor = CameraSupervisor(bus=bus, cfg=cfg, laptop_index=0, min_brightness=6.0)

    zone_calibrator = ZoneCalibrator(bus=bus, cfg=cfg)
    player_lock = PlayerLock(bus=bus, cfg=cfg)
    action_detector = ActionDetector(bus=bus, cfg=cfg)
    academy = TutorialAcademy()

    active_view = "HUB"  # "HUB", "ACADEMY", "MINI_DOCK"
    hub_selected_idx = 0

    portal_buttons = [
        ("Background Mode (Play ANY web or PC game)", "background"),
        ("🏃 Temple Run 2 (Direct WebGL)", "temple_run"),
        ("🚆 Subway Surfers (Direct WebGL)", "subway_surfers"),
        ("🌐 Poki Motion Arcade (All Free Games)", "poki"),
        ("🏎️ CrazyGames 3D Hub (Racing & Driving)", "crazy_games"),
        ("🥊 Iron Snout Fighting (Punch & Kick)", "iron_snout"),
        ("🧟 Zombie Derby (Steer & Shoot)", "zombie_derby"),
        ("🎓 Motion Academy & Gesture Guide", "academy"),
    ]

    desk_test_mode = False
    running = True
    last_frame_ts = -1.0
    locked_pose = None
    pose_result = None
    preview_surf = None

    log.info("Universal Motion Controller started successfully.")

    while running:
        dt = clock.tick(30) / 1000.0  # Runs at 30 FPS (< 2% CPU)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if active_view != "HUB":
                        active_view = "HUB"
                        motion_bridge.stop_bridge()
                    else:
                        running = False

                elif event.key == pygame.K_F2:
                    desk_test_mode = not desk_test_mode
                    log.info("Desk test mode (zone bypass): %s", "ON" if desk_test_mode else "OFF")

                elif active_view == "HUB":
                    if event.key == pygame.K_UP:
                        hub_selected_idx = (hub_selected_idx - 1) % len(portal_buttons)
                    elif event.key == pygame.K_DOWN:
                        hub_selected_idx = (hub_selected_idx + 1) % len(portal_buttons)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        label, key = portal_buttons[hub_selected_idx]
                        if key == "academy":
                            active_view = "ACADEMY"
                        elif key == "background":
                            active_view = "MINI_DOCK"
                            motion_bridge.start_background_mode()
                        else:
                            active_view = "MINI_DOCK"
                            motion_bridge.launch_portal_or_game(key)

                elif active_view == "ACADEMY":
                    if event.key == pygame.K_LEFT:
                        academy.prev_lesson()
                    elif event.key == pygame.K_RIGHT:
                        academy.next_lesson()
                    elif event.key == pygame.K_TAB:
                        academy.toggle_cheat_sheet()

                elif active_view == "MINI_DOCK":
                    if event.key == pygame.K_F10:
                        active_view = "HUB"
                        motion_bridge.stop_bridge()

        # Camera & Vision Pipeline
        cam_frame = camera_supervisor.get_frame()
        if cam_frame is None or cam_frame.image is None:
            locked_pose = None
            pose_result = None
            preview_surf = None
        elif cam_frame.timestamp != last_frame_ts:
            last_frame_ts = cam_frame.timestamp
            pose_result = pose_tracker.process_frame(cam_frame.image, cam_frame.timestamp)
            candidates = [pose_result] if pose_result.has_person else []
            locked_pose = player_lock.update(candidates, zone_calibrator, dt)

            # F2 allows seated desk testing without standing floor zone
            if desk_test_mode and locked_pose is None and pose_result.has_person:
                locked_pose = pose_result

            if locked_pose and locked_pose.has_person:
                action_detector.process_pose(locked_pose, cam_frame.timestamp)

            try:
                small_bgr = cv2.resize(cam_frame.image, (240, 180))
                small_rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)
                preview_surf = pygame.image.frombuffer(small_rgb.tobytes(), (240, 180), "RGB")
            except Exception:
                pass

        bus.drain()

        # Rendering
        if active_view == "HUB":
            screen.fill((14, 18, 30))
            font_title = pygame.font.Font(None, 46)
            font_btn = pygame.font.Font(None, 32)
            font_desc = pygame.font.Font(None, 22)

            title = font_title.render("UNIVERSAL MOTION GAME CONTROLLER", True, (0, 255, 200))
            screen.blit(title, (sw // 2 - title.get_width() // 2, 35))

            sub = font_desc.render("Play web & PC games with body gestures! Select an arcade game or Background Mode:", True, (190, 205, 225))
            screen.blit(sub, (sw // 2 - sub.get_width() // 2, 85))

            start_y = 125
            for i, (label, key) in enumerate(portal_buttons):
                is_sel = (i == hub_selected_idx)
                box_rect = (sw // 2 - 340, start_y + i * 54, 680, 46)
                box_col = (241, 196, 15) if is_sel else (45, 55, 75)
                pygame.draw.rect(screen, (22, 28, 44), box_rect, border_radius=6)
                pygame.draw.rect(screen, box_col, box_rect, 2 if is_sel else 1, border_radius=6)

                btn_col = (255, 255, 255) if is_sel else (180, 195, 215)
                btn_surf = font_btn.render(label, True, btn_col)
                screen.blit(btn_surf, (box_rect[0] + 25, box_rect[1] + 10))

            bridge_state = "LIVE" if motion_bridge.enabled else "OFF"
            stat_surf = font_desc.render(
                f"CAMERA: [{camera_supervisor.active_source.value.upper()}]  |  "
                f"ACTION: [{action_detector.debug_last_action}]  |  "
                f"CONTROLLER: [{bridge_state}]  |  [F2] Desk Test: {'ON' if desk_test_mode else 'OFF'}",
                True, (46, 204, 113)
            )
            screen.blit(stat_surf, (sw // 2 - stat_surf.get_width() // 2, sh - 45))

        elif active_view == "ACADEMY":
            academy.draw(screen, last_action=action_detector.debug_last_action, pose=locked_pose)

        elif active_view == "MINI_DOCK":
            screen.fill((10, 14, 22))
            font_dock = pygame.font.Font(None, 28)
            font_small = pygame.font.Font(None, 20)

            if preview_surf:
                screen.blit(preview_surf, (sw // 2 - 120, sh // 2 - 120))
                pygame.draw.rect(screen, (52, 152, 219), (sw // 2 - 120, sh // 2 - 120, 240, 180), 2)

            act_surf = font_dock.render(f"DETECTED ACTION: {action_detector.debug_last_action}", True, (46, 204, 113))
            screen.blit(act_surf, (sw // 2 - act_surf.get_width() // 2, sh // 2 + 80))

            tip_text = "Controller Active! Click the game window to focus it. [Esc] Return to Hub"
            tip_surf = font_small.render(tip_text, True, (170, 185, 205))
            screen.blit(tip_surf, (sw // 2 - tip_surf.get_width() // 2, sh // 2 + 120))

        pygame.display.flip()

    motion_bridge.stop_bridge()
    camera_supervisor.close()
    pose_tracker.close()
    pygame.quit()


if __name__ == "__main__":
    run()