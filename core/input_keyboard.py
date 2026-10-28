import time
import threading
from typing import Dict, Set, Optional
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("input_keyboard")

# Standard default key names
DEFAULT_KEY_MAP = {
    "jump": "space",
    "duck": "down",
    "lean_left": "left",
    "lean_right": "right",
    "pause": "p",
    "debug": "f3",
}


class KeyboardInputAdapter:
    """
    Translates keyboard presses into game events on the Event Bus.
    Can be driven directly in headless/unit tests, or fed by pygame events.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        # Load key mapping with safe fallback (UC 03.06)
        self.key_map = self._load_key_map()

        # State tracking
        self._held_keys: Set[str] = set()
        self._is_ducking: bool = False
        self._active_lean: str = EventType.LEAN_CENTER

        # Input mode & latency simulation (UC 03.08, 03.09)
        self.enabled: bool = True
        self.simulated_latency_sec: float = 0.0  # e.g., 0.150 for 150 ms

    def _load_key_map(self) -> Dict[str, str]:
        """Loads keybindings from config with validation (UC 03.06)."""
        mapping = {}
        for action, default_key in DEFAULT_KEY_MAP.items():
            conf_val = self.config.get(f"keyboard.{action}")
            if isinstance(conf_val, str) and conf_val.strip():
                mapping[action] = conf_val.lower().strip()
            else:
                log.warning("Invalid keybinding for '%s'. Using default '%s' (UC 03.06).", action, default_key)
                mapping[action] = default_key
        return mapping

    def _dispatch(self, event_name: str, payload: Optional[dict] = None) -> None:
        """Dispatches an event, optionally after simulated latency delay (UC 03.09)."""
        if not self.enabled:
            return

        payload = payload or {}

        if self.simulated_latency_sec > 0:
            # Build the event NOW so its timestamp is the real key-press time.
            event = Event(event_name, payload, source="keyboard_delayed")
            delay = self.simulated_latency_sec

            def delayed():
                time.sleep(delay)
                # Background threads must use post(), never publish().
                self.bus.post(event)

            threading.Thread(target=delayed, daemon=True).start()
        else:
            self.bus.publish(Event(event_name, payload, source="keyboard"))

    # -------------------------------------------------------------------------
    # Key Event Handling (UC 03.01 - 03.07)
    # -------------------------------------------------------------------------

    def on_key_down(self, key_name: str, is_repeat: bool = False, ctrl_held: bool = False) -> None:
        """Called when a physical key is pressed down."""
        key = key_name.lower()

        # Check Parent Controls first - requires Ctrl modifier (UC 03.07, Gap G11)
        if ctrl_held:
            if key == self.key_map["pause"]:
                self._dispatch(EventType.GAME_PAUSE, {"reason": "parent_key", "action": "toggle"})
                return
            elif key == self.key_map["debug"]:
                self._dispatch(EventType.DEBUG_TOGGLED)
                return

        # Suppress OS auto-repeat for actions (UC 03.01)
        if is_repeat or key in self._held_keys:
            return

        self._held_keys.add(key)

        # 1. JUMP action (UC 03.01, 03.04)
        if key == self.key_map["jump"]:
            self._dispatch(EventType.JUMP)

        # 2. DUCK action (UC 03.02)
        elif key == self.key_map["duck"]:
            self._is_ducking = True
            self._dispatch(EventType.DUCK)

        # 3. LEAN actions (UC 03.03, 03.04)
        elif key in (self.key_map["lean_left"], self.key_map["lean_right"]):
            self._update_lean_state()

    def on_key_up(self, key_name: str) -> None:
        """Called when a physical key is released."""
        key = key_name.lower()
        if key in self._held_keys:
            self._held_keys.remove(key)

        # Release DUCK -> STAND (UC 03.02)
        if key == self.key_map["duck"]:
            if self._is_ducking:
                self._is_ducking = False
                self._dispatch(EventType.STAND)

        # Release LEAN -> update center/direction (UC 03.03)
        elif key in (self.key_map["lean_left"], self.key_map["lean_right"]):
            self._update_lean_state()

    def _update_lean_state(self) -> None:
        """Calculates current lean: left, right, or center if both or neither pressed (UC 03.03)."""
        left_held = self.key_map["lean_left"] in self._held_keys
        right_held = self.key_map["lean_right"] in self._held_keys

        # Both keys pressed simultaneously cancel out to LEAN_CENTER (UC 03.03)
        if left_held and right_held:
            new_state = EventType.LEAN_CENTER
        elif left_held:
            new_state = EventType.LEAN_LEFT
        elif right_held:
            new_state = EventType.LEAN_RIGHT
        else:
            new_state = EventType.LEAN_CENTER

        if new_state != self._active_lean:
            self._active_lean = new_state
            self._dispatch(new_state)

    def on_focus_lost(self) -> None:
        """
        Window loses focus while keys are held (UC 03.05).
        Releases all virtual inputs to prevent the player staying stuck in duck or lean.
        """
        if not self._held_keys and not self._is_ducking and self._active_lean == EventType.LEAN_CENTER:
            return

        log.info("Window focus lost: resetting all held keyboard states (UC 03.05).")
        self._held_keys.clear()

        if self._is_ducking:
            self._is_ducking = False
            self._dispatch(EventType.STAND)

        if self._active_lean != EventType.LEAN_CENTER:
            self._active_lean = EventType.LEAN_CENTER
            self._dispatch(EventType.LEAN_CENTER)