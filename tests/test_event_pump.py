import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from core.events import EventType
from core.event_bus import EventBus
from core.input_keyboard import KeyboardInputAdapter, DEFAULT_KEY_MAP
from engine.display import DisplayManager
from engine.event_pump import EventPump


class FakeConfig:
    """Minimal stand-in for Config, so these tests never touch the real config.json."""
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


def key_event(kind, key, mod=0):
    return pygame.event.Event(kind, key=key, mod=mod, unicode="", scancode=0)


class TestEventPump(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.bus = EventBus()
        keys = {f"keyboard.{k}": v for k, v in DEFAULT_KEY_MAP.items()}
        self.cfg = FakeConfig(keys)
        self.display = DisplayManager(bus=self.bus, cfg=self.cfg)
        self.keyboard = KeyboardInputAdapter(bus=self.bus, cfg=self.cfg)
        self.pump = EventPump(self.display, self.keyboard)

        self.received = []
        for name in (EventType.JUMP, EventType.DUCK, EventType.STAND, EventType.LEAN_LEFT,
                     EventType.LEAN_CENTER, EventType.GAME_PAUSE):
            self.bus.subscribe(name, lambda e: self.received.append((e.name, e.payload)))

    def tearDown(self):
        self.display.close()

    def names(self):
        return [n for n, _ in self.received]

    def test_03_01_via_pump_space_press_jumps(self):
        """UC 03.01 (via pygame): a space key press reaches the keyboard adapter and fires JUMP."""
        self.pump.pump([key_event(pygame.KEYDOWN, pygame.K_SPACE)])
        self.assertEqual(self.names(), [EventType.JUMP])

    def test_03_02_via_pump_duck_hold_and_release(self):
        """UC 03.02 (via pygame): down arrow ducks on press and stands on release."""
        self.pump.pump([key_event(pygame.KEYDOWN, pygame.K_DOWN)])
        self.pump.pump([key_event(pygame.KEYUP, pygame.K_DOWN)])
        self.assertEqual(self.names(), [EventType.DUCK, EventType.STAND])

    def test_03_07_via_pump_ctrl_p_pauses(self):
        """UC 03.07 (via pygame): Ctrl+P toggles pause; plain P does nothing."""
        self.pump.pump([key_event(pygame.KEYDOWN, pygame.K_p)])
        self.assertEqual(self.names(), [])
        self.pump.pump([key_event(pygame.KEYUP, pygame.K_p)])
        self.pump.pump([key_event(pygame.KEYDOWN, pygame.K_p, mod=pygame.KMOD_CTRL)])
        self.assertEqual(self.names(), [EventType.GAME_PAUSE])

    def test_03_05_via_pump_focus_loss_resets_held_keys_and_pauses(self):
        """UC 03.05 and 04.13: focus loss while ducking and leaning releases both and pauses the game."""
        self.pump.pump([key_event(pygame.KEYDOWN, pygame.K_DOWN),
                        key_event(pygame.KEYDOWN, pygame.K_LEFT)])
        self.received.clear()

        self.pump.pump([pygame.event.Event(pygame.WINDOWFOCUSLOST)])

        names = self.names()
        self.assertIn(EventType.STAND, names)
        self.assertIn(EventType.LEAN_CENTER, names)
        self.assertIn(EventType.GAME_PAUSE, names)

    def test_04_13_via_pump_window_close_requests_quit(self):
        """UC 04.13: closing the window sets quit_requested and sends no game events."""
        self.pump.pump([pygame.event.Event(pygame.QUIT)])
        self.assertTrue(self.display.quit_requested)
        self.assertEqual(self.names(), [])

    def test_04_13_via_pump_unrelated_events_are_ignored(self):
        """UC 04.13: mouse movement and other events are ignored without errors."""
        self.pump.pump([pygame.event.Event(pygame.MOUSEMOTION, pos=(5, 5), rel=(1, 1), buttons=(0, 0, 0))])
        self.assertEqual(self.names(), [])


if __name__ == "__main__":
    unittest.main()