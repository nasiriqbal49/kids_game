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

### Current State
- **Phase A: Foundation is 100% COMPLETE & CERTIFIED:**
  - **Module 1 (Config & Logging):** `core/logger.py`, `core/config.py`, `tests/test_config.py` (Passed 01.01–01.06).
  - **Module 2 (Event Bus):** `core/events.py`, `core/event_bus.py`, `tests/test_event_bus.py` (Passed 02.01–02.11).
  - **Module 3 (Input Adapter - Keyboard):** `core/input_keyboard.py`, `tests/test_input_keyboard.py` (Passed 03.01–03.09).
- **All 3 unit test suites pass (24 total unit tests).**
- **Git status:** Clean, all docs and code pushed to `main`.

### Next Immediate Step (Starting Phase B: Playable Game with Keyboard)
- **Next Task:** Module 4 (Display and UI) in `engine/display.py`.
- **Pre-requisite:** Install `pygame` in the virtual environment (`pip install pygame`).
- **Module 4 Requirements (Use Cases 04.01–04.13):**
  - Open a 1080p full-screen window on the TV (second display / extended desktop).
  - Fallback window on laptop if TV is not plugged in (UC 04.02).
  - Render HUD: score, health bar, speed, power-ups, streak (UC 04.05, 04.06).
  - Draw menus (main menu, pause, game over, results).
  - Fail-soft handling if HDMI is disconnected mid-game (UC 04.03).