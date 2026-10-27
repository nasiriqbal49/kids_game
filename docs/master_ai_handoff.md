# Master AI Handoff & Project Context Snapshot

> **Instructions for Any Incoming AI (Claude, GPT, etc.):**  
> Read this document first. Do NOT re-write or re-explain existing completed modules. Continue directly from the **Next Immediate Step** indicated below.

---

## 1. Project Identity
- **Project Name:** Kids Motion Game
- **Target Platform:** Python 3.12 on Windows 11 (Lenovo ThinkPad i5 12th gen, 8 GB RAM)
- **Primary Outputs:** Xiaomi TV 43" (1080p pygame via HDMI in Game Mode) + HDMI audio
- **Inputs:** Keyboard (Phase A/B fallback), Phone/Webcam (Phase C/D/E via OpenCV + MediaPipe)
- **Repo:** Git tracking with clean modular architecture

## 2. Completed Architecture (DO NOT RECREATE)
- `core/logger.py`: Rotating file logger (`logs/kidsgame.log`) + stdout with clean formatting.
- `core/config.py`: Robust JSON config system with range validation, type enforcement, typo detection (`difflib`), `.bad` backup on corrupted JSON, and CLI override support.
- `config.json`: Project root settings.
- `tests/test_config.py`: Unit tests for Module 1 (100% passing).

## 3. Strict Coding Rules
1. **Pacing:** Small, testable portions. No bloated multi-module scripts in a single step.
2. **Event Bus Rule:** No module directly calls another module; all communication is via pub/sub events.
3. **Decoupled Loops:** Camera runs in separate thread (30 FPS max); game renders at locked 60 FPS.
4. **Git Discipline:** After every working module/test, guide the user to git add, commit with a descriptive message, and push.

## 4. Current Exact State & Next Immediate Step
- **Completed:**
  - Module 1 (Config & Logging): `core/logger.py`, `core/config.py`, `tests/test_config.py`.
  - Module 2 (Event Bus): `core/events.py`, `core/event_bus.py`, `tests/test_event_bus.py`.
- **Next Task:** Module 3 (Input Adapter - Keyboard) in `core/input_keyboard.py`.
- **Module 3 Requirements (Use Cases 03.01–03.09):**
  - Stand-in player that converts physical keystrokes into Event Bus events (`JUMP`, `DUCK`, `STAND`, `LEAN_LEFT`, `LEAN_RIGHT`, `LEAN_CENTER`).
  - Key-repeat suppression (UC 03.01: single physical press = 1 jump).
  - Hold-to-duck with `STAND` emitted on key release and focus loss (UC 03.02, 03.05).
  - Simultaneous opposite keys cancel out to `LEAN_CENTER` (UC 03.03).
  - Independent simultaneous jump + lean (UC 03.04).
  - Parent modifier hotkeys for pause, quit, recalibrate (UC 03.07).
  - Simulated latency delay toggle for early difficulty tuning (UC 03.09).