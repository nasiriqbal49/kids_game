import time
from typing import List, Dict, Optional, Tuple, Any
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from vision.pose_tracker import PoseResult
from vision.zone_calibration import ZoneCalibrator

log = get_logger("player_lock")


class PlayerLock:
    """
    Identifies, locks onto, and tracks a single player (Module 13).
    Ignores bystanders, siblings, and handles brief occlusions.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        # Lock states
        self.is_locked: bool = False
        self.lock_acquire_threshold_sec: float = 0.5  # 0.5s stable presence (UC 13.01)
        self.occlusion_timeout_sec: float = 2.0       # 2.0s occlusion hold (UC 13.04)

        # Timers
        self.presence_timer: float = 0.0
        self.occlusion_timer: float = 0.0
        self.multiple_people_emitted: bool = False

        # Locked player memory
        self.locked_pose: Optional[PoseResult] = None
        self.locked_proportions: Optional[Dict[str, float]] = None
        self.last_known_x: float = 0.5

    @staticmethod
    def calculate_body_proportions(pose: PoseResult) -> Optional[Dict[str, float]]:
        """Extracts relative body proportions (shoulder width, torso span) (UC 13.08)."""
        lms = pose.landmarks
        l_sh = lms.get("left_shoulder")
        r_sh = lms.get("right_shoulder")
        l_hip = lms.get("left_hip")
        r_hip = lms.get("right_hip")

        if l_sh and r_sh and l_hip and r_hip:
            shoulder_w = abs(l_sh.x - r_sh.x)
            torso_h = abs(((l_sh.y + r_sh.y) / 2.0) - ((l_hip.y + r_hip.y) / 2.0))
            return {
                "shoulder_width": shoulder_w,
                "torso_height": torso_h,
                "ratio": (shoulder_w / max(0.01, torso_h))
            }
        return None

    def update(self, candidates: List[PoseResult], zone_calibrator: ZoneCalibrator,
               dt: float) -> Optional[PoseResult]:
        """
        Processes candidate persons in the frame and returns the locked player's pose
        (UC 13.01 - 13.06, 13.08).
        """
        # Filter candidates inside or at the edge of the play zone
        in_zone = [
            p for p in candidates
            if p.has_person and zone_calibrator.evaluate_player_zone(p) in ("INSIDE", "EDGE")
        ]

        # Multiple people warning (UC 13.02)
        if len(in_zone) > 1 and not self.multiple_people_emitted:
            self.multiple_people_emitted = True
            log.warning("Multiple people detected in play zone (UC 13.02).")
            self.bus.post(Event(EventType.MULTIPLE_PEOPLE, {
                "count": len(in_zone)
            }, source="player_lock"))
        elif len(in_zone) <= 1:
            self.multiple_people_emitted = False

        # --- STATE A: NOT YET LOCKED ---
        if not self.is_locked:
            if not in_zone:
                self.presence_timer = 0.0
                return None

            # Pick person closest to zone center (x = 0.50) (UC 13.02)
            best_cand = min(
                in_zone,
                key=lambda p: abs(zone_calibrator.get_foot_position(p)[0] - 0.50)
                if zone_calibrator.get_foot_position(p) else 1.0
            )

            self.presence_timer += dt
            if self.presence_timer >= self.lock_acquire_threshold_sec:
                self.is_locked = True
                self.presence_timer = 0.0
                self.occlusion_timer = 0.0
                self.locked_pose = best_cand
                self.locked_proportions = self.calculate_body_proportions(best_cand)

                foot_pos = zone_calibrator.get_foot_position(best_cand)
                self.last_known_x = foot_pos[0] if foot_pos else 0.5

                log.info("Player locked successfully in play zone (UC 13.01).")
                self.bus.post(Event(EventType.PLAYER_LOCKED, {
                    "last_known_x": round(self.last_known_x, 2)
                }, source="player_lock"))
                return best_cand

            return None

        # --- STATE B: CURRENTLY LOCKED ---
        # Match locked player among all in-zone candidates (UC 13.03, 13.08)
        matched_candidate = None

        if in_zone:
            # Score each candidate by proximity to last known position + body proportion similarity
            best_match = None
            best_score = float("inf")

            for cand in in_zone:
                foot = zone_calibrator.get_foot_position(cand)
                if not foot:
                    continue
                pos_diff = abs(foot[0] - self.last_known_x)

                cand_prop = self.calculate_body_proportions(cand)
                prop_diff = 0.0
                if self.locked_proportions and cand_prop:
                    prop_diff = abs(self.locked_proportions["ratio"] - cand_prop["ratio"])

                # Combined match score (lower is closer)
                score = (pos_diff * 1.5) + (prop_diff * 2.0)
                if score < best_score:
                    best_score = score
                    best_match = cand

            # Require match distance to be plausible (within 0.35 normalized width)
            if best_match and best_score < 0.60:
                matched_candidate = best_match

        # Matched player found
        if matched_candidate is not None:
            self.occlusion_timer = 0.0
            self.locked_pose = matched_candidate
            foot = zone_calibrator.get_foot_position(matched_candidate)
            if foot:
                self.last_known_x = foot[0]

            prop = self.calculate_body_proportions(matched_candidate)
            if prop:
                self.locked_proportions = prop

            return matched_candidate

        # Player not directly visible: Handle Occlusion / Jump (UC 13.04, 13.06)
        self.occlusion_timer += dt
        if self.occlusion_timer <= self.occlusion_timeout_sec:
            # Hold lock during occlusion grace period
            return self.locked_pose

        # Timeout reached: Release lock (UC 13.05)
        log.info("Player lock released after occlusion timeout (UC 13.05).")
        self.is_locked = False
        self.locked_pose = None
        self.locked_proportions = None
        self.occlusion_timer = 0.0
        self.bus.post(Event(EventType.PLAYER_LOST, {
            "reason": "lock_timeout"
        }, source="player_lock"))
        return None

    def release_lock(self) -> None:
        """Manually releases the lock."""
        self.is_locked = False
        self.locked_pose = None
        self.locked_proportions = None
        self.presence_timer = 0.0
        self.occlusion_timer = 0.0