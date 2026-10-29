import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger
from vision.pose_tracker import PoseResult
from identity.profile_manager import ProfileManager

log = get_logger("measurement_capture")

MIN_PLAUSIBLE_HEIGHT_CM = 80.0
MAX_PLAUSIBLE_HEIGHT_CM = 190.0


class MeasurementState:
    IDLE = "IDLE"
    WAITING_FOR_PLAYER = "WAITING_FOR_PLAYER"
    STABILIZING_POSE = "STABILIZING_POSE"
    WAITING_FOR_JUMP = "WAITING_FOR_JUMP"
    CONFIRMING = "CONFIRMING"
    MANUAL_FALLBACK = "MANUAL_FALLBACK"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


@dataclass
class MeasurementFeedback:
    """Feedback sent to display HUD so the child sees simple on-screen instructions."""
    state: str
    instruction: str
    progress_pct: float = 0.0
    is_stable: bool = False
    measured_height_cm: Optional[float] = None
    standing_baseline_y: Optional[float] = None
    jump_peak_rise: Optional[float] = None
    failed_attempts: int = 0
    error_message: Optional[str] = None


class MeasurementCapture:
    """
    Guides a child through standard calibration to extract and store their
    personal height, proportions, and jump baseline into their Profile (Module 16).
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 profile_manager: Optional[ProfileManager] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.profile_manager = profile_manager or ProfileManager(bus=self.bus, cfg=self.config)

        self.state: str = MeasurementState.IDLE
        self.target_profile_id: Optional[str] = None

        # Stability Tracking (UC 16.03)
        self.required_hold_duration_sec: float = 2.0
        self.hold_timer: float = 0.0
        self.last_hip_y: Optional[float] = None
        self.max_movement_jitter: float = 0.035
        self.sampled_heights: List[float] = []
        self.sampled_hip_y: List[float] = []
        self.sampled_shoulder_w: List[float] = []

        # Failure & Fallback Guard (UC 16.04)
        self.failed_attempts: int = 0
        self.max_failed_attempts: int = 3

        # Interruption Guard (UC 16.05)
        self.absence_timer: float = 0.0
        self.max_absence_sec: float = 3.0

        # Jump Test Tracking (UC 16.08)
        self.standing_baseline_y: Optional[float] = None
        self.jump_peak_rise: float = 0.0
        self.jump_detected: bool = False

        # Results
        self.final_measurements: Dict[str, Any] = {}

    def start_session(self, profile_id: str) -> bool:
        """Starts a guided measurement session for a player profile (UC 16.01)."""
        profile = self.profile_manager.get_profile(profile_id)
        if not profile:
            log.error("Cannot start measurement: profile '%s' not found.", profile_id)
            return False

        self.target_profile_id = profile_id
        self.state = MeasurementState.WAITING_FOR_PLAYER
        self.hold_timer = 0.0
        self.absence_timer = 0.0
        self.failed_attempts = 0
        self.sampled_heights.clear()
        self.sampled_hip_y.clear()
        self.sampled_shoulder_w.clear()
        self.standing_baseline_y = None
        self.jump_peak_rise = 0.0
        self.jump_detected = False
        self.final_measurements.clear()

        log.info("Measurement capture session started for profile '%s' (UC 16.01).", profile.name)
        self.bus.publish(Event(EventType.MEASUREMENT_STARTED, {
            "profile_id": profile_id,
            "profile_name": profile.name
        }))
        return True

    def process_pose(self, pose: PoseResult, dt: float) -> MeasurementFeedback:
        """
        Main per-frame guidance step (UC 16.01 - 16.08).
        Returns visual feedback with plain instructions for the TV screen.
        """
        if self.state == MeasurementState.IDLE:
            return MeasurementFeedback(state=self.state, instruction="Press Start to measure.")

        if self.state in (MeasurementState.CONFIRMING, MeasurementState.CANCELLED,
                          MeasurementState.FAILED, MeasurementState.MANUAL_FALLBACK):
            return MeasurementFeedback(
                state=self.state,
                instruction="Measurement complete." if self.state == MeasurementState.CONFIRMING
                else ("Parent: Enter child height manually." if self.state == MeasurementState.MANUAL_FALLBACK
                      else "Session ended."),
                progress_pct=1.0 if self.state == MeasurementState.CONFIRMING else 0.0,
                measured_height_cm=self.final_measurements.get("height_cm"),
                standing_baseline_y=self.final_measurements.get("standing_baseline_y"),
                jump_peak_rise=self.final_measurements.get("jump_peak_rise"),
                failed_attempts=self.failed_attempts
            )

        # 1. Absence / Interruption Check (UC 16.05)
        if not pose.has_person or not pose.landmarks:
            self.absence_timer += dt
            if self.absence_timer >= self.max_absence_sec:
                log.warning("Player left during measurement. Cancelling session (UC 16.05).")
                self.cancel_session(reason="player_left")
                return MeasurementFeedback(state=self.state, instruction="Player walked away. Session cancelled.")
            return MeasurementFeedback(state=self.state, instruction="Step onto the marked center tile!")

        self.absence_timer = 0.0
        lms = pose.landmarks
        nose = lms.get("nose")
        l_ankle = lms.get("left_ankle")
        r_ankle = lms.get("right_ankle")
        l_hip = lms.get("left_hip")
        r_hip = lms.get("right_hip")
        l_sh = lms.get("left_shoulder")
        r_sh = lms.get("right_shoulder")
        l_wrist = lms.get("left_wrist")
        r_wrist = lms.get("right_wrist")

        # 2. Framing & Full-Body Visibility Check (UC 16.02)
        if pose.is_partial or not (nose and (l_ankle or r_ankle) and l_hip and r_hip):
            self.hold_timer = 0.0
            self.state = MeasurementState.WAITING_FOR_PLAYER
            return MeasurementFeedback(
                state=self.state,
                instruction="Step back! We need to see your head and feet.",
                progress_pct=0.0
            )

        ankle_y = (l_ankle.y if l_ankle else r_ankle.y)
        body_height_norm = abs(ankle_y - nose.y)
        hip_y = (l_hip.y + r_hip.y) / 2.0
        sh_w = abs(l_sh.x - r_sh.x) if (l_sh and r_sh) else 0.20

        # 3. Wrong Pose Detection: Arms pinned to side (UC 16.07)
        if l_wrist and r_wrist:
            wrist_span = abs(l_wrist.x - r_wrist.x)
            if wrist_span < 0.16 and self.state != MeasurementState.WAITING_FOR_JUMP:
                self.hold_timer = 0.0
                return MeasurementFeedback(
                    state=self.state,
                    instruction="Spread your arms out wide like a superhero!",
                    progress_pct=0.0
                )

        # 4. State: Superhero Still Pose Capture (UC 16.01, 16.03, 16.04, 16.06)
        if self.state in (MeasurementState.WAITING_FOR_PLAYER, MeasurementState.STABILIZING_POSE):
            self.state = MeasurementState.STABILIZING_POSE

            # Check jitter/fidgeting
            if self.last_hip_y is not None and abs(hip_y - self.last_hip_y) > self.max_movement_jitter:
                self.hold_timer = 0.0
                self.sampled_heights.clear()
                self.sampled_hip_y.clear()
                self.sampled_shoulder_w.clear()
                self.last_hip_y = hip_y
                self.failed_attempts += 1

                # Check if 3 tries failed -> fallback to manual entry (UC 16.04)
                if self.failed_attempts >= self.max_failed_attempts:
                    log.warning("Child fidgeted past 3 attempts. Enabling manual entry fallback (UC 16.04).")
                    self.state = MeasurementState.MANUAL_FALLBACK
                    return MeasurementFeedback(
                        state=self.state,
                        instruction="Parent: Enter child height manually.",
                        failed_attempts=self.failed_attempts
                    )

                return MeasurementFeedback(
                    state=self.state,
                    instruction="Hold still like a superhero!",
                    progress_pct=0.0,
                    is_stable=False,
                    failed_attempts=self.failed_attempts
                )

            self.last_hip_y = hip_y
            self.hold_timer += dt
            self.sampled_heights.append(body_height_norm)
            self.sampled_hip_y.append(hip_y)
            self.sampled_shoulder_w.append(sh_w)

            progress = min(1.0, self.hold_timer / self.required_hold_duration_sec)

            if progress < 1.0:
                return MeasurementFeedback(
                    state=self.state,
                    instruction=f"Hold still! {int((1.0 - progress) * self.required_hold_duration_sec) + 1}...",
                    progress_pct=progress,
                    is_stable=True,
                    failed_attempts=self.failed_attempts
                )

            # Hold achieved! Compute median values
            self.sampled_heights.sort()
            self.sampled_hip_y.sort()
            self.sampled_shoulder_w.sort()
            med_idx = len(self.sampled_heights) // 2

            med_height_norm = self.sampled_heights[med_idx]
            med_hip_y = self.sampled_hip_y[med_idx]
            med_sh_w = self.sampled_shoulder_w[med_idx]
            height_cm = round(med_height_norm * 200.0, 1)

            # UC 16.06: Plausible Height Guard
            if height_cm < MIN_PLAUSIBLE_HEIGHT_CM or height_cm > MAX_PLAUSIBLE_HEIGHT_CM:
                log.warning("Implausible height measured (%.1f cm). Retrying (UC 16.06).", height_cm)
                self.hold_timer = 0.0
                self.sampled_heights.clear()
                self.sampled_hip_y.clear()
                self.sampled_shoulder_w.clear()
                self.failed_attempts += 1
                return MeasurementFeedback(
                    state=self.state,
                    instruction="Height check failed. Please stand straight on the center tile.",
                    error_message=f"Implausible height: {height_cm} cm",
                    failed_attempts=self.failed_attempts
                )

            # Save still baseline and transition to Jump Test (UC 16.08)
            self.standing_baseline_y = med_hip_y
            self.final_measurements = {
                "height_norm": round(med_height_norm, 3),
                "height_cm": height_cm,
                "standing_baseline_y": round(med_hip_y, 3),
                "shoulder_width_norm": round(med_sh_w, 3),
            }
            self.state = MeasurementState.WAITING_FOR_JUMP
            log.info("Superhero still pose captured. Ready for test jump (UC 16.08).")

            return MeasurementFeedback(
                state=self.state,
                instruction="Now do 1 big superhero jump!",
                progress_pct=0.0,
                measured_height_cm=height_cm,
                standing_baseline_y=med_hip_y
            )

        # 5. State: Test Jump Capture (UC 16.08)
        if self.state == MeasurementState.WAITING_FOR_JUMP:
            baseline = self.standing_baseline_y or hip_y
            vertical_rise = baseline - hip_y

            # Track peak vertical rise in air
            if vertical_rise > 0.07:
                self.jump_detected = True
                if vertical_rise > self.jump_peak_rise:
                    self.jump_peak_rise = vertical_rise

            # Landed back near ground after jumping
            if self.jump_detected and vertical_rise <= 0.035:
                peak_cm = round(self.jump_peak_rise * 200.0, 1)
                self.final_measurements["jump_peak_rise"] = round(self.jump_peak_rise, 3)
                self.final_measurements["jump_peak_cm"] = peak_cm
                # Set jump threshold to 60% of test jump apex
                self.final_measurements["jump_threshold"] = round(self.jump_peak_rise * 0.60, 3)
                self.final_measurements["measured_at"] = time.time()

                self.state = MeasurementState.CONFIRMING
                self.apply_to_profile()
                log.info("Test jump recorded: peak rise = %.1f cm (UC 16.08).", peak_cm)

                return MeasurementFeedback(
                    state=self.state,
                    instruction="Fantastic jump! Calibration complete!",
                    progress_pct=1.0,
                    measured_height_cm=self.final_measurements.get("height_cm"),
                    standing_baseline_y=self.standing_baseline_y,
                    jump_peak_rise=self.jump_peak_rise
                )

            return MeasurementFeedback(
                state=self.state,
                instruction="Now do 1 big superhero jump!",
                measured_height_cm=self.final_measurements.get("height_cm"),
                standing_baseline_y=self.standing_baseline_y
            )

        return MeasurementFeedback(state=self.state, instruction="Standing by...")

    def set_manual_height(self, height_cm: float, standing_baseline_y: float = 0.55) -> bool:
        """
        Parent manual height entry fallback (UC 16.04, 16.09).
        Allows saving safe measurements when camera capture fails.
        """
        if height_cm < MIN_PLAUSIBLE_HEIGHT_CM or height_cm > MAX_PLAUSIBLE_HEIGHT_CM:
            log.warning("Manual height entry rejected: %.1f cm out of range [%.0f, %.0f].",
                        height_cm, MIN_PLAUSIBLE_HEIGHT_CM, MAX_PLAUSIBLE_HEIGHT_CM)
            return False

        self.final_measurements = {
            "height_cm": height_cm,
            "height_norm": round(height_cm / 200.0, 3),
            "standing_baseline_y": round(standing_baseline_y, 3),
            "jump_peak_rise": 0.12,
            "jump_threshold": 0.07,
            "shoulder_width_norm": 0.20,
            "calibrated_manually": True,
            "measured_at": time.time()
        }

        self.state = MeasurementState.CONFIRMING
        return self.apply_to_profile()

    def cancel_session(self, reason: str = "user_cancelled") -> None:
        """Cancels measurement and saves nothing (UC 16.05)."""
        self.state = MeasurementState.CANCELLED
        self.final_measurements.clear()
        self.hold_timer = 0.0

        log.info("Measurement capture cancelled (%s). Nothing saved (UC 16.05).", reason)
        self.bus.publish(Event(EventType.MEASUREMENT_FAILED, {
            "profile_id": self.target_profile_id,
            "reason": reason
        }))

    def apply_to_profile(self) -> bool:
        """Atomically commits final measurements into player profile (UC 16.01, 16.09)."""
        if not self.target_profile_id or not self.final_measurements:
            return False

        success = self.profile_manager.update_measurements(self.target_profile_id, self.final_measurements)
        if success:
            log.info("Measurements successfully applied to profile '%s' (UC 16.01).", self.target_profile_id)
            self.bus.publish(Event(EventType.MEASUREMENT_DONE, {
                "profile_id": self.target_profile_id,
                "measurements": self.final_measurements
            }))
            return True
        return False