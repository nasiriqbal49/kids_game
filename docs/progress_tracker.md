# Kids Motion Game - Development & Use-Case Progress Tracker

**Last Updated:** 2026-10-28
**Current Milestone Target:** Milestone M1 (Keyboard Runner)
**Current Phase:** Phase A (Foundation) complete; Phase B (Playable game with keyboard) in progress (Module 4)
**Verified unit tests (from real output):** 80 run, 80 passing (verified 2026-10-28) (`python -m unittest discover -s tests -t .`)

> **Rule for this file:** a use case is "Pass" only if a test carrying its ID exists, runs, and passed in output pasted by the owner. A module is DONE only when every P1 and P2 use case has a passing test; any deferred use case is listed explicitly below. See `docs/AI_START_HERE.md`.

---

| # | Module Name | Phase | Total Use Cases | Status | Completed At | Notes |
|---|---|---|---|---|---|---|
| **1** | **Config and Logging** | **A** | **10** | **DONE (01.10 deferred, P3)** | 2026-10-28 | 9 of 10 verified, 20 tests (15 config, 5 logger). 01.10 privacy filter deferred (P3). |
| **2** | **Event Bus** | **A** | **11** | **DONE** | 2026-10-28 | 11 of 11 verified, 13 tests (11 catalogue + 2 extra: consecutive-failure reset, concurrent posting). Thread-safe lock added after review. |
| **3** | **Input Adapter (Keyboard)** | **A** | **9** | **DONE (03.07 partial)** | 2026-10-28 | 9 of 9 have tests, 10 tests. 03.07 covers pause and debug only; quit and recalibrate keys deferred until those features exist. |
| **4** | **Display and UI** | **B** | **13** | **DONE** | 2026-10-28 | 24 display tests (+6 pump). All 13 use cases verified. 1080p HUD scaling, low-health warning badge, particles toggle, player name, HDMI disconnect pause & 3s countdown (04.03), menu drawing & keyboard fallback (04.08, 04.09). |
| **5** | **Audio Manager** | **B** | **10** | **DONE (05.09, 05.10 deferred, P3)** | 2026-10-28 | 7 tests. In-memory procedural synth (05.03), volume cap & mute (05.06), low-health alert state (05.07), pause/resume channels (05.08), priority channel for hits/game-over (05.02), state-controlled looping (05.05). |
| **6** | **Game Engine Core** | **B** | **12** | **UP NEXT** | — | Fixed timestep loop, state machine, difficulty curve, timer management. |
| 7 | Game Mechanics Library | B | 15 | PENDING | - | Spawning, hitboxes, power-ups. |
| 8 | Game 1: Runner | B | 9 | PENDING | - | Playable keyboard game (Milestone M1). |
| 9 | Camera Manager | C | 14 | PENDING | - | OpenCV frame acquisition thread. |
| 10 | Debug & Replay Tools | C | 9 | PENDING | - | Landmark recorder and visual overlay. |
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

## Test counts by file (verified 2026-10-28)

| Test file | Tests |
|---|---|
| `tests/test_config.py` | 15 |
| `tests/test_display.py` | 24 |
| `tests/test_event_bus.py` | 13 |
| `tests/test_event_pump.py` | 6 |
| `tests/test_input_keyboard.py` | 10 |
| `tests/test_logger.py` | 5 |
| `tests/test_audio.py` | 7 |
| **Total** | **80** |

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
| G11 | `input_keyboard.py` sends pause payload as `{"action": "toggle"}`, whereas `event_contracts.md` specifies `{"reason": "parent_key"}`. Align when building Game Engine (Module 6). | Low | Open |
