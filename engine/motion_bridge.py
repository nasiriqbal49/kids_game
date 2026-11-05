import ctypes
import os
import sys
import threading
import time
import webbrowser
from typing import Optional, Callable, Dict

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("motion_bridge")

# Windows Scan Codes for DirectInput
SCAN_UP = 0x48       # Up Arrow
SCAN_DOWN = 0x50     # Down Arrow
SCAN_LEFT = 0x4B     # Left Arrow
SCAN_RIGHT = 0x4D    # Right Arrow
SCAN_SPACE = 0x39    # Spacebar (Fire / Action)
SCAN_F = 0x21        # 'F' key (Punch / Attack)
SCAN_K = 0x25        # 'K' key (Kick)
SCAN_Z = 0x2C        # 'Z' key (Power Attack)
SCAN_X = 0x2D        # 'X' key (Shield Block)

KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

# Top Free Arcade Game Portals & Direct Games
ARCADE_PORTALS: Dict[str, str] = {
    "poki": "https://poki.com",
    "crazy_games": "https://www.crazygames.com",
    "gamepix": "https://www.gamepix.com",
    "kizi": "https://kizi.com",
    "temple_run": "https://poki.com/en/g/temple-run-2",
    "subway_surfers": "https://poki.com/en/g/subway-surfers",
    "iron_snout": "https://poki.com/en/g/iron-snout",
    "zombie_derby": "https://www.crazygames.com/game/zombie-derby",
}

# Minimum seconds between two sends of the same action. Gestures such as PUNCH,
# STEER and SHIELD_BLOCK are detected on every camera frame while the pose is
# held (~30 times per second); without a cooldown they would spam the game.
DEFAULT_ACTION_COOLDOWNS: Dict[str, float] = {
    "UP": 0.30,
    "DOWN": 0.15,
    "LEFT": 0.25,
    "RIGHT": 0.25,
    "PUNCH": 0.35,
    "KICK": 0.35,
    "SHOOT": 0.25,
    "POWER_BLAST": 0.60,
    "SHIELD_BLOCK": 0.60,
}

KNOWN_ACTIONS = frozenset(DEFAULT_ACTION_COOLDOWNS.keys())


def press_and_release_scancode(scancode: int, duration_sec: float = 0.08) -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.user32.keybd_event(0, scancode, KEYEVENTF_SCANCODE, 0)
        time.sleep(duration_sec)
        ctypes.windll.user32.keybd_event(0, scancode, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0)
    except Exception as err:
        log.error("Failed sending keypress: %s", err)


def simulate_mouse_click(duration_sec: float = 0.05) -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(duration_sec)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    except Exception as err:
        log.error("Failed sending mouse click: %s", err)


class MotionControllerBridge:
    """
    Universal Hardware Controller Bridge:
    Translates body actions, steering gestures, punches, kicks, and shooting into
    real hardware keystrokes and mouse clicks for any PC/Web game.

    Keystrokes go to whichever window currently has keyboard focus, so the game
    window must be the foreground window while playing.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 key_emitter: Optional[Callable[[int], None]] = None,
                 click_emitter: Optional[Callable[[], None]] = None,
                 cooldowns: Optional[Dict[str, float]] = None,
                 clock: Optional[Callable[[], float]] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.key_emitter = key_emitter or press_and_release_scancode
        self.click_emitter = click_emitter or simulate_mouse_click

        # Pass cooldowns={} to disable rate limiting (useful in unit tests).
        self.cooldowns: Dict[str, float] = dict(DEFAULT_ACTION_COOLDOWNS) if cooldowns is None else dict(cooldowns)
        self._clock: Callable[[], float] = clock or time.monotonic
        self._last_sent: Dict[str, float] = {}

        self.enabled: bool = False
        self.active_external_portal: Optional[str] = None
        self._subscribe_events()

    def _subscribe_events(self) -> None:
        self.bus.subscribe(EventType.JUMP, lambda e: self.send_action("UP"))
        self.bus.subscribe(EventType.DUCK, lambda e: self.send_action("DOWN"))
        self.bus.subscribe(EventType.LEAN_LEFT, lambda e: self.send_action("LEFT"))
        self.bus.subscribe(EventType.LEAN_RIGHT, lambda e: self.send_action("RIGHT"))
        self.bus.subscribe(EventType.STEER_LEFT, lambda e: self.send_action("LEFT"))
        self.bus.subscribe(EventType.STEER_RIGHT, lambda e: self.send_action("RIGHT"))
        self.bus.subscribe(EventType.PUNCH, lambda e: self.send_action("PUNCH"))
        self.bus.subscribe(EventType.KICK, lambda e: self.send_action("KICK"))
        self.bus.subscribe(EventType.SHOOT, lambda e: self.send_action("SHOOT"))
        self.bus.subscribe(EventType.POWER_BLAST, lambda e: self.send_action("POWER_BLAST"))
        self.bus.subscribe(EventType.SHIELD_BLOCK, lambda e: self.send_action("SHIELD_BLOCK"))

    def _cooldown_ok(self, action: str) -> bool:
        """Returns True if enough time passed since the last send of this action."""
        min_gap = self.cooldowns.get(action, 0.0)
        if min_gap <= 0.0:
            return True
        now = self._clock()
        last = self._last_sent.get(action)
        if last is not None and (now - last) < min_gap:
            return False
        self._last_sent[action] = now
        return True

    def send_action(self, action: str) -> bool:
        if not self.enabled:
            return False

        if action not in KNOWN_ACTIONS:
            return False

        if not self._cooldown_ok(action):
            return False

        if action == "UP":
            threading.Thread(target=self.key_emitter, args=(SCAN_UP,), daemon=True).start()
            return True
        elif action == "DOWN":
            threading.Thread(target=self.key_emitter, args=(SCAN_DOWN,), daemon=True).start()
            return True
        elif action == "LEFT":
            threading.Thread(target=self.key_emitter, args=(SCAN_LEFT,), daemon=True).start()
            return True
        elif action == "RIGHT":
            threading.Thread(target=self.key_emitter, args=(SCAN_RIGHT,), daemon=True).start()
            return True
        elif action == "PUNCH":
            threading.Thread(target=self.key_emitter, args=(SCAN_F,), daemon=True).start()
            threading.Thread(target=self.key_emitter, args=(SCAN_Z,), daemon=True).start()
            return True
        elif action == "KICK":
            threading.Thread(target=self.key_emitter, args=(SCAN_K,), daemon=True).start()
            return True
        elif action == "SHOOT":
            threading.Thread(target=self.click_emitter, daemon=True).start()
            threading.Thread(target=self.key_emitter, args=(SCAN_SPACE,), daemon=True).start()
            return True
        elif action == "POWER_BLAST":
            threading.Thread(target=self.key_emitter, args=(SCAN_Z,), daemon=True).start()
            return True
        elif action == "SHIELD_BLOCK":
            threading.Thread(target=self.key_emitter, args=(SCAN_X,), daemon=True).start()
            return True

        return False

    def launch_portal_or_game(self, portal_key: str) -> bool:
        """
        Launches external web game portal. If Chrome or Edge is installed,
        opens in Sandboxed App Mode (--app=URL) without address bars or tabs,
        preventing children from accidentally navigating to personal files.
        """
        url = ARCADE_PORTALS.get(portal_key, portal_key)
        self.enabled = True
        self._last_sent.clear()
        self.active_external_portal = portal_key
        log.info("Motion Bridge activated! Launching %s (%s)...", portal_key, url)

        # Look for Chrome or Edge for kiosk/app sandboxing
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]

        browser_exe = None
        for p in chrome_paths + edge_paths:
            if os.path.exists(p):
                browser_exe = p
                break

        if browser_exe:
            try:
                # --app creates a borderless window locking kids directly into the game
                subprocess.Popen([browser_exe, f"--app={url}", "--start-maximized"])
                log.info("Launched sandboxed Kiosk window via %s", browser_exe)
                return True
            except Exception as err:
                log.warning("Kiosk launch failed: %s. Falling back to default browser.", err)

        try:
            webbrowser.open(url)
            return True
        except Exception as err:
            log.error("Failed opening browser: %s", err)
            return False

    def start_background_mode(self) -> None:
        """
        Enables the bridge WITHOUT opening any browser page. Gestures are sent to
        whichever window has focus, so any game or site can be opened manually.
        """
        self.enabled = True
        self._last_sent.clear()
        self.active_external_portal = "background"
        log.info("Motion Bridge activated in BACKGROUND mode (no browser launched).")

    def stop_bridge(self) -> None:
        self.enabled = False
        self.active_external_portal = None
        self._last_sent.clear()
        log.info("Motion Controller Bridge disabled.")