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
    Tuned with pre-jump spring detection and dual hip/ankle tracking.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        # Dynamic Standing Baselines
        self.baseline_hip_y: Optional[float] = None
        self.baseline_ankle_y: Optional[float] = None
        self.baseline_body_height: float = 0.55
        self.last_hip_y: Optional[float] = None
        self.lowest_hip_in_crouch: Optional[float] = None
        self.last_timestamp: float = 0.0

        # State Machines
        self.is_airborne: bool = False
        self.is_ducking: bool = False
        self.current_lean: str = EventType.LEAN_CENTER

        # Debug metrics for live display
        self.debug_vertical_rise: float = 0.0
        self.debug_velocity: float = 0.0
        self.debug_last_action: str = "STAND"

        # Timers & Cooldowns
        self.jump_refractory_sec: float = 0.45  # Locks out double-triggers during air-time
        self.last_jump_time: float = 0.0
        self.duck_timer: float = 0.0
        self.max_duck_duration_sec: float = 5.0

        # Kid-friendly sensitivity thresholds
        self.jump_threshold_ratio: float = 0.040   # 4% body rise
        self.jump_min_velocity: float = 0.065      # Gentle upward velocity
        self.duck_threshold_ratio: float = 0.080   # Deliberate duck (won't trigger on tiny knee bend)
        self.ankle_jump_lift_ratio: float = 0.030  # Shoes lifting off floor

        # Lean Hysteresis thresholds
        self.lean_enter_threshold: float = 0.025
        self.lean_exit_threshold: float = 0.012

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
            self.lowest_hip_in_crouch = None
            self.bus.post(Event(EventType.STAND, source="action_detector"))

        if self.current_lean != EventType.LEAN_CENTER:
            self.current_lean = EventType.LEAN_CENTER
            self.bus.post(Event(EventType.LEAN_CENTER, source="action_detector"))

        self.debug_last_action = "STAND"

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

        current_ankle_y = None
        if l_ankle and r_ankle:
            current_ankle_y = (l_ankle.y + r_ankle.y) / 2.0
        elif l_ankle or r_ankle:
            current_ankle_y = (l_ankle.y if l_ankle else r_ankle.y)

        # Update body height reference
        if nose and current_ankle_y is not None:
            self.baseline_body_height = max(0.20, abs(current_ankle_y - nose.y))

        # Dynamic Standing Baselines
        if self.baseline_hip_y is None:
            self.baseline_hip_y = hip_y
            self.last_hip_y = hip_y
            if current_ankle_y is not None:
                self.baseline_ankle_y = current_ankle_y
            return

        if self.baseline_ankle_y is None and current_ankle_y is not None:
            self.baseline_ankle_y = current_ankle_y

        # Calculate vertical displacement and velocity
        vertical_rise = self.baseline_hip_y - hip_y
        vertical_velocity = (self.last_hip_y - hip_y) / dt if self.last_hip_y is not None else 0.0
        self.last_hip_y = hip_y

        # Save for live debug display
        self.debug_vertical_rise = vertical_rise
        self.debug_velocity = vertical_velocity

        # Ankle lift displacement (shoes leaving the floor)
        ankle_lift = 0.0
        if self.baseline_ankle_y is not None and current_ankle_y is not None:
            ankle_lift = self.baseline_ankle_y - current_ankle_y

        # Track depth during crouch for spring-jump detection
        if self.is_ducking:
            if self.lowest_hip_in_crouch is None or hip_y > self.lowest_hip_in_crouch:
                self.lowest_hip_in_crouch = hip_y

        # Dynamic baseline drift adjustment when standing still
        if abs(vertical_rise) < 0.02 and not self.is_airborne and not self.is_ducking:
            self.baseline_hip_y = (self.baseline_hip_y * 0.96) + (hip_y * 0.04)
            if current_ankle_y is not None and self.baseline_ankle_y is not None:
                self.baseline_ankle_y = (self.baseline_ankle_y * 0.96) + (current_ankle_y * 0.04)

        # -------------------------------------------------------------
        # 1. HANDS UP Detection (UC 14.13)
        # -------------------------------------------------------------
        l_wrist = lms.get("left_wrist")
        r_wrist = lms.get("right_wrist")
        if l_wrist and r_wrist and nose:
            if l_wrist.y < nose.y and r_wrist.y < nose.y:
                self.debug_last_action = "HANDS_UP"
                self.bus.post(Event(EventType.HANDS_UP, source="action_detector"))

        # -------------------------------------------------------------
        # 2. JUMP and LAND Detection (Handles Pre-Jump Crouch Springs!)
        # -------------------------------------------------------------
        jump_threshold = self.jump_threshold_ratio * self.baseline_body_height
        ankle_threshold = self.ankle_jump_lift_ratio * self.baseline_body_height
        time_since_last_jump = now - self.last_jump_time

        # Spring jump calculation: how fast and far did they rise from the bottom of their crouch?
        rise_from_crouch = (self.lowest_hip_in_crouch - hip_y) if (self.is_ducking and self.lowest_hip_in_crouch) else 0.0

        is_jump_movement = (
            # Case A: Standard jump from standing position
            (vertical_rise > jump_threshold and vertical_velocity > self.jump_min_velocity) or
            # Case B: Direct shoes/ankles leaving the floor
            (ankle_lift > ankle_threshold and vertical_velocity > 0.05) or
            # Case C: Explosive spring out of a pre-jump knee bend / crouch!
            (self.is_ducking and rise_from_crouch > 0.04 and vertical_velocity > 0.10)
        )

        if not self.is_airborne and is_jump_movement and time_since_last_jump >= self.jump_refractory_sec:
            if self.is_ducking:
                self.is_ducking = False
                self.duck_timer = 0.0
                self.lowest_hip_in_crouch = None
                self.bus.post(Event(EventType.STAND, source="action_detector"))

            self.is_airborne = True
            self.last_jump_time = now
            self.debug_last_action = "JUMP"
            log.info("Action JUMP detected (rise=%.3f, vel=%.2f, ankle_lift=%.3f) (UC 14.01).",
                     vertical_rise, vertical_velocity, ankle_lift)
            self.bus.post(Event(EventType.JUMP, source="action_detector"))

        elif self.is_airborne:
            # Landing: hips return near baseline
            landing_threshold = max(0.025, jump_threshold * 0.60)
            if vertical_rise <= landing_threshold:
                self.is_airborne = False
                self.debug_last_action = "LAND"
                log.info("Action LAND detected (UC 14.01).")
                self.bus.post(Event(EventType.LAND, source="action_detector"))

        # -------------------------------------------------------------
        # 3. DUCK and STAND Detection (Only when not airborne or jumping)
        # -------------------------------------------------------------
        duck_threshold = self.duck_threshold_ratio * self.baseline_body_height

        if not self.is_airborne and not is_jump_movement:
            # Body drops downward past threshold
            if -vertical_rise > duck_threshold:
                if not self.is_ducking:
                    self.is_ducking = True
                    self.duck_timer = 0.0
                    self.lowest_hip_in_crouch = hip_y
                    self.debug_last_action = "DUCK"
                    log.info("Action DUCK detected (drop=%.3f) (UC 14.06).", -vertical_rise)
                    self.bus.post(Event(EventType.DUCK, source="action_detector"))
                else:
                    self.duck_timer += dt
                    if self.duck_timer >= self.max_duck_duration_sec:
                        log.info("Auto-resetting duck after 5.0s timeout (UC 14.14).")
                        self.is_ducking = False
                        self.duck_timer = 0.0
                        self.lowest_hip_in_crouch = None
                        self.debug_last_action = "STAND"
                        self.bus.post(Event(EventType.STAND, source="action_detector"))

            elif self.is_ducking and -vertical_rise <= (duck_threshold * 0.50):
                self.is_ducking = False
                self.duck_timer = 0.0
                self.lowest_hip_in_crouch = None
                self.debug_last_action = "STAND"
                log.info("Action STAND detected on rise (UC 14.06).")
                self.bus.post(Event(EventType.STAND, source="action_detector"))

        # -------------------------------------------------------------
        # 4. LEAN LEFT / RIGHT / CENTER
        # -------------------------------------------------------------
        torso_tilt = sh_x - hip_x

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
            self.debug_last_action = new_lean
            log.info("Action LEAN changed: %s (tilt=%.3f) (UC 14.07).", new_lean, torso_tilt)
            self.bus.post(Event(new_lean, source="action_detector"))