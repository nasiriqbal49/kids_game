# Universal Motion Game Controller — Developer Guide

## 1. Project Purpose
A lightweight (< 2% CPU) motion controller for Windows. Tracks human body movements and toy props via webcam/phone at 30 FPS, and injects real hardware keystrokes and mouse clicks (< 1ms latency) via DirectInput scan codes so players can control any Web game (Poki, CrazyGames, WebGL) or PC game.

---

## 2. Architecture & Data Flow

Camera (Phone Iriun / Laptop Webcam)
  │ (320x240 BGR Frames)
  ▼
vision/pose_tracker.py (MediaPipe 0.10.14 - 33 body landmarks)
  │
  ▼
vision/player_lock.py (Locks nearest player in zone; 2.0s occlusion grace)
  │
  ▼
vision/zone_calibration.py (Floor boundaries & seated couch detection)
  │
  ▼
vision/action_detector.py (Detects Jump, Duck, Lean, Steer, Shoot, Punch, Kick)
  │ (EventType Signals)
  ▼
core/event_bus.py (Pub/Sub Event Broker)
  │
  ▼
engine/motion_bridge.py (DirectInput user32.dll ScanCode & Mouse Injection)
  │
  ▼
Active Foreground Window (Poki / CrazyGames / Steam / PC Games)

---

## 3. Gestures & Hardware Key Mappings

| Motion Gesture | Physical Movement | Hardware Signal Sent | Target Games |
|---|---|---|---|
| **Jump** | Vertical body leap | `Up Arrow` (0x48) | Subway Surfers, Temple Run 2 |
| **Crouch / Duck** | Squat down low | `Down Arrow` (0x50) | Subway Surfers, Temple Run 2 |
| **Lean Left / Right** | Upper body torso tilt | `Left` / `Right Arrow` | Subway Surfers, Slope 3D |
| **Steering Wheel** | Hold plate & rotate arms | `Left` / `Right Arrow` | Madalin Stunt Cars, Racing games |
| **Nerf Recoil** | Aim toy gun + upward jerk | `Left Click` + `Space` | Zombie Derby, Shooting games |
| **Boxing Punch** | Punch fist forward | `F key` / `Z key` | Iron Snout, Fighting games |
| **Karate Kick** | Kick leg forward | `K key` / `X key` | Fighting games |
| **Chicken Flap** | Flap elbows up/down | `W key` | Flight / gliding games |
| **Flamingo Balance**| Lift 1 foot for 1 second | `L key` | Balance challenges |

---

## 4. Critical Technical Constraints (DO NOT BREAK)

1. **MediaPipe Version Pinned:** `mediapipe==0.10.14`. Never upgrade to 1.2+ where `mp.solutions.pose` was removed.
2. **Single Camera Stream Rule:** Never open more than 1 OpenCV capture stream simultaneously to prevent USB controller bandwidth choke.
3. **DirectShow on Windows:** Always initialize with `cv2.VideoCapture(index, cv2.CAP_DSHOW)` to prevent camera driver hangs.
4. **Pre-scaling to 320x240:** Frames must be resized to 320x240 before passing to MediaPipe to keep CPU usage under 15% on ThinkPad i5.
5. **DirectInput Scan Codes:** Keystrokes are injected with `KEYEVENTF_SCANCODE` directly to the active foreground window.
6. **Cross-Thread Rule:** Background vision threads use `bus.post(event)`. Only the main thread calls `bus.publish()` and `bus.drain()`.