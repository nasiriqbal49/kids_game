import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import cv2
import pygame

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))

from core.logger import setup_logging, get_logger
from core.config import get_config
from core.event_bus import get_event_bus
from core.events import EventType
from vision.camera_supervisor import CameraSupervisor, ActiveSource
from vision.pose_tracker import PoseTracker
from vision.action_detector import ActionDetector

setup_logging()
cfg = get_config()
log = get_logger("calibrate_session")

SKELETON_CONNECTIONS = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle")
]

CALIBRATION_TESTS = [
    {"id": "JUMP", "name": "REAL JUMP TEST", "prompt": "Get ready to JUMP on zero!"},
    {"id": "DUCK", "name": "DUCK / CROUCH TEST", "prompt": "Get ready to CROUCH on zero!"},
    {"id": "LEAN_LEFT", "name": "LEAN LEFT TEST", "prompt": "Get ready to LEAN LEFT on zero!"},
    {"id": "LEAN_RIGHT", "name": "LEAN RIGHT TEST", "prompt": "Get ready to LEAN RIGHT on zero!"},
    {"id": "PUNCH", "name": "BOXING PUNCH TEST", "prompt": "Get ready to PUNCH on zero!"},
    {"id": "NERF_GUN", "name": "NERF RECOIL TEST", "prompt": "Aim toy gun and SHOOT with recoil on zero!"},
    {"id": "STEERING", "name": "STEERING WHEEL TEST", "prompt": "Hold wheel/plate and TURN on zero!"},
    {"id": "CHICKEN_FLAP", "name": "CHICKEN FLAP TEST", "prompt": "Flap your wings on zero!"},
    {"id": "FLAMINGO", "name": "1-LEG BALANCE TEST", "prompt": "Lift one foot and BALANCE on zero!"}
]


class TimePromptedCalibrator:
    """
    Time-Prompted Biomechanics Calibration Studio.
    Counts down '3... 2... 1... NOW!' and records the true physical motion window
    regardless of whether the detector triggered, resolving empty reports.
    """

    def __init__(self):
        self.metadata = {
            "player_type": "Child",
            "real_height_cm": 120.0,
            "distance_ft": 8.0,
            "camera_height_ft": 2.5,
            "camera_name": "Front Camera",
            "body_height_norm": 0.55,
            "res_w": 640,
            "res_h": 480,
            "fps": 30.0,
            "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.stage = "METADATA"
        self.test_idx = 0
        self.trial_attempt = 1
        self.max_attempts = 3

        self.countdown_timer = 3.0
        self.window_timer = 0.0
        self.window_active = False

        self.attempt_peak_rise = 0.0
        self.attempt_peak_vel = 0.0
        self.attempt_detected = False

        self.framing_hold_timer = 0.0
        self.session_data: Dict[str, Any] = {
            "metadata": self.metadata,
            "trials": []
        }

    def run(self):
        pygame.init()
        pygame.font.init()

        sw, sh = 1100, 720
        screen = pygame.display.set_mode((sw, sh))
        pygame.display.set_caption("Kids Motion Game - Countdown Biomechanics Calibrator")
        clock = pygame.time.Clock()

        bus = get_event_bus()
        camera_supervisor = CameraSupervisor(bus=bus, cfg=cfg)
        pose_tracker = PoseTracker(bus=bus, cfg=cfg)
        action_detector = ActionDetector(bus=bus, cfg=cfg)

        font_huge = pygame.font.Font(None, 56)
        font_big = pygame.font.Font(None, 40)
        font_mid = pygame.font.Font(None, 30)
        font_small = pygame.font.Font(None, 24)

        running = True
        input_field = 0

        while running:
            dt = clock.tick(30) / 1000.0
            now = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False

                elif event.type == pygame.KEYDOWN and self.stage == "METADATA":
                    if event.key == pygame.K_UP:
                        input_field = (input_field - 1) % 4
                    elif event.key == pygame.K_DOWN:
                        input_field = (input_field + 1) % 4
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        if input_field == 0:
                            self.metadata["player_type"] = "Adult" if self.metadata["player_type"] == "Child" else "Child"
                            self.metadata["real_height_cm"] = 175.0 if self.metadata["player_type"] == "Adult" else 120.0
                        elif input_field == 1:
                            delta = 5.0 if event.key == pygame.K_RIGHT else -5.0
                            self.metadata["real_height_cm"] = max(80.0, min(210.0, self.metadata["real_height_cm"] + delta))
                        elif input_field == 2:
                            delta = 0.5 if event.key == pygame.K_RIGHT else -0.5
                            self.metadata["distance_ft"] = max(4.0, min(16.0, self.metadata["distance_ft"] + delta))
                        elif input_field == 3:
                            delta = 0.5 if event.key == pygame.K_RIGHT else -0.5
                            self.metadata["camera_height_ft"] = max(1.0, min(6.0, self.metadata["camera_height_ft"] + delta))
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.stage = "FRAMING"

            cam_frame = camera_supervisor.get_frame()
            pose_result = None
            preview_surf = None
            detected_action = "STAND"

            if cam_frame is not None and cam_frame.image is not None:
                self.metadata["camera_name"] = camera_supervisor.active_source.value
                self.metadata["res_w"] = cam_frame.width
                self.metadata["res_h"] = cam_frame.height

                pose_result = pose_tracker.process_frame(cam_frame.image, cam_frame.timestamp)
                if pose_result and pose_result.has_person:
                    action_detector.process_pose(pose_result, cam_frame.timestamp)
                    detected_action = action_detector.debug_last_action
                    if action_detector.baseline_body_height:
                        self.metadata["body_height_norm"] = round(action_detector.baseline_body_height, 3)

                try:
                    small_bgr = cv2.resize(cam_frame.image, (320, 240))
                    if pose_result and pose_result.has_person and pose_result.landmarks:
                        lms = pose_result.landmarks
                        for ja, jb in SKELETON_CONNECTIONS:
                            pa = lms.get(ja)
                            pb = lms.get(jb)
                            if pa and pb and pa.visibility > 0.4 and pb.visibility > 0.4:
                                cv2.line(small_bgr, (int(pa.x * 320), int(pa.y * 240)), (int(pb.x * 320), int(pb.y * 240)), (200, 255, 0), 2)
                        for lm in pose_result.raw_landmarks:
                            if lm.visibility > 0.4:
                                cv2.circle(small_bgr, (int(lm.x * 320), int(lm.y * 240)), 4, (0, 255, 100), -1)

                    rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)
                    preview_surf = pygame.image.frombuffer(rgb.tobytes(), (320, 240), "RGB")
                except Exception:
                    pass

            bus.drain()

            if self.stage == "FRAMING":
                if pose_result and pose_result.has_person and not pose_result.is_partial:
                    self.framing_hold_timer += dt
                    if self.framing_hold_timer >= 2.0:
                        self.stage = "TRIALS"
                        self.test_idx = 0
                        self.trial_attempt = 1
                        self.countdown_timer = 3.0
                        self.window_active = False
                else:
                    self.framing_hold_timer = 0.0

            elif self.stage == "TRIALS":
                curr_t = CALIBRATION_TESTS[self.test_idx]

                if not self.window_active:
                    self.countdown_timer -= dt
                    if self.countdown_timer <= 0.0:
                        self.window_active = True
                        self.window_timer = 1.4
                        self.attempt_peak_rise = 0.0
                        self.attempt_peak_vel = 0.0
                        self.attempt_detected = False
                else:
                    self.window_timer -= dt
                    rise = abs(action_detector.debug_vertical_rise)
                    vel = abs(action_detector.debug_velocity)
                    if rise > self.attempt_peak_rise:
                        self.attempt_peak_rise = rise
                    if vel > self.attempt_peak_vel:
                        self.attempt_peak_vel = vel
                    if curr_t["id"] in detected_action or detected_action in curr_t["id"]:
                        self.attempt_detected = True

                    if self.window_timer <= 0.0:
                        self.session_data["trials"].append({
                            "gesture": curr_t["id"],
                            "attempt": self.trial_attempt,
                            "detected": self.attempt_detected,
                            "peak_rise": round(self.attempt_peak_rise, 4),
                            "peak_vel": round(self.attempt_peak_vel, 3),
                            "body_h": round(action_detector.baseline_body_height, 3)
                        })

                        self.trial_attempt += 1
                        self.window_active = False
                        self.countdown_timer = 2.0

                        if self.trial_attempt > self.max_attempts:
                            self.trial_attempt = 1
                            self.test_idx += 1
                            if self.test_idx >= len(CALIBRATION_TESTS):
                                self.stage = "DONE"
                                running = False

            screen.fill((14, 18, 30))
            title_surf = font_huge.render("BIOMECHANICS COUNTDOWN CALIBRATOR", True, (0, 255, 200))
            screen.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, 25))

            if self.stage == "METADATA":
                sub = font_mid.render("Step 1 of 3: Confirm Setup (Press Enter to Lock)", True, (241, 196, 15))
                screen.blit(sub, (sw // 2 - sub.get_width() // 2, 85))

                fields = [
                    (f"1. Player:        [ {self.metadata['player_type']} ]", "Left/Right to toggle Child vs Adult"),
                    (f"2. Real Height:   [ {self.metadata['real_height_cm']:.0f} cm ]", "Left/Right to adjust real height in cm"),
                    (f"3. Distance:      [ {self.metadata['distance_ft']:.1f} Feet ]", "Measured with tape to camera"),
                    (f"4. Camera Height: [ {self.metadata['camera_height_ft']:.1f} Feet ]", "Height from floor"),
                ]
                for i, (lab, hint) in enumerate(fields):
                    is_act = (i == input_field)
                    r = (sw // 2 - 360, 150 + i * 85, 720, 68)
                    pygame.draw.rect(screen, (22, 28, 44), r, border_radius=8)
                    pygame.draw.rect(screen, (241, 196, 15) if is_act else (50, 60, 80), r, 3 if is_act else 1, border_radius=8)
                    screen.blit(font_big.render(lab, True, (255, 255, 255)), (r[0] + 25, r[1] + 10))
                    screen.blit(font_small.render(hint, True, (130, 145, 165)), (r[0] + 25, r[1] + 42))

                screen.blit(font_mid.render("[Up/Down] Select  |  [Left/Right] Adjust  |  [Enter] Confirm & Next", True, (241, 196, 15)), (sw // 2 - 340, sh - 60))

            elif self.stage == "FRAMING":
                sub = font_mid.render("Step 2 of 3: Stand Head-to-Toe in Camera View", True, (241, 196, 15))
                screen.blit(sub, (sw // 2 - sub.get_width() // 2, 85))
                if preview_surf:
                    screen.blit(preview_surf, (sw // 2 - 160, 140))
                    pygame.draw.rect(screen, (52, 152, 219), (sw // 2 - 160, 140, 320, 240), 2)

                pct = min(1.0, self.framing_hold_timer / 2.0)
                bar = (sw // 2 - 250, 440, 500, 30)
                pygame.draw.rect(screen, (40, 50, 70), bar, border_radius=6)
                pygame.draw.rect(screen, (46, 204, 113), (bar[0], bar[1], int(500 * pct), 30), border_radius=6)
                pygame.draw.rect(screen, (255, 255, 255), bar, 2, border_radius=6)
                txt = f"LOCKING FRAMING: {int(pct * 100)}%" if pct > 0 else "PLEASE STEP FULLY INTO VIEW"
                screen.blit(font_mid.render(txt, True, (255, 255, 255)), (sw // 2 - 160, 485))

            elif self.stage == "TRIALS":
                curr_t = CALIBRATION_TESTS[self.test_idx]
                hdr = font_big.render(f"TEST {self.test_idx + 1}/{len(CALIBRATION_TESTS)}: {curr_t['name']} (Attempt {self.trial_attempt}/3)", True, (241, 196, 15))
                screen.blit(hdr, (sw // 2 - hdr.get_width() // 2, 85))

                if not self.window_active:
                    count_txt = f"{int(self.countdown_timer) + 1}..."
                    count_surf = font_huge.render(count_txt, True, (255, 220, 0))
                    screen.blit(count_surf, (sw // 2 - count_surf.get_width() // 2, 135))
                    screen.blit(font_mid.render(curr_t["prompt"], True, (200, 220, 240)), (sw // 2 - 180, 195))
                else:
                    now_surf = font_huge.render("PERFORM ACTION NOW!", True, (46, 204, 113))
                    screen.blit(now_surf, (sw // 2 - now_surf.get_width() // 2, 135))

                if preview_surf:
                    screen.blit(preview_surf, (sw // 2 - 160, 250))
                    pygame.draw.rect(screen, (52, 152, 219), (sw // 2 - 160, 250, 320, 240), 2)

                stat = f"Action: [{detected_action}] | Live Rise: {action_detector.debug_vertical_rise:+.3f} | Vel: {action_detector.debug_velocity:+.2f}"
                screen.blit(font_mid.render(stat, True, (0, 255, 200)), (sw // 2 - 250, 520))

            pygame.display.flip()

        camera_supervisor.close()
        pose_tracker.close()
        pygame.quit()
        self.save_reports()

    def save_reports(self):
        reports_dir = REPO_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        p_tag = self.metadata['player_type'].lower()
        d_tag = f"{self.metadata['distance_ft']:.0f}ft"
        ts_tag = time.strftime("%Y%m%d_%H%M%S")
        base_name = f"report_{p_tag}_{d_tag}_{ts_tag}"

        json_path = reports_dir / f"{base_name}.json"
        md_path = reports_dir / f"{base_name}.md"
        latest_root_md = REPO_DIR / "session_report.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.session_data, f, indent=2)

        body_h = max(0.10, self.session_data["metadata"].get("body_height_norm", 0.55))
        scale_cm = self.metadata["real_height_cm"] / body_h if self.session_data["trials"] else 200.0

        lines = [
            "# AI Biomechanics Calibration Report (Time-Prompted Analysis)",
            f"**File:** `{md_path.name}`",
            f"**Generated:** {self.metadata['recorded_at']}",
            f"**Player Type:** `{self.metadata['player_type']}` ({self.metadata['real_height_cm']:.0f} cm)",
            f"**Distance from TV/Camera:** `{self.metadata['distance_ft']:.1f} Feet`",
            f"**Camera Hardware:** `{self.metadata['camera_name']}` ({self.metadata['res_w']}x{self.metadata['res_h']})",
            f"**Computed Real Scale:** `1.0 norm = {scale_cm:.1f} cm in physical space`",
            "",
            "---",
            "",
            "## 1. Measured Physical Gesture Trials (3 Countdown Attempts Each)",
            "| Gesture Tested | Attempt # | Peak Norm Motion | Real Physical Measurement | Peak Velocity | Detection Result |",
            "|---|---|---|---|---|---|",
        ]

        for tr in self.session_data["trials"]:
            real_cm = tr["peak_rise"] * scale_cm
            status = "DETECTED" if tr["detected"] else "MISSED (Below Threshold)"
            lines.append(f"| `{tr['gesture']}` | #{tr['attempt']} | `{tr['peak_rise']:+.4f}` | **{real_cm:+.1f} cm** | `{tr['peak_vel']:+.2f}` | {status} |")

        prompt_block = (
            "```text\n"
            "Hi Gemini! Here is our time-prompted session report from our living-room trial.\n\n"
            f"CONTEXT:\n"
            f"- Player: {self.metadata['player_type']} ({self.metadata['real_height_cm']:.0f} cm tall)\n"
            f"- Distance from camera: {self.metadata['distance_ft']:.1f} ft\n"
            f"- Physical scale factor: 1.0 norm = {scale_cm:.1f} cm\n\n"
            "Based on the measured physical motion numbers and missed attempts in Section 1:\n"
            "1. Give me the mathematically optimal thresholds to achieve 100% detection for this setup.\n"
            "```"
        )

        lines.extend([
            "",
            "---",
            "",
            "## 2. Mathematical AI Tuning Prompt (Copy & Paste to Gemini)",
            prompt_block,
            ""
        ])

        md_content = "\n".join(lines)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        with open(latest_root_md, "w", encoding="utf-8") as f:
            f.write(md_content)

        print("\n==================================================")
        print(" CALIBRATION COMPLETE & ARCHIVED!")
        print(f" Permanent Archive : {md_path}")
        print(f" Latest Root Copy  : {latest_root_md}")
        print("==================================================")


if __name__ == "__main__":
    TimePromptedCalibrator().run()