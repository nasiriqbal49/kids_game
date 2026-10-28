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

### Current State (2026-10-28)
- **Phase A (Foundation) is complete**, after an independent review that found and fixed these issues (details in `issues_and_resolutions.md`, #005 to #012): an unindented test that never ran, event bus thread-safety and failure counting, keyboard latency thread rule, ignored logging config, missing tests, config hardening, over-claimed status docs.
- Module 1: 9 of 10 use cases verified; **01.10 (privacy filter for logs) deferred, P3**.
- Module 2: 11 of 11 verified.
- Module 3: 9 of 9 have tests; 03.07 covers pause and debug only (quit and recalibrate deferred).
- Git: all work committed and pushed to `main` (last verified push after the 01.09 reload commit; confirm with `git status` and `git log --oneline -5`).

### Next Immediate Step
1. **Resume check:** ask the owner to run `git pull origin main`, `git status`, and `python -m unittest discover -s tests -t .` and confirm 43 tests pass.
2. **Gap G3 (small step, before Module 4):** define payload contracts for the events Modules 4 to 8 will use (for example HEALTH_CHANGED, SCORE_CHANGED, OBSTACLE_HIT, STREAK_CHANGED, SPEED_CHANGED, STATE_CHANGED, COUNTDOWN_TICK): which fields each carries, who publishes, who listens. Add as `docs/event_contracts.md` and keep `core/events.py` in sync. Ask the owner for approval before changing the event catalogue.
3. **Optional, small:** 01.10 privacy filter for logs (see tracker gap G1).
4. **Module 4: Display and UI** in `engine/display.py`:
   - Install pygame in the venv: `pip install pygame` and create `requirements.txt` with `pip freeze`.
   - Use cases 04.01 to 04.13 from `docs/use_case_catalogue.md`; read them all first.
   - Open a 1080p full-screen window on the TV (second display) with laptop-window fallback (04.02), HUD (04.05, 04.06), menus, auto-pause if HDMI disconnects (04.03).
   - First slice: a window that opens on the chosen display, runs at a steady 60 FPS, and shows a test HUD updated from events (the "Done when" in the plan). Use the keyboard adapter for input.

### Known open items
See "Known gaps and open items" in `docs/progress_tracker.md` (G1 to G6).
