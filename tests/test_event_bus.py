import time
import threading
import unittest
from core.events import Event, EventType
from core.event_bus import EventBus, CRITICAL_EVENTS


class TestEventBus(unittest.TestCase):

    def setUp(self):
        # Create a fresh isolated EventBus instance for each test
        self.bus = EventBus(max_queue_size=5, max_subscriber_errors=3)

    def test_02_01_two_subscribers_receive_in_order(self):
        """UC 02.01: Both subscribers receive the event in publish order."""
        received_a = []
        received_b = []

        self.bus.subscribe(EventType.JUMP, lambda e: received_a.append(e.payload.get("val")))
        self.bus.subscribe(EventType.JUMP, lambda e: received_b.append(e.payload.get("val")))

        self.bus.publish(Event(EventType.JUMP, {"val": 1}))
        self.bus.publish(Event(EventType.JUMP, {"val": 2}))

        self.assertEqual(received_a, [1, 2])
        self.assertEqual(received_b, [1, 2])

    def test_02_02_event_with_no_subscribers_dropped_quietly(self):
        """UC 02.02: Event with no listeners is safely dropped without error."""
        # Should execute cleanly and return without raising
        self.bus.publish(Event(EventType.LAND, {"sound": "thud"}))

    def test_02_03_subscriber_error_isolation_and_auto_disable(self):
        """UC 02.03: A crashing subscriber does not crash others, and is auto-disabled after repeated failures."""
        normal_received = []

        def faulty_subscriber(event):
            raise RuntimeError("Simulated crash in buggy subscriber")

        def good_subscriber(event):
            normal_received.append(event.name)

        self.bus.subscribe(EventType.DUCK, faulty_subscriber)
        self.bus.subscribe(EventType.DUCK, good_subscriber)

        # Trigger 4 times (max allowed errors is 3)
        for _ in range(4):
            self.bus.publish(Event(EventType.DUCK))

        # The good subscriber must have received all 4 events intact
        self.assertEqual(len(normal_received), 4)
        # Faulty subscriber failed 3 times and was disabled on subsequent calls
        self.assertGreaterEqual(self.bus._failure_counts[faulty_subscriber], 3)

    def test_02_04_queue_congestion_and_critical_events_preserved(self):
        """UC 02.04: Non-critical events are dropped on congestion, but CRITICAL events are never dropped."""
        # Max queue size is 5 in setUp. Fill it with non-critical JUMP events:
        for i in range(5):
            self.assertTrue(self.bus.post(Event(EventType.JUMP, {"seq": i})))

        # 6th non-critical event must be dropped
        overflow_non_critical = self.bus.post(Event(EventType.JUMP, {"seq": 99}))
        self.assertFalse(overflow_non_critical)

        # But a CRITICAL event (e.g. GAME_OVER) must be accepted by dropping oldest non-critical
        overflow_critical = self.bus.post(Event(EventType.GAME_OVER, {"reason": "health_zero"}))
        self.assertTrue(overflow_critical)

        # Drain and confirm GAME_OVER made it into the queue
        drained_events = []
        self.bus.subscribe(EventType.GAME_OVER, lambda e: drained_events.append(e.name))
        self.bus.subscribe(EventType.JUMP, lambda e: drained_events.append(e.name))
        self.bus.drain(max_events=10)

        self.assertIn(EventType.GAME_OVER, drained_events)

    def test_02_05_unknown_event_rejected(self):
        """UC 02.05: Unknown event name cannot be published or subscribed to."""
        with self.assertRaises(ValueError):
            Event("UNREGISTERED_GHOST_EVENT")

    def test_02_06_payload_type_validation(self):
        """UC 02.06: Events with invalid payloads (non-dict) are rejected safely."""
        received = []
        self.bus.subscribe(EventType.JUMP, lambda e: received.append(e))

        # Manually bypass post_init check to test EventBus guard directly
        bad_event = object.__new__(Event)
        object.__setattr__(bad_event, "name", EventType.JUMP)
        object.__setattr__(bad_event, "payload", "not-a-dict")
        object.__setattr__(bad_event, "source", "test")
        object.__setattr__(bad_event, "timestamp", time.time())

        self.bus.publish(bad_event)
        # Listener should not have been called with invalid payload shape
        self.assertEqual(len(received), 0)

    def test_02_07_cross_thread_post_and_main_thread_drain(self):
        """UC 02.07: Worker thread posts event safely, main loop drains it."""
        received = []
        self.bus.subscribe(EventType.HANDS_UP, lambda e: received.append(e.source))

        def background_camera_worker():
            # Simulates MediaPipe background thread posting an action
            self.bus.post(Event(EventType.HANDS_UP, source="camera_thread"))

        worker = threading.Thread(target=background_camera_worker)
        worker.start()
        worker.join()

        # Before drain, listener has not run
        self.assertEqual(len(received), 0)

        # Main thread drains the frame
        processed = self.bus.drain()
        self.assertEqual(processed, 1)
        self.assertEqual(received, ["camera_thread"])

    def test_02_08_unsubscribe_during_delivery_finishes_cleanly(self):
        """UC 02.08: Subscriber unsubscribing during delivery does not cause iteration errors."""
        order = []

        def self_removing_sub(event):
            order.append("self_removing")
            self.bus.unsubscribe(EventType.STAND, self_removing_sub)

        def secondary_sub(event):
            order.append("secondary")

        self.bus.subscribe(EventType.STAND, self_removing_sub)
        self.bus.subscribe(EventType.STAND, secondary_sub)

        # First publish: both run, and self_removing unsubscribes itself mid-dispatch
        self.bus.publish(Event(EventType.STAND))
        self.assertEqual(order, ["self_removing", "secondary"])

        # Second publish: only secondary remains
        self.bus.publish(Event(EventType.STAND))
        self.assertEqual(order, ["self_removing", "secondary", "secondary"])

    def test_02_09_debug_tap_and_sampling(self):
        """UC 02.09: Debug tap observes events; high-rate sampling skips excess ticks."""
        tap_log = []
        self.bus.set_debug_tap(lambda e: tap_log.append(e.name))

        # Sample LEAN_LEFT: only 1 in every 3 events forwarded to tap
        self.bus.set_tap_sample_rate(EventType.LEAN_LEFT, sample_interval=3)

        for _ in range(6):
            self.bus.publish(Event(EventType.LEAN_LEFT))

        # Out of 6 events, exactly 2 should have been forwarded to debug tap
        self.assertEqual(len(tap_log), 2)

    def test_02_10_stale_event_helper(self):
        """UC 02.10: Stale events older than threshold are flagged."""
        fresh_event = Event(EventType.JUMP, timestamp=time.time())
        old_event = Event(EventType.JUMP, timestamp=time.time() - 2.0)

        self.assertFalse(EventBus.is_stale(fresh_event, max_age_seconds=0.5))
        self.assertTrue(EventBus.is_stale(old_event, max_age_seconds=0.5))

def test_02_11_shutdown_flushes_and_stops_acceptance(self):
        """UC 02.11: Shutdown flushes pending queue and rejects new events."""
        received = []
        self.bus.subscribe(EventType.GAME_PAUSE, lambda e: received.append(e.name))

        # Enqueue one pending event
        self.bus.post(Event(EventType.GAME_PAUSE))

        # Shutdown with flush
        self.bus.shutdown(timeout_seconds=0.2)

        # The pending event must have been flushed out to subscribers
        self.assertEqual(received, [EventType.GAME_PAUSE])

        # New events must be rejected after shutdown
        self.assertFalse(self.bus.post(Event(EventType.JUMP)))


if __name__ == "__main__":
    unittest.main()