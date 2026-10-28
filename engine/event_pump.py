import pygame
from typing import Optional

from core.logger import get_logger

log = get_logger("event_pump")


class EventPump:
    """
    Owns the pygame event loop (gap G10): the game loop calls pump() once per frame.

    pygame.event.get() is called in ONE place only. Window events (focus loss, close)
    go to the DisplayManager; keyboard events go to the KeyboardInputAdapter.
    Nothing else may read pygame events, otherwise key presses would silently disappear.
    """

    def __init__(self, display, keyboard):
        self.display = display
        self.keyboard = keyboard

    def pump(self, events: Optional[list] = None) -> None:
        if events is None:
            if not pygame.get_init():
                return
            events = pygame.event.get()

        # Reset held keys on real focus loss so the player never stays stuck in a duck or lean (UC 03.05)
        if any(e.type == pygame.WINDOWFOCUSLOST for e in events):
            self.keyboard.on_focus_lost()

        # Window events (focus loss pause, close request) are handled by the display (UC 04.13)
        remaining = self.display.process_window_events(events)

        for event in remaining:
            if event.type == pygame.KEYDOWN:
                ctrl_held = bool(event.mod & pygame.KMOD_CTRL)
                self.keyboard.on_key_down(pygame.key.name(event.key), is_repeat=False, ctrl_held=ctrl_held)
            elif event.type == pygame.KEYUP:
                self.keyboard.on_key_up(pygame.key.name(event.key))