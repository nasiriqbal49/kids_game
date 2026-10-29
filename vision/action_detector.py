import time
from typing import Dict, Optional, Tuple
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from vision.pose_tracker import PoseResult

log = get_logger("action_detector")


class ActionDetector:
    """
    Converts 33-point body landmarks into game action events (Module 14 - Milestone M2).
    Outputs JUMP, LAND, DUCK, STAND, LEAN_LEFT, LEAN_RIGHT, LEAN_CENTER, HANDS_UP.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        # Dynamic Standing Baseline (UC 14.12)
        self.baseline_hip_y: Optional[float] = None
        self.baseline_body_height: float = 0.55
        self.last_hip_y: Optional[float] = None
        self.last_timestamp: float = 0.0

        # State Machines
        self.is_airborne: bool = False
        self.is_ducking: bool = False
        self.current_lean: str = EventType.LEAN_CENTER  # LEAN_LEFT, LEAN_RIGHT, LEAN_CENTER

        # Timers & Cooldowns
        self.jump_refractory_sec: float = 0.25  # Refractory time between jumps (UC 14.05)
        self.last_jump_time: float = 0.0
        self.duck_timer: float = 0.0
        self.max_duck_duration_sec: float = 5.0  # Auto-reset stuck duck (UC 14.14)

        # Sensitivity thresholds (relative to body height) (UC 14.11, 14.15)
        self.jump_threshold_ratio: float = 0.10  # 10% vertical body rise
        self.jump_min_velocity: float = 0.20     # Minimum vertical speed
        self.duck_threshold_ratio: float = 0.09  # 9% vertical body drop

        # Lean Hysteresis thresholds (UC 14.07)
        self.lean_enter_threshold: float = 0.055
        self.lean_exit_threshold: float = 0.025

        self._subscribe_events()

    def _subscribe_events(self) -> None:
        """Subscribe to tracking state changes."""
        self.bus.subscribe(EventType.PLAYER_LOST, self._on_player_lost)

    def _on_player_lost(self, event: Event) -> None:
        """Tracking lost resets avatar to neutral posture (UC 14.08)."""
        self.reset_neutral_posture()

    def reset_neutral_posture(self) -> None:
        """Resets all action states to neutral (UC 14.08)."""
        if self.is_airborne:
            self.is_airborne = False
            self.bus.post(Event(EventType.LAND, source="action_detector"))

        if self.is_ducking:
            self.is_ducking = False
            self.duck_timer = 0.0
            self.bus.post(Event(EventType.STAND, source="action_detector"))

        if self.current_lean != EventType.LEAN_CENTER:
            self.current_lean = EventType.LEAN_CENTER
            self.bus.post(Event(EventType.LEAN_CENTER, source="action_detector"))

    def process_pose(self, pose: PoseResult, timestamp: Optional[float] = None) -> None:
        """Main detection step for a single locked player frame (UC 14.01 - 14.14)."""
        now = timestamp if timestamp is not None else time.time()
        dt = max(0.001, now - self.last_timestamp) if self.last_timestamp > 0 else 0.033
        self.last_timestamp = now

        if not pose.has_person or not pose.landmarks:
            return

        lms = pose.landmarks
        l_hip = lms.get("left_hip")
        r_hip = lms.get("right_hip")
        l_sh = lms.get("left_shoulder")
        r_sh = lms.get("right_shoulder")
        nose = lms.get("nose")
        l_ankle = lms.get("left_ankle")
        r_ankle = lms.get("right_ankle")

        if not (l_hip and r_hip and l_sh and r_sh):
            return

        hip_y = (l_hip.y + r_hip.y) / 2.0
        sh_x = (l_sh.x + r_sh.x) / 2.0
        hip_x = (l_hip.x + r_hip.x) / 2.0

        # Update body height reference (nose to ankles) (UC 14.11)
        if nose and (l_ankle or r_ankle):
            ankle_y = (l_ankle.y if l_ankle else r_ankle.y)
            self.baseline_body_height = max(0.20, abs(ankle_y - nose.y))

        # Dynamic Standing Baseline Initialization & Calm Drift Adaptation (UC 14.12)
        if self.baseline_hip_y is None:
            self.baseline_hip_y = hip_y
            self.last_hip_y = hip_y
            return

        # Calculate vertical displacement and velocity
        # (In MediaPipe, y=0 is top, y=1 is bottom, so negative delta is upward motion)
        vertical_rise = self.baseline_hip_y - hip_y
        vertical_velocity = (self.last_hip_y - hip_y) / dt if self.last_hip_y is not None else 0.0
        self.last_hip_y = hip_y

        # Adapt baseline gently when calm on the floor (drift compensation)
        if abs(vertical_rise) < 0.03 and not self.is_airborne and not self.is_ducking:
            self.baseline_hip_y = (self.baseline_hip_y * 0.95) + (hip_y * 0.05)

        # -------------------------------------------------------------
        # 1. HANDS UP Detection (UC 14.13)
        # Wrists above nose -> HANDS_UP, never triggers JUMP!
        # -------------------------------------------------------------
        l_wrist = lms.get("left_wrist")
        r_wrist = lms.get("right_wrist")
        if l_wrist and r_wrist and nose:
            if l_wrist.y < nose.y and r_wrist.y < nose.y:
                self.bus.post(Event(EventType.HANDS_UP, source="action_detector"))

        # -------------------------------------------------------------
        # 2. JUMP and LAND Detection (UC 14.01 - 14.05, 14.13)
        # -------------------------------------------------------------
        jump_threshold = self.jump_threshold_ratio * self.baseline_body_height

        if not self.is_airborne and not self.is_ducking:
            # Must rise fast and high enough (UC 14.01, 14.03)
            time_since_last_jump = now - self.last_jump_time
            if (vertical_rise > jump_threshold and
                vertical_velocity > self.jump_min_velocity and
                time_since_last_jump >= self.jump_refractory_sec):
                self.is_airborne = True
                self.last_jump_time = now
                log.info("Action JUMP detected (rise=%.3f, vel=%.2f) (UC 14.01).", vertical_rise, vertical_velocity)
                self.bus.post(Event(EventType.JUMP, source="action_detector"))
        elif self.is_airborne:
            # Landing condition: hips return near baseline (UC 14.01, 14.05)
            if vertical_rise <= (jump_threshold * 0.40):
                self.is_airborne = False
                log.info("Action LAND detected (UC 14.01).")
                self.bus.post(Event(EventType.LAND, source="action_detector"))

        # -------------------------------------------------------------
        # 3. DUCK and STAND Detection (UC 14.06, 14.14)
        # -------------------------------------------------------------
        duck_threshold = self.duck_threshold_ratio * self.baseline_body_height

        if not self.is_airborne:
            # Hips drop downward past threshold (negative vertical rise)
            if -vertical_rise > duck_threshold:
                if not self.is_ducking:
                    self.is_ducking = True
                    self.duck_timer = 0.0
                    log.info("Action DUCK detected (drop=%.3f) (UC 14.06).", -vertical_rise)
                    self.bus.post(Event(EventType.DUCK, source="action_detector"))
                else:
                    self.duck_timer += dt
                    # Auto-reset stuck duck after 5 seconds (UC 14.14)
                    if self.duck_timer >= self.max_duck_duration_sec:
                        log.info("Auto-resetting duck after 5.0s timeout (UC 14.14).")
                        self.is_ducking = False
                        self.duck_timer = 0.0
                        self.bus.post(Event(EventType.STAND, source="action_detector"))
            elif self.is_ducking and -vertical_rise <= (duck_threshold * 0.50):
                # Rising back up emits STAND (UC 14.06)
                self.is_ducking = False
                self.duck_timer = 0.0
                log.info("Action STAND detected on rise (UC 14.06).")
                self.bus.post(Event(EventType.STAND, source="action_detector"))

        # -------------------------------------------------------------
        # 4. LEAN LEFT / RIGHT / CENTER with Hysteresis (UC 14.07, 14.10)
        # -------------------------------------------------------------
        torso_tilt = sh_x - hip_x  # Negative = Left lean, Positive = Right lean

        new_lean = self.current_lean

        if self.current_lean == EventType.LEAN_CENTER:
            if torso_tilt < -self.lean_enter_threshold:
                new_lean = EventType.LEAN_LEFT
            elif torso_tilt > self.lean_enter_threshold:
                new_lean = EventType.LEAN_RIGHT
        elif self.current_lean == EventType.LEAN_LEFT:
            if torso_tilt > -self.lean_exit_threshold:
                new_lean = EventType.LEAN_CENTER
        elif self.current_lean == EventType.LEAN_RIGHT:
            if torso_tilt < self.lean_exit_threshold:
                new_lean = EventType.LEAN_CENTER

        if new_lean != self.current_lean:
            self.current_lean = new_lean
            log.info("Action LEAN state changed: %s (UC 14.07).", new_lean)
            self.bus.post(Event(new_lean, source="action_detector"))