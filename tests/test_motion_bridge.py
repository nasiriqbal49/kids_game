import unittest
from core.events import Event, EventType
from core.event_bus import EventBus
from engine.motion_bridge import MotionControllerBridge, SCAN_UP, SCAN_DOWN, SCAN_LEFT, SCAN_RIGHT


class TestMotionBridge(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.dispatched_scancodes = []

        # Mock emitter for testing without pressing physical keys
        def mock_emitter(scancode):
            self.dispatched_scancodes.append(scancode)

        self.bridge = MotionControllerBridge(bus=self.bus, key_emitter=mock_emitter)
        self.bridge.enabled = True

    def test_jump_event_sends_up_scancode(self):
        """Publishing JUMP on EventBus translates to SCAN_UP for Temple Run."""
        self.bus.publish(Event(EventType.JUMP))
        self.assertIn(SCAN_UP, self.dispatched_scancodes)

    def test_duck_event_sends_down_scancode(self):
        """Publishing DUCK on EventBus translates to SCAN_DOWN."""
        self.bus.publish(Event(EventType.DUCK))
        self.assertIn(SCAN_DOWN, self.dispatched_scancodes)

    def test_lean_events_send_left_and_right_scancodes(self):
        """Publishing LEAN_LEFT and LEAN_RIGHT translates to SCAN_LEFT and SCAN_RIGHT."""
        self.bus.publish(Event(EventType.LEAN_LEFT))
        self.bus.publish(Event(EventType.LEAN_RIGHT))
        self.assertIn(SCAN_LEFT, self.dispatched_scancodes)
        self.assertIn(SCAN_RIGHT, self.dispatched_scancodes)

    def test_bridge_disabled_sends_nothing(self):
        """When bridge is disabled, body events do not trigger keypresses."""
        self.bridge.enabled = False
        self.bus.publish(Event(EventType.JUMP))
        self.assertEqual(len(self.dispatched_scancodes), 0)


if __name__ == "__main__":
    unittest.main()