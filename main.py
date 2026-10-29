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
from engine.games.runner import RunnerGame
from engine.game_engine import GameState

# 1. Setup Logging and Config
setup_logging()
cfg = get_config()
configure_from(cfg)
log = get_logger("main")

log.info("--- Starting Kids Motion Game (Milestone M1: Keyboard Runner) ---")


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

    # Instantiate Runner Game (Module 8)
    runner = RunnerGame(bus=bus, cfg=cfg, display=display, audio=audio)

    # Start gameplay immediately
    runner.start_new_game()

    log.info("Controls:")
    log.info("  [Space]       - JUMP over low hurdles (air-time locked)")
    log.info("  [Down Arrow]  - DUCK under high bars (hold to crouch)")
    log.info("  [Left/Right]  - LEAN to switch lanes (Left, Center, Right)")
    log.info("  [Up/Down]     - Navigate Menus / Results Screen")
    log.info("  [Enter/Space] - Select option in Menu / Results Screen")
    log.info("  [Ctrl + P]    - Toggle PAUSE MENU")
    log.info("  [Esc]         - QUIT game")

    running = True
    while running and not display.quit_requested:
        dt = clock.tick(60) / 1000.0  # Lock at 60 FPS, dt in seconds

        events = pygame.event.get()
        pump_events = []

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                # 1. Results Screen Navigation (Play Again vs Main Menu)
                elif runner.engine.state == GameState.RESULTS:
                    if event.key == pygame.K_UP:
                        runner.results_nav_prev()
                    elif event.key == pygame.K_DOWN:
                        runner.results_nav_next()
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        choice = runner.results_select()
                        log.info("Results choice selected: %s", choice)
                        if choice == "Play Again":
                            runner.start_new_game()
                        elif choice == "Main Menu":
                            runner.engine.transition_to(GameState.MENU)

                # 2. Main Menu / Pause Menu Navigation
                elif runner.engine.state in (GameState.MENU, GameState.PAUSED):
                    if event.key == pygame.K_UP:
                        display.menu_nav_prev()
                    elif event.key == pygame.K_DOWN:
                        display.menu_nav_next()
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        selected = display.menu_select_instant()
                        log.info("Menu choice selected: %s", selected)
                        if selected in ("Start Game", "Play Again", "Restart"):
                            runner.start_new_game()
                        elif selected == "Resume":
                            runner.engine.transition_to(GameState.PLAYING)
                        elif selected in ("Quit", "Quit to Menu"):
                            if runner.engine.state == GameState.PAUSED:
                                runner.engine.transition_to(GameState.MENU)
                            else:
                                running = False

                # 3. Active Gameplay Jump Request
                elif event.key == pygame.K_SPACE and runner.engine.state == GameState.PLAYING:
                    runner.request_jump()
                else:
                    pump_events.append(event)
            else:
                pump_events.append(event)

        # Feed non-intercepted events into EventPump
        pump.pump(pump_events)

        # Monitor display connection & frame rate
        display.check_display_connection()
        display.check_fps(clock.get_fps())

        # Update game world
        runner.update(dt)

        # Render 3D Perspective Road, Obstacles, Player Avatar, and HUD
        runner.draw(screen)

        # Draw Menu Overlay if menu is active
        if display.menu_title and runner.engine.state in (GameState.MENU, GameState.PAUSED):
            display.draw_menu(screen)

        pygame.display.flip()

    display.close()
    audio.close()
    log.info("--- Game loop finished cleanly ---")


if __name__ == "__main__":
    run()