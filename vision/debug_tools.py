import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
import pygame
from core.events import Event, EventType
from core.event_bus import EventBus, get_event_bus
from core.config import Config, get_config
from core.logger import get_logger

log = get_logger("debug_tools")


class DebugOverlay:
    """
    Diagnostic visual HUD for tracking sessions (UC 10.01).
    Toggled by DEBUG_TOGGLED (Ctrl + F3).
    When disabled, render() has zero overhead.
    """

    def __init__(self, bus: Optional[EventBus] = None, cfg: Optional[Config] = None):
        self.bus = bus or get_event_bus()
        self.config = cfg or get_config()
        self.enabled: bool = False
        self.recent_events: List[str] = []

        self._subscribe_events()

    def _subscribe_events(self) -> None:
        """Subscribes to toggle and action events."""
        self.bus.subscribe(EventType.DEBUG_TOGGLED, self._on_debug_toggled)

        # Track recent actions for visual diagnostic log
        for evt in (EventType.JUMP, EventType.DUCK, EventType.STAND,
                    EventType.LEAN_LEFT, EventType.LEAN_RIGHT, EventType.LEAN_CENTER,
                    EventType.OBSTACLE_HIT, EventType.OBSTACLE_CLEARED):
            self.bus.subscribe(evt, self._on_action_event)

    def _on_debug_toggled(self, event: Event) -> None:
        self.enabled = not self.enabled
        log.info("Debug overlay toggled: %s (UC 10.01).", self.enabled)

    def _on_action_event(self, event: Event) -> None:
        self.recent_events.append(f"{event.name} ({time.strftime('%H:%M:%S')})")
        if len(self.recent_events) > 5:
            self.recent_events.pop(0)

    def render(self, surface: pygame.Surface, fps: float = 0.0, camera_fps: float = 0.0,
               latency_ms: float = 0.0, landmarks: Optional[list] = None,
               zone_rect: Optional[Tuple[int, int, int, int]] = None) -> None:
        """
        Renders diagnostic overlay onto surface.
        Returns immediately with 0% cost if not enabled (UC 10.01).
        """
        if not self.enabled:
            return

        sw = surface.get_width()
        sh = surface.get_height()

        # 1. Diagnostic Box (Top-Right)
        box_w, box_h = 360, 220
        box_x = sw - box_w - 20
        box_y = 60

        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill((12, 18, 28, 220))
        surface.blit(panel, (box_x, box_y))
        pygame.draw.rect(surface, (52, 152, 219), (box_x, box_y, box_w, box_h), 2)

        font_header = pygame.font.Font(None, 26)
        font_stat = pygame.font.Font(None, 22)

        # Header
        hdr = font_header.render("[ DEBUG DIAGNOSTICS (F3) ]", True, (241, 196, 15))
        surface.blit(hdr, (box_x + 15, box_y + 12))

        # Metrics
        stats = [
            f"Game FPS: {fps:.1f} | Cam FPS: {camera_fps:.1f}",
            f"Latency: {latency_ms:.1f} ms",
            f"Landmarks Tracked: {len(landmarks) if landmarks else 0}",
            "Recent Events:",
        ]
        curr_y = box_y + 40
        for st in stats:
            surf_st = font_stat.render(st, True, (220, 230, 240))
            surface.blit(surf_st, (box_x + 15, curr_y))
            curr_y += 22

        # Recent events list
        for ev_str in self.recent_events[-3:]:
            ev_surf = font_stat.render(f" > {ev_str}", True, (46, 204, 113))
            surface.blit(ev_surf, (box_x + 25, curr_y))
            curr_y += 20

        # 2. Zone Outline Overlay (if provided)
        if zone_rect is not None:
            zx, zy, zw, zh = zone_rect
            pygame.draw.rect(surface, (46, 204, 113), (zx, zy, zw, zh), 3)

        # 3. Skeleton Dots (if landmarks provided)
        if landmarks:
            for pt in landmarks:
                if isinstance(pt, (tuple, list)) and len(pt) >= 2:
                    px, py = int(pt[0]), int(pt[1])
                    pygame.draw.circle(surface, (231, 76, 60), (px, py), 5)


class SessionRecorder:
    """
    Records landmark sessions to local JSON files with metadata header (UC 10.02).
    Privacy-first: stores numbers and coordinates only, never raw camera video.
    """

    def __init__(self, output_dir: str = "recordings", min_disk_mb: float = 50.0):
        self.output_dir = Path(output_dir)
        self.min_disk_mb = min_disk_mb
        self.is_recording: bool = False
        self.metadata: Dict[str, Any] = {}
        self.frames: List[Dict[str, Any]] = []
        self.ground_truth_events: List[Dict[str, Any]] = []

    def start_recording(self, camera_info: dict, profile_name: str = "Player 1") -> bool:
        """Initializes new recording session after checking disk space (UC 10.02, 10.06)."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check free disk space (UC 10.06)
        try:
            free_mb = shutil.disk_usage(self.output_dir).free / (1024 * 1024)
            if free_mb < self.min_disk_mb:
                log.warning("Disk space too low (%.1f MB < %.1f MB). Recording aborted (UC 10.06).",
                            free_mb, self.min_disk_mb)
                return False
        except Exception:
            pass

        self.metadata = {
            "version": "1.0",
            "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "profile_name": profile_name,
            "camera_info": camera_info,
        }
        self.frames = []
        self.ground_truth_events = []
        self.is_recording = True
        log.info("Session recording started for '%s' (UC 10.02).", profile_name)
        return True

    def record_frame(self, frame_index: int, timestamp: float, landmarks: list,
                     ground_truth: Optional[str] = None) -> bool:
        """Appends landmark frame to active recording."""
        if not self.is_recording:
            return False

        entry = {
            "frame_index": frame_index,
            "timestamp": timestamp,
            "landmarks": landmarks,
        }
        if ground_truth:
            entry["ground_truth"] = ground_truth
            self.ground_truth_events.append({"frame_index": frame_index, "event": ground_truth})

        self.frames.append(entry)
        return True

    def mark_ground_truth(self, event_name: str, frame_index: int) -> None:
        """Manual parent key press marking actual real jumps (UC 10.05)."""
        if self.is_recording:
            self.ground_truth_events.append({"frame_index": frame_index, "event": event_name})

    def stop_recording(self) -> Optional[Path]:
        """Saves session to JSON file atomically (UC 10.02)."""
        if not self.is_recording:
            return None

        self.is_recording = False
        filename = f"session_{int(time.time())}.json"
        target_path = self.output_dir / filename

        self.metadata["total_frames"] = len(self.frames)
        self.metadata["ground_truth_events"] = self.ground_truth_events

        payload = {
            "metadata": self.metadata,
            "frames": self.frames,
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        log.info("Session recording saved to %s with %d frames (UC 10.02).", target_path, len(self.frames))
        return target_path

    def delete_all_recordings(self) -> int:
        """Deletes all session recording files in parent mode (UC 10.09)."""
        count = 0
        if self.output_dir.exists():
            for p in self.output_dir.glob("session_*.json"):
                try:
                    p.unlink()
                    count += 1
                except OSError:
                    pass
        log.info("Deleted %d recording files (UC 10.09).", count)
        return count


class SessionReplayer:
    """
    Replays recorded landmark sessions deterministically (UC 10.03).
    Guards against corrupt recording files (UC 10.07).
    """

    def __init__(self):
        self.metadata: Dict[str, Any] = {}
        self.frames: List[Dict[str, Any]] = []
        self.current_frame_idx: int = 0

    def load_recording(self, file_path: Path) -> bool:
        """Loads and validates recording integrity (UC 10.03, 10.07)."""
        path = Path(file_path)
        if not path.exists():
            log.error("Recording file not found: %s", path)
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                log.error("Corrupt recording: top level must be object (UC 10.07).")
                return False

            # Header validation (UC 10.07)
            if "metadata" not in data or "frames" not in data:
                log.error("Corrupt recording: missing metadata or frames header (UC 10.07).")
                return False

            meta = data["metadata"]
            if not isinstance(meta, dict) or "version" not in meta or "camera_info" not in meta:
                log.error("Corrupt recording: invalid metadata structure (UC 10.07).")
                return False

            self.metadata = meta
            self.frames = data.get("frames", [])
            self.current_frame_idx = 0
            log.info("Loaded recording '%s' with %d frames (UC 10.03).", path.name, len(self.frames))
            return True
        except Exception as err:
            log.error("Failed loading recording file %s: %s (UC 10.07).", path, err)
            return False

    def step_frame(self) -> Optional[Dict[str, Any]]:
        """Returns the next frame deterministically (UC 10.03)."""
        if self.current_frame_idx < len(self.frames):
            frame = self.frames[self.current_frame_idx]
            self.current_frame_idx += 1
            return frame
        return None

    def reset(self) -> None:
        """Resets replay playback to frame 0."""
        self.current_frame_idx = 0

    def calculate_accuracy(self, detected_jump_frames: List[int], tolerance_frames: int = 3) -> Dict[str, Any]:
        """
        Calculates accuracy against parent ground-truth markers (UC 10.05).
        Returns detected count, missed count, and false jump count.
        """
        gt_jumps = [gt["frame_index"] for gt in self.metadata.get("ground_truth_events", [])
                    if gt.get("event") == EventType.JUMP]

        detected = 0
        matched_gt = set()

        for det_frame in detected_jump_frames:
            # Check if this detected frame matches a ground-truth jump within tolerance
            for gt_idx, gt_frame in enumerate(gt_jumps):
                if gt_idx not in matched_gt and abs(det_frame - gt_frame) <= tolerance_frames:
                    matched_gt.add(gt_idx)
                    detected += 1
                    break

        missed = len(gt_jumps) - len(matched_gt)
        false_positives = len(detected_jump_frames) - detected
        accuracy = (detected / len(gt_jumps) * 100.0) if gt_jumps else 100.0

        return {
            "ground_truth_total": len(gt_jumps),
            "detected_true_jumps": detected,
            "missed_jumps": missed,
            "false_jumps": false_positives,
            "accuracy_pct": round(accuracy, 1),
        }

    def compare_thresholds(self, run_detector_fn: Callable[[list, float], List[int]],
                           threshold_variants: List[float]) -> Dict[float, int]:
        """
        Runs recorded landmark frames against different detector thresholds
        and returns side-by-side event counts (UC 10.04).
        """
        results = {}
        for thresh in threshold_variants:
            detected_events = run_detector_fn(self.frames, thresh)
            results[thresh] = len(detected_events)
        return results