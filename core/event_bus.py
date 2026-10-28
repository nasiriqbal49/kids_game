import time
import threading
from typing import Callable, Dict, List, Optional, Set
from collections import deque
from core.events import Event, EventType, VALID_EVENT_NAMES
from core.logger import get_logger

log = get_logger("event_bus")

# Critical events that must NEVER be dropped even if queues get backlogged (UC 02.04)
CRITICAL_EVENTS: Set[str] = {
    EventType.GAME_OVER,
    EventType.GAME_PAUSE,
    EventType.GAME_START,
    EventType.STATE_CHANGED,
    EventType.ERROR,
    EventType.PLAYER_LOST,
}


class EventBus:
    """
    Central Event Bus for the Kids Motion Game.
    Serves as the decoupled nervous system between cameras, input adapters, 
    game engine, audio, and UI.
    """

    def __init__(self, max_queue_size: int = 1000, max_subscriber_errors: int = 5):
        # Subscribers keyed by event name: {event_name: [callbacks]}
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}

        # Cross-thread safe queue (UC 02.07)
        self._max_queue_size = max_queue_size
        self._thread_queue: deque = deque()
        self._queue_lock = threading.Lock()

        # Error tracking & isolation per subscriber (UC 02.03)
        self._failure_counts: Dict[Callable, int] = {}
        self.max_subscriber_errors = max_subscriber_errors

        # Debug tap & sampling controls (UC 02.09)
        self.debug_tap: Optional[Callable[[Event], None]] = None
        self._tap_sample_rates: Dict[str, int] = {}
        self._tap_counters: Dict[str, int] = {}

        # Lifecycle flag (UC 02.11)
        self._is_active: bool = True

    # -------------------------------------------------------------------------
    # Subscription Management (UC 02.01, 02.08)
    # -------------------------------------------------------------------------

    def subscribe(self, event_name: str, callback: Callable[[Event], None]) -> None:
        """Subscribe a listener to an event in the catalogue."""
        if event_name not in VALID_EVENT_NAMES:
            log.warning("Subscription rejected: '%s' is not in Event Catalogue (UC 02.05).", event_name)
            return

        if event_name not in self._subscribers:
            self._subscribers[event_name] = []

        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Event], None]) -> None:
        """Unsubscribe cleanly. Safe to call during event delivery (UC 02.08)."""
        if event_name in self._subscribers:
            if callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)

    def clear_subscribers(self) -> None:
        """Clear all subscribers (useful for clean unit testing and state resets)."""
        self._subscribers.clear()
        self._failure_counts.clear()

    # -------------------------------------------------------------------------
    # Synchronous Publishing (Same-Thread Dispatch)
    # -------------------------------------------------------------------------

    def publish(self, event: Event) -> None:
        """
        Immediately dispatches an event to all registered listeners.
        - Isolates subscriber exceptions so one crash never hurts another (UC 02.03).
        - Copies listener list before looping to handle unsubscriptions mid-dispatch (UC 02.08).
        """
        if not self._is_active:
            log.warning("Publish ignored: EventBus is shut down (UC 02.11).")
            return

        # Validate event name against catalogue (UC 02.05)
        if event.name not in VALID_EVENT_NAMES:
            log.error("Rejected unknown event '%s' from source '%s' (UC 02.05).", event.name, event.source)
            return

        # Validate payload shape (UC 02.06)
        if not isinstance(event.payload, dict):
            log.error("Event '%s' rejected: payload must be a dictionary, got %s (UC 02.06).",
                      event.name, type(event.payload).__name__)
            return

        # Deliver to debug tap with optional sampling (UC 02.09)
        if self.debug_tap is not None:
            self._forward_to_debug_tap(event)

        listeners = self._subscribers.get(event.name)
        if not listeners:
            log.debug("Event '%s' dropped: no active subscribers (UC 02.02).", event.name)
            return

        # Snapshot copy of listeners ensures safety if any listener unsubscribes during loop (UC 02.08)
        for callback in list(listeners):
            # Guard against repeated crashing callbacks (UC 02.03)
            if self._failure_counts.get(callback, 0) >= self.max_subscriber_errors:
                continue

            try:
                callback(event)
            except Exception as err:
                failures = self._failure_counts.get(callback, 0) + 1
                self._failure_counts[callback] = failures
                sub_name = getattr(callback, "__name__", repr(callback))
                log.error("Subscriber '%s' raised exception on event '%s': %s (Failures: %d/%d) (UC 02.03)",
                          sub_name, event.name, err, failures, self.max_subscriber_errors)

                if failures >= self.max_subscriber_errors:
                    log.warning("Subscriber '%s' disabled after %d consecutive failures.",
                                sub_name, self.max_subscriber_errors)
            else:
                self._failure_counts.pop(callback, None)

    # -------------------------------------------------------------------------
    # Cross-Thread Asynchronous Queue (UC 02.04, 02.07)
    # -------------------------------------------------------------------------

    def post(self, event: Event) -> bool:
        """
        Thread-safe enqueue from background threads. Never blocks the publisher.
        """
        if not self._is_active:
            log.warning("Post ignored: EventBus is shut down (UC 02.11).")
            return False

        if event.name not in VALID_EVENT_NAMES:
            log.error("Cannot post unknown event '%s' (UC 02.05).", event.name)
            return False

        with self._queue_lock:
            if len(self._thread_queue) >= self._max_queue_size:
                if event.name in CRITICAL_EVENTS:
                    self._drop_oldest_non_critical()
                    self._thread_queue.append(event)
                    return True
                log.warning("EventBus queue full. Dropped non-critical event '%s' (UC 02.04).", event.name)
                return False

            self._thread_queue.append(event)
            return True

    def drain(self, max_events: int = 150) -> int:
        """Dispatch queued cross-thread events on the main loop thread (UC 02.07)."""
        processed = 0
        while processed < max_events:
            with self._queue_lock:
                if not self._thread_queue:
                    break
                event = self._thread_queue.popleft()
            self.publish(event)
            processed += 1
        return processed

    def _drop_oldest_non_critical(self) -> None:
        """Drops the oldest non-critical event from the queue to free space for critical signals."""
        for i, queued_evt in enumerate(self._thread_queue):
            if queued_evt.name not in CRITICAL_EVENTS:
                del self._thread_queue[i]
                log.warning("Congestion relief: dropped oldest non-critical '%s' (UC 02.04).", queued_evt.name)
                return
        # If all events in queue are critical, pop the oldest critical as an absolute last resort
        dropped = self._thread_queue.popleft()
        log.error("Severe backlog: dropped critical event '%s' to prevent crash.", dropped.name)

    # -------------------------------------------------------------------------
    # Diagnostic, Debug Tap & Sampling (UC 02.09, 02.10)
    # -------------------------------------------------------------------------

    def set_debug_tap(self, tap_callback: Optional[Callable[[Event], None]]) -> None:
        """Set a global listener that monitors or records all dispatched events."""
        self.debug_tap = tap_callback

    def set_tap_sample_rate(self, event_name: str, sample_interval: int) -> None:
        """Sample high-rate events (e.g. process only every Nth tracking frame) to prevent lag (UC 02.09)."""
        self._tap_sample_rates[event_name] = max(1, sample_interval)
        self._tap_counters[event_name] = 0

    def _forward_to_debug_tap(self, event: Event) -> None:
        rate = self._tap_sample_rates.get(event.name, 1)
        if rate > 1:
            count = self._tap_counters.get(event.name, 0) + 1
            self._tap_counters[event.name] = count
            if count % rate != 0:
                return

        try:
            self.debug_tap(event)
        except Exception as err:
            log.error("Exception in debug tap listener: %s", err)

    @staticmethod
    def is_stale(event: Event, max_age_seconds: float = 0.5) -> bool:
        """Helper to discard outdated events arriving from high-latency sensors (UC 02.10)."""
        return (time.time() - event.timestamp) > max_age_seconds

    # -------------------------------------------------------------------------
    # Shutdown & Teardown (UC 02.11)
    # -------------------------------------------------------------------------

    def shutdown(self, timeout_seconds: float = 0.5) -> None:
        """Flushes pending events within a time budget, then halts acceptance (UC 02.11)."""
        log.info("EventBus shutdown initiated. Flushing queue (timeout: %.2fs)...", timeout_seconds)
        start_time = time.time()

        while (time.time() - start_time) < timeout_seconds:
            with self._queue_lock:
                if not self._thread_queue:
                    break
                event = self._thread_queue.popleft()
            self.publish(event)

        with self._queue_lock:
            remaining = len(self._thread_queue)
            self._thread_queue.clear()
        if remaining > 0:
            log.warning("Shutdown timeout reached with %d pending events dropped (UC 02.11).", remaining)
        self._is_active = False
        log.info("EventBus shutdown complete.")


# Global singleton instance
_event_bus_instance: Optional[EventBus] = None


def get_event_bus(reset: bool = False) -> EventBus:
    global _event_bus_instance
    if _event_bus_instance is None or reset:
        _event_bus_instance = EventBus()
    return _event_bus_instance