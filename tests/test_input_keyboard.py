import time
import unittest
from core.events import EventType
from core.event_bus import EventBus
from core.input_keyboard import KeyboardInputAdapter, DEFAULT_KEY_MAP

class FakeConfig:
    """Minimal stand-in for Config, so these tests never touch the real config.json."""
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


def default_key_values():
    return {f"keyboard.{k}": v for k, v in DEFAULT_KEY_MAP.items()}

class TestKeyboardInputAdapter(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.adapter = KeyboardInputAdapter(bus=self.bus, cfg=FakeConfig(default_key_values()))
        self.events_received = []

        # Listen to all relevant player and system events
        for evt in [
            EventType.JUMP, EventType.DUCK, EventType.STAND,
            EventType.LEAN_LEFT, EventType.LEAN_RIGHT, EventType.LEAN_CENTER,
            EventType.GAME_PAUSE, EventType.DEBUG_TOGGLED
        ]:
            self.bus.subscribe(evt, lambda e: self.events_received.append(e.name))

    def test_03_01_space_pressed_single_jump_and_ignores_repeat(self):
        """UC 03.01: Pressing space fires exactly one JUMP; OS key-repeat is ignored."""
        self.adapter.on_key_down("space")
        self.assertEqual(self.events_received, [EventType.JUMP])

        # Simulate OS repeat while holding down space
        self.adapter.on_key_down("space", is_repeat=True)
        self.adapter.on_key_down("space", is_repeat=False)  # Key is already in _held_keys
        self.assertEqual(self.events_received, [EventType.JUMP])  # Still only 1 jump

    def test_03_02_duck_and_stand_on_release(self):
        """UC 03.02: Down arrow emits DUCK; releasing it emits STAND."""
        self.adapter.on_key_down("down")
        self.assertEqual(self.events_received, [EventType.DUCK])

        self.adapter.on_key_up("down")
        self.assertEqual(self.events_received, [EventType.DUCK, EventType.STAND])

    def test_03_03_lean_left_right_and_cancellation(self):
        """UC 03.03: Left/right leans work; pressing both cancels to LEAN_CENTER."""
        # Press Left
        self.adapter.on_key_down("left")
        self.assertEqual(self.events_received[-1], EventType.LEAN_LEFT)

        # Press Right while Left is still held -> cancel to LEAN_CENTER
        self.adapter.on_key_down("right")
        self.assertEqual(self.events_received[-1], EventType.LEAN_CENTER)

        # Release Left -> now only Right is active
        self.adapter.on_key_up("left")
        self.assertEqual(self.events_received[-1], EventType.LEAN_RIGHT)

        # Release Right -> returns to LEAN_CENTER
        self.adapter.on_key_up("right")
        self.assertEqual(self.events_received[-1], EventType.LEAN_CENTER)

    def test_03_04_jump_and_lean_simultaneous(self):
        """UC 03.04: Jump and lean can be pressed together without either being swallowed."""
        self.adapter.on_key_down("left")
        self.adapter.on_key_down("space")

        self.assertIn(EventType.LEAN_LEFT, self.events_received)
        self.assertIn(EventType.JUMP, self.events_received)

    def test_03_05_window_focus_loss_resets_held_state(self):
        """UC 03.05: Focus loss releases held keys and resets posture to neutral."""
        # Player was holding duck and left lean
        self.adapter.on_key_down("down")
        self.adapter.on_key_down("left")
        self.events_received.clear()

        # Window loses focus (e.g. OS popup or alt-tab)
        self.adapter.on_focus_lost()

        # Must have sent STAND and LEAN_CENTER
        self.assertIn(EventType.STAND, self.events_received)
        self.assertIn(EventType.LEAN_CENTER, self.events_received)
        self.assertFalse(self.adapter._is_ducking)
        self.assertEqual(self.adapter._active_lean, EventType.LEAN_CENTER)

    def test_03_07_parent_control_keys_require_ctrl_modifier(self):
        """UC 03.07: Pause/debug shortcuts require Ctrl modifier so kids don't hit them by accident."""
        # Pressing 'p' alone without Ctrl must NOT trigger pause
        self.adapter.on_key_down("p", ctrl_held=False)
        self.assertNotIn(EventType.GAME_PAUSE, self.events_received)

        # Pressing 'p' with Ctrl held triggers GAME_PAUSE
        self.adapter.on_key_down("p", ctrl_held=True)
        self.assertIn(EventType.GAME_PAUSE, self.events_received)

    def test_03_08_keyboard_mode_disable(self):
        """UC 03.08: When keyboard adapter is disabled (e.g. camera-only play), keys are ignored."""
        self.adapter.enabled = False
        self.adapter.on_key_down("space")
        self.assertEqual(len(self.events_received), 0)

    def test_03_06_custom_keybindings_from_config(self):
        """UC 03.06: Key bindings come from config, so keys can be remapped."""
        values = default_key_values()
        values["keyboard.jump"] = "w"
        adapter = KeyboardInputAdapter(bus=self.bus, cfg=FakeConfig(values))
        adapter.on_key_down("space")
        self.assertEqual(self.events_received, [])
        adapter.on_key_down("w")
        self.assertEqual(self.events_received, [EventType.JUMP])

    def test_03_06_invalid_keybinding_falls_back_to_default(self):
        """UC 03.06: An invalid key name in config falls back to the default key."""
        values = default_key_values()
        values["keyboard.jump"] = ""
        values["keyboard.duck"] = 123
        adapter = KeyboardInputAdapter(bus=self.bus, cfg=FakeConfig(values))
        adapter.on_key_down("space")
        adapter.on_key_down("down")
        self.assertEqual(self.events_received, [EventType.JUMP, EventType.DUCK])

    def test_03_09_simulated_latency(self):
        """UC 03.09: Latency switch delays event dispatch for difficulty tuning."""
        self.adapter.simulated_latency_sec = 0.05  # 50 ms delay
        start_time = time.time()
        self.adapter.on_key_down("space")

        # Not delivered immediately
        self.assertEqual(len(self.events_received), 0)

        # Even after the delay, the event waits in the thread-safe queue
        time.sleep(0.12)
        self.assertEqual(len(self.events_received), 0)

        # The main loop drains it, which is when listeners receive it
        self.bus.drain()
        self.assertIn(EventType.JUMP, self.events_received)
        self.assertGreaterEqual(time.time() - start_time, 0.05)


if __name__ == "__main__":
    unittest.main()