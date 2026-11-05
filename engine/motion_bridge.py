import ctypes
import os
import subprocess
import sys
import threading
import time
import webbrowser
from typing import Optional, Callable, Dict, Set

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("motion_bridge")

# Windows Virtual Key Codes
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_SPACE = 0x20
VK_W = 0x57
VK_F = 0x46
VK_K = 0x4B
VK_Z = 0x5A
VK_X = 0x58
VK_B = 0x42
VK_L = 0x4C
VK_T = 0x54

# Hardware Scan Codes
SCAN_UP = 0x48
SCAN_DOWN = 0x50
SCAN_LEFT = 0x4B
SCAN_RIGHT = 0x4D
SCAN_SPACE = 0x39
SCAN_W = 0x11
SCAN_F = 0x21
SCAN_K = 0x25
SCAN_Z = 0x2C
SCAN_X = 0x2D
SCAN_B = 0x30
SCAN_L = 0x26
SCAN_T = 0x14

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800

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

KEY_BINDINGS = {
    "UP": (VK_UP, SCAN_UP, True),
    "DOWN": (VK_DOWN, SCAN_DOWN, True),
    "LEFT": (VK_LEFT, SCAN_LEFT, True),
    "RIGHT": (VK_RIGHT, SCAN_RIGHT, True),
    "SPACE": (VK_SPACE, SCAN_SPACE, False),
    "W": (VK_W, SCAN_W, False),
    "PUNCH": (VK_F, SCAN_F, False),
    "KICK": (VK_K, SCAN_K, False),
    "POWER_BLAST": (VK_Z, SCAN_Z, False),
    "SHIELD_BLOCK": (VK_X, SCAN_X, False),
    "FART_BLAST": (VK_B, SCAN_B, False),
    "FLAMINGO_BALANCE": (VK_L, SCAN_L, False),
    "TICKLE_SWAT": (VK_T, SCAN_T, False),
}


def win32_key_down(vk: int, scancode: int, is_extended: bool = False) -> None:
    if os.name != "nt":
        return
    flags = KEYEVENTF_SCANCODE | (KEYEVENTF_EXTENDEDKEY if is_extended else 0)
    ctypes.windll.user32.keybd_event(vk, scancode, flags, 0)


def win32_key_up(vk: int, scancode: int, is_extended: bool = False) -> None:
    if os.name != "nt":
        return
    flags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP | (KEYEVENTF_EXTENDEDKEY if is_extended else 0)
    ctypes.windll.user32.keybd_event(vk, scancode, flags, 0)


def win32_tap_key(vk: int, scancode: int, is_extended: bool = False, duration_sec: float = 0.08) -> None:
    win32_key_down(vk, scancode, is_extended)
    time.sleep(duration_sec)
    win32_key_up(vk, scancode, is_extended)


def simulate_mouse_click(duration_sec: float = 0.05) -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(duration_sec)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    except Exception as err:
        log.error("Failed sending mouse click: %s", err)


def simulate_right_click(duration_sec: float = 0.05) -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(duration_sec)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    except Exception as err:
        log.error("Failed sending right click: %s", err)


class MotionControllerBridge:
    """
    Universal Hardware Controller Bridge:
    Translates body gestures, steering, and Air Mouse into Windows hardware inputs.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 key_emitter: Optional[Callable[[int], None]] = None,
                 click_emitter: Optional[Callable[[], None]] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.key_emitter = key_emitter
        self.click_emitter = click_emitter

        self.enabled: bool = False
        self.active_external_portal: Optional[str] = None
        self._active_holds: Set[str] = set()

        # Desktop dimensions for Air Mouse mapping
        self.screen_w: int = ctypes.windll.user32.GetSystemMetrics(0) if os.name == "nt" else 1920
        self.screen_h: int = ctypes.windll.user32.GetSystemMetrics(1) if os.name == "nt" else 1080
        self.cursor_x: float = float(self.screen_w // 2)
        self.cursor_y: float = float(self.screen_h // 2)

        self._subscribe_events()

    def _subscribe_events(self) -> None:
        # Standard Runner Actions
        self.bus.subscribe(EventType.JUMP, lambda e: self.tap_action("UP"))
        self.bus.subscribe(EventType.DUCK, lambda e: self.tap_action("DOWN"))
        self.bus.subscribe(EventType.LEAN_LEFT, lambda e: self.tap_action("LEFT"))
        self.bus.subscribe(EventType.LEAN_RIGHT, lambda e: self.tap_action("RIGHT"))
        self.bus.subscribe(EventType.HANDS_UP, lambda e: self.tap_action("SPACE"))

        # Combat & Comedic Gestures
        self.bus.subscribe(EventType.PUNCH, lambda e: self.tap_action("PUNCH"))
        self.bus.subscribe(EventType.KICK, lambda e: self.tap_action("KICK"))
        self.bus.subscribe(EventType.SHOOT, lambda e: self.shoot_action())
        self.bus.subscribe(EventType.POWER_BLAST, lambda e: self.tap_action("POWER_BLAST"))
        self.bus.subscribe(EventType.SHIELD_BLOCK, lambda e: self.tap_action("SHIELD_BLOCK"))
        self.bus.subscribe(EventType.CHICKEN_FLAP, lambda e: self.tap_action("W"))
        self.bus.subscribe(EventType.FLAMINGO_BALANCE, lambda e: self.tap_action("FLAMINGO_BALANCE"))
        self.bus.subscribe(EventType.FART_BLAST, lambda e: self.tap_action("FART_BLAST"))
        self.bus.subscribe(EventType.TICKLE_SWAT, lambda e: self.tap_action("TICKLE_SWAT"))

        # Continuous Steering (Car / Racing Games)
        self.bus.subscribe(EventType.STEER_LEFT, lambda e: self.set_steering_hold("LEFT"))
        self.bus.subscribe(EventType.STEER_RIGHT, lambda e: self.set_steering_hold("RIGHT"))
        self.bus.subscribe(EventType.STEER_CENTER, lambda e: self.release_steering_holds())

        # Complete Air Mouse Controls
        self.bus.subscribe(EventType.CURSOR_MOVE, self._on_cursor_move)
        self.bus.subscribe(EventType.MOUSE_CLICK, self._on_mouse_click)
        self.bus.subscribe(EventType.MOUSE_DRAG_START, self._on_drag_start)
        self.bus.subscribe(EventType.MOUSE_DRAG_END, self._on_drag_end)
        self.bus.subscribe(EventType.MOUSE_RIGHT_CLICK, self._on_right_click)
        self.bus.subscribe(EventType.MOUSE_SCROLL, self._on_mouse_scroll)

    def tap_action(self, action: str) -> None:
        """Sends an instant keypress tap."""
        if not self.enabled or action not in KEY_BINDINGS:
            return
        vk, scan, is_ext = KEY_BINDINGS[action]

        if self.key_emitter:
            self.key_emitter(scan)
        else:
            threading.Thread(target=win32_tap_key, args=(vk, scan, is_ext), daemon=True).start()

    def set_steering_hold(self, direction: str) -> None:
        """Holds down the Left or Right Arrow key continuously while turned."""
        if not self.enabled or direction not in KEY_BINDINGS:
            return

        other_direction = "RIGHT" if direction == "LEFT" else "LEFT"
        if other_direction in self._active_holds:
            self._release_key(other_direction)

        if direction not in self._active_holds:
            self._active_holds.add(direction)
            vk, scan, is_ext = KEY_BINDINGS[direction]
            if self.key_emitter:
                self.key_emitter(scan)
            else:
                win32_key_down(vk, scan, is_ext)
            log.info("Holding key: %s (DirectInput Active)", direction)

    def release_steering_holds(self) -> None:
        """Releases both Left and Right Arrow keys when steering is centered."""
        for d in ("LEFT", "RIGHT"):
            if d in self._active_holds:
                self._release_key(d)

    def _release_key(self, direction: str) -> None:
        if direction in self._active_holds:
            self._active_holds.remove(direction)
            vk, scan, is_ext = KEY_BINDINGS[direction]
            if not self.key_emitter:
                win32_key_up(vk, scan, is_ext)
            log.info("Released key: %s", direction)

    def shoot_action(self) -> None:
        """Fires weapon via Left Click + Spacebar."""
        if not self.enabled:
            return
        if self.click_emitter:
            self.click_emitter()
        else:
            threading.Thread(target=simulate_mouse_click, daemon=True).start()
        self.tap_action("SPACE")

    # -------------------------------------------------------------
    # Air Mouse Hardware Injection
    # -------------------------------------------------------------
    def _on_cursor_move(self, event: Event) -> None:
        if not self.enabled or os.name != "nt":
            return
        target_x = event.payload.get("x", 0.5) * self.screen_w
        target_y = event.payload.get("y", 0.5) * self.screen_h

        # Exponential Moving Average for smooth gliding cursor
        self.cursor_x = (self.cursor_x * 0.65) + (target_x * 0.35)
        self.cursor_y = (self.cursor_y * 0.65) + (target_y * 0.35)
        ctypes.windll.user32.SetCursorPos(int(self.cursor_x), int(self.cursor_y))

    def _on_mouse_click(self, event: Event) -> None:
        if not self.enabled:
            return
        if self.click_emitter:
            self.click_emitter()
        else:
            threading.Thread(target=simulate_mouse_click, daemon=True).start()

    def _on_drag_start(self, event: Event) -> None:
        if not self.enabled or os.name != "nt":
            return
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

    def _on_drag_end(self, event: Event) -> None:
        if not self.enabled or os.name != "nt":
            return
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def _on_right_click(self, event: Event) -> None:
        if not self.enabled or os.name != "nt":
            return
        threading.Thread(target=simulate_right_click, daemon=True).start()

    def _on_mouse_scroll(self, event: Event) -> None:
        if not self.enabled or os.name != "nt":
            return
        delta = event.payload.get("delta", 0)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, int(delta), 0)

    def launch_portal_or_game(self, portal_key: str) -> bool:
        url = ARCADE_PORTALS.get(portal_key, portal_key)
        self.enabled = True
        self.active_external_portal = portal_key
        log.info("Motion Bridge activated! Launching %s (%s)...", portal_key, url)

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
        self.enabled = True
        self.active_external_portal = "background"
        log.info("Motion Bridge activated in BACKGROUND mode.")

    def stop_bridge(self) -> None:
        self.release_steering_holds()
        if os.name == "nt":
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        self.enabled = False
        self.active_external_portal = None
        log.info("Motion Controller Bridge disabled.")