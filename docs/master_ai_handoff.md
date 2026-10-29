# Master AI Handoff & Project Context Snapshot

> **Instructions for Any Incoming AI (Claude, Gemini, GPT, etc.):**
> 1. Read `docs/AI_START_HERE.md` FIRST and follow its reading order and rules.
> 2. Do NOT re-write or re-explain completed modules.
> 3. Do NOT shorten, summarise, reword or redact any document or use case.
> 4. Continue from the **Next Immediate Step** below, after verifying the state (see AI_START_HERE section 6).

---

## 1. Project Identity
- **Project Name:** Kids Motion Game
- **Target Platform:** Python 3.12 (virtual environment `.venv`) on Windows 11 (Lenovo ThinkPad i5 12th gen, 8 GB RAM), PowerShell, VS Code
- **Primary Outputs:** Xiaomi TV 43" (1080p pygame via HDMI in Game Mode) + HDMI audio
- **Inputs:** Keyboard (Phase A/B fallback), Phone/Webcam (Phase C/D/E via OpenCV + MediaPipe)
- **Repo:** private GitHub repo `nasiriqbal49/kids_game`, branch `main`, local folder `D:\kids_game`. The AI cannot see the private repo; ask the owner to paste files or run the commands in AI_START_HERE section 6.
- **Original PDF plan:** deleted from the repo by the owner. `docs/full_game_plan.md` and `docs/use_case_catalogue.md` are the only source of truth.

## 2. Completed Architecture (DO NOT RECREATE)
- `core/logger.py`: rotating file logger (`logs/kidsgame.log`) + console; `setup_logging()` and `configure_from(cfg)` apply level, size and backup count from config; handlers closed properly on reconfigure.
- `core/config.py`: JSON config with range/type validation (bool rejected for numbers), typo detection (`difflib`), `.bad` backup on malformed JSON or non-object JSON, CLI overrides (applied even after a broken file; strict bool parsing), volume vs `max_volume_cap` cross-check, `reload()` / `has_pending_changes()` / `apply_pending()` (live-safe keys apply immediately, the rest at next game start).
- `config.json`: project root settings.
- `core/events.py`: event catalogue and immutable `Event` dataclass.
- `core/event_bus.py`: pub/sub with catalogue enforcement, payload validation, subscriber error isolation (disabled after consecutive failures; success resets the count), thread-safe `post()`/`drain()` guarded by a lock, critical-event protection under congestion, debug tap with sampling, stale-event helper, time-limited shutdown flush.
- `core/input_keyboard.py`: keyboard adapter (key-repeat suppression, duck hold, lean cancel, focus-loss reset, Ctrl for parent keys, config key bindings with fallback, camera-only mode switch, latency simulation through `bus.post()`).
- `tools/show_tree.py`: regenerates the directory tree doc.
- Tests: `tests/test_config.py` (15), `tests/test_event_bus.py` (13), `tests/test_input_keyboard.py` (10), `tests/test_logger.py` (5). **43 tests, all passing** (verified from real output on 2026-10-28).

## 3. Strict Coding Rules
1. **Pacing:** small, testable portions. No bloated multi-module scripts in a single step.
2. **Event Bus Rule:** no module directly calls another module; all communication is via pub/sub events.
3. **Cross-thread rule:** background threads use `bus.post()`; only the main thread calls `bus.publish()` and `bus.drain()`.
4. **Decoupled loops:** camera runs in a separate thread (30 FPS max); game renders at locked 60 FPS.
5. **Honesty:** never claim "Pass" or a test count without real test output.
6. **Git discipline:** after every working module/test, guide the user to `git add .`, commit with a descriptive message naming module and use-case IDs, then `git push`.
7. Full rules are in `docs/AI_START_HERE.md`.

## 4. Current Exact State & Next Immediate Step

### Current State (2026-10-29)
- **Phase A (Foundation) certified:** Modules 1, 2, 3 (43 tests).
- **Phase B (Playable Game with Keyboard) COMPLETE (Milestone M1 Achieved):** Modules 4, 5, 6, 7, 8 (70 tests).
- **Phase C (Computer Vision & Tracking) in progress:**
  - **Module 9 (Camera Manager) COMPLETE:** 12 tests (`tests/test_camera_manager.py`). Background acquisition thread (09.01, 09.09), camera disconnect & reconnect retry loop (09.02, 09.03, 09.04), busy camera reporting (09.05), stale frame detection (09.06), hardware device discovery & picker (09.07), low FPS detection & auto-downscale (09.08), secondary camera throttling under bandwidth pressure (09.10), horizontal mirroring (09.12), clean shutdown (09.14). 09.11 OS permissions & 09.13 auto-exposure deferred.
- **Total Test Suite:** **125 verified passing unit tests** across 11 test files (`python -m unittest discover -s tests -t . -v`).
- **Dependencies:** `pygame==2.6.1`, `opencv-python>=4.8.0`, `numpy>=2.0.0`.

### Next Immediate Step
- **Begin Module 10: Debug and Replay Tools** in `vision/debug_tools.py`:
  - Visual overlay view showing camera frame, skeleton, zone outline, and live signals (10.01).
  - Landmark session recording to local JSON without saving raw video (privacy-first, 10.02).
  - Replay system feeding recorded sessions back through tracking chain deterministically (10.03).
  - Satisfy use cases 10.01 to 10.07.

### Known open items
See "Known gaps and open items" in `docs/progress_tracker.md` (G1, G2, G4, G5, G6 open).

