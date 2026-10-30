import time
from typing import Dict, Optional, Tuple, List
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from vision.pose_tracker import PoseResult

log = get_logger("action_detector")


class ActionDetector:
    """
    Converts 33-point body landmarks into game action events.
    Detects JUMP, LAND, DUCK, STAND, LEAN_LEFT, LEAN_RIGHT, LEAN_CENTER, HANDS_UP,
    plus Comedic Gestures: CHICKEN_FLAP, FART_BLAST, FLAMINGO_BALANCE, TICKLE_SWAT, GIANT_STOMP.
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
        self.jump_refractory_sec: float = 0.45
        self.last_jump_time: float = 0.0
        self.duck_timer: float = 0.0
        self.max_duck_duration_sec: float = 5.0

        # Sensitivity thresholds tuned for kids
        self.jump_threshold_ratio: float = 0.040
        self.jump_min_velocity: float = 0.065
        self.duck_threshold_ratio: float = 0.080
        self.ankle_jump_lift_ratio: float = 0.030

        # Lean Hysteresis thresholds
        self.lean_enter_threshold: float = 0.025
        self.lean_exit_threshold: float = 0.012

        # Comedic Gesture Tracking State
        self.last_elbow_y: Optional[float] = None
        self.flap_count: int = 0
        self.last_flap_time: float = 0.0

        self.balance_timer: float = 0.0
        self.balance_emitted: bool = False
        self.last_fart_time: float = 0.0

        self.swat_oscillations: int = 0
        self.last_wrist_x: Optional[float] = None
        self.last_swat_time: float = 0.0

        self._subscribe_events()

    def _subscribe_events(self) -> None:
        self.bus.subscribe(EventType.PLAYER_LOST, self._on_player_lost)

    def _on_player_lost(self, event: Event) -> None:
        self.reset_neutral_posture()

    def reset_neutral_posture(self) -> None:
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
        self.balance_timer = 0.0
        self.balance_emitted = False

    def process_pose(self, pose: PoseResult, timestamp: Optional[float] = None) -> None:
        """Main detection step for standard and comedic gestures."""
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
        l_elbow = lms.get("left_elbow")
        r_elbow = lms.get("right_elbow")
        l_wrist = lms.get("left_wrist")
        r_wrist = lms.get("right_wrist")

        if not (l_hip and r_hip and l_sh and r_sh):
            return

        hip_y = (l_hip.y + r_hip.y) / 2.0
        sh_x = (l_sh.x + r_sh.x) / 2.0
        hip_x = (l_hip.x + r_hip.x) / 2.0
        sh_y = (l_sh.y + r_sh.y) / 2.0

        current_ankle_y = None
        if l_ankle and r_ankle:
            current_ankle_y = (l_ankle.y + r_ankle.y) / 2.0
        elif l_ankle or r_ankle:
            current_ankle_y = (l_ankle.y if l_ankle else r_ankle.y)

        if nose and current_ankle_y is not None:
            self.baseline_body_height = max(0.20, abs(current_ankle_y - nose.y))

        # Dynamic Standing Baselines & Joint Initialization on Frame 0
        if self.baseline_hip_y is None:
            self.baseline_hip_y = hip_y
            self.last_hip_y = hip_y
            if current_ankle_y is not None:
                self.baseline_ankle_y = current_ankle_y
            if l_elbow and r_elbow:
                self.last_elbow_y = (l_elbow.y + r_elbow.y) / 2.0
            if l_wrist and r_wrist:
                self.last_wrist_x = (l_wrist.x + r_wrist.x) / 2.0
            return

        if self.baseline_ankle_y is None and current_ankle_y is not None:
            self.baseline_ankle_y = current_ankle_y

        vertical_rise = self.baseline_hip_y - hip_y
        vertical_velocity = (self.last_hip_y - hip_y) / dt if self.last_hip_y is not None else 0.0
        self.last_hip_y = hip_y

        self.debug_vertical_rise = vertical_rise
        self.debug_velocity = vertical_velocity

        ankle_lift = 0.0
        if self.baseline_ankle_y is not None and current_ankle_y is not None:
            ankle_lift = self.baseline_ankle_y - current_ankle_y

        if self.is_ducking:
            if self.lowest_hip_in_crouch is None or hip_y > self.lowest_hip_in_crouch:
                self.lowest_hip_in_crouch = hip_y

        if abs(vertical_rise) < 0.02 and not self.is_airborne and not self.is_ducking:
            self.baseline_hip_y = (self.baseline_hip_y * 0.96) + (hip_y * 0.04)
            if current_ankle_y is not None and self.baseline_ankle_y is not None:
                self.baseline_ankle_y = (self.baseline_ankle_y * 0.96) + (current_ankle_y * 0.04)

        # -------------------------------------------------------------
        # COMEDIC GESTURE 1: CHICKEN FLAP (Wings Glide Flight)
        # -------------------------------------------------------------
        if l_elbow and r_elbow:
            avg_elbow_y = (l_elbow.y + r_elbow.y) / 2.0
            if self.last_elbow_y is not None:
                elbow_delta = self.last_elbow_y - avg_elbow_y
                if elbow_delta > 0.035 and (now - self.last_flap_time) > 0.08:
                    self.flap_count += 1
                    self.last_flap_time = now
                    if self.flap_count >= 2:
                        self.flap_count = 0
                        self.debug_last_action = "CHICKEN_FLAP"
                        log.info("Comedic Action: CHICKEN_FLAP wing glide detected!")
                        self.bus.post(Event(EventType.CHICKEN_FLAP, source="action_detector"))
            self.last_elbow_y = avg_elbow_y

        if self.last_flap_time > 0 and (now - self.last_flap_time) > 1.2:
            self.flap_count = 0

        # -------------------------------------------------------------
        # COMEDIC GESTURE 2: FART BLAST POSE
        # -------------------------------------------------------------
        if not self.is_airborne and current_ankle_y is not None:
            ankle_x = (l_ankle.x + r_ankle.x) / 2.0 if (l_ankle and r_ankle) else hip_x
            hip_side_shift = abs(hip_x - ankle_x)
            is_crouched = (hip_y - self.baseline_hip_y) > 0.04

            if hip_side_shift > 0.070 and is_crouched and (now - self.last_fart_time) > 1.5:
                self.last_fart_time = now
                self.debug_last_action = "FART_BLAST"
                log.info("Comedic Action: FART_BLAST green cloud detected!")
                self.bus.post(Event(EventType.FART_BLAST, source="action_detector"))

        # -------------------------------------------------------------
        # COMEDIC GESTURE 3: FLAMINGO 1-LEG BALANCE
        # -------------------------------------------------------------
        if l_ankle and r_ankle and not self.is_airborne:
            ankle_split_y = abs(l_ankle.y - r_ankle.y)
            if ankle_split_y > 0.09:
                self.balance_timer += dt
                if self.balance_timer >= 1.0 and not self.balance_emitted:
                    self.balance_emitted = True
                    self.debug_last_action = "FLAMINGO_BALANCE"
                    log.info("Comedic Action: FLAMINGO_BALANCE 1-leg hold completed!")
                    self.bus.post(Event(EventType.FLAMINGO_BALANCE, source="action_detector"))
            else:
                self.balance_timer = 0.0
                self.balance_emitted = False

        # -------------------------------------------------------------
        # COMEDIC GESTURE 4: TICKLE SWAT (Rapid Hand Waving)
        # -------------------------------------------------------------
        if l_wrist and r_wrist and nose:
            if l_wrist.y < hip_y and r_wrist.y < hip_y:
                avg_wrist_x = (l_wrist.x + r_wrist.x) / 2.0
                if self.last_wrist_x is not None:
                    dx = abs(avg_wrist_x - self.last_wrist_x)
                    if dx > 0.045 and (now - self.last_swat_time) > 0.06:
                        self.swat_oscillations += 1
                        self.last_swat_time = now
                        if self.swat_oscillations >= 3:
                            self.swat_oscillations = 0
                            self.debug_last_action = "TICKLE_SWAT"
                            log.info("Comedic Action: TICKLE_SWAT rapid waving detected!")
                            self.bus.post(Event(EventType.TICKLE_SWAT, source="action_detector"))
                self.last_wrist_x = avg_wrist_x

        if self.last_swat_time > 0 and (now - self.last_swat_time) > 0.8:
            self.swat_oscillations = 0

        # -------------------------------------------------------------
        # STANDARD 1: HANDS UP / PUNCH
        # -------------------------------------------------------------
        if l_wrist and r_wrist and nose:
            if l_wrist.y < nose.y and r_wrist.y < nose.y:
                self.debug_last_action = "HANDS_UP"
                self.bus.post(Event(EventType.HANDS_UP, source="action_detector"))

        # -------------------------------------------------------------
        # STANDARD 2: JUMP and LAND Detection
        # -------------------------------------------------------------
        jump_threshold = self.jump_threshold_ratio * self.baseline_body_height
        ankle_threshold = self.ankle_jump_lift_ratio * self.baseline_body_height
        time_since_last_jump = now - self.last_jump_time
        rise_from_crouch = (self.lowest_hip_in_crouch - hip_y) if (self.is_ducking and self.lowest_hip_in_crouch) else 0.0

        is_jump_movement = (
            (vertical_rise > jump_threshold and vertical_velocity > self.jump_min_velocity) or
            (ankle_lift > ankle_threshold and vertical_velocity > 0.05) or
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
            log.info("Action JUMP detected (rise=%.3f, vel=%.2f) (UC 14.01).", vertical_rise, vertical_velocity)
            self.bus.post(Event(EventType.JUMP, source="action_detector"))

        elif self.is_airborne:
            landing_threshold = max(0.025, jump_threshold * 0.60)
            if vertical_rise <= landing_threshold:
                self.is_airborne = False
                self.debug_last_action = "LAND"
                log.info("Action LAND detected (UC 14.01).")
                self.bus.post(Event(EventType.LAND, source="action_detector"))

        # -------------------------------------------------------------
        # STANDARD 3: DUCK and STAND Detection
        # -------------------------------------------------------------
        duck_threshold = self.duck_threshold_ratio * self.baseline_body_height

        if not self.is_airborne and not is_jump_movement:
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
        # STANDARD 4: LEAN LEFT / RIGHT / CENTER
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