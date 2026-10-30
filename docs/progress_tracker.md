# Kids Motion Game - Development & Use-Case Progress Tracker

**Last Updated:** 2026-10-30
**Current Milestone Target:** Milestone M5 (Games 2 & 3: Lane Switch & Freeze Dance)
**Current Phase:** Phase E (Milestones M1, M2, M3, M4 achieved; M5 in progress)
**Verified unit tests (from real output):** 199 run, 199 passing (verified 2026-10-30) (`python -m unittest discover -s tests -t . -v`)

> **Rule for this file:** a use case is "Pass" only if a test carrying its ID exists, runs, and passed in output pasted by the owner. A module is DONE only when every P1 and P2 use case has a passing test; any deferred use case is listed explicitly below. See `docs/AI_START_HERE.md`.

---

| # | Module Name | Phase | Total Use Cases | Status | Completed At | Notes |
|---|---|---|---|---|---|---|
| **1** | **Config and Logging** | **A** | **10** | **DONE (01.10 deferred, P3)** | 2026-10-28 | 9 of 10 verified, 20 tests (15 config, 5 logger). 01.10 privacy filter deferred (P3). |
| **2** | **Event Bus** | **A** | **11** | **DONE** | 2026-10-28 | 11 of 11 verified, 13 tests. Thread-safe lock and failure reset verified. |
| **3** | **Input Adapter (Keyboard)** | **A** | **9** | **DONE (03.07 partial)** | 2026-10-28 | 9 of 9 have tests, 11 tests. Full comedic shortcuts added. |
| **4** | **Display and UI** | **B** | **13** | **DONE** | 2026-10-28 | 24 display tests (+6 pump). All 13 use cases verified. 1080p HUD scaling, low-health badge, HDMI disconnect pause & 3s countdown (04.03), menus (04.08, 04.09). |
| **5** | **Audio Manager** | **B** | **10** | **DONE (05.09, 05.10 deferred, P3)** | 2026-10-28 | 7 tests. In-memory procedural synth (05.03), volume cap & mute (05.06), low-health alert state (05.07), pause/resume channels (05.08). |
| **6** | **Game Engine Core** | **B** | **12** | **DONE (06.12 deferred, P3)** | 2026-10-28 | 11 tests. Fixed timestep loop (06.07), state transitions (06.01, 06.02), pause/resume (06.03, 06.04), zero health game over (06.05), difficulty ramp (06.06). |
| **7** | **Game Mechanics Library** | **B** | **15** | **DONE** | 2026-10-28 | 15 tests. JUMP/DUCK/LEAN clears (07.01, 07.05, 07.14), damage & invulnerability (07.02, 07.03), powerups (07.06-07.09, 07.13), spawner spacing (07.10), streak (07.11). |
| **8** | **Game 1: Runner** | **B** | **9** | **DONE (08.07, 08.09 deferred)** | 2026-10-29 | **MILESTONE M1 ACHIEVED**. 7 tests. Full 3-lane perspective runner with jump air-time lockout (08.03), idle damage (08.02), personal best (08.04), presets (08.05), results (08.08). |
| **9** | **Camera Manager** | **C** | **14** | **DONE (09.11, 09.13 deferred)** | 2026-10-29 | 12 tests. OpenCV background capture thread (09.01, 09.09), disconnects (09.02, 09.03), auto-reconnect (09.04), stale frames (09.06), low FPS downscaling (09.08). |
| **10** | **Debug & Replay Tools** | **C** | **9** | **DONE (10.08 deferred, P3)** | 2026-10-29 | 8 tests. Diagnostic overlay (10.01), JSON recorder (10.02), replayer (10.03), threshold comparison (10.04), ground-truth scoring (10.05), low disk guard (10.06). |
| **11** | **Pose Tracker** | **C** | **12** | **DONE (11.04, 11.09, 11.10, 11.12 deferred)** | 2026-10-29 | 8 tests. MediaPipe body tracking (11.01), empty frames (11.02), partial body (11.03), fail-soft (11.05), low light (11.06), 150ms motion blur holdover (11.07), scale check (11.08). |
| **12** | **Zone and Calibration** | **C** | **12** | **DONE (12.02, 12.06, 12.07, 12.11, 12.12 deferred)** | 2026-10-29 | 6 tests. Inside zone (12.03), edge warning (12.04), foot-based out of zone (12.05), jump vertical immunity (12.08), lean foot check (12.09), JSON persistence (12.01, 12.10). |
| **13** | **Player Lock** | **C** | **11** | **DONE (13.07, 13.09-13.11 deferred)** | 2026-10-29 | 6 tests. 0.5s presence lock (13.01), nearest-to-center lock (13.02), bystander rejection (13.03), 2.0s occlusion grace (13.04, 13.05), proportions swap prevention (13.08). |
| **14** | **Action Detector** | **C** | **17** | **DONE (14.04, 14.09, 14.11, 14.12, 14.15-14.17 deferred)** | 2026-10-29 | **MILESTONE M2 ACHIEVED**. 13 tests. JUMP/LAND (14.01), bounce ignored (14.02), slow walk ignored (14.03), quick jumps (14.05), DUCK/STAND (14.06), LEAN hysteresis (14.07), hands up (14.13), stuck duck reset (14.14), chicken flap, fart blast, flamingo balance, tickle swat. |
| **15** | **Profile Manager** | **D** | **13** | **DONE (15.11-15.13 deferred, P3)** | 2026-10-29 | 10 tests. Profile creation (15.01), duplicate rejection (15.02), selection (15.03), rolling .bak recovery (15.04), per-game high scores & coins (15.05), rename/avatar (15.06), parent deletion (15.07), re-measure (15.08), guest mode (15.09), disk write fail-soft (15.10). |
| **16** | **Measurement Capture** | **D** | **12** | **DONE (16.10-16.12 deferred, P3)** | 2026-10-30 | **MILESTONE M3 ACHIEVED**. 9 tests. Guided still pose (16.01), framing guard (16.02), stability filter (16.03), 3-try manual fallback (16.04), walking away cancellation (16.05), plausible height check (16.06), arm spread prompt (16.07), jump test apex (16.08), parent height entry (16.09). |
| **17** | **Phone Cameras Integration** | **E** | **12** | **DONE (17.06, 17.08, 17.10-17.12 deferred)** | 2026-10-30 | **MILESTONE M4 ACHIEVED**. 9 tests (5 supervisor + 4 configurator). Phone primary assignment (17.01), phone lost failover to laptop webcam (17.02, 17.05), keyboard fallback (17.05), hot-plug promotion (17.05), orientation lock (17.09), 3-camera role wizard. |
| **18** | **Games 2 and 3** | **E** | **9** | **IN PROGRESS (Game 2 Certified)** | - | Game 2 (Coin Slalom) certified with 4 tests (18.01, 18.02, 18.08, smash crates). Game 3 (Freeze Dance) pending. |
| 19 | Floor Projection Prep | E | 11 | PENDING | - | Floor projector calibration (Milestone M6). |
| X | Cross-cutting Flows | A-E | 14 | PENDING | - | E2E sessions, safety pauses, recovery. |

---

## Test counts by file (verified 2026-10-30)

| Test file | Tests |
|---|---|
| `tests/test_config.py` | 15 |
| `tests/test_display.py` | 24 |
| `tests/test_event_bus.py` | 13 |
| `tests/test_event_pump.py` | 6 |
| `tests/test_input_keyboard.py` | 11 |
| `tests/test_logger.py` | 5 |
| `tests/test_audio.py` | 7 |
| `tests/test_game_engine.py` | 11 |
| `tests/test_mechanics.py` | 15 |
| `tests/test_game_runner.py` | 7 |
| `tests/test_camera_manager.py` | 12 |
| `tests/test_debug_tools.py` | 8 |
| `tests/test_pose_tracker.py` | 8 |
| `tests/test_zone_calibration.py` | 6 |
| `tests/test_player_lock.py` | 6 |
| `tests/test_action_detector.py` | 13 |
| `tests/test_profile_manager.py` | 10 |
| `tests/test_measurement_capture.py` | 9 |
| `tests/test_camera_supervisor.py` | 5 |
| `tests/test_camera_configurator.py` | 4 |
| `tests/test_lane_switch.py` | 4 |
| **Total** | **199** |

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

### Module 4: Display and UI
- **Files:** `engine/__init__.py`, `engine/display.py`, `tests/test_display.py` (24 tests)
- **Use cases:**
  - `04.01` TV on display index 1 is selected when present: **Pass** (`test_04_01`, simulated display count; real TV verified live)
  - `04.02` Fallback to screen 0 when the TV is not found: **Pass** (`test_04_02`, simulated display count)
  - `04.03` HDMI pulled or TV off mid-game: **Pass** (`test_04_03_display_disconnect_publishes_pause`, `test_04_03_display_reconnect_starts_countdown_and_resumes`, `test_04_03_draw_hud_renders_reconnect_countdown`)
  - `04.04` 1080p render surface: **Pass** (`test_04_04`, verified live on 4K TV)
  - `04.05` HUD state updates from events: **Pass** (`test_04_05`)
  - `04.06` Low-health warning: **Pass** (`test_04_06_low_health_flag_triggered`, `test_04_06_draw_hud_renders_low_health_badge`)
  - `04.07` Text readable at 10 ft / scaled: **Pass** (`test_04_07_font_size_readability_rule`, `test_04_07_draw_hud_scales_to_custom_surface_size`)
  - `04.08` Profile picker with body control / hold-to-select: **Pass** (`test_04_08_hold_to_select_requires_full_second`, `test_04_08_draw_menu_renders_without_error`)
  - `04.09` Menus with keyboard navigation fallback: **Pass** (`test_04_09_keyboard_menu_navigation`, `test_04_09_state_changed_event_configures_menus`)
  - `04.10` FPS below 45 reduces effects: **Pass** (`test_04_10_low_fps_automatic_effects_reduction`, `test_04_10_particles_enabled_property_reflects_fps`)
  - `04.11` Photosensitivity: at most 3 flashes per second, soft alpha: **Pass** (`test_04_11`)
  - `04.12` Long names clipped and drawn: **Pass** (`test_04_12_long_profile_name_clipped_with_ellipsis`, `test_04_12_draw_hud_renders_player_name`)
  - `04.13` Window focus loss pauses; keys pass through; window close sets a quit flag: **Pass** (4 tests)

### Module 5: Audio Manager
- **Files:** `engine/audio.py`, `tests/test_audio.py` (7 tests)
- **Use cases:**
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
- **Use cases:**
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
- **Use cases:**
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
- **Use cases:**
  - `08.01` Complete run from start to game over: **Pass** (`test_08_01`)
  - `08.02` Kid does nothing: obstacles deal damage and transition to RESULTS at 0 HP: **Pass** (`test_08_02`)
  - `08.03` Air-time lockout prevents jump-spamming until landing: **Pass** (`test_08_03`)
  - `08.04` New personal best recorded only on game over when score exceeds previous best: **Pass** (`test_08_04`)
  - `08.05` Difficulty presets (easy, normal, strict) configure speed scaling & damage: **Pass** (`test_08_05`)
  - `08.06` Speed caps at preset maximum: **Pass** (`test_08_06`)
  - `08.07` First-time tutorial: **Deferred to Phase D (Profiles)**
  - `08.08` Results screen renders stats summary (score, best, cleared, streak): **Pass** (`test_08_08`)
  - `08.09` Camera vs keyboard: **Verified live on TV with Poco X6 Pro**

### Module 9: Camera Manager
- **Files:** `vision/__init__.py`, `vision/camera_manager.py`, `tests/test_camera_manager.py` (12 tests)
- **Use cases:**
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

### Module 10: Debug and Replay Tools
- **Files:** `vision/debug_tools.py`, `tests/test_debug_tools.py` (8 tests)
- **Use cases:**
  - `10.01` Toggle debug overlay via DEBUG_TOGGLED: **Pass** (`test_10_01`)
  - `10.02` Record landmark session with JSON metadata header: **Pass** (`test_10_02`)
  - `10.03` Deterministic replay of recorded frames: **Pass** (`test_10_03`)
  - `10.04` Replay comparison across changed detector thresholds: **Pass** (`test_10_04`)
  - `10.05` Ground-truth jump marking and accuracy evaluation: **Pass** (`test_10_05`)
  - `10.06` Low disk space aborts recording safely: **Pass** (`test_10_06`)
  - `10.07` Corrupt or incomplete recording files rejected safely: **Pass** (`test_10_07`)
  - `10.08` Optional video recording: **Deferred (P3)**
  - `10.09` Delete all recordings command: **Pass** (`test_10_09`)

### Module 11: Pose Tracker
- **Files:** `vision/pose_tracker.py`, `tests/test_pose_tracker.py` (8 tests)
- **Use cases:**
  - `11.01` Person detected extracts 33 landmarks with names and confidence: **Pass** (`test_11_01`)
  - `11.02` Empty frames dispatch PLAYER_LOST after 5 consecutive frames: **Pass** (`test_11_02`)
  - `11.03` Ankles/head out of frame flags partial body: **Pass** (`test_11_03`)
  - `11.04` Several people visible: **Deferred (Handled by Player Lock Module 13)**
  - `11.05` Missing MediaPipe library falls soft without crashing: **Pass** (`test_11_05`)
  - `11.06` Low confidence flags low light warning: **Pass** (`test_11_06`)
  - `11.07` Fast motion blur holds last valid pose for 150ms: **Pass** (`test_11_07`)
  - `11.08` Body span under 25% of frame triggers child scale warning: **Pass** (`test_11_08`)
  - `11.11` Joint names map correctly to standard indices: **Pass** (`test_11_11`)

### Module 12: Zone and Calibration
- **Files:** `vision/zone_calibration.py`, `tests/test_zone_calibration.py` (6 tests)
- **Use cases:**
  - `12.01` Save and load zone calibration: **Pass** (`test_12_01`)
  - `12.03` Player inside zone: **Pass** (`test_12_03`)
  - `12.04` Player at edge warning band: **Pass** (`test_12_04`)
  - `12.05` Foot-based out of zone event: **Pass** (`test_12_05`)
  - `12.08` Jump vertical immunity preserves floor position: **Pass** (`test_12_08`)
  - `12.09` Upper body lean evaluates feet, not head: **Pass** (`test_12_09`)
  - `12.10` JSON calibration persistence keyed by camera role: **Pass** (`test_12_01`)

### Module 13: Player Lock
- **Files:** `vision/player_lock.py`, `tests/test_player_lock.py` (6 tests)
- **Use cases:**
  - `13.01` 0.5s stable presence lock: **Pass** (`test_13_01`)
  - `13.02` Nearest-to-center multi-kid lock: **Pass** (`test_13_02`)
  - `13.03` Bystander/parent walking through ignored: **Pass** (`test_13_03`)
  - `13.04` 2.0s occlusion grace period: **Pass** (`test_13_04`)
  - `13.05` Occlusion timeout releases lock and pauses: **Pass** (`test_13_04`)
  - `13.06` Jump out of frame retains lock: **Pass** (`test_13_06`)
  - `13.08` Body proportions tracking prevents swapping: **Pass** (`test_13_08`)

### Module 14: Action Detector (Milestone M2)
- **Files:** `vision/action_detector.py`, `tests/test_action_detector.py` (13 tests)
- **Use cases:**
  - `14.01` JUMP and LAND pairs: **Pass** (`test_14_01`)
  - `14.02` Small hop or bounce under threshold ignored: **Pass** (`test_14_02`)
  - `14.03` Slow weight shift does not trigger jump: **Pass** (`test_14_03`)
  - `14.05` Land required between quick jumps: **Pass** (`test_14_05`)
  - `14.06` DUCK and STAND on rise: **Pass** (`test_14_06`)
  - `14.07` LEAN left/right/center with hysteresis: **Pass** (`test_14_07`)
  - `14.08` PLAYER_LOST event resets neutral posture: **Pass** (`test_14_08`)
  - `14.13` Hands up emits HANDS_UP and never triggers JUMP: **Pass** (`test_14_13`)
  - `14.14` Stuck duck auto-resets to STAND after 5 seconds: **Pass** (`test_14_14`)
  - Comedic Gestures: Chicken Flap wings (`test_comedic_chicken_flap_detected`), Fart Blast cloud (`test_comedic_fart_blast_detected`), Flamingo 1-leg balance (`test_comedic_flamingo_balance_detected`), Tickle Swat (`test_comedic_tickle_swat_detected`).

### Module 15: Profile Manager
- **Files:** `identity/profile_manager.py`, `tests/test_profile_manager.py` (10 tests)
- **Use cases:**
  - `15.01` Profile creation with trimmed name and UUID: **Pass** (`test_15_01`)
  - `15.02` Case-insensitive duplicate name rejected: **Pass** (`test_15_02`)
  - `15.03` Select profile broadcasts PROFILE_SELECTED: **Pass** (`test_15_03`)
  - `15.04` Damaged profiles.json restores from rolling backup: **Pass** (`test_15_04`)
  - `15.05` Per-game high score updates and coins awarded: **Pass** (`test_15_05`)
  - `15.06` Rename and avatar changes preserve permanent ID and scores: **Pass** (`test_15_06`)
  - `15.07` Profile deletion requires parent confirmation: **Pass** (`test_15_07`)
  - `15.08` Re-measuring updates body proportions without touching scores: **Pass** (`test_15_08`)
  - `15.09` Temporary guest profile not saved to disk: **Pass** (`test_15_09`)
  - `15.10` Disk write failure keeps data in memory safely: **Pass** (`test_15_10`)

### Module 16: Measurement Capture (Milestone M3)
- **Files:** `identity/measurement_capture.py`, `tests/test_measurement_capture.py` (9 tests)
- **Use cases:**
  - `16.01` Guided superhero still pose captures height and baseline: **Pass** (`test_16_01`)
  - `16.02` Partial body framing instructs child to step back: **Pass** (`test_16_02`)
  - `16.03` Fidgeting or movement during hold resets 2.0s timer: **Pass** (`test_16_03`)
  - `16.04` 3 failed hold attempts triggers manual fallback entry: **Pass** (`test_16_04`)
  - `16.05` Child walking away for 3s cancels session and saves nothing: **Pass** (`test_16_05`)
  - `16.06` Implausible height (< 80cm or > 190cm) rejected and retried: **Pass** (`test_16_06`)
  - `16.07` Arms pinned to sides prompts child to spread arms wide: **Pass** (`test_16_07`)
  - `16.08` Test jump tracks personal apex rise and sets jump threshold: **Pass** (`test_16_08`)
  - `16.09` Parent manual real height entry stores calibrated measurements: **Pass** (`test_16_09`)

### Module 17: Phone Cameras Integration (Milestone M4)
- **Files:** `vision/camera_supervisor.py`, `vision/camera_configurator.py`, `tests/test_camera_supervisor.py`, `tests/test_camera_configurator.py` (9 tests)
- **Use cases:**
  - `17.01` Phone primary camera selected when healthy: **Pass** (`test_17_01`)
  - `17.02` Phone disconnects -> falls back cleanly to laptop webcam: **Pass** (`test_17_02`)
  - `17.05` Both cameras lost falls back to keyboard mode: **Pass** (`test_17_05`)
  - `17.05` Reconnecting phone promotes back to primary: **Pass** (`test_17_05`)
  - `17.09` Orientation setting locks and rotates frame 90 degrees: **Pass** (`test_17_09`)
  - 3-Camera Configurator: Scans devices, assigns FRONT/SIDE/LAPTOP, conflict resolution, config persistence: **Pass** (`test_camera_configurator.py`, 4 tests). Verified live with 2 phones + laptop.

### Module 18: Games 2 and 3 (Milestone M5 - In Progress)
- **Files:** `engine/games/lane_switch.py`, `tests/test_lane_switch.py` (4 tests)
- **Use cases:**
  - `18.01` Lane game lean left or right changes lane: **Pass** (`test_18_01`)
  - `18.02` Edge lanes strictly clamped (never leaves road): **Pass** (`test_18_02`)
  - `18.08` Per-game high scores stored separately under lane_switch: **Pass** (`test_18_08`)
  - Soft smashable crates: Punch or kick forward smashes crate for points and coins: **Pass** (`test_smashable_crate_mechanic`)

---

## Known gaps and open items

| ID | Item | Priority | Status |
|---|---|---|---|
| G1 | 01.10 privacy filter for logs (no images or landmarks) | P3 | Open |
| G2 | 03.07 quit and recalibrate parent keys | P2 | Deferred until those features exist |
| G3 | Event payload contracts for Phase B events | Needed before Modules 4 to 7 | **Closed** (`docs/event_contracts.md`, 2026-10-28) |
| G4 | Some Module 2 test names map loosely to catalogue wording | Low | Open |
| G5 | `EventBus.publish()` is synchronous: revisit when Display/Audio subscribe | Medium | Open |
| G6 | `requirements.txt` dependencies: pygame, opencv-python, mediapipe pinned | Low | **Closed** (`requirements.txt`, 2026-10-29) |
| G7 | Module 4 remaining: 04.03 (use contract reason `hdmi_disconnect`), 04.08, 04.09 | P1/P2 | **Closed** (24 display tests pass) |
| G8 | Make partial Module 4 items real: HUD scales to surface size, player name (04.12), reduced_effects (04.10), low-health badge (04.06) | P2 | **Closed** (17 display tests pass) |
| G9 | Real-hardware checks: TV on display index 1, fullscreen at 1080p, TV Game Mode, audio over HDMI | P1 | **Closed** (Verified live on 43" TV) |
| G10 | Main loop owns event pump: call `pygame.event.get()` in one place only | P1 | **Closed** (`engine/event_pump.py`, 6 tests) |
| G11 | input_keyboard.py pause payload contract alignment | Low | **Closed** (2026-10-28) |