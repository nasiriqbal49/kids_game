# Kids Motion Game — Development & Use-Case Progress Tracker

**Last Updated:** Current Session  
**Current Milestone Target:** Milestone M1 (Keyboard Runner)  
**Current Phase:** Phase A (Foundation)

---

## Module Status Summary

| # | Module Name | Phase | Total Use Cases | Status | Completed At | Notes |
|---|---|---|---|---|---|---|
| **1** | **Config and Logging** | **A** | **10** | **DONE** | Session 1 | Verified with unit tests (01.01–01.06). |
| **2** | **Event Bus** | **A** | **11** | **UP NEXT** | — | Thread-safe queue, pub/sub, validation. |
| 3 | Input Adapter (Keyboard) | A | 9 | PENDING | — | Stand-in player for testing without camera. |
| 4 | Display and UI | B | 13 | PENDING | — | Pygame TV output, HUD, 1080p full-screen. |
| 5 | Audio Manager | B | 10 | PENDING | — | HDMI TV audio, SFX mixing. |
| 6 | Game Engine Core | B | 12 | PENDING | — | State machine, fixed-timestep loop. |
| 7 | Game Mechanics Library | B | 15 | PENDING | — | Spawning, hitboxes, power-ups. |
| 8 | Game 1: Runner | B | 9 | PENDING | — | Playable keyboard game (Milestone M1). |
| 9 | Camera Manager | C | 14 | PENDING | — | OpenCV frame acquisition thread. |
| 10 | Debug & Replay Tools | C | 9 | PENDING | — | Landmark recorder and visual overlay. |
| 11 | Pose Tracker | C | 12 | PENDING | — | MediaPipe body tracking at 30 FPS. |
| 12 | Zone & Calibration | C | 12 | PENDING | — | Tile boundaries & floor scale. |
| 13 | Player Lock | C | 11 | PENDING | — | Target child lock-on, ignores siblings. |
| 14 | Action Detector | C | 17 | PENDING | — | Jump/Duck/Lean detection (Milestone M2). |
| 15 | Profile Manager | D | 13 | PENDING | — | Local JSON child profiles and stats. |
| 16 | Measurement Capture | D | 12 | PENDING | — | Calibration routine (Milestone M3). |
| 17 | Phone Cameras Integration | E | 12 | PENDING | — | Dual phone cameras via USB (Milestone M4). |
| 18 | Games 2 and 3 | E | 9 | PENDING | — | Lane switch & freeze dance (Milestone M5). |
| 19 | Floor Projection Prep | E | 11 | PENDING | — | Floor projector calibration (Milestone M6). |
| X | Cross-cutting Flows | A-E | 14 | PENDING | — | E2E sessions, safety pauses, recovery. |

---

## Detailed Log for Completed Modules

### Module 1: Config and Logging
- **Files Created:** `core/logger.py`, `core/config.py`, `tests/test_config.py`, `config.json`
- **Use Cases Verified:**
  - `01.01` (Auto-create default `config.json` on missing): **Pass**
  - `01.02` (Fill missing keys with sensible defaults): **Pass**
  - `01.03` (Clamp out-of-range values e.g. volume 350 -> 100): **Pass**
  - `01.04` (Detect malformed JSON, backup to `.bad`, load defaults): **Pass**
  - `01.05` (Typo detection & suggestion using difflib): **Pass**
  - `01.06` (CLI overrides via `--key=value`): **Pass**
  - `01.07` / `01.08` (Formatted rotating log output): **Pass**