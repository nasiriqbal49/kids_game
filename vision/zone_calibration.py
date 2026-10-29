import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from vision.pose_tracker import PoseResult, PoseLandmark

log = get_logger("zone_calibration")


@dataclass
class ZoneGeometry:
    """Normalized 2D floor bounding box representing the marked floor tiles."""
    min_x: float = 0.25   # Left boundary (normalized 0.0 - 1.0)
    max_x: float = 0.75   # Right boundary
    min_y: float = 0.50   # Top boundary (back of zone)
    max_y: float = 0.98   # Bottom boundary (front of zone nearest camera)
    edge_margin: float = 0.08  # 8% edge warning band (UC 12.04)
    pixels_per_meter: float = 320.0  # Scale reference from 2ft tiles (UC 12.01)


class ZoneCalibrator:
    """
    Supervises play zone boundaries and real-world floor scale (Module 12).
    Evaluates player foot position to decide INSIDE, EDGE, or OUTSIDE.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 calibration_dir: str = "calibrations"):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.calibration_dir = Path(calibration_dir)

        self.zone = ZoneGeometry()
        self.current_zone_state: str = "INSIDE"  # "INSIDE", "EDGE", "OUTSIDE"

        # Tracking foot baseline for jump immunity (UC 12.08)
        self.last_ground_foot_x: float = 0.5
        self.last_ground_foot_y: float = 0.85

    def set_zone(self, min_x: float, max_x: float, min_y: float, max_y: float,
                 pixels_per_meter: float = 320.0) -> None:
        """Sets zone geometry with validation (UC 12.01)."""
        self.zone.min_x = max(0.0, min(1.0, min_x))
        self.zone.max_x = max(0.0, min(1.0, max_x))
        self.zone.min_y = max(0.0, min(1.0, min_y))
        self.zone.max_y = max(0.0, min(1.0, max_y))
        self.zone.pixels_per_meter = max(50.0, pixels_per_meter)

    def save_calibration(self, camera_role: str = "front", file_path: Optional[Path] = None) -> Path:
        """Saves calibration keyed by camera role (UC 12.01, 12.10)."""
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        target = file_path or (self.calibration_dir / f"zone_{camera_role}.json")

        payload = {
            "camera_role": camera_role,
            "min_x": self.zone.min_x,
            "max_x": self.zone.max_x,
            "min_y": self.zone.min_y,
            "max_y": self.zone.max_y,
            "edge_margin": self.zone.edge_margin,
            "pixels_per_meter": self.zone.pixels_per_meter
        }

        with open(target, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        log.info("Saved zone calibration for '%s' to %s (UC 12.01).", camera_role, target)
        return target

    def load_calibration(self, camera_role: str = "front", file_path: Optional[Path] = None) -> bool:
        """Loads saved zone calibration for camera role (UC 12.01, 12.10)."""
        target = file_path or (self.calibration_dir / f"zone_{camera_role}.json")
        if not target.exists():
            log.warning("No calibration found at %s. Using default zone.", target)
            return False

        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.set_zone(
                min_x=data.get("min_x", 0.25),
                max_x=data.get("max_x", 0.75),
                min_y=data.get("min_y", 0.50),
                max_y=data.get("max_y", 0.98),
                pixels_per_meter=data.get("pixels_per_meter", 320.0)
            )
            self.zone.edge_margin = data.get("edge_margin", 0.08)
            log.info("Loaded calibration for '%s' (UC 12.01).", camera_role)
            return True
        except Exception as err:
            log.error("Failed loading calibration %s: %s", target, err)
            return False

    def get_foot_position(self, pose: PoseResult) -> Optional[Tuple[float, float]]:
        """
        Calculates ground contact position using feet/ankles (UC 12.05, 12.09).
        Never uses head position to prevent lean false-positives!
        """
        if not pose.has_person or not pose.landmarks:
            return None

        left_ankle = pose.landmarks.get("left_ankle")
        right_ankle = pose.landmarks.get("right_ankle")

        if left_ankle and right_ankle:
            foot_x = (left_ankle.x + right_ankle.x) / 2.0
            foot_y = max(left_ankle.y, right_ankle.y)
            return foot_x, foot_y
        elif left_ankle:
            return left_ankle.x, left_ankle.y
        elif right_ankle:
            return right_ankle.x, right_ankle.y

        # Fallback to hips if ankles not visible
        left_hip = pose.landmarks.get("left_hip")
        right_hip = pose.landmarks.get("right_hip")
        if left_hip and right_hip:
            return (left_hip.x + right_hip.x) / 2.0, max(left_hip.y, right_hip.y)

        return None

    def evaluate_player_zone(self, pose: PoseResult, is_jumping: bool = False) -> str:
        """
        Evaluates player position relative to zone boundaries (UC 12.03, 12.04, 12.05).
        - If jumping: uses floor footprint before take-off (UC 12.08).
        - Returns: 'INSIDE', 'EDGE', or 'OUTSIDE'
        """
        foot_pos = self.get_foot_position(pose)
        if foot_pos is None:
            return self.current_zone_state

        foot_x, foot_y = foot_pos

        # If jumping, freeze y floor position to take-off ground position (UC 12.08)
        if is_jumping:
            foot_y = self.last_ground_foot_y
        else:
            self.last_ground_foot_x = foot_x
            self.last_ground_foot_y = foot_y

        # Check boundaries
        z = self.zone
        is_outside = (foot_x < z.min_x or foot_x > z.max_x or
                      foot_y < z.min_y or foot_y > z.max_y)

        if is_outside:
            new_state = "OUTSIDE"
        else:
            # Check edge warning band (UC 12.04)
            near_left = (foot_x - z.min_x) < z.edge_margin
            near_right = (z.max_x - foot_x) < z.edge_margin
            near_top = (foot_y - z.min_y) < z.edge_margin
            near_bot = (z.max_y - foot_y) < z.edge_margin

            if near_left or near_right or near_top or near_bot:
                new_state = "EDGE"
            else:
                new_state = "INSIDE"

        # State transition event emission (UC 12.03, 12.05)
        old_state = self.current_zone_state
        self.current_zone_state = new_state

        if new_state == "OUTSIDE" and old_state != "OUTSIDE":
            log.warning("Player stepped outside the zone (UC 12.05).")
            self.bus.post(Event(EventType.PLAYER_OUT_OF_ZONE, {
                "foot_x": round(foot_x, 2),
                "foot_y": round(foot_y, 2)
            }, source="zone_calibration"))
        elif new_state in ("INSIDE", "EDGE") and old_state == "OUTSIDE":
            log.info("Player returned to zone (UC 12.03).")
            self.bus.post(Event(EventType.PLAYER_IN_ZONE, source="zone_calibration"))

        return new_state