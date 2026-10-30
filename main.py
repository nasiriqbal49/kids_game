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
from engine.games import RunnerGame, LaneSwitchGame, FreezeDanceGame, SpookyRedLightGame
from engine.game_engine import GameState

# Vision Pipeline
from vision.camera_manager import CameraManager
from vision.camera_supervisor import CameraSupervisor
from vision.camera_configurator import CameraConfigurator, CameraRole
from vision.pose_tracker import PoseTracker
from vision.zone_calibration import ZoneCalibrator
from vision.player_lock import PlayerLock
from vision.action_detector import ActionDetector
from vision.debug_tools import DebugOverlay

# Identity & Economy Pipeline
from identity.profile_manager import ProfileManager
from identity.shop_manager import ShopManager

setup_logging()
cfg = get_config()
configure_from(cfg)
log = get_logger("main")

log.info("--- Starting Kids Motion Game (4 Complete Arcade Games + Shop Suite) ---")


def run():
    bus = get_event_bus()
    keyboard = KeyboardInputAdapter(bus=bus, cfg=cfg)
    display = DisplayManager(bus=bus, cfg=cfg)
    audio = AudioManager(bus=bus, cfg=cfg)
    pump = EventPump(display=display, keyboard=keyboard)

    display.init_display(headless=False)
    screen = display.screen
    clock = display.clock

    # Profile & Shop Managers
    profile_mgr = ProfileManager(bus=bus, cfg=cfg)
    all_profiles = profile_mgr.list_profiles()
    active_player = all_profiles[0] if all_profiles else profile_mgr.create_profile("Champion")
    profile_mgr.select_profile(active_player.profile_id)
    display.hud_state["player_name"] = active_player.name

    shop_mgr = ShopManager(bus=bus, cfg=cfg, profile_manager=profile_mgr)

    # Camera Configurator & Supervisor
    configurator = CameraConfigurator(bus=bus, cfg=cfg)

    def create_supervisor():
        f_idx = configurator.get_assigned_device(CameraRole.FRONT)
        if f_idx is None:
            f_idx = cfg.get("camera.camera_index", 0)
        l_idx = configurator.get_assigned_device(CameraRole.LAPTOP) or 0
        return CameraSupervisor(bus=bus, cfg=cfg, phone_index=f_idx, laptop_index=l_idx)

    camera_supervisor = create_supervisor()

    # Vision Tracking
    pose_tracker = PoseTracker(bus=bus, cfg=cfg)
    zone_calibrator = ZoneCalibrator(bus=bus, cfg=cfg)
    zone_calibrator.load_calibration("front")
    player_lock = PlayerLock(bus=bus, cfg=cfg)
    action_detector = ActionDetector(bus=bus, cfg=cfg)
    debug_overlay = DebugOverlay(bus=bus, cfg=cfg)

    # Instantiate All 4 Games
    runner_game = RunnerGame(bus=bus, cfg=cfg, display=display, audio=audio)
    slalom_game = LaneSwitchGame(bus=bus, cfg=cfg, display=display, audio=audio)
    freeze_game = FreezeDanceGame(bus=bus, cfg=cfg, display=display, audio=audio)
    spooky_game = SpookyRedLightGame(bus=bus, cfg=cfg, display=display, audio=audio)

    active_game = runner_game
    active_game.engine.transition_to(GameState.MENU)

    def refresh_menu():
        p_name = profile_mgr.active_profile.name if profile_mgr.active_profile else "None"
        display.set_menu("KIDS MOTION GAME", [
            "Game 1: 3D Hurdle Runner (Jump & Duck)",
            "Game 2: Coin Slalom (Lean & Smash)",
            "Game 3: Freeze Dance & Floor is Lava!",
            "Game 4: Spooky Red Light (Creep & Freeze)",
            "🛒 Virtual Coin Shop (Buy Power-ups)",
            "🛠️ Parent Workshop (Bonus Coins & Art)",
            "Camera Setup (3-Camera Wizard)",
            f"Active Player: {p_name} (Click to Change)",
            "Quit"
        ])

    refresh_menu()

    running = True
    show_camera_setup = False
    show_shop = False
    show_workshop = False

    shop_selected_idx = 0
    shop_feedback_msg = ""
    workshop_selected_idx = 0
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
                    elif show_shop:
                        show_shop = False
                        refresh_menu()
                    elif show_workshop:
                        show_workshop = False
                        refresh_menu()
                    elif active_game.engine.state == GameState.PLAYING:
                        active_game.engine.transition_to(GameState.PAUSED)
                    else:
                        running = False

                # Quick Key [C] to open Camera Setup
                elif event.key == pygame.K_c and not (show_camera_setup or show_shop or show_workshop):
                    show_camera_setup = True
                    camera_supervisor.close()
                    configurator.scan_devices(max_to_test=8)

                # -------------------------------------------------------------
                # 1. Camera Setup Screen Navigation
                # -------------------------------------------------------------
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

                # -------------------------------------------------------------
                # 2. Virtual Coin Shop Navigation
                # -------------------------------------------------------------
                elif show_shop:
                    catalog_items = shop_mgr.list_items()
                    if event.key == pygame.K_UP:
                        shop_selected_idx = (shop_selected_idx - 1) % len(catalog_items)
                        shop_feedback_msg = ""
                    elif event.key == pygame.K_DOWN:
                        shop_selected_idx = (shop_selected_idx + 1) % len(catalog_items)
                        shop_feedback_msg = ""
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if catalog_items and profile_mgr.active_profile:
                            item = catalog_items[shop_selected_idx]
                            success, msg = shop_mgr.buy_item(profile_mgr.active_profile.profile_id, item.item_id)
                            shop_feedback_msg = msg
                            if success:
                                audio.play_sound("powerup")
                            else:
                                audio.play_sound("hit")

                # -------------------------------------------------------------
                # 3. Parent Workshop Navigation
                # -------------------------------------------------------------
                elif show_workshop:
                    workshop_options = ["Grant +100 Coins", "Grant +500 Coins", "Open Custom Assets Folder", "Return to Menu"]
                    if event.key == pygame.K_UP:
                        workshop_selected_idx = (workshop_selected_idx - 1) % len(workshop_options)
                    elif event.key == pygame.K_DOWN:
                        workshop_selected_idx = (workshop_selected_idx + 1) % len(workshop_options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        opt = workshop_options[workshop_selected_idx]
                        if opt == "Grant +100 Coins" and profile_mgr.active_profile:
                            shop_mgr.parent_grant_coins(profile_mgr.active_profile.profile_id, 100)
                            audio.play_sound("powerup")
                        elif opt == "Grant +500 Coins" and profile_mgr.active_profile:
                            shop_mgr.parent_grant_coins(profile_mgr.active_profile.profile_id, 500)
                            audio.play_sound("powerup")
                        elif opt == "Open Custom Assets Folder":
                            shop_mgr.open_assets_folder_in_explorer()
                        elif opt == "Return to Menu":
                            show_workshop = False
                            refresh_menu()

                # -------------------------------------------------------------
                # 4. Results Screen Navigation
                # -------------------------------------------------------------
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
                            if active_game == runner_game:
                                profile_mgr.record_game_result("runner", runner_game.mechanics.score, coins_earned=runner_game.mechanics.score // 50)
                            elif active_game == slalom_game:
                                profile_mgr.record_game_result("lane_switch", slalom_game.mechanics.score, coins_earned=slalom_game.coins_collected)
                            elif active_game == freeze_game:
                                profile_mgr.record_game_result("freeze_dance", freeze_game.score, coins_earned=freeze_game.coins)
                            elif active_game == spooky_game:
                                profile_mgr.record_game_result("spooky_red_light", spooky_game.score, coins_earned=spooky_game.coins)

                            active_game.engine.transition_to(GameState.MENU)
                            refresh_menu()

                # -------------------------------------------------------------
                # 5. Main Menu Navigation
                # -------------------------------------------------------------
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
                        elif selected and "Game 3:" in selected:
                            active_game = freeze_game
                            active_game.start_new_game()
                        elif selected and "Game 4:" in selected:
                            active_game = spooky_game
                            active_game.start_new_game()
                        elif selected and "Virtual Coin Shop" in selected:
                            show_shop = True
                            shop_selected_idx = 0
                            shop_feedback_msg = ""
                        elif selected and "Parent Workshop" in selected:
                            show_workshop = True
                            workshop_selected_idx = 0
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

                # Keyboard Gameplay Controls
                elif active_game.engine.state == GameState.PLAYING:
                    if event.key == pygame.K_SPACE and hasattr(active_game, "request_jump"):
                        active_game.request_jump()
                    elif event.key == pygame.K_LEFT and hasattr(active_game, "shift_lane_relative"):
                        active_game.shift_lane_relative(-1)
                    elif event.key == pygame.K_RIGHT and hasattr(active_game, "shift_lane_relative"):
                        active_game.shift_lane_relative(1)
                    elif event.key in (pygame.K_UP, pygame.K_w) and hasattr(active_game, "advance_manually"):
                        active_game.advance_manually()
                    else:
                        pump_events.append(event)
                else:
                    pump_events.append(event)

        pump.pump(pump_events)

        # -------------------------------------------------------------
        # Vision Pipeline Processing
        # -------------------------------------------------------------
        in_overlay_screen = show_camera_setup or show_shop or show_workshop
        cam_frame = None if in_overlay_screen else camera_supervisor.get_frame()
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

                    if active_game == freeze_game:
                        l_hip = locked_pose.landmarks.get("left_hip")
                        r_hip = locked_pose.landmarks.get("right_hip")
                        if l_hip and r_hip:
                            freeze_game.evaluate_body_pose((l_hip.x + r_hip.x)/2.0, (l_hip.y + r_hip.y)/2.0, dt)

                    elif active_game == spooky_game:
                        foot_pos = zone_calibrator.get_foot_position(locked_pose)
                        if foot_pos:
                            spooky_game.evaluate_player_movement(foot_pos[0], foot_pos[1], dt)

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

        if active_game.engine.state == GameState.PLAYING and not in_overlay_screen:
            active_game.update(dt)

        # Render Active Game World
        active_game.draw(screen)

        # Draw Corner Camera Preview when in game
        if cam_preview_surf is not None and not in_overlay_screen:
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

        # -------------------------------------------------------------
        # 6. Render Overlays (Camera Setup / Shop / Parent Workshop)
        # -------------------------------------------------------------
        if show_camera_setup:
            configurator.draw(screen)

        elif show_shop:
            # Render Virtual Coin Shop UI
            sw, sh = screen.get_width(), screen.get_height()
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((12, 16, 26, 245))
            screen.blit(overlay, (0, 0))

            font_title = pygame.font.Font(None, 54)
            font_item = pygame.font.Font(None, 36)
            font_desc = pygame.font.Font(None, 24)

            title = font_title.render("🛒 VIRTUAL COIN SHOP", True, (241, 196, 15))
            screen.blit(title, (sw // 2 - title.get_width() // 2, 40))

            p_coins = profile_mgr.active_profile.coins if profile_mgr.active_profile else 0
            coin_wallet_surf = font_item.render(f"YOUR BALANCE: {p_coins} COINS 🟡", True, (255, 255, 255))
            screen.blit(coin_wallet_surf, (sw // 2 - coin_wallet_surf.get_width() // 2, 95))

            items = shop_mgr.list_items()
            start_y = 160
            for i, it in enumerate(items):
                is_sel = (i == shop_selected_idx)
                owned_count = profile_mgr.active_profile.inventory.get(it.item_id, 0) if profile_mgr.active_profile else 0
                box_color = (241, 196, 15) if is_sel else (50, 60, 80)

                box_rect = (sw // 2 - 380, start_y + i * 65, 760, 56)
                pygame.draw.rect(screen, (22, 28, 42), box_rect, border_radius=8)
                pygame.draw.rect(screen, box_color, box_rect, 3 if is_sel else 1, border_radius=8)

                name_color = (255, 255, 255) if is_sel else (200, 210, 220)
                name_surf = font_item.render(it.name, True, name_color)
                price_surf = font_item.render(f"{it.price} 🟡", True, (241, 196, 15))
                screen.blit(name_surf, (box_rect[0] + 20, box_rect[1] + 10))
                screen.blit(price_surf, (box_rect[0] + 450, box_rect[1] + 10))

                owned_txt = f"OWNED: {owned_count}" if it.category == "powerup" else ("EQUIPPED" if it.item_id in profile_mgr.active_profile.avatar else "UNLOCKED")
                owned_surf = font_desc.render(owned_txt, True, (46, 204, 113) if owned_count > 0 else (120, 130, 140))
                screen.blit(owned_surf, (box_rect[0] + 620, box_rect[1] + 18))

            if shop_feedback_msg:
                msg_surf = font_item.render(shop_feedback_msg, True, (46, 204, 113) if "Bought" in shop_feedback_msg else (231, 76, 60))
                screen.blit(msg_surf, (sw // 2 - msg_surf.get_width() // 2, sh - 100))

            foot_surf = font_desc.render("[Up/Down] Select  |  [Enter] Buy  |  [Esc] Return to Menu", True, (160, 170, 190))
            screen.blit(foot_surf, (sw // 2 - foot_surf.get_width() // 2, sh - 50))

        elif show_workshop:
            # Render Parent Workshop UI
            sw, sh = screen.get_height(), screen.get_height()
            overlay = pygame.Surface((screen.get_width(), sh), pygame.SRCALPHA)
            overlay.fill((16, 18, 28, 245))
            screen.blit(overlay, (0, 0))

            font_title = pygame.font.Font(None, 54)
            font_opt = pygame.font.Font(None, 40)
            font_sub = pygame.font.Font(None, 26)

            title = font_title.render("🛠️ PARENT WORKSHOP STUDIO", True, (52, 152, 219))
            screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 50))

            sub = font_sub.render("Reward good behavior with coins or add your child's drawings & voice recordings!", True, (200, 210, 220))
            screen.blit(sub, (screen.get_width() // 2 - sub.get_width() // 2, 110))

            opts = [
                "Reward +100 Coins (Good Chores / Reading)",
                "Reward +500 Coins (Big Achievement)",
                "Open Custom Assets Folder (Drop Child Art & Audio)",
                "Return to Main Menu"
            ]

            start_y = 200
            for i, op_text in enumerate(opts):
                is_sel = (i == workshop_selected_idx)
                color = (241, 196, 15) if is_sel else (180, 190, 205)
                box_color = (241, 196, 15) if is_sel else (50, 60, 80)
                box_rect = (screen.get_width() // 2 - 420, start_y + i * 85, 840, 65)

                pygame.draw.rect(screen, (24, 30, 45), box_rect, border_radius=8)
                pygame.draw.rect(screen, box_color, box_rect, 3 if is_sel else 1, border_radius=8)

                opt_surf = font_opt.render(op_text, True, color)
                screen.blit(opt_surf, (box_rect[0] + 30, box_rect[1] + 15))

            foot = font_sub.render("[Up/Down] Select Option  |  [Enter] Confirm  |  [Esc] Return to Menu", True, (160, 170, 190))
            screen.blit(foot, (screen.get_width() // 2 - foot.get_width() // 2, sh - 60))

        # Draw Menu Overlay if in Menu or Paused
        if display.menu_title and active_game.engine.state in (GameState.MENU, GameState.PAUSED) and not in_overlay_screen:
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