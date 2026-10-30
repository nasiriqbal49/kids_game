import time
import threading
from typing import Dict, Set, Optional
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("input_keyboard")

# Standard default key names with comedic shortcuts
DEFAULT_KEY_MAP = {
    "jump": "space",
    "duck": "down",
    "lean_left": "left",
    "lean_right": "right",
    "punch": "f",
    "kick": "k",
    "flap": "w",         # Wings / Chicken flap
    "fart": "b",         # Blast
    "stomp": "s",        # Giant Stomp
    "balance": "l",      # Flamingo 1-leg balance
    "swat": "t",         # Tickle swat
    "smile": "1",        # Emotion smile
    "angry": "2",        # Emotion angry
    "surprise": "3",     # Emotion surprise
    "pause": "p",
    "debug": "f3",
}


class KeyboardInputAdapter:
    """
    Translates keyboard presses into game events on the Event Bus.
    Supports all standard, comedic, and emotion gestures for testing.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        self.key_map = self._load_key_map()

        self._held_keys: Set[str] = set()
        self._is_ducking: bool = False
        self._active_lean: str = EventType.LEAN_CENTER

        self.enabled: bool = True
        self.simulated_latency_sec: float = 0.0

    def _load_key_map(self) -> Dict[str, str]:
        """Loads keybindings from config with validation (UC 03.06)."""
        mapping = {}
        for action, default_key in DEFAULT_KEY_MAP.items():
            conf_val = self.config.get(f"keyboard.{action}")
            if isinstance(conf_val, str) and conf_val.strip():
                mapping[action] = conf_val.lower().strip()
            else:
                mapping[action] = default_key
        return mapping

    def _dispatch(self, event_name: str, payload: Optional[dict] = None) -> None:
        if not self.enabled:
            return

        payload = payload or {}

        if self.simulated_latency_sec > 0:
            event = Event(event_name, payload, source="keyboard_delayed")
            delay = self.simulated_latency_sec

            def delayed():
                time.sleep(delay)
                self.bus.post(event)

            threading.Thread(target=delayed, daemon=True).start()
        else:
            self.bus.publish(Event(event_name, payload, source="keyboard"))

    def on_key_down(self, key_name: str, is_repeat: bool = False, ctrl_held: bool = False) -> None:
        key = key_name.lower()

        # Parent Controls (requires Ctrl modifier)
        if ctrl_held:
            if key == self.key_map.get("pause", "p"):
                self._dispatch(EventType.GAME_PAUSE, {"reason": "parent_key", "action": "toggle"})
                return
            elif key == self.key_map.get("debug", "f3"):
                self._dispatch(EventType.DEBUG_TOGGLED)
                return

        if is_repeat or key in self._held_keys:
            return

        self._held_keys.add(key)

        # Standard Actions
        if key == self.key_map.get("jump"):
            self._dispatch(EventType.JUMP)
        elif key == self.key_map.get("duck"):
            self._is_ducking = True
            self._dispatch(EventType.DUCK)
        elif key in (self.key_map.get("lean_left"), self.key_map.get("lean_right")):
            self._update_lean_state()

        # Punch & Kick
        elif key in (self.key_map.get("punch"), "up"):
            self._dispatch(EventType.PUNCH)
        elif key in (self.key_map.get("kick"), "x"):
            self._dispatch(EventType.KICK)

        # Comedic Actions
        elif key == self.key_map.get("flap"):
            self._dispatch(EventType.CHICKEN_FLAP)
        elif key == self.key_map.get("fart"):
            self._dispatch(EventType.FART_BLAST)
        elif key == self.key_map.get("stomp"):
            self._dispatch(EventType.GIANT_STOMP)
        elif key == self.key_map.get("balance"):
            self._dispatch(EventType.FLAMINGO_BALANCE)
        elif key == self.key_map.get("swat"):
            self._dispatch(EventType.TICKLE_SWAT)

        # Emotion Gestures
        elif key == self.key_map.get("smile"):
            self._dispatch(EventType.EMOTION_SMILE)
        elif key == self.key_map.get("angry"):
            self._dispatch(EventType.EMOTION_ANGRY)
        elif key == self.key_map.get("surprise"):
            self._dispatch(EventType.EMOTION_SURPRISED)

    def on_key_up(self, key_name: str) -> None:
        key = key_name.lower()
        if key in self._held_keys:
            self._held_keys.remove(key)

        if key == self.key_map.get("duck"):
            if self._is_ducking:
                self._is_ducking = False
                self._dispatch(EventType.STAND)

        elif key in (self.key_map.get("lean_left"), self.key_map.get("lean_right")):
            self._update_lean_state()

    def _update_lean_state(self) -> None:
        left_held = self.key_map.get("lean_left") in self._held_keys
        right_held = self.key_map.get("lean_right") in self._held_keys

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
        if not self._held_keys and not self._is_ducking and self._active_lean == EventType.LEAN_CENTER:
            return

        log.info("Window focus lost: resetting held keyboard states.")
        self._held_keys.clear()

        if self._is_ducking:
            self._is_ducking = False
            self._dispatch(EventType.STAND)

        if self._active_lean != EventType.LEAN_CENTER:
            self._active_lean = EventType.LEAN_CENTER
            self._dispatch(EventType.LEAN_CENTER)