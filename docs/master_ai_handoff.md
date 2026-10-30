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
- **Inputs:** Keyboard (Phase A/B fallback), Phone/Webcam (Xiaomi Poco X6 Pro, Poco X3 NFC via Iriun/DroidCam), Laptop Webcam (backup)
- **Repo:** private GitHub repo `nasiriqbal49/kids_game`, branch `main`, local folder `D:\kids_game`.
- **Original PDF plan:** deleted from the repo by the owner. `docs/full_game_plan.md` and `docs/use_case_catalogue.md` are the only source of truth.

## 2. Completed Architecture (DO NOT RECREATE)
- `core/logger.py`: rotating file logger (`logs/kidsgame.log`) + console; `setup_logging()` and `configure_from(cfg)` apply level, size and backup count from config; handlers closed properly on reconfigure.
- `core/config.py`: JSON config with range/type validation (bool rejected for numbers), typo detection (`difflib`), `.bad` backup on malformed JSON or non-object JSON, CLI overrides (applied even after a broken file; strict bool parsing), volume vs `max_volume_cap` cross-check, `reload()` / `has_pending_changes()` / `apply_pending()` (live-safe keys apply immediately, the rest at next game start).
- `config.json`: project root settings.
- `core/events.py`: event catalogue and immutable `Event` dataclass with full standard, comedic gesture, and emotion action catalogue (`CHICKEN_FLAP`, `FART_BLAST`, `GIANT_STOMP`, `FLAMINGO_BALANCE`, `TICKLE_SWAT`, `GUEST_STAR`, `EMOTION_SMILE`, `EMOTION_ANGRY`, `EMOTION_SURPRISED`, `EMOTION_CRY`).
- `core/event_bus.py`: pub/sub with catalogue enforcement, payload validation, subscriber error isolation (disabled after consecutive failures; success resets the count), thread-safe `post()`/`drain()` guarded by a lock, critical-event protection under congestion, debug tap with sampling, stale-event helper, time-limited shutdown flush.
- `core/input_keyboard.py`: keyboard adapter (key-repeat suppression, duck hold, lean cancel, focus-loss reset, Ctrl for parent keys, config key bindings with fallback, camera-only mode switch, latency simulation through `bus.post()`, full keyboard shortcuts for all comedic actions).
- `engine/display.py`: Pygame 1080p rendering surface targeted to TV (display index 1) with laptop screen fallback, surface-scaled HUD, photosensitivity limits (<= 3 flashes/sec), low FPS automatic degradation, 10-ft readable fonts, menu hold-to-select, and HDMI disconnect auto-pause + 3s countdown.
- `engine/audio.py`: Pygame mixer with in-memory synthetic procedural waveform generator (sine/square) fallback, priority channels for hits/game-over, low-health warning buzzer, state-controlled running loop, and volume cap enforcement.
- `engine/event_pump.py`: Central owner of the pygame event pump (Gap G10); routes window events to display and key events to input adapter.
- `engine/game_engine.py`: Reusable game loop, state machine with legal transition enforcement, fixed-timestep accumulator with lag spike clamp, auto-pause on zone exit past 1.0s grace, speed ramping, error boundary, and idle timeout.
- `engine/mechanics/`: Reusable gameplay library (`entities.py`, `manager.py`) with obstacles (hurdles, high bars, lane barriers, smashable crates), power-ups (shield, slow_down, double_points, health_refill), collision verification, forgiving hitboxes, streak multipliers, and safe spawn spacing.
- `engine/games/runner.py`: Game 1: 3-lane pseudo-3D perspective road runner taking 86% of screen, player jump arc/duck, power-up collection, personal best tracking, difficulty presets, and navigable results screen.
- `engine/games/lane_switch.py`: Game 2: Coin Slalom & Lane Switch runner with lean boundary clamping, golden coin trails, and punch/kick crate smashing.
- `vision/camera_manager.py`: Multi-threaded OpenCV capture, horizontal mirroring, auto-reconnect retry loop, stale frame detection, hardware discovery, and low FPS downscaling.
- `vision/camera_supervisor.py`: Multi-camera supervisor managing the automatic fallback chain (`Phone -> Laptop Webcam -> Keyboard`), hot-plug re-promotion, and orientation locking (0°, 90°, 180°, 270°).
- `vision/camera_configurator.py`: 3-camera role configurator wizard with live video feeds in all cards, conflict resolution, validation, and config persistence.
- `vision/debug_tools.py`: On-screen diagnostic overlay (F3), JSON landmark session recorder with metadata, deterministic replayer, ground-truth jump accuracy scoring, and disk space protection.
- `vision/pose_tracker.py`: MediaPipe 33-point body tracking (pinned `mediapipe==0.10.14`), 150ms motion blur holdover, partial body check, child scale check, and fail-soft fallback.
- `vision/zone_calibration.py`: 2D floor bounding box, foot-tracking, jump vertical immunity, edge warning band, and JSON persistence.
- `vision/player_lock.py`: 0.5s stable presence lock, nearest-to-center multi-kid selection, bystander rejection, 2.0s occlusion grace, and body proportions tracking.
- `vision/action_detector.py`: JUMP, LAND, DUCK, STAND, LEAN_LEFT, LEAN_RIGHT, LEAN_CENTER, HANDS_UP, PUNCH, KICK, CHICKEN_FLAP, FART_BLAST, FLAMINGO_BALANCE, TICKLE_SWAT with pre-jump crouch spring detection, ankle-lift tracking, and dynamic drift adaptation.
- `identity/profile_manager.py`: Universal player profile database, atomic JSON save with rolling `.bak` backup, virtual coin economy wallet, per-game high scores, avatar customization, parent-confirmed deletion, and guest mode.
- `identity/measurement_capture.py`: Guided superhero pose calibration, 2.0s stability filter, test jump apex tracking, implausible height guard, and parent manual entry fallback.
- `tools/show_tree.py`: regenerates the directory tree doc.
- `tools/update_git_commits.py`: regenerates the commit log doc.
- **Verified Unit Tests:** 199 unit tests across 21 test files, all passing.

## 3. Strict Coding Rules
1. **Pacing:** small, testable portions. No bloated multi-module scripts in a single step.
2. **Event Bus Rule:** no module directly calls another module; all communication is via pub/sub events.
3. **Cross-thread rule:** background threads use `bus.post()`; only the main thread calls `bus.publish()` and `bus.drain()`.
4. **Decoupled loops:** camera runs in a separate thread (30 FPS max); game renders at locked 60 FPS.
5. **Honesty:** never claim "Pass" or a test count without real test output.
6. **Exact instructions:** when providing code changes, provide the complete replacement file or complete method to prevent indentation errors.
7. **Git discipline:** after every working module/test, guide the user to `git add .`, commit with a descriptive message naming module and use-case IDs, then `git push`.
8. **No Redaction:** Never shorten, summarise, or drop sections from reference documents.

## 4. Current Exact State & Next Immediate Step

### Current State (2026-10-30)
- **Phase A (Foundation) certified:** Modules 1, 2, 3 (43 tests).
- **Phase B (Playable Game with Keyboard) certified (Milestone M1):** Modules 4, 5, 6, 7, 8 (70 tests).
- **Phase C (Computer Vision & Tracking) certified (Milestone M2):** Modules 9, 10, 11, 12, 13, 14 (53 tests).
- **Phase D (Identity & Measurement) certified (Milestone M3):** Modules 15, 16 (19 tests).
- **Phase E (Multi-Camera & More Games):** 
  - Module 17 (Camera Supervisor & 3-Camera Configurator) certified (9 tests).
  - Module 18 (Game 2: Coin Slalom certified; Game 3 pending) (4 tests).
- **Live Playtest Verified:** Real child jump, duck, and lean tested live on 43" Xiaomi TV via USB phone camera. Multi-camera setup with 2 phones + laptop webcam verified.
- **Total Test Suite:** **199 verified passing unit tests** across 21 test files (`python -m unittest discover -s tests -t . -v`).

### Next Immediate Step
- Build **Game 3: Freeze Dance & Floor is Lava** (`engine/games/freeze_dance.py`) to complete Module 18 and officially achieve **Milestone M5**!
- Or build the **Pre-Game Virtual Coin Shop & Parent Workshop UI** in the Main Menu.

### Known open items
See "Known gaps and open items" in `docs/progress_tracker.md` (G1, G2, G4, G5 open).