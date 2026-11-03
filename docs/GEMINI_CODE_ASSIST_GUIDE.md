# Gemini Code Assist & Local IDE AI System Guide

> **Instructions for Google Gemini Code Assist inside VS Code:**
> Read this file FIRST when assisting in this workspace. It maps the active architecture, dependency graph, and critical technical constraints.

---

## 1. Project Purpose
A lightweight, high-performance **Universal Motion Game Controller**. It tracks human body movements via a single webcam or phone (Iriun) at 30 FPS, and injects real hardware keystrokes and mouse clicks (< 1ms latency) into Windows so kids and adults can play any Web game (Poki, CrazyGames), PC game, or emulator using full-body motion, toy Nerf guns, and toy steering wheels.

---

## 2. Architecture & Data Flow Graph

```mermaid
graph TD
    A[Camera: Iriun Phone or Laptop Webcam] -->|320x240 BGR Frames| B[vision/pose_tracker.py MediaPipe 33 Landmarks]
    B --> C[vision/player_lock.py 0.5s Stable Lock]
    C --> D[vision/zone_calibration.py Floor Bounding Box]
    D --> E[vision/action_detector.py Gestures & Actions]
    E -->|EventType Signals| F[core/event_bus.py Pub/Sub Broker]
    F --> G[engine/motion_bridge.py Hardware Keystrokes & Clicks]
    G -->|SendInput user32.dll| H[Active Game: Poki, CrazyGames, Temple Run, Steam]
    
    I[engine/tutorial_ui.py] -.->|Interactive Academy| E
    J[tools/calibrate_session.py] -.->|Physical Biomechanics Data| E


## 3. Critical Technical Nuances & Watchouts (DO NOT VIOLATE)

### Nuance 1: MediaPipe Version Pinning (mediapipe==0.10.14)
- Do NOT upgrade to MediaPipe 1.2+! In MediaPipe 1.2+, Google removed mp.solutions.pose.
- 0.10.14 has full native Python 3.12 support and all 33 body landmarks pre-bundled.

### Nuance 2: Single Camera Stream Rule (No USB Choke)
- Never open more than ONE camera stream in OpenCV simultaneously.
- Opening multiple capture streams over USB saturates the USB controller and drops FPS to 8.7.
- Always prioritize Iriun Webcam; if absent, fall back to Laptop Webcam (Index 0).

### Nuance 3: DirectShow on Windows (cv2.CAP_DSHOW)
- Windows Media Foundation (MSMF) hangs or drops virtual phone webcams like Iriun.
- Always open cameras on Windows using cv2.VideoCapture(index, cv2.CAP_DSHOW).

### Nuance 4: MediaPipe 320x240 Pre-Scaling (< 15% CPU)
- MediaPipe's neural net operates on a 256x256 matrix.
- Always downscale camera frames to 320x240 before passing to pose_tracker.process_frame().
- Passing full 720p/1080p frames wastes 80% of CPU resizing pixels in Python.

### Nuance 5: Cross-Thread EventBus Rule
- Background vision threads MUST use bus.post(event).
- Only the main game loop thread calls bus.publish() and bus.drain().

### Nuance 6: Windows Hardware DirectInput Injection
- engine/motion_bridge.py uses ctypes.windll.user32.keybd_event with KEYEVENTF_SCANCODE and mouse_event.
- This bypasses software hooks and sends real hardware signals directly into the active foreground window (< 1ms latency).

---

## 4. Key Module Index

| Module | File Path | Primary Responsibility |
|---|---|---|
| Motion Bridge | engine/motion_bridge.py | DirectInput scan codes (Up, Down, Left, Right, F, K, Z, Space, Click) |
| Tutorial Academy | engine/tutorial_ui.py | Procedural animated stickman lessons & [Tab] Master Cheat Sheet |
| Pose Tracker | vision/pose_tracker.py | MediaPipe 33 3D landmarks extraction |
| Action Detector | vision/action_detector.py | JUMP, DUCK, LEAN, NERF RECOIL, STEERING, PUNCH, KICK |
| Camera Supervisor | vision/camera_supervisor.py | Auto-priority: Iriun Phone -> Laptop Webcam -> Keyboard |
| Calibration Studio | tools/calibrate_session.py | 4-stage guided studio with live neon skeleton overlay |
| Arcade Launcher | main.py | Universal Controller suite & Web Arcade Hub |
| Desktop Launchers | Play_Kids_Game.bat / tools/build_exe.py | 1-click execution & PyInstaller .exe packaging |