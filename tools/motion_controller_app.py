import os
import sys
import time
import cv2
import pygame

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.logger import setup_logging, get_logger
from core.config import get_config
from core.event_bus import get_event_bus
from engine.motion_bridge import MotionControllerBridge, ARCADE_PORTALS
from engine.tutorial_ui import TutorialAcademy
from vision.camera_supervisor import CameraSupervisor
from vision.camera_configurator import CameraConfigurator, CameraRole
from vision.pose_tracker import PoseTracker
from vision.player_lock import PlayerLock
from vision.zone_calibration import ZoneCalibrator
from vision.action_detector import ActionDetector

setup_logging()
cfg = get_config()
log = get_logger("motion_controller_app")


def run_controller():
    pygame.init()
    pygame.font.init()

    sw, sh = 1280, 720
    screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
    pygame.display.set_caption("Universal Motion Game Controller")
    clock = pygame.time.Clock()

    bus = get_event_bus()
    motion_bridge = MotionControllerBridge(bus=bus, cfg=cfg)
    configurator = CameraConfigurator(bus=bus, cfg=cfg)
    configurator.scan_devices(max_to_test=8)

    def build_supervisor() -> CameraSupervisor:
        """Creates a fresh camera supervisor from the currently assigned FRONT camera."""
        front_idx = configurator.get_assigned_device(CameraRole.FRONT)
        if front_idx is None:
            front_idx = 0
        return CameraSupervisor(bus=bus, cfg=cfg, phone_index=front_idx, laptop_index=0)

    # The setup scan above opened preview captures; free them so the supervisor can open the camera.
    configurator.release_caps()
    camera_supervisor = build_supervisor()

    pose_tracker = PoseTracker(bus=bus, cfg=cfg)
    zone_calibrator = ZoneCalibrator(bus=bus, cfg=cfg)
    player_lock = PlayerLock(bus=bus, cfg=cfg)
    action_detector = ActionDetector(bus=bus, cfg=cfg)
    academy = TutorialAcademy()

    active_view = "HUB"  # "HUB", "ACADEMY", "CAMERA_SETUP", "MINI_DOCK"
    hub_selected_idx = 0

    portal_buttons = [
        ("Background Mode (use ANY game / browser)", "background"),
        ("Poki Motion Arcade (All Games)", "poki"),
        ("CrazyGames 3D Hub (Racing & Shooters)", "crazy_games"),
        ("Temple Run 2 (Direct WebGL)", "temple_run"),
        ("Subway Surfers (Direct WebGL)", "subway_surfers"),
        ("Iron Snout Fighting (Punch & Kick)", "iron_snout"),
        ("Zombie Derby (Steer & Shoot)", "zombie_derby"),
        ("Motion Academy & Gesture Guide", "academy"),
        ("Camera Setup Wizard", "camera_setup"),
    ]

    desk_test_mode = False  # F2: bypass zone/lock so a seated webcam test works

    running = True

    while running:
        dt = clock.tick(30) / 1000.0  # Runs at lightweight 30 FPS (< 2% CPU)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if active_view != "HUB":
                        if active_view == "CAMERA_SETUP":
                            # Leaving setup without saving: release previews and restart the
                            # camera supervisor (it was closed when the wizard opened).
                            configurator.release_caps()
                            camera_supervisor.close()
                            camera_supervisor = build_supervisor()
                        active_view = "HUB"
                        motion_bridge.stop_bridge()
                    else:
                        running = False

                elif event.key == pygame.K_F2:
                    desk_test_mode = not desk_test_mode
                    log.info("Desk test mode %s (zone/lock bypass).", "ON" if desk_test_mode else "OFF")

                # HUB Navigation
                elif active_view == "HUB":
                    if event.key == pygame.K_UP:
                        hub_selected_idx = (hub_selected_idx - 1) % len(portal_buttons)
                    elif event.key == pygame.K_DOWN:
                        hub_selected_idx = (hub_selected_idx + 1) % len(portal_buttons)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        label, key = portal_buttons[hub_selected_idx]
                        if key == "academy":
                            active_view = "ACADEMY"
                        elif key == "camera_setup":
                            active_view = "CAMERA_SETUP"
                            camera_supervisor.close()
                            configurator.scan_devices(max_to_test=8)
                        elif key == "background":
                            active_view = "MINI_DOCK"
                            motion_bridge.start_background_mode()
                        else:
                            active_view = "MINI_DOCK"
                            motion_bridge.launch_portal_or_game(key)

                # ACADEMY Navigation
                elif active_view == "ACADEMY":
                    if event.key == pygame.K_LEFT:
                        academy.prev_lesson()
                    elif event.key == pygame.K_RIGHT:
                        academy.next_lesson()
                    elif event.key == pygame.K_TAB:
                        academy.toggle_cheat_sheet()

                # CAMERA SETUP Navigation
                elif active_view == "CAMERA_SETUP":
                    if event.key == pygame.K_LEFT:
                        configurator.selected_device_idx = max(0, configurator.selected_device_idx - 1)
                    elif event.key == pygame.K_RIGHT:
                        configurator.selected_device_idx = max(
                            0, min(len(configurator.detected_devices) - 1, configurator.selected_device_idx + 1))
                    elif event.key == pygame.K_1:
                        if configurator.detected_devices:
                            dev_idx = configurator.detected_devices[configurator.selected_device_idx]["device_index"]
                            configurator.assign_role(CameraRole.FRONT, dev_idx)
                    elif event.key == pygame.K_r:
                        configurator.scan_devices(max_to_test=8)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        configurator.save_to_config()
                        configurator.release_caps()
                        active_view = "HUB"
                        camera_supervisor.close()
                        camera_supervisor = build_supervisor()

                # MINI DOCK Mode
                elif active_view == "MINI_DOCK":
                    if event.key == pygame.K_F10:
                        active_view = "HUB"
                        motion_bridge.stop_bridge()

        # Camera & Pose Processing
        cam_frame = None if active_view == "CAMERA_SETUP" else camera_supervisor.get_frame()
        locked_pose = None
        pose_result = None
        preview_surf = None

        if cam_frame is not None and cam_frame.image is not None:
            pose_result = pose_tracker.process_frame(cam_frame.image, cam_frame.timestamp)
            candidates = [pose_result] if pose_result.has_person else []
            locked_pose = player_lock.update(candidates, zone_calibrator, dt)

            # Desk test: if the zone/lock rejected the person, use the raw detection anyway
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

        # Render Views
        if active_view == "HUB":
            screen.fill((14, 18, 30))
            font_title = pygame.font.Font(None, 46)
            font_btn = pygame.font.Font(None, 32)
            font_desc = pygame.font.Font(None, 22)

            title = font_title.render("UNIVERSAL MOTION GAME CONTROLLER", True, (0, 255, 200))
            screen.blit(title, (sw // 2 - title.get_width() // 2, 35))

            sub = font_desc.render("Play any web game with your body! Pick an arcade portal, direct game, or Background Mode:", True, (190, 205, 225))
            screen.blit(sub, (sw // 2 - sub.get_width() // 2, 85))

            # Render Buttons List
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

            # Bottom Status
            bridge_state = "ON" if motion_bridge.enabled else "OFF"
            stat_surf = font_desc.render(
                f"ACTIVE CAMERA: [{camera_supervisor.active_source.value.upper()}]  |  "
                f"LAST ACTION: [{action_detector.debug_last_action}]  |  BRIDGE: [{bridge_state}]",
                True, (46, 204, 113))
            screen.blit(stat_surf, (sw // 2 - stat_surf.get_width() // 2, sh - 45))

        elif active_view == "ACADEMY":
            academy.draw(screen, last_action=action_detector.debug_last_action, pose=locked_pose)

            # Diagnostic line: shows which stage of the pipeline is failing
            diag_font = pygame.font.Font(None, 22)
            diag_msg = (
                f"CAM: {camera_supervisor.active_source.value} | "
                f"frame: {'yes' if cam_frame is not None else 'NO'} | "
                f"mediapipe: {'yes' if pose_tracker.is_available else 'NO'} | "
                f"pose: {'yes' if (pose_result is not None and pose_result.has_person) else 'NO'} | "
                f"zone: {zone_calibrator.current_zone_state} | "
                f"locked: {'yes' if player_lock.is_locked else 'NO'} | "
                f"[F2] desk test: {'ON' if desk_test_mode else 'off'}"
            )
            screen.blit(diag_font.render(diag_msg, True, (255, 255, 255)), (20, sh - 28))

        elif active_view == "CAMERA_SETUP":
            configurator.draw(screen)

        elif active_view == "MINI_DOCK":
            # Floating Mini-Widget Companion View
            screen.fill((10, 14, 22))
            font_dock = pygame.font.Font(None, 28)
            font_small = pygame.font.Font(None, 20)

            # Draw preview feed
            if preview_surf:
                screen.blit(preview_surf, (sw // 2 - 120, sh // 2 - 120))
                pygame.draw.rect(screen, (52, 152, 219), (sw // 2 - 120, sh // 2 - 120, 240, 180), 2)

            act_surf = font_dock.render(f"ACTION: {action_detector.debug_last_action}", True, (46, 204, 113))
            screen.blit(act_surf, (sw // 2 - act_surf.get_width() // 2, sh // 2 + 80))

            if motion_bridge.active_external_portal == "background":
                tip_text = "BACKGROUND MODE ON: minimize this window, open any game, and CLICK the game so it has focus. [Esc]/[F10] = stop."
            else:
                tip_text = "Web Game Running! Minimize this window and click the game to focus it. [Esc]/[F10] = stop and return to menu."
            tip_surf = font_small.render(tip_text, True, (170, 185, 205))
            screen.blit(tip_surf, (sw // 2 - tip_surf.get_width() // 2, sh // 2 + 120))

        pygame.display.flip()

    motion_bridge.stop_bridge()
    configurator.release_caps()
    camera_supervisor.close()
    pose_tracker.close()
    pygame.quit()


if __name__ == "__main__":
    run_controller()