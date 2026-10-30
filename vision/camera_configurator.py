import json
import time
from typing import Dict, List, Optional, Tuple, Callable, Any
import cv2
import numpy as np
import pygame

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("camera_configurator")


class CameraRole:
    FRONT = "front"      # Main full-body player tracking (Phone 1)
    SIDE = "side"        # Jump height & landing confirmer (Phone 2)
    LAPTOP = "laptop"    # Menu navigation & safety backup (Webcam)
    NONE = "none"


class CameraConfigurator:
    """
    Manages multi-camera discovery, live multi-feed previews, and visual role assignment.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 capture_factory: Optional[Callable[[int], Any]] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.capture_factory = capture_factory or (lambda idx: cv2.VideoCapture(idx))

        self.detected_devices: List[Dict[str, Any]] = []
        self.active_caps: Dict[int, Any] = {}
        
        self.role_assignments: Dict[str, Optional[int]] = {
            CameraRole.FRONT: None,
            CameraRole.SIDE: None,
            CameraRole.LAPTOP: None,
        }

        self.selected_device_idx: int = 0
        self.load_from_config()

    def scan_devices(self, max_to_test: int = 8) -> List[Dict[str, Any]]:
        """Probes video capture slots and opens preview feeds."""
        self.release_caps()
        self.detected_devices.clear()

        for idx in range(max_to_test):
            try:
                cap = self.capture_factory(idx)
                if cap is not None and cap.isOpened():
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
                    self.detected_devices.append({
                        "device_index": idx,
                        "name": f"Camera #{idx}",
                        "width": w,
                        "height": h,
                    })
                    self.active_caps[idx] = cap
            except Exception as err:
                log.debug("Error probing camera index %d: %s", idx, err)

        log.info("Camera scan complete. Found %d active devices.", len(self.detected_devices))
        return self.detected_devices

    def release_caps(self) -> None:
        """Releases preview capture instances."""
        for cap in self.active_caps.values():
            try:
                cap.release()
            except Exception:
                pass
        self.active_caps.clear()

    def get_live_preview_frames(self) -> Dict[int, np.ndarray]:
        """Grabs a live preview frame from each active camera for on-screen cards."""
        frames = {}
        for idx, cap in self.active_caps.items():
            try:
                ret, frame = cap.read()
                if ret and frame is not None:
                    frames[idx] = frame
            except Exception:
                pass
        return frames

    def assign_role(self, role: str, device_index: int) -> bool:
        """Assigns camera index to a role with conflict resolution."""
        if role not in (CameraRole.FRONT, CameraRole.SIDE, CameraRole.LAPTOP, CameraRole.NONE):
            return False

        for r, d_idx in list(self.role_assignments.items()):
            if d_idx == device_index:
                self.role_assignments[r] = None

        if role != CameraRole.NONE:
            self.role_assignments[role] = device_index
            log.info("Assigned Camera %d to role '%s'.", device_index, role)

        return True

    def get_assigned_device(self, role: str) -> Optional[int]:
        return self.role_assignments.get(role)

    def validate_setup(self) -> Tuple[bool, List[str]]:
        errors = []
        if self.role_assignments.get(CameraRole.FRONT) is None:
            errors.append("FRONT camera is required for player tracking.")
        return len(errors) == 0, errors

    def save_to_config(self) -> None:
        front_idx = self.role_assignments.get(CameraRole.FRONT)
        if front_idx is not None:
            self.config.set("camera.camera_index", front_idx)

        roles_dict = {
            "front": self.role_assignments.get(CameraRole.FRONT),
            "side": self.role_assignments.get(CameraRole.SIDE),
            "laptop": self.role_assignments.get(CameraRole.LAPTOP),
        }
        self.config.set("camera.roles", roles_dict)
        log.info("Saved camera role configuration: %s", roles_dict)

    def load_from_config(self) -> None:
        saved_roles = self.config.get("camera.roles")
        if isinstance(saved_roles, dict):
            self.role_assignments[CameraRole.FRONT] = saved_roles.get("front")
            self.role_assignments[CameraRole.SIDE] = saved_roles.get("side")
            self.role_assignments[CameraRole.LAPTOP] = saved_roles.get("laptop")
        else:
            default_cam = self.config.get("camera.camera_index", 0)
            self.role_assignments[CameraRole.FRONT] = default_cam
            self.role_assignments[CameraRole.LAPTOP] = 0

    def draw(self, surface: pygame.Surface) -> None:
        """Renders TV setup cards with live video in every box."""
        sw = surface.get_width()
        sh = surface.get_height()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 245))
        surface.blit(overlay, (0, 0))

        font_title = pygame.font.Font(None, 52)
        font_card = pygame.font.Font(None, 30)
        font_desc = pygame.font.Font(None, 24)

        # Header
        title = font_title.render("3-CAMERA SETUP & ROLE CONFIGURATOR", True, (255, 255, 255))
        surface.blit(title, (sw // 2 - title.get_width() // 2, 35))

        instructions = "[Left/Right] Select Camera  |  [1] Set FRONT  |  [2] Set SIDE  |  [3] Set LAPTOP  |  [R] Re-Scan  |  [Enter] SAVE"
        desc = font_desc.render(instructions, True, (241, 196, 15))
        surface.blit(desc, (sw // 2 - desc.get_width() // 2, 95))

        if not self.detected_devices:
            no_cam = font_card.render("No cameras detected! Plug in USB cables and press [R] to Re-Scan.", True, (231, 76, 60))
            surface.blit(no_cam, (sw // 2 - no_cam.get_width() // 2, sh // 2))
            return

        live_frames = self.get_live_preview_frames()

        # Layout Cards horizontally
        num_cams = len(self.detected_devices)
        card_w, card_h = 320, 310
        total_w = num_cams * card_w + (num_cams - 1) * 25
        start_x = max(30, (sw - total_w) // 2)
        card_y = 150

        for i, dev in enumerate(self.detected_devices):
            cx = start_x + i * (card_w + 25)
            dev_idx = dev["device_index"]
            is_selected = (i == self.selected_device_idx)

            # Determine assigned role
            current_role = "UNASSIGNED"
            for role, bound_idx in self.role_assignments.items():
                if bound_idx == dev_idx:
                    current_role = role.upper()

            border_color = (241, 196, 15) if is_selected else (60, 70, 90)
            if current_role == "FRONT":
                tag_color = (46, 204, 113)  # Green
                tag_title = "FRONT (Main Tracker)"
            elif current_role == "SIDE":
                tag_color = (52, 152, 219)  # Blue
                tag_title = "SIDE (Jump Confirmer)"
            elif current_role == "LAPTOP":
                tag_color = (155, 89, 182) # Purple
                tag_title = "LAPTOP (Menu / Backup)"
            else:
                tag_color = (120, 130, 140)
                tag_title = "UNASSIGNED"

            pygame.draw.rect(surface, (20, 26, 38), (cx, card_y, card_w, card_h), border_radius=8)
            pygame.draw.rect(surface, border_color, (cx, card_y, card_w, card_h), 3 if is_selected else 1, border_radius=8)

            # Camera Number
            hdr = font_card.render(f"Camera #{dev_idx}", True, (255, 255, 255))
            surface.blit(hdr, (cx + 15, card_y + 12))

            # Role Tag Banner
            tag_surf = font_desc.render(tag_title, True, tag_color)
            surface.blit(tag_surf, (cx + 15, card_y + 44))

            # Live Preview Window
            prev_x, prev_y = cx + 15, card_y + 75
            prev_w, prev_h = card_w - 30, 180
            pygame.draw.rect(surface, (0, 0, 0), (prev_x, prev_y, prev_w, prev_h), border_radius=4)

            if dev_idx in live_frames and live_frames[dev_idx] is not None:
                try:
                    small_img = cv2.resize(live_frames[dev_idx], (prev_w, prev_h))
                    rgb = cv2.cvtColor(small_img, cv2.COLOR_BGR2RGB)
                    surf = pygame.image.frombuffer(rgb.tobytes(), (prev_w, prev_h), "RGB")
                    surface.blit(surf, (prev_x, prev_y))
                except Exception:
                    pass
            else:
                standby = font_desc.render("[ Connecting Feed... ]", True, (120, 130, 140))
                surface.blit(standby, (prev_x + prev_w // 2 - standby.get_width() // 2, prev_y + prev_h // 2 - 10))

            # Selection marker below card
            if is_selected:
                sel_text = font_desc.render("^ SELECTED ^", True, (241, 196, 15))
                surface.blit(sel_text, (cx + card_w // 2 - sel_text.get_width() // 2, card_y + card_h + 8))

        # Bottom Validation Banner
        valid, errors = self.validate_setup()
        status_y = sh - 80
        if valid:
            status_surf = font_card.render("[ READY ] FRONT camera assigned! Press [Enter] to Save and Play!", True, (46, 204, 113))
        else:
            status_surf = font_card.render(f"[ ATTENTION ] {errors[0]} Highlight camera and press [1].", True, (231, 76, 60))

        surface.blit(status_surf, (sw // 2 - status_surf.get_width() // 2, status_y))