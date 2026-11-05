import os
import sys
import time
import ctypes
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

# Windows API Constants for Floating Always-On-Top Mini-Dock
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_SHOWWINDOW = 0x0040


def set_window_always_on_top(enable: bool, x: int = 0, y: int = 0, w: int = 320, h: int = 240):
    """Pins Pygame window to the corner as an always-on-top mini dock over the browser."""
    if os.name != "nt":
        return
    try:
        hwnd = pygame.display.get_wm_info().get("window")
        if hwnd:
            flag = HWND_TOPMOST if enable else HWND_NOTOPMOST
            ctypes.windll.user32.SetWindowPos(hwnd, flag, x, y, w, h, SWP_SHOWWINDOW)
    except Exception as err:
        log.warning("Could not set always-on-top window pos: %s", err)


def run():
    pygame.init()
    pygame.font.init()

    # Get primary display resolution from Windows
    screen_w = ctypes.windll.user32.GetSystemMetrics(0) if os.name == "nt" else 1920
    screen_h = ctypes.windll.user32.GetSystemMetrics(1) if os.name == "nt" else 1080

    hub_w, hub_h = 1280, 720
    dock_w, dock_h = 320, 240
    dock_x = screen_w - dock_w - 30
    dock_y = screen_h - dock_h - 60

    screen = pygame.display.set_mode((hub_w, hub_h), pygame.RESIZABLE)
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

    def switch_to_dock():
        nonlocal screen, active_view
        active_view = "MINI_DOCK"
        screen = pygame.display.set_mode((dock_w, dock_h), pygame.NOFRAME)
        set_window_always_on_top(True, dock_x, dock_y, dock_w, dock_h)

    def switch_to_hub():
        nonlocal screen, active_view
        active_view = "HUB"
        screen = pygame.display.set_mode((hub_w, hub_h), pygame.RESIZABLE)
        set_window_always_on_top(False, screen_w // 2 - hub_w // 2, screen_h // 2 - hub_h // 2, hub_w, hub_h)
        motion_bridge.stop_bridge()

    log.info("Universal Motion Controller started successfully.")

    while running:
        dt = clock.tick(30) / 1000.0

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if active_view != "HUB":
                        switch_to_hub()
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
                            switch_to_dock()
                            motion_bridge.start_background_mode()
                        else:
                            switch_to_dock()
                            motion_bridge.launch_portal_or_game(key)

                elif active_view == "ACADEMY":
                    if event.key == pygame.K_LEFT:
                        academy.prev_lesson()
                    elif event.key == pygame.K_RIGHT:
                        academy.next_lesson()
                    elif event.key == pygame.K_TAB:
                        academy.toggle_cheat_sheet()

                elif active_view == "MINI_DOCK":
                    if event.key in (pygame.K_F10, pygame.K_ESCAPE):
                        switch_to_hub()

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

            # Auto Seated Mode or Desk Mode: if upper body is clearly present, retain lock!
            if (desk_test_mode or pose_result.is_partial) and locked_pose is None and pose_result.has_person:
                locked_pose = pose_result

            if locked_pose and locked_pose.has_person:
                action_detector.process_pose(locked_pose, cam_frame.timestamp)

            try:
                # Resize for preview
                pw, ph = (320, 180) if active_view == "MINI_DOCK" else (240, 180)
                small_bgr = cv2.resize(cam_frame.image, (pw, ph))

                # Draw green skeleton landmarks on preview
                if locked_pose and locked_pose.landmarks:
                    for lm in locked_pose.raw_landmarks:
                        if lm.visibility > 0.5:
                            cx = int(lm.x * pw)
                            cy = int(lm.y * ph)
                            cv2.circle(small_bgr, (cx, cy), 3, (0, 255, 100), -1)

                small_rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)
                preview_surf = pygame.image.frombuffer(small_rgb.tobytes(), (pw, ph), "RGB")
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
            screen.blit(title, (hub_w // 2 - title.get_width() // 2, 35))

            sub = font_desc.render("Play web & PC games with body gestures! Select an arcade game or Background Mode:", True, (190, 205, 225))
            screen.blit(sub, (hub_w // 2 - sub.get_width() // 2, 85))

            start_y = 125
            for i, (label, key) in enumerate(portal_buttons):
                is_sel = (i == hub_selected_idx)
                box_rect = (hub_w // 2 - 340, start_y + i * 54, 680, 46)
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
            screen.blit(stat_surf, (hub_w // 2 - stat_surf.get_width() // 2, hub_h - 45))

        elif active_view == "ACADEMY":
            academy.draw(screen, last_action=action_detector.debug_last_action, pose=locked_pose)

        elif active_view == "MINI_DOCK":
            # Floating Mini-Widget (Always-On-Top Corner Box)
            screen.fill((12, 16, 26))
            font_action = pygame.font.Font(None, 24)
            font_hint = pygame.font.Font(None, 18)

            # Draw camera feed with skeleton
            if preview_surf:
                screen.blit(preview_surf, (0, 0))
                pygame.draw.rect(screen, (52, 152, 219), (0, 0, dock_w, 180), 2)

            # Action Indicator Banner
            act_text = f"ACTION: {action_detector.debug_last_action}"
            act_col = (46, 204, 113) if action_detector.debug_last_action != "STAND" else (200, 220, 240)
            act_surf = font_action.render(act_text, True, act_col)
            screen.blit(act_surf, (10, 190))

            hint_surf = font_hint.render("[Esc] Return to Menu  |  Click game to play", True, (160, 175, 195))
            screen.blit(hint_surf, (10, 218))

        pygame.display.flip()

    set_window_always_on_top(False)
    motion_bridge.stop_bridge()
    camera_supervisor.close()
    pose_tracker.close()
    pygame.quit()


if __name__ == "__main__":
    run()