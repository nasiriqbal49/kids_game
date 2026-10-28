import sys
import pygame
from core.logger import setup_logging, configure_from, get_logger
from core.config import get_config
from core.events import Event, EventType
from core.event_bus import get_event_bus
from core.input_keyboard import KeyboardInputAdapter
from engine.display import DisplayManager
from engine.event_pump import EventPump
from engine.audio import AudioManager

# 1. Setup Logging and Config
setup_logging()
cfg = get_config()
configure_from(cfg)
log = get_logger("main")

log.info("--- Starting Kids Motion Game (Interactive Display Test) ---")


def run():
    bus = get_event_bus()
    keyboard = KeyboardInputAdapter(bus=bus, cfg=cfg)
    display = DisplayManager(bus=bus, cfg=cfg)
    audio = AudioManager(bus=bus, cfg=cfg)
    pump = EventPump(display=display, keyboard=keyboard)

    # Open window (automatically picks laptop screen 0 in office; TV at home)
    display.init_display(headless=False)
    screen = display.screen
    clock = display.clock

    # Mock game tracking variables for visual test
    current_action = "STAND"
    streak_count = 0
    score_count = 0
    jump_timer = 0.0  # Tracks jump air-time

    # Local listeners to update test state
    def on_jump(e):
        nonlocal current_action, score_count, streak_count
        current_action = "JUMP"
        score_count += 50
        streak_count += 1
        bus.publish(Event(EventType.SCORE_CHANGED, {"score": score_count, "delta": 50}))
        bus.publish(Event(EventType.STREAK_CHANGED, {"streak": streak_count, "multiplier": 1.0}))

    def on_duck(e):
        nonlocal current_action
        current_action = "DUCK"

    def on_stand(e):
        nonlocal current_action
        current_action = "STAND"

    def on_lean(e):
        nonlocal current_action
        current_action = e.name

    bus.subscribe(EventType.JUMP, on_jump)
    bus.subscribe(EventType.DUCK, on_duck)
    bus.subscribe(EventType.STAND, on_stand)
    bus.subscribe(EventType.LEAN_LEFT, on_lean)
    bus.subscribe(EventType.LEAN_RIGHT, on_lean)
    bus.subscribe(EventType.LEAN_CENTER, on_lean)

    # Start in PLAYING state so HUD is visible immediately
    bus.publish(Event(EventType.STATE_CHANGED, {"old_state": "MENU", "new_state": "PLAYING"}))

    log.info("Controls:")
    log.info("  [Space]       - JUMP (adds points & streak)")
    log.info("  [Down Arrow]  - DUCK (hold to duck, release to stand)")
    log.info("  [Left/Right]  - LEAN LEFT / LEAN RIGHT")
    log.info("  [H]           - Simulate OBSTACLE HIT (damage + red flash)")
    log.info("  [R]           - REFILL HEALTH (100 HP)")
    log.info("  [Ctrl + P]    - Toggle PAUSE MENU (Up/Down to navigate, Enter to select)")
    log.info("  [Esc]         - QUIT test")

    running = True
    while running and not display.quit_requested:
        # 1. Process OS and Keyboard Events through EventPump (Gap G10)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.KEYDOWN:
                # Quit test on Escape
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Test helper: 'H' key simulates obstacle hit
                elif event.key == pygame.K_h:
                    current_hp = max(0, display.hud_state["health"] - 20)
                    streak_count = 0
                    bus.publish(Event(EventType.OBSTACLE_HIT, {"obstacle_type": "low_hurdle"}))
                    bus.publish(Event(EventType.HEALTH_CHANGED, {"current": current_hp, "max": 100, "delta": -20, "is_low": current_hp <= 25}))
                    bus.publish(Event(EventType.STREAK_CHANGED, {"streak": 0, "multiplier": 1.0}))
                # Test helper: 'R' key refills health
                elif event.key == pygame.K_r:
                    bus.publish(Event(EventType.HEALTH_CHANGED, {"current": 100, "max": 100, "delta": 100, "is_low": False}))
                # Menu navigation keys when menu is open
                elif display.menu_title:
                    if event.key == pygame.K_UP:
                        display.menu_nav_prev()
                    elif event.key == pygame.K_DOWN:
                        display.menu_nav_next()
                    elif event.key == pygame.K_RETURN:
                        selected = display.menu_select_instant()
                        log.info("Menu selected: %s", selected)
                        if selected in ("Resume", "Start Game", "Play Again"):
                            bus.publish(Event(EventType.STATE_CHANGED, {"old_state": display.current_state, "new_state": "PLAYING"}))
                        elif selected in ("Quit", "Quit to Menu"):
                            running = False

        # Feed non-intercepted events into EventPump
        pump.pump(events)

        # 2. Check Display connection & FPS health (UC 04.03, 04.10)
        display.check_display_connection()
        clock.tick(60)  # Lock at 60 FPS
        # Auto-land after 0.5s air time if jumping
        if current_action == "JUMP":
            jump_timer += 1.0 / 60.0
            if jump_timer >= 0.5:
                current_action = "STAND"
                jump_timer = 0.0
                bus.publish(Event(EventType.LAND))
        current_fps = clock.get_fps()
        display.check_fps(current_fps)

        # 3. Render Background & Motion Avatar
        screen.fill((25, 30, 45))  # Dark navy background

        sw, sh = screen.get_width(), screen.get_height()

        # Draw a visual box representing the player's posture
        box_w, box_h = 100, 160
        box_x = sw // 2 - box_w // 2
        box_y = sh // 2 - 20

        # Adjust posture visually
        box_color = (52, 152, 219)  # Blue
        if current_action == "JUMP":
            box_y -= 120
            box_color = (241, 196, 15)  # Gold
        elif current_action == "DUCK":
            box_h = 80
            box_y += 60
            box_color = (155, 89, 182)  # Purple
        elif current_action == "LEAN_LEFT":
            box_x -= 100
        elif current_action == "LEAN_RIGHT":
            box_x += 100

        pygame.draw.rect(screen, box_color, (box_x, box_y, box_w, box_h), border_radius=12)

        # Draw action text under avatar
        font = pygame.font.Font(None, 36)
        action_surf = font.render(f"ACTION: {current_action}", True, (255, 255, 255))
        screen.blit(action_surf, (sw // 2 - action_surf.get_width() // 2, sh // 2 + 180))

        # 4. Draw HUD & Menus (Module 4)
        display.draw_hud(screen)
        display.draw_menu(screen)

        pygame.display.flip()

    display.close()
    audio.close()
    log.info("--- Test loop finished cleanly ---")


if __name__ == "__main__":
    run()