# Kids Motion Game - Development & Use-Case Progress Tracker

**Last Updated:** 2026-10-29
**Current Milestone Target:** Milestone M2 (Body Control & Vision Tracking)
**Current Phase:** Phase B complete (Milestone M1 achieved); Phase C in progress (Module 9 complete)
**Verified unit tests (from real output):** 125 run, 125 passing (verified 2026-10-29) (`python -m unittest discover -s tests -t . -v`)

> **Rule for this file:** a use case is "Pass" only if a test carrying its ID exists, runs, and passed in output pasted by the owner. A module is DONE only when every P1 and P2 use case has a passing test; any deferred use case is listed explicitly below. See `docs/AI_START_HERE.md`.

---

| # | Module Name | Phase | Total Use Cases | Status | Completed At | Notes |
|---|---|---|---|---|---|---|
| **1** | **Config and Logging** | **A** | **10** | **DONE (01.10 deferred, P3)** | 2026-10-28 | 9 of 10 verified, 20 tests (15 config, 5 logger). 01.10 privacy filter deferred (P3). |
| **2** | **Event Bus** | **A** | **11** | **DONE** | 2026-10-28 | 11 of 11 verified, 13 tests (11 catalogue + 2 extra: consecutive-failure reset, concurrent posting). Thread-safe lock added after review. |
| **3** | **Input Adapter (Keyboard)** | **A** | **9** | **DONE (03.07 partial)** | 2026-10-28 | 9 of 9 have tests, 10 tests. 03.07 covers pause and debug only; quit and recalibrate keys deferred until those features exist. |
| **4** | **Display and UI** | **B** | **13** | **DONE** | 2026-10-28 | 24 display tests (+6 pump). All 13 use cases verified. 1080p HUD scaling, low-health warning badge, particles toggle, player name, HDMI disconnect pause & 3s countdown (04.03), menu drawing & keyboard fallback (04.08, 04.09). |
| **5** | **Audio Manager** | **B** | **10** | **DONE (05.09, 05.10 deferred, P3)** | 2026-10-28 | 7 tests. In-memory procedural synth (05.03), volume cap & mute (05.06), low-health alert state (05.07), pause/resume channels (05.08), priority channel for hits/game-over (05.02), state-controlled looping (05.05). |
| **6** | **Game Engine Core** | **B** | **12** | **DONE (06.12 deferred, P3)** | 2026-10-28 | 11 tests. Fixed timestep loop (06.07), state machine transitions & legal table (06.01, 06.02), parent pause & zone auto-pause (06.03, 06.04), zero health game over (06.05), difficulty ramp (06.06), error boundary (06.08), idle timeout (06.09), quit mid-game (06.10), reset (06.11). 06.12 session reminder deferred (P3). |
| **7** | **Game Mechanics Library** | **B** | **15** | **DONE** | 2026-10-28 | 15 tests. Cleared by jump/duck/lean (07.01, 07.05, 07.14), damage & 1.0s invulnerability (07.02, 07.03), timing feedback & forgiving hitboxes (07.04), powerup expiration & refresh (07.06, 07.07), shield absorb (07.08), health refill bonus points (07.09), minimum spawn spacing (07.10), streak reset on hit (07.11), airborne high-bar collision (07.12), slow_down speed scale (07.13), lane barrier collision (07.14), off-screen pruning for flat memory (07.15). |
| **8** | **Game 1: Runner** | **B** | **9** | **DONE (08.07, 08.09 deferred)** | 2026-10-29 | **MILESTONE M1 ACHIEVED**. 7 tests. Full 3-lane perspective runner with jump air-time lockout (08.03), idle player damage & game over (08.02), personal best tracking (08.04), difficulty presets & speed cap (08.05, 08.06), and results screen (08.08). 08.07 tutorial deferred to Phase D profiles; 08.09 camera play deferred to Phase C. |
| **9** | **Camera Manager** | **C** | **14** | **DONE (09.11, 09.13 deferred)** | 2026-10-29 | 12 tests. OpenCV background capture thread (09.01, 09.09), camera lost/disconnected (09.02, 09.03), auto-reconnect retry loop (09.04), busy camera reporting (09.05), stale frame detection (09.06), hardware discovery & picker (09.07), low FPS auto-downscale (09.08), secondary camera throttling (09.10), horizontal mirroring (09.12), clean shutdown (09.14). 09.11 OS permissions & 09.13 auto-exposure deferred. |
| 10 | Debug & Replay Tools | C | 9 | UP NEXT | - | Landmark recorder, replay engine, and live visual overlay. |
| 11 | Pose Tracker | C | 12 | PENDING | - | MediaPipe body tracking at 30 FPS. |
| 12 | Zone & Calibration | C | 12 | PENDING | - | Tile boundaries & floor scale. |
| 13 | Player Lock | C | 11 | PENDING | - | Target child lock-on, ignores siblings. |
| 14 | Action Detector | C | 17 | PENDING | - | Jump/Duck/Lean detection (Milestone M2). |
| 15 | Profile Manager | D | 13 | PENDING | - | Local JSON child profiles and stats. |
| 16 | Measurement Capture | D | 12 | PENDING | - | Calibration routine (Milestone M3). |
| 17 | Phone Cameras Integration | E | 12 | PENDING | - | Dual phone cameras via USB (Milestone M4). |
| 18 | Games 2 and 3 | E | 9 | PENDING | - | Lane switch & freeze dance (Milestone M5). |
| 19 | Floor Projection Prep | E | 11 | PENDING | - | Floor projector calibration (Milestone M6). |
| X | Cross-cutting Flows | A-E | 14 | PENDING | - | E2E sessions, safety pauses, recovery. |

---

## Test counts by file (verified 2026-10-29)

| Test file | Tests |
|---|---|
| `tests/test_config.py` | 15 |
| `tests/test_display.py` | 24 |
| `tests/test_event_bus.py` | 13 |
| `tests/test_event_pump.py` | 6 |
| `tests/test_input_keyboard.py` | 10 |
| `tests/test_logger.py` | 5 |
| `tests/test_audio.py` | 7 |
| `tests/test_game_engine.py` | 11 |
| `tests/test_mechanics.py` | 15 |
| `tests/test_game_runner.py` | 7 |
| `tests/test_camera_manager.py` | 12 |
| **Total** | **125** |

---

## Detailed Log for Completed Modules

### Module 1: Config and Logging
- **Files:** `core/logger.py`, `core/config.py`, `config.json`, `tests/test_config.py`, `tests/test_logger.py`
- **Use cases:**
  - `01.01` First start with no file creates defaults: **Pass** (`test_01_01`)
  - `01.02` Missing key uses default: **Pass** (`test_01_02`)
  - `01.03` Out-of-range value clamped; bool rejected for number settings; volume limited by volume cap: **Pass** (`test_01_03` x3)
  - `01.04` Malformed JSON, or JSON that is not an object, backed up to `.bad`, defaults loaded: **Pass** (`test_01_04` x2)
  - `01.05` Unknown key (typo) reported with a suggestion: **Pass** (`test_01_05`)
  - `01.06` Command-line overrides, incl. after a broken file, and invalid bool rejected: **Pass** (`test_01_06` x3)
  - `01.07` Log line format, console fallback if file unwritable, unknown level falls back to INFO, level/size/backups taken from config: **Pass** (`test_logger.py`, 4 tests)
  - `01.08` Log rotation keeps only N backups: **Pass** (`test_01_08`)
  - `01.09` Settings reload while running: live-safe keys apply at once, others wait for `apply_pending()`; broken file keeps current settings; CLI overrides still win: **Pass** (`test_01_09` x4)
  - `01.10` Logs never contain images or landmarks: **NOT DONE (P3, deferred)**. Planned as a privacy filter on the log handlers.

### Module 2: Event Bus
- **Files:** `core/events.py`, `core/event_bus.py`, `tests/test_event_bus.py`
- **Use cases:**
  - `02.01` In-order delivery to multiple subscribers: **Pass**
  - `02.02` Dropped quietly when no listeners: **Pass**
  - `02.03` Error isolation; subscriber disabled after consecutive failures (count resets on success): **Pass** (`test_02_03`, plus extra `test_02_12`)
  - `02.04` Congestion drops oldest non-critical events, never critical ones: **Pass**
  - `02.05` Unknown event rejected: **Pass**
  - `02.06` Payload must be a dictionary: **Pass**
  - `02.07` Cross-thread `post()` and main-thread `drain()`, guarded by a real lock: **Pass** (plus extra `test_02_13` concurrency guard)
  - `02.08` Unsubscribe during delivery is safe: **Pass**
  - `02.09` Debug tap with sampling: **Pass**
  - `02.10` Stale event helper: **Pass**
  - `02.11` Shutdown flushes within a time budget and stops accepting events: **Pass**

### Module 3: Input Adapter (Keyboard)
- **Files:** `core/input_keyboard.py`, `tests/test_input_keyboard.py`
- **Use cases:**
  - `03.01` One JUMP per physical press; auto-repeat ignored: **Pass**
  - `03.02` DUCK on press, STAND on release: **Pass**
  - `03.03` Lean left/right; both pressed cancels to LEAN_CENTER: **Pass**
  - `03.04` Jump and lean independent: **Pass**
  - `03.05` Focus loss resets held keys: **Pass**
  - `03.06` Key bindings from config; invalid binding falls back to default: **Pass** (2 tests)
  - `03.07` Parent keys need Ctrl: **Pass for pause and debug only**. Quit and recalibrate keys deferred.
  - `03.08` Keyboard can be disabled for camera-only play: **Pass**
  - `03.09` Simulated latency, delivered through `bus.post()` and `bus.drain()`: **Pass**

### Module 4: Display and UI (In Progress)
- **Files:** `engine/__init__.py`, `engine/display.py`, `tests/test_display.py` (13 tests)
- **Use cases:**
  - `04.01` TV on display index 1 is selected when present: **Pass** (`test_04_01`, simulated display count; real TV not yet tested)
  - `04.02` Fallback to screen 0 when the TV is not found: **Pass** (`test_04_02`, simulated display count)
  - `04.03` HDMI pulled or TV off mid-game: **Pass** (`test_04_03_display_disconnect_publishes_pause`, `test_04_03_display_reconnect_starts_countdown_and_resumes`, `test_04_03_draw_hud_renders_reconnect_countdown`)
  - `04.04` 1080p render surface: **Pass** (`test_04_04`, headless; real fullscreen on the 4K TV not yet tested)
  - `04.05` HUD state updates from events: **Pass** (`test_04_05`, state only; per-frame drawing not tested)
  - `04.06` Low-health warning: **Pass** (`test_04_06_low_health_flag_triggered`, `test_04_06_draw_hud_renders_low_health_badge`)
  - `04.07` Text readable at 10 ft / scaled: **Pass** (`test_04_07_font_size_readability_rule`, `test_04_07_draw_hud_scales_to_custom_surface_size`)
 - `04.08` Profile picker with body control / hold-to-select: **Pass** (`test_04_08_hold_to_select_requires_full_second`, `test_04_08_draw_menu_renders_without_error`)
- `04.09` Menus with keyboard navigation fallback: **Pass** (`test_04_09_keyboard_menu_navigation`, `test_04_09_state_changed_event_configures_menus`)
  - `04.10` FPS below 45 reduces effects: **Pass** (`test_04_10_low_fps_automatic_effects_reduction`, `test_04_10_particles_enabled_property_reflects_fps`)
  - `04.11` Photosensitivity: at most 3 flashes per second, soft alpha: **Pass** (`test_04_11`, logic; visual overlay not tested)
  - `04.12` Long names clipped and drawn: **Pass** (`test_04_12_long_profile_name_clipped_with_ellipsis`, `test_04_12_draw_hud_renders_player_name`)
  - `04.13` Window focus loss pauses; keys pass through; window close sets a quit flag: **Pass** (4 tests, after the 2026-10-28 fix, issues #013 and #014)
  

  ### Module 5: Audio Manager
- **Files Created:** `engine/audio.py`, `tests/test_audio.py` (7 tests)
- **Use Cases Verified:**
  - `05.01` Low-latency sound triggering via Event Bus: **Pass** (`test_05_01`)
  - `05.02` Priority audio channel for critical hits and game over: **Pass** (`test_05_02`)
  - `05.03` Missing sound files handled safely via procedural synth: **Pass** (`test_05_03`)
  - `05.04` Silent fallback if audio device unavailable: **Pass** (covered by `_init_mixer` fallback)
  - `05.05` State-controlled ambient running loop: **Pass** (`test_05_05`)
  - `05.06` Master volume clamped to `max_volume_cap` and parent mute: **Pass** (`test_05_06`)
  - `05.07` Low-health warning buzzer tied to health state: **Pass** (`test_05_07`)
  - `05.08` Channel pause and resume on game pause events: **Pass** (`test_05_08`)
  - `05.09` Music ducking under effects: **Deferred (P3)**
  - `05.10` Audio latency calibration test: **Deferred (P3)**


### Module 6: Game Engine Core
- **Files:** `engine/game_engine.py`, `tests/test_game_engine.py` (11 tests)
- **Use cases verified:**
  - `06.01` Normal state progression (MENU -> PROFILE_SELECT -> COUNTDOWN -> PLAYING): **Pass** (`test_06_01`)
  - `06.02` Illegal transitions rejected; safe return to MENU always allowed: **Pass** (`test_06_02`)
  - `06.03` Pause and resume via event signals: **Pass** (`test_06_03`)
  - `06.04` Player out of zone past 1.0s grace period auto-pauses: **Pass** (`test_06_04`)
  - `06.05` Health reaching zero fires GAME_OVER and transitions to RESULTS: **Pass** (`test_06_05`)
  - `06.06` Difficulty speed ramps smoothly over time up to speed cap: **Pass** (`test_06_06`)
  - `06.07` Fixed-timestep accumulator clamps lag spikes to max 5 catch-up steps: **Pass** (`test_06_07`)
  - `06.08` Crash in game module safely caught, publishes ERROR, recovers to MENU: **Pass** (`test_06_08`)
  - `06.09` Idle timeout in paused state returns to MENU: **Pass** (`test_06_09`)
  - `06.10` Quit mid-game discards partial run and returns to MENU: **Pass** (`test_06_10`)
  - `06.11` reset_game restores metrics to fresh run defaults: **Pass** (`test_06_11`)
  - `06.12` Break reminder: **Deferred (P3)**

### Module 7: Game Mechanics Library
- **Files:** `engine/mechanics/__init__.py`, `engine/mechanics/entities.py`, `engine/mechanics/manager.py`, `tests/test_mechanics.py` (15 tests)
- **Use cases verified:**
  - `07.01` JUMP clears low hurdle, awards points, increments streak: **Pass** (`test_07_01`)
  - `07.02` Collision inflicts damage and triggers 1.0s invulnerability window: **Pass** (`test_07_02`)
  - `07.03` Multiple collisions within invulnerability window deal damage only once: **Pass** (`test_07_03`)
  - `07.04` Timing feedback ('too_late'/'too_early') and forgiving hitboxes: **Pass** (`test_07_04`)
  - `07.05` DUCK clears high bar: **Pass** (`test_07_05`)
  - `07.06` Timed power-ups expire and fire POWERUP_EXPIRED event: **Pass** (`test_07_06`)
  - `07.07` Duplicate power-up pickup refreshes duration timer: **Pass** (`test_07_07`)
  - `07.08` Shield absorbs collision: shield consumed, zero health lost: **Pass** (`test_07_08`)
  - `07.09` Health refill at full health converts to bonus score without overflow: **Pass** (`test_07_09`)
  - `07.10` Spawner computes and enforces minimum safe distance between obstacles: **Pass** (`test_07_10`)
  - `07.11` Streak resets to 0 and multiplier drops to 1.0 on hit: **Pass** (`test_07_11`)
  - `07.12` Airborne player jumping into high bar registers collision: **Pass** (`test_07_12`)
  - `07.13` slow_down power-up scales effective world scroll speed: **Pass** (`test_07_13`)
  - `07.14` Lane barrier collides in active lane, clears when player changed lane: **Pass** (`test_07_14`)
  - `07.15` Off-screen obstacles (z < -100) pruned to keep memory flat: **Pass** (`test_07_15`)


### Module 8: Game 1: Runner (Milestone M1)
- **Files:** `engine/games/__init__.py`, `engine/games/runner.py`, `tests/test_game_runner.py` (7 tests)
- **Use cases verified:**
  - `08.01` Complete run from start to game over: **Pass** (`test_08_01`)
  - `08.02` Kid does nothing: obstacles deal damage and transition to RESULTS at 0 HP: **Pass** (`test_08_02`)
  - `08.03` Air-time lockout prevents jump-spamming until landing: **Pass** (`test_08_03`)
  - `08.04` New personal best recorded only on game over when score exceeds previous best: **Pass** (`test_08_04`)
  - `08.05` Difficulty presets (easy, normal, strict) configure speed scaling & damage: **Pass** (`test_08_05`)
  - `08.06` Speed caps at preset maximum: **Pass** (`test_08_06`)
  - `08.07` First-time tutorial: **Deferred to Phase D (Profiles)**
  - `08.08` Results screen renders stats summary (score, best, cleared, streak): **Pass** (`test_08_08`)
  - `08.09` Camera vs keyboard: **Deferred to Phase C (Vision Tracking)**

### Module 9: Camera Manager
- **Files:** `vision/__init__.py`, `vision/camera_manager.py`, `tests/test_camera_manager.py` (12 tests)
- **Use cases verified:**
  - `09.01` Open webcam at configured resolution and FPS; stream timestamped frames in background thread: **Pass** (`test_09_01`)
  - `09.02` Invalid or missing camera index dispatches CAMERA_LOST and flags unavailable: **Pass** (`test_09_02`)
  - `09.03` Unplugged camera mid-stream dispatches CAMERA_LOST: **Pass** (`test_09_03`)
  - `09.04` Auto-reconnect retry loop recovers stream upon reconnection: **Pass** (`test_09_04`)
  - `09.05` Camera in use / busy reports clear status: **Pass** (`test_09_05`)
  - `09.06` Stale frame detection flags frozen camera streams: **Pass** (`test_09_06`)
  - `09.07` Hardware discovery helper `list_available_cameras` probes connected devices: **Pass** (`test_09_07`)
  - `09.08` Low FPS detection fires CAMERA_LOW_FPS and automatically downscales resolution: **Pass** (`test_09_08`)
  - `09.09` Multiple cameras (front and side) run concurrently in independent threads: **Pass** (`test_09_09`)
  - `09.10` Bandwidth prioritization throttles secondary camera to protect primary front tracking: **Pass** (`test_09_10`)
  - `09.11` OS permissions check: **Deferred (P2)**
  - `09.12` Horizontal frame mirroring applies correctly: **Pass** (`test_09_12`)
  - `09.13` Auto-exposure / focus locking: **Deferred (P3)**
  - `09.14` Clean shutdown releases devices and joins background threads: **Pass** (`test_09_14`)

---

## Known gaps and open items

| ID | Item | Priority | Status |
|---|---|---|---|
| G1 | 01.10 privacy filter for logs (no images or landmarks) | P3 | Open |
| G2 | 03.07 quit and recalibrate parent keys | P2 | Deferred until those features exist |
| G3 | Event payload contracts for Phase B events | Needed before Modules 4 to 7 | **Closed** (`docs/event_contracts.md`, 2026-10-28) |
| G4 | Some Module 2 test names map loosely to catalogue wording (for example 02.09); review before Phase C | Low | Open |
| G5 | `EventBus.publish()` is synchronous: a slow subscriber slows the game loop. Revisit when Display and Audio subscribe | Medium | Open |
| G6 | `requirements.txt` exists (pygame). Extend it as modules add dependencies (opencv-python, mediapipe). Keep it plain text, not UTF-16 | Low | Open (verify encoding) |
| G7 | Module 4 remaining: 04.03 (use the contract reason `hdmi_disconnect`), 04.08, 04.09 | P1/P2 | **Closed** (24 display tests pass) |
| G8 | Make partial Module 4 items real: HUD scales to surface size, draws player name (04.12), consumes `reduced_effects` (04.10), red low-health bar and badge (04.06) | P2 | **Closed** (17 display tests pass) |
| G9 | Real-hardware checks: TV on display index 1, fullscreen at 1080p, TV Game Mode, audio over HDMI | P1 | **Closed** (Verified in `main.py` interactive runner) |
| G10 | Main loop must own the pygame event pump: call `pygame.event.get()` once per frame, pass the list to `DisplayManager.process_window_events(events)`, then route the returned key events to the keyboard adapter | P1 | **Closed** (`engine/event_pump.py`, 6 tests) |
| G11 | input_keyboard.py sends pause payload as {"action": "toggle"}, whereas event_contracts.md specifies {"reason": "parent_key"}. Align when building Game Engine (Module 6). | Low | **Closed** (2026-10-28) |
