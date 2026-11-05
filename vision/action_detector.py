import math
import time
from typing import Dict, Optional, Tuple, List
from collections import deque
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from vision.pose_tracker import PoseResult

log = get_logger("action_detector")


class ActionDetector:
    """
    Converts 33-point body landmarks into game actions.
    Features velocity smoothing (eliminates vel=31.3 spikes) and deliberate arm aim
    for Nerf recoil (eliminates desk mouse/typing false triggers).
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()

        self.baseline_hip_y: Optional[float] = None
        self.baseline_ankle_y: Optional[float] = None
        self.baseline_body_height: float = 0.55
        self.last_hip_y: Optional[float] = None
        self.lowest_hip_in_crouch: Optional[float] = None
        self.last_timestamp: float = 0.0

        # Velocity smoothing deque
        self.velocity_history = deque(maxlen=3)

        self.is_airborne: bool = False
        self._lower_visible_prev: bool = True
        self.is_ducking: bool = False
        self.current_lean: str = EventType.LEAN_CENTER

        self.debug_vertical_rise: float = 0.0
        self.debug_velocity: float = 0.0
        self.debug_last_action: str = "STAND"

        self.jump_refractory_sec: float = 0.45
        self.last_jump_time: float = 0.0
        self.duck_timer: float = 0.0
        self.max_duck_duration_sec: float = 5.0

        # Steering Wheel State & Smoothing Filter
        self.current_steer: str = EventType.STEER_CENTER
        self.smoothed_wrist_dy: float = 0.0

        # Air Mouse State (Click, Drag, Right-Click, Scroll)
        self.air_mouse_active: bool = False
        self.is_pinching: bool = False
        self.is_dragging: bool = False
        self.pinch_start_time: float = 0.0
        self.last_click_time: float = 0.0
        self.last_right_click_time: float = 0.0
        self.last_scroll_time: float = 0.0
        self.last_left_wrist_y: Optional[float] = None

        # Calibrated sensitivity ratios
        self.jump_threshold_ratio: float = 0.040
        self.jump_min_velocity: float = 0.065
        self.duck_threshold_ratio: float = 0.080
        self.ankle_jump_lift_ratio: float = 0.030

        self.lean_enter_threshold: float = 0.025
        self.lean_exit_threshold: float = 0.012
        
        # Lean thresholds scale with shoulder width (works seated and standing)
        self.lean_enter_ratio: float = 0.15
        self.lean_exit_ratio: float = 0.07
        # Nerf recoil: minimum upward wrist speed (normalized units/sec)
        self.recoil_min_velocity: float = 0.60

        # Comedic state
        self.last_elbow_y: Optional[float] = None
        self.flap_count: int = 0
        self.last_flap_time: float = 0.0

        self.balance_timer: float = 0.0
        self.balance_emitted: bool = False
        self.last_fart_time: float = 0.0

        self.swat_oscillations: int = 0
        self.last_wrist_x: Optional[float] = None
        self.last_swat_time: float = 0.0

        self.last_recoil_y: Optional[float] = None
        self.last_recoil_time: float = 0.0

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
        now = timestamp if timestamp is not None else time.time()
        raw_dt = now - self.last_timestamp if self.last_timestamp > 0 else 0.033
        dt = max(0.015, raw_dt)
        self.last_timestamp = now

        if not pose.has_person or not pose.landmarks:
            return

        lms = pose.landmarks
        nose = lms.get("nose")
        l_sh = lms.get("left_shoulder")
        r_sh = lms.get("right_shoulder")
        l_hip = lms.get("left_hip")
        r_hip = lms.get("right_hip")
        l_ankle = lms.get("left_ankle")
        r_ankle = lms.get("right_ankle")
        l_elbow = lms.get("left_elbow")
        r_elbow = lms.get("right_elbow")
        l_wrist = lms.get("left_wrist")
        r_wrist = lms.get("right_wrist")
        r_index = lms.get("right_index")
        r_thumb = lms.get("right_thumb")
        r_pinky = lms.get("right_pinky")
        l_index = lms.get("left_index")

        # Ignore occluded ankles if seated
        if l_ankle and l_ankle.visibility < 0.5:
            l_ankle = None
        if r_ankle and r_ankle.visibility < 0.5:
            r_ankle = None

        # -------------------------------------------------------------
        # 1. AIR MOUSE (Seated or Standing - Requires ONLY Right Hand!)
        # -------------------------------------------------------------
        # Activates whenever the right hand is raised with index visible
        if r_wrist and r_index and r_wrist.visibility > 0.4 and r_index.visibility > 0.4:
            if self.current_steer == EventType.STEER_CENTER:
                self.air_mouse_active = True
                self.debug_last_action = "AIR_MOUSE"

                # Map index finger position (comfortable active range)
                norm_x = max(0.0, min(1.0, (r_index.x - 0.20) / 0.60))
                norm_y = max(0.0, min(1.0, (r_index.y - 0.15) / 0.55))

                # Freeze cursor position during pinch so clicking does not wiggle off the button
                if not self.is_pinching:
                    self.bus.post(Event(EventType.CURSOR_MOVE, {"x": norm_x, "y": norm_y}, source="action_detector"))

                # Left Click & Drag (Thumb + Index Pinch)
                if r_thumb and r_thumb.visibility > 0.4:
                    pinch_dist = math.hypot(r_index.x - r_thumb.x, r_index.y - r_thumb.y)
                    is_currently_pinched = (pinch_dist < 0.045)

                    if is_currently_pinched:
                        if not self.is_pinching:
                            self.is_pinching = True
                            self.pinch_start_time = now
                        elif (now - self.pinch_start_time) > 0.25 and not self.is_dragging:
                            self.is_dragging = True
                            log.info("Air Mouse: DRAG START")
                            self.bus.post(Event(EventType.MOUSE_DRAG_START, source="action_detector"))
                    else:
                        if self.is_pinching:
                            if self.is_dragging:
                                self.is_dragging = False
                                log.info("Air Mouse: DRAG END (Dropped)")
                                self.bus.post(Event(EventType.MOUSE_DRAG_END, source="action_detector"))
                            elif (now - self.last_click_time) > 0.35:
                                self.last_click_time = now
                                log.info("Air Mouse: LEFT CLICK")
                                self.bus.post(Event(EventType.MOUSE_CLICK, {"type": "left"}, source="action_detector"))
                            self.is_pinching = False

                # Right Click (Thumb touches Pinky)
                if r_pinky and r_thumb and not self.is_pinching:
                    pinky_dist = math.hypot(r_pinky.x - r_thumb.x, r_pinky.y - r_thumb.y)
                    if pinky_dist < 0.048 and (now - self.last_right_click_time) > 0.60:
                        self.last_right_click_time = now
                        log.info("Air Mouse: RIGHT CLICK")
                        self.bus.post(Event(EventType.MOUSE_RIGHT_CLICK, source="action_detector"))

                # Scroll Throttle (Left Hand: Point index UP to scroll UP, DOWN to scroll DOWN)
                if l_wrist and l_index and l_wrist.visibility > 0.4 and l_index.visibility > 0.4:
                    scroll_tilt = l_wrist.y - l_index.y  # Positive = index is above wrist (pointing UP)
                    if abs(scroll_tilt) > 0.05 and (now - self.last_scroll_time) > 0.12:
                        self.last_scroll_time = now
                        scroll_amount = 120 if scroll_tilt > 0.05 else -120
                        self.bus.post(Event(EventType.MOUSE_SCROLL, {"delta": scroll_amount}, source="action_detector"))
        else:
            if self.is_dragging:
                self.is_dragging = False
                self.bus.post(Event(EventType.MOUSE_DRAG_END, source="action_detector"))
            self.air_mouse_active = False
            self.is_pinching = False

        # -------------------------------------------------------------
        # 2. BODY GEOMETRY REFERENCE (Hips & Shoulders)
        # -------------------------------------------------------------
        # Safely compute hip reference even if seated close to camera
        if l_hip and r_hip and l_hip.visibility > 0.4 and r_hip.visibility > 0.4:
            hip_y = (l_hip.y + r_hip.y) / 2.0
            hip_x = (l_hip.x + r_hip.x) / 2.0
        elif l_sh and r_sh:
            hip_y = ((l_sh.y + r_sh.y) / 2.0) + 0.30
            hip_x = (l_sh.x + r_sh.x) / 2.0
        else:
            return  # Need at least shoulders for full-body / torso gestures

        if not (l_sh and r_sh):
            return

        sh_x = (l_sh.x + r_sh.x) / 2.0
        current_ankle_y = None
        if l_ankle and r_ankle:
            current_ankle_y = (l_ankle.y + r_ankle.y) / 2.0
        elif l_ankle or r_ankle:
            current_ankle_y = (l_ankle.y if l_ankle else r_ankle.y)

        if nose and current_ankle_y is not None:
            self.baseline_body_height = max(0.20, abs(current_ankle_y - nose.y))

        # Initialize Frame 0
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

        lower_body_visible = (l_hip is not None and r_hip is not None and l_hip.visibility >= 0.5 and r_hip.visibility >= 0.5)
        if (not lower_body_visible) or (not self._lower_visible_prev):
            if self.is_airborne or self.is_ducking:
                self.reset_neutral_posture()
            self.baseline_hip_y = hip_y
            self.last_hip_y = hip_y
            self.baseline_ankle_y = None
            self.velocity_history.clear()
        self._lower_visible_prev = lower_body_visible

        if self.baseline_ankle_y is None and current_ankle_y is not None:
            self.baseline_ankle_y = current_ankle_y

        vertical_rise = self.baseline_hip_y - hip_y

        # Velocity with 3-frame rolling average smoothing
        raw_vel = (self.last_hip_y - hip_y) / dt if self.last_hip_y is not None else 0.0
        self.velocity_history.append(raw_vel)
        vertical_velocity = sum(self.velocity_history) / len(self.velocity_history)
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
        # 3. CHICKEN FLAP WINGS
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
                        self.bus.post(Event(EventType.CHICKEN_FLAP, source="action_detector"))
            self.last_elbow_y = avg_elbow_y

        if self.last_flap_time > 0 and (now - self.last_flap_time) > 1.2:
            self.flap_count = 0

        # -------------------------------------------------------------
        # 4. FART BLAST POSE
        # -------------------------------------------------------------
        if not self.is_airborne and current_ankle_y is not None:
            ankle_x = (l_ankle.x + r_ankle.x) / 2.0 if (l_ankle and r_ankle) else hip_x
            hip_side_shift = abs(hip_x - ankle_x)
            is_crouched = (hip_y - self.baseline_hip_y) > 0.04

            if hip_side_shift > 0.070 and is_crouched and (now - self.last_fart_time) > 1.5:
                self.last_fart_time = now
                self.debug_last_action = "FART_BLAST"
                self.bus.post(Event(EventType.FART_BLAST, source="action_detector"))

        # -------------------------------------------------------------
        # 5. FLAMINGO BALANCE
        # -------------------------------------------------------------
        if l_ankle and r_ankle and not self.is_airborne:
            ankle_split_y = abs(l_ankle.y - r_ankle.y)
            if ankle_split_y > 0.09:
                self.balance_timer += dt
                if self.balance_timer >= 1.0 and not self.balance_emitted:
                    self.balance_emitted = True
                    self.debug_last_action = "FLAMINGO_BALANCE"
                    self.bus.post(Event(EventType.FLAMINGO_BALANCE, source="action_detector"))
            else:
                self.balance_timer = 0.0
                self.balance_emitted = False

        # -------------------------------------------------------------
        # 6. TICKLE SWAT
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
                            self.bus.post(Event(EventType.TICKLE_SWAT, source="action_detector"))
                self.last_wrist_x = avg_wrist_x

        if self.last_swat_time > 0 and (now - self.last_swat_time) > 0.8:
            self.swat_oscillations = 0

        # -------------------------------------------------------------
        # 7. NERF GUN RECOIL
        # -------------------------------------------------------------
        if l_wrist and r_wrist:
            wrist_distance = abs(l_wrist.x - r_wrist.x)
            avg_wrist_y = (l_wrist.y + r_wrist.y) / 2.0
            is_aiming_posture = (wrist_distance < 0.14) and (avg_wrist_y < (hip_y - 0.12))

            if is_aiming_posture:
                if self.last_recoil_y is not None:
                    recoil_velocity = (self.last_recoil_y - avg_wrist_y) / dt
                    if recoil_velocity > self.recoil_min_velocity and (now - self.last_recoil_time) > 0.25:
                        self.last_recoil_time = now
                        self.debug_last_action = "SHOOT"
                        log.info("Action: NERF RECOIL SHOT fired!")
                        self.bus.post(Event(EventType.SHOOT, source="action_detector"))
                self.last_recoil_y = avg_wrist_y
            else:
                self.last_recoil_y = None

        # -------------------------------------------------------------
        # 8. STEERING WHEEL (EMA Smoothed + Hysteresis Deadband)
        # -------------------------------------------------------------
        if l_wrist and r_wrist:
            raw_wrist_dy = l_wrist.y - r_wrist.y
            wrist_dx = abs(l_wrist.x - r_wrist.x)
            self.smoothed_wrist_dy = (self.smoothed_wrist_dy * 0.65) + (raw_wrist_dy * 0.35)

            if wrist_dx > 0.12:
                new_steer = self.current_steer

                if self.current_steer == EventType.STEER_CENTER:
                    if self.smoothed_wrist_dy < -0.075:
                        new_steer = EventType.STEER_LEFT
                    elif self.smoothed_wrist_dy > 0.075:
                        new_steer = EventType.STEER_RIGHT
                elif self.current_steer == EventType.STEER_LEFT:
                    if self.smoothed_wrist_dy > -0.035:
                        new_steer = EventType.STEER_CENTER
                elif self.current_steer == EventType.STEER_RIGHT:
                    if self.smoothed_wrist_dy < 0.035:
                        new_steer = EventType.STEER_CENTER

                if new_steer != self.current_steer:
                    self.current_steer = new_steer
                    self.debug_last_action = new_steer if new_steer != EventType.STEER_CENTER else "STAND"
                    if new_steer == EventType.STEER_LEFT:
                        log.info("Action STEER: LEFT (Holding Left Arrow)")
                        self.bus.post(Event(EventType.STEER_LEFT, source="action_detector"))
                    elif new_steer == EventType.STEER_RIGHT:
                        log.info("Action STEER: RIGHT (Holding Right Arrow)")
                        self.bus.post(Event(EventType.STEER_RIGHT, source="action_detector"))
                    else:
                        log.info("Action STEER: CENTER (Released Steering Keys)")
                        self.bus.post(Event(EventType.STEER_CENTER, source="action_detector"))

        # -------------------------------------------------------------
        # 9. HANDS UP
        # -------------------------------------------------------------
        if l_wrist and r_wrist and nose:
            if l_wrist.y < nose.y and r_wrist.y < nose.y:
                self.debug_last_action = "HANDS_UP"
                self.bus.post(Event(EventType.HANDS_UP, source="action_detector"))

        # -------------------------------------------------------------
        # 10. JUMP and LAND Detection
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
        # 11. DUCK and STAND Detection
        # -------------------------------------------------------------
        duck_threshold = self.duck_threshold_ratio * self.baseline_body_height
        is_steering_active = (self.current_steer != EventType.STEER_CENTER)

        if not self.is_airborne and not is_jump_movement and not is_steering_active:
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
        # 12. LEAN LEFT / RIGHT / CENTER
        # -------------------------------------------------------------
        torso_tilt = sh_x - hip_x
        shoulder_width = max(0.05, abs(l_sh.x - r_sh.x))
        lean_enter = self.lean_enter_ratio * shoulder_width
        lean_exit = self.lean_exit_ratio * shoulder_width
        new_lean = self.current_lean

        if self.current_lean == EventType.LEAN_CENTER:
            if torso_tilt < -lean_enter:
                new_lean = EventType.LEAN_LEFT
            elif torso_tilt > lean_enter:
                new_lean = EventType.LEAN_RIGHT
        elif self.current_lean == EventType.LEAN_LEFT:
            if torso_tilt > -lean_exit:
                new_lean = EventType.LEAN_CENTER
        elif self.current_lean == EventType.LEAN_RIGHT:
            if torso_tilt < lean_exit:
                new_lean = EventType.LEAN_CENTER

        if new_lean != self.current_lean:
            self.current_lean = new_lean
            self.debug_last_action = new_lean
            log.info("Action LEAN changed: %s (tilt=%.3f) (UC 14.07).", new_lean, torso_tilt)
            self.bus.post(Event(new_lean, source="action_detector"))