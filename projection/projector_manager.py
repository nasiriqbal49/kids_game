import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import cv2
import numpy as np
import pygame

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("projector_manager")

DEFAULT_CALIBRATION_DIR = Path("calibrations")


class ProjectionMode:
    TV_ONLY = "tv_only"            # Standard mode (everything on TV)
    PROJECTOR_ONLY = "projector"   # Everything on floor
    HYBRID = "hybrid"              # TV shows HUD/avatar, Floor shows road/lava


@dataclass
class KeystoneCalibration:
    """4-corner floor tile homography mapping for tilted projectors (UC 19.02)."""
    top_left: Tuple[int, int] = (100, 100)
    top_right: Tuple[int, int] = (700, 100)
    bottom_right: Tuple[int, int] = (750, 500)
    bottom_left: Tuple[int, int] = (50, 500)


class ProjectorManager:
    """
    Manages floor projection display output, 4-corner keystone correction,
    and hybrid dual-screen rendering (Module 19 - Milestone M6).
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 calibration_dir: Optional[Path] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.calibration_dir = Path(calibration_dir) if calibration_dir else DEFAULT_CALIBRATION_DIR
        self.calibration_path = self.calibration_dir / "projector_keystone.json"

        # Mode configuration (UC 19.11)
        self.mode: str = self.config.get("projection.mode", ProjectionMode.TV_ONLY)
        self.projector_display_index: int = self.config.get("projection.display_index", 2)

        # Hardware connection state (UC 19.01, 19.07)
        self.is_projector_connected: bool = False
        self.projector_surface: Optional[pygame.Surface] = None

        # Keystone geometry (UC 19.02)
        self.keystone = KeystoneCalibration()
        self.homography_matrix: Optional[np.ndarray] = None

        self.load_calibration()

    def check_projector_connection(self, num_displays: Optional[int] = None) -> bool:
        """
        Checks if a third display (floor projector) is connected (UC 19.01, 19.07).
        If projector disconnects during Hybrid play, triggers safety pause!
        """
        if num_displays is None:
            if not pygame.get_init():
                return self.is_projector_connected
            num_displays = pygame.display.get_num_displays()

        was_connected = self.is_projector_connected
        self.is_projector_connected = num_displays > self.projector_display_index

        # Display lost mid-game -> auto-pause (UC 19.07)
        if was_connected and not self.is_projector_connected and self.mode == ProjectionMode.HYBRID:
            log.warning("Projector disconnected! Triggering safety pause (UC 19.07).")
            self.bus.publish(Event(EventType.GAME_PAUSE, {"reason": "projector_disconnect"}))

        return self.is_projector_connected

    def set_keystone_corners(self, tl: Tuple[int, int], tr: Tuple[int, int],
                             br: Tuple[int, int], bl: Tuple[int, int]) -> None:
        """Sets 4-corner floor boundary calibration points (UC 19.02)."""
        self.keystone.top_left = tl
        self.keystone.top_right = tr
        self.keystone.bottom_right = br
        self.keystone.bottom_left = bl
        self._compute_homography()
        self.save_calibration()

    def _compute_homography(self, target_w: int = 800, target_h: int = 600) -> None:
        """Calculates 3x3 homography matrix to un-warp perspective distortion."""
        src_pts = np.float32([
            self.keystone.top_left,
            self.keystone.top_right,
            self.keystone.bottom_right,
            self.keystone.bottom_left
        ])
        dst_pts = np.float32([
            [0, 0],
            [target_w, 0],
            [target_w, target_h],
            [0, target_h]
        ])
        self.homography_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

    def warp_for_floor(self, surface: pygame.Surface) -> pygame.Surface:
        """
        Warps a rendered game surface through the homography matrix
        so projected lines align perfectly with the real-world floor tiles (UC 19.02).
        """
        if self.homography_matrix is None:
            self._compute_homography(surface.get_width(), surface.get_height())

        # Convert surface to cv2 image
        w, h = surface.get_width(), surface.get_height()
        raw_str = pygame.image.tostring(surface, "RGB")
        img = np.frombuffer(raw_str, dtype=np.uint8).reshape((h, w, 3))

        # Apply perspective warp
        warped = cv2.warpPerspective(img, self.homography_matrix, (w, h))

        # Convert back to pygame surface
        return pygame.image.frombuffer(warped.tobytes(), (w, h), "RGB")

    def draw_calibration_grid(self, surface: pygame.Surface) -> None:
        """Draws high-contrast calibration pattern for room setup (UC 19.02)."""
        w, h = surface.get_width(), surface.get_height()
        surface.fill((0, 0, 0))

        # Draw grid
        for x in range(0, w, 50):
            pygame.draw.line(surface, (0, 255, 200), (x, 0), (x, h), 1)
        for y in range(0, h, 50):
            pygame.draw.line(surface, (0, 255, 200), (0, y), (w, y), 1)

        # Highlight 4 Keystone Corners
        corners = [
            self.keystone.top_left,
            self.keystone.top_right,
            self.keystone.bottom_right,
            self.keystone.bottom_left
        ]
        pygame.draw.polygon(surface, (241, 196, 15), corners, 3)

        for pt in corners:
            pygame.draw.circle(surface, (231, 76, 60), pt, 8)

        font = pygame.font.Font(None, 36)
        text = font.render("Align the 4 Red Dots to the Corners of the Floor Tiles!", True, (255, 255, 255))
        surface.blit(text, (w // 2 - text.get_width() // 2, h // 2))

    def save_calibration(self) -> bool:
        """Persists keystone corners to JSON (UC 19.02)."""
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "top_left": list(self.keystone.top_left),
            "top_right": list(self.keystone.top_right),
            "bottom_right": list(self.keystone.bottom_right),
            "bottom_left": list(self.keystone.bottom_left),
            "mode": self.mode,
            "saved_at": time.time()
        }
        try:
            with open(self.calibration_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            log.info("Saved projector keystone calibration to %s", self.calibration_path)
            return True
        except OSError as err:
            log.error("Failed saving projector calibration: %s", err)
            return False

    def load_calibration(self) -> bool:
        """Loads keystone calibration from JSON."""
        if not self.calibration_path.exists():
            return False

        try:
            with open(self.calibration_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.keystone.top_left = tuple(data.get("top_left", (100, 100)))
            self.keystone.top_right = tuple(data.get("top_right", (700, 100)))
            self.keystone.bottom_right = tuple(data.get("bottom_right", (750, 500)))
            self.keystone.bottom_left = tuple(data.get("bottom_left", (50, 500)))
            self.mode = data.get("mode", self.mode)
            self._compute_homography()
            return True
        except Exception as err:
            log.error("Error loading projector calibration: %s", err)
            return False