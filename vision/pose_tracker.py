import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
import numpy as np
import cv2

from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("pose_tracker")

# Standard MediaPipe 33 Landmark Names
LANDMARK_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index"
]


@dataclass(frozen=True)
class PoseLandmark:
    """Normalized 3D body landmark."""
    id: int
    name: str
    x: float           # 0.0 to 1.0 (horizontal normalized coordinate)
    y: float           # 0.0 to 1.0 (vertical normalized coordinate)
    z: float           # Normalized depth relative to hips
    visibility: float  # 0.0 to 1.0 confidence that landmark is in frame


@dataclass
class PoseResult:
    """Detection outcome for a single video frame."""
    has_person: bool
    landmarks: Dict[str, PoseLandmark]
    raw_landmarks: List[PoseLandmark]
    confidence: float
    timestamp: float
    is_partial: bool = False              # Head or feet cut off (UC 11.03)
    is_held: bool = False                 # Held over during fast motion blur (UC 11.07)
    child_scale_warning: bool = False     # Small child in large frame (UC 11.08)
    low_light_warning: bool = False       # Low confidence due to dim lighting (UC 11.06)


class PoseTracker:
    """
    Turns camera frames into body skeleton landmarks at 20-30 FPS (Module 11).
    Fail-soft: degrades gracefully to keyboard mode if MediaPipe fails to load (UC 11.05).
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 backend: Optional[Callable[[np.ndarray], Any]] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.backend = backend

        self.is_available: bool = False
        self.detector = None

        # Tracking state
        self.empty_frame_count: int = 0
        self.player_lost_emitted: bool = False
        self.last_valid_pose: Optional[PoseResult] = None
        self.motion_blur_hold_sec: float = 0.150  # 150 ms motion blur holdover (UC 11.07)

        self._init_detector()

    def _init_detector(self) -> None:
        """Initializes MediaPipe Pose with fail-soft safety (UC 11.05)."""
        if self.backend is not None:
            self.is_available = True
            return

        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            # Model complexity 1 = full balance of speed and accuracy on ThinkPad i5
            self.detector = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.is_available = True
            log.info("MediaPipe Pose Tracker initialized successfully (UC 11.01).")
        except Exception as err:
            self.is_available = False
            log.warning("MediaPipe Pose unavailable (%s). Running in keyboard-only mode (UC 11.05).", err)

    def process_frame(self, image: np.ndarray, timestamp: Optional[float] = None) -> PoseResult:
        """Processes a single BGR camera frame into body landmarks."""
        now = timestamp if timestamp is not None else time.time()

        if not self.is_available or image is None:
            return PoseResult(has_person=False, landmarks={}, raw_landmarks=[],
                              confidence=0.0, timestamp=now)

        raw_results = None
        try:
            if self.backend is not None:
                raw_results = self.backend(image)
            elif self.detector is not None:
                # MediaPipe expects RGB
                rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                raw_results = self.detector.process(rgb_frame)
        except Exception as err:
            log.error("Exception in pose tracker inference: %s", err)
            raw_results = None

        # Check if landmarks were detected
        detected_landmarks = getattr(raw_results, "pose_landmarks", None)

        if detected_landmarks and getattr(detected_landmarks, "landmark", None):
            self.empty_frame_count = 0
            self.player_lost_emitted = False

            landmarks_dict = {}
            raw_list = []
            total_vis = 0.0

            for i, lm in enumerate(detected_landmarks.landmark):
                name = LANDMARK_NAMES[i] if i < len(LANDMARK_NAMES) else f"point_{i}"
                p_lm = PoseLandmark(
                    id=i,
                    name=name,
                    x=float(lm.x),
                    y=float(lm.y),
                    z=float(getattr(lm, "z", 0.0)),
                    visibility=float(getattr(lm, "visibility", 1.0))
                )
                landmarks_dict[name] = p_lm
                raw_list.append(p_lm)
                total_vis += p_lm.visibility

            avg_conf = total_vis / max(1, len(raw_list))

            # 1. Partial body framing check (UC 11.03)
            # Head (nose) or feet (ankles) cut off
            nose_vis = landmarks_dict.get("nose", PoseLandmark(0, "nose", 0, 0, 0, 0)).visibility
            left_ankle_vis = landmarks_dict.get("left_ankle", PoseLandmark(27, "", 0, 0, 0, 0)).visibility
            right_ankle_vis = landmarks_dict.get("right_ankle", PoseLandmark(28, "", 0, 0, 0, 0)).visibility
            is_partial = (nose_vis < 0.4) or (left_ankle_vis < 0.4 and right_ankle_vis < 0.4)

            # 2. Child scale check (UC 11.08)
            # Height in frame (vertical span between nose and ankles)
            nose_y = landmarks_dict.get("nose", PoseLandmark(0, "nose", 0, 0, 0, 0)).y
            left_ankle_y = landmarks_dict.get("left_ankle", PoseLandmark(27, "", 0, 1, 0, 0)).y
            body_span = abs(left_ankle_y - nose_y)
            child_scale_warning = (body_span < 0.25)  # Under 25% of frame height

            # 3. Low light check (UC 11.06)
            low_light_warning = (avg_conf < 0.40)

            result = PoseResult(
                has_person=True,
                landmarks=landmarks_dict,
                raw_landmarks=raw_list,
                confidence=round(avg_conf, 2),
                timestamp=now,
                is_partial=is_partial,
                is_held=False,
                child_scale_warning=child_scale_warning,
                low_light_warning=low_light_warning
            )
            self.last_valid_pose = result
            return result

        # Nobody detected in this frame
        # Check motion blur holdover (UC 11.07): hold last good pose for up to 150 ms
        if self.last_valid_pose is not None and (now - self.last_valid_pose.timestamp) <= self.motion_blur_hold_sec:
            held = PoseResult(
                has_person=True,
                landmarks=self.last_valid_pose.landmarks,
                raw_landmarks=self.last_valid_pose.raw_landmarks,
                confidence=self.last_valid_pose.confidence,
                timestamp=self.last_valid_pose.timestamp,
                is_partial=self.last_valid_pose.is_partial,
                is_held=True,  # Flagged as held
                child_scale_warning=self.last_valid_pose.child_scale_warning,
                low_light_warning=self.last_valid_pose.low_light_warning
            )
            return held

        # Person officially lost
        self.empty_frame_count += 1
        if self.empty_frame_count >= 5 and not self.player_lost_emitted:
            self.player_lost_emitted = True
            log.info("Player lost: nobody in view for 5 consecutive frames (UC 11.02).")
            self.bus.post(Event(EventType.PLAYER_LOST, source="pose_tracker"))

        return PoseResult(has_person=False, landmarks={}, raw_landmarks=[],
                          confidence=0.0, timestamp=now)

    def close(self) -> None:
        """Releases detector resources."""
        if self.detector is not None:
            try:
                self.detector.close()
            except Exception:
                pass
            self.detector = None