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
    id: int
    name: str
    x: float
    y: float
    z: float
    visibility: float


@dataclass
class PoseResult:
    has_person: bool
    landmarks: Dict[str, PoseLandmark]
    raw_landmarks: List[PoseLandmark]
    confidence: float
    timestamp: float
    is_partial: bool = False
    is_held: bool = False
    child_scale_warning: bool = False
    low_light_warning: bool = False


class PoseTracker:
    """
    Extracts 33 body landmarks via MediaPipe.
    Pre-scales frames to 320x240 before inference to run under 15% CPU on Intel i5.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None,
                 backend: Optional[Callable[[np.ndarray], Any]] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.backend = backend

        self.is_available: bool = False
        self.detector = None

        self.empty_frame_count: int = 0
        self.player_lost_emitted: bool = False
        self.last_valid_pose: Optional[PoseResult] = None
        self.motion_blur_hold_sec: float = 0.150

        self._init_detector()

    def _init_detector(self) -> None:
        if self.backend is not None:
            self.is_available = True
            return

        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
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
        now = timestamp if timestamp is not None else time.time()

        if not self.is_available or image is None:
            return PoseResult(has_person=False, landmarks={}, raw_landmarks=[], confidence=0.0, timestamp=now)

        raw_results = None
        try:
            if self.backend is not None:
                raw_results = self.backend(image)
            elif self.detector is not None:
                h, w = image.shape[:2]
                if w > 320:
                    infer_img = cv2.resize(image, (320, 240))
                else:
                    infer_img = image

                rgb_frame = cv2.cvtColor(infer_img, cv2.COLOR_BGR2RGB)
                raw_results = self.detector.process(rgb_frame)
        except Exception as err:
            log.error("Exception in pose inference: %s", err)
            raw_results = None

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

            nose_vis = landmarks_dict.get("nose", PoseLandmark(0, "", 0, 0, 0, 0)).visibility
            left_ankle_vis = landmarks_dict.get("left_ankle", PoseLandmark(27, "", 0, 0, 0, 0)).visibility
            right_ankle_vis = landmarks_dict.get("right_ankle", PoseLandmark(28, "", 0, 0, 0, 0)).visibility
            is_partial = (nose_vis < 0.4) or (left_ankle_vis < 0.4 and right_ankle_vis < 0.4)

            nose_y = landmarks_dict.get("nose", PoseLandmark(0, "", 0, 0, 0, 0)).y
            left_ankle_y = landmarks_dict.get("left_ankle", PoseLandmark(27, "", 0, 1, 0, 0)).y
            body_span = abs(left_ankle_y - nose_y)
            child_scale_warning = (body_span < 0.25)
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

        if self.last_valid_pose is not None and (now - self.last_valid_pose.timestamp) <= self.motion_blur_hold_sec:
            return PoseResult(
                has_person=True,
                landmarks=self.last_valid_pose.landmarks,
                raw_landmarks=self.last_valid_pose.raw_landmarks,
                confidence=self.last_valid_pose.confidence,
                timestamp=self.last_valid_pose.timestamp,
                is_partial=self.last_valid_pose.is_partial,
                is_held=True,
                child_scale_warning=self.last_valid_pose.child_scale_warning,
                low_light_warning=self.last_valid_pose.low_light_warning
            )

        self.empty_frame_count += 1
        if self.empty_frame_count >= 5 and not self.player_lost_emitted:
            self.player_lost_emitted = True
            log.info("Player lost: nobody in view for 5 consecutive frames (UC 11.02).")
            self.bus.post(Event(EventType.PLAYER_LOST, source="pose_tracker"))

        return PoseResult(has_person=False, landmarks={}, raw_landmarks=[], confidence=0.0, timestamp=now)

    def close(self) -> None:
        if self.detector is not None:
            try:
                self.detector.close()
            except Exception:
                pass
            self.detector = None