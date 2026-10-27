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
- **Completed:** Module 1 (Config & Logging), Module 2 Piece 1 (`events.py`), Module 2 Piece 2 (`event_bus.py`).
- **Next Task:** Unit tests for Module 2 in `tests/test_event_bus.py` verifying Use Cases `02.01` to `02.11`.
- **Module 2 Requirements:**
  - Fast, thread-safe publish-subscribe message bus.
  - Event contract: `timestamp`, `source`, `name`, `payload`.
  - Validate event names against the system Event Catalogue.
  - Thread-safe queue to pass events between camera thread and main thread.
  - Handle failing/slow listeners safely without blocking 60 FPS loop.