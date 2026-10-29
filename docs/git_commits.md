# Git Commit History

- **Repository:** `D:\kids_game`
- **Total commits included:** 57
- **History scope:** `all`
- **Generated automatically from local Git history.**

> Run `python tools/update_git_commits.py` to regenerate this document.

| No. | Short Hash | Commit Date & Time | Commit Subject | Files Changed | Lines Added | Lines Deleted | Changed File Paths |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1acb50a | 2026-10-29 16:14:12 | Certify Phase C (Modules 11-14) and achieve Milestone M2: Body Control [162 tests passing] | 4 | 83 | 24 | docs/change.md, docs/master_ai_handoff.md, docs/progress_tracker.md, docs/project_directory_structure.md |
| 2 | d3db361 | 2026-10-29 16:10:56 | Certify Module 14 (Action Detector) and achieve Milestone M2: Body Control [162 tests passing] | 2 | 365 | 0 | tests/test_action_detector.py, vision/action_detector.py |
| 3 | 7b3bd9b | 2026-10-29 16:08:22 | Certify Module 13 (Player Lock) [153 tests passing] | 2 | 308 | 0 | tests/test_player_lock.py, vision/player_lock.py |
| 4 | a8b2de5 | 2026-10-29 16:05:44 | Certify Module 12 (Zone and Calibration) [147 tests passing] | 2 | 291 | 0 | tests/test_zone_calibration.py, vision/zone_calibration.py |
| 5 | eaff24d | 2026-10-29 16:03:28 | Certify Module 11 (Pose Tracker) [141 tests passing, MediaPipe integrated] | 5 | 879 | 3 | tests/test_camera_manager.py, tests/test_debug_tools.py, tests/test_pose_tracker.py, vision/debug_tools.py, vision/pose_tracker.py |
| 6 | a9c7f59 | 2026-10-29 14:31:21 | Implement Multi-AI session protocol, docs/change.md, and diff/spec extraction tools | 5 | 133 | 1 | docs/AI_START_HERE.md, docs/change.md, docs/project_directory_structure.md, tools/extract_module.py, tools/make_session_diff.py |
| 7 | 4d6c94e | 2026-10-29 12:43:01 | Fix .gitingestignore file name | 2 | 6 | 6 | .gitingestignore, gitingestignore.py |
| 8 | ef74151 | 2026-10-29 12:38:15 | Certify Module 9 (Camera Manager) [125 tests passing], integrate OpenCV, and add .gitingestignore | 3 | 58 | 50 | docs/git_commits.md, docs/project_directory_structure.md, gitingestignore.py |
| 9 | 3a3b539 | 2026-10-29 12:29:08 | Certify Module 9 (Camera Manager) [125 tests passing, OpenCV integrated] | 10 | 740 | 69 | docs/full_game_plan.md, docs/git_commits.md, docs/issues_and_resolutions.md, docs/master_ai_handoff.md, docs/progress_tracker.md, docs/project_directory_structure.md, requirements.txt, tests/test_camera_manager.py, vision/__init__.py, vision/camera_manager.py |
| 10 | b907407 | 2026-10-29 11:51:12 | Certify Module 8 (Game 1: Runner), achieve Milestone M1 [113 tests passing], and approve camera configurator & gating enhancements | 13 | 710 | 200 | config.json, docs/full_game_plan.md, docs/git_commits.md, docs/issues_and_resolutions.md, docs/master_ai_handoff.md, docs/progress_tracker.md, docs/project_directory_structure.md, engine/display.py, engine/games/__init__.py, engine/games/runner.py, engine/mechanics/manager.py, main.py, tests/test_game_runner.py |
| 11 | fa851fa | 2026-10-28 21:55:40 | Certify Module 6 (Game Engine) & Module 7 (Game Mechanics Library) [106 passing tests, G11 closed] | 10 | 631 | 66 | core/input_keyboard.py, docs/git_commits.md, docs/issues_and_resolutions.md, docs/master_ai_handoff.md, docs/progress_tracker.md, docs/project_directory_structure.md, engine/mechanics/__init__.py, engine/mechanics/entities.py, engine/mechanics/manager.py, tests/test_mechanics.py |
| 12 | b6175ba | 2026-10-28 21:28:42 | new update | 2 | 74 | 0 | engine/game_engine.py, tests/test_game_engine.py |
| 13 | 03c15d9 | 2026-10-28 21:23:11 | Module 6: fixed-timestep accumulator, speed ramping, zone grace auto-pause, and idle timeout (06.04, 06.06, 06.07, 06.09) | 2 | 161 | 1 | engine/game_engine.py, tests/test_game_engine.py |
| 14 | 4d7a722 | 2026-10-28 21:20:05 | Module 6: state machine, legal transitions, pause/resume, and zero-health game-over (06.01-06.03, 06.05, 06.11) | 2 | 239 | 0 | engine/game_engine.py, tests/test_game_engine.py |
| 15 | ee847c4 | 2026-10-28 18:13:55 | docs: regenerate git_commits.md | 1 | 43 | 42 | docs/git_commits.md |
| 16 | ca86164 | 2026-10-28 18:13:50 | Certify Module 4 (Display) & Module 5 (Audio) [80 passing tests, G7 & G9 closed, live audio demo] | 5 | 90 | 56 | docs/git_commits.md, docs/master_ai_handoff.md, docs/progress_tracker.md, docs/project_directory_structure.md, main.py |
| 17 | 88d4db9 | 2026-10-28 18:06:59 | Module 5: priority channels for hits/game-over and state-driven looping audio (05.02, 05.05) | 2 | 67 | 4 | engine/audio.py, tests/test_audio.py |
| 18 | 04955c3 | 2026-10-28 18:01:03 | Module 5: audio manager with procedural synth fallback, volume cap, low health alert, and pause state (05.01, 05.03, 05.04, 05.06-05.08) | 2 | 258 | 0 | engine/audio.py, tests/test_audio.py |
| 19 | 90a99e7 | 2026-10-28 17:50:21 | main: interactive display and HUD test runner with jump air-time (UC 04.01-04.13, G9) | 1 | 161 | 19 | main.py |
| 20 | 042b220 | 2026-10-28 17:42:26 | Module 4: menu drawing, body control hold-to-select, and keyboard navigation (04.08, 04.09) | 2 | 191 | 0 | engine/display.py, tests/test_display.py |
| 21 | ddadb9e | 2026-10-28 17:36:55 | docs: regenerate git_commits.md | 1 | 37 | 36 | docs/git_commits.md |
| 22 | cbd42ea | 2026-10-28 17:36:50 | Module 4: HDMI disconnect auto-pause and reconnect countdown (04.03) | 5 | 187 | 49 | docs/git_commits.md, docs/master_ai_handoff.md, docs/progress_tracker.md, engine/display.py, tests/test_display.py |
| 23 | ca759bc | 2026-10-28 17:29:22 | docs: regenerate git_commits.md | 1 | 35 | 34 | docs/git_commits.md |
| 24 | 58c797b | 2026-10-28 17:29:16 | Module 4: surface-scaled HUD drawing, player name, low-health badge, and reduced effects toggle (G8; 04.06, 04.07, 04.10, 04.12) | 5 | 137 | 62 | docs/git_commits.md, docs/master_ai_handoff.md, docs/progress_tracker.md, engine/display.py, tests/test_display.py |
| 25 | e6fd51f | 2026-10-28 17:11:34 | docs: regenerate git_commits.md | 1 | 33 | 32 | docs/git_commits.md |
| 26 | 7ff44c2 | 2026-10-28 17:11:28 | docs: update progress tracker and handoff for EventPump (62 passing tests, G10 closed, G11 added) | 4 | 53 | 48 | docs/git_commits.md, docs/master_ai_handoff.md, docs/progress_tracker.md, docs/project_directory_structure.md |
| 27 | 074418b | 2026-10-28 17:03:12 | Engine: EventPump owns pygame events, routes window events to display and keys to keyboard adapter (G10; 03.01, 03.02, 03.05, 03.07, 04.13) | 2 | 134 | 0 | engine/event_pump.py, tests/test_event_pump.py |
| 28 | 2c640c9 | 2026-10-28 17:01:43 | Remove accidental junk file | 1 | 0 | 10 | "\\357\\200\\233\\357\\200\\233" |
| 29 | ea89535 | 2026-10-28 16:59:34 | docs: refresh git_commits | 1 | 29 | 26 | docs/git_commits.md |
| 30 | ecf1508 | 2026-10-28 16:59:22 | docs: correct Module 4 status (6 verified, 4 partial, 3 not started), close G3, add gaps G7-G10, issues #013-#015, 56 tests | 5 | 84 | 43 | docs/AI_START_HERE.md, docs/issues_and_resolutions.md, docs/master_ai_handoff.md, docs/progress_tracker.md, "\\357\\200\\233\\357\\200\\233" |
| 31 | c33d3c5 | 2026-10-28 16:52:49 | Module 4: fix focus-loss pause, stop swallowing key events, quit flag (04.13); regenerate directory doc; utf-8 requirements | 3 | 57 | 26 | engine/display.py, requirements.txt, tests/test_display.py |
| 32 | 211e439 | 2026-10-28 15:53:58 | docs: regenerate git_commits.md with commit history reference | 1 | 26 | 25 | docs/git_commits.md |
| 33 | 959b0fc | 2026-10-28 15:53:55 | Module 4: drawing routines, 10-ft text sizing, and safety rules (04.07, 04.10-04.13) | 7 | 251 | 59 | docs/AI_START_HERE.md, docs/git_commits.md, docs/issues_and_resolutions.md, docs/master_ai_handoff.md, docs/progress_tracker.md, engine/display.py, tests/test_display.py |
| 34 | fcdebcd | 2026-10-28 15:42:32 | Module 4: display targeting and HUD event state (04.01, 04.02, 04.04, 04.05, 04.06) | 7 | 260 | 15 | docs/master_ai_handoff.md, docs/progress_tracker.md, docs/project_directory_structure.md, engine/__init__.py, engine/display.py, requirements.txt, tests/test_display.py |
| 35 | c47bdf1 | 2026-10-28 15:33:37 | docs: define event payload contracts for Phase B (Modules 4-8) [Gap G3] | 2 | 167 | 3 | docs/event_contracts.md, docs/project_directory_structure.md |
| 36 | 81187b8 | 2026-10-28 15:29:50 | docs: streamline git_commits.md columns for clean AI handoff | 2 | 24 | 34 | docs/git_commits.md, tools/update_git_commits.py |
| 37 | 9d735f6 | 2026-10-28 15:23:58 | added git_commits in docs for tracing | 3 | 525 | 0 | core/config.py, docs/git_commits.md, tools/update_git_commits.py |
| 38 | 24d8e71 | 2026-10-28 12:29:17 | docs Updated for next AI session | 3 | 197 | 89 | docs/issues_and_resolutions.md, docs/master_ai_handoff.md, docs/progress_tracker.md |
| 39 | cdd65d9 | 2026-10-28 12:23:29 | Module 1: reload settings while running, live-safe vs next-game-start (01.09) | 2 | 109 | 0 | core/config.py, tests/test_config.py |
| 40 | 04548c5 | 2026-10-28 12:20:02 | Module 1: config hardening (01.03, 01.04, 01.06), volume cap cross-check (05.06) | 2 | 89 | 22 | core/config.py, tests/test_config.py |
| 41 | 97de702 | 2026-10-28 12:16:00 | Tests: add 01.05, 03.06; isolate keyboard tests from real config; quiet rotation test | 3 | 50 | 3 | tests/test_config.py, tests/test_input_keyboard.py, tests/test_logger.py |
| 42 | 2589a60 | 2026-10-28 12:11:50 | Module 1: logging configured from config, handle leak fixed, logger tests (01.07, 01.08) | 3 | 113 | 16 | core/logger.py, main.py, tests/test_logger.py |
| 43 | 9f56124 | 2026-10-28 12:09:17 | Module 3: keyboard latency simulation uses bus.post (03.09); AI_START_HERE: remove PDF reference | 3 | 16 | 8 | core/input_keyboard.py, docs/AI_START_HERE.md, tests/test_input_keyboard.py |
| 44 | 6366fe2 | 2026-10-28 12:05:47 | Merge branch 'main' of https://github.com/nasiriqbal49/kids_game | 0 | 0 | 0 |  |
| 45 | 2dce68b | 2026-10-28 12:03:40 | Module 2: thread-safe post/drain, consecutive failure counting (02.03, 02.04, 02.07, 02.11) | 2 | 146 | 2 | core/event_bus.py, docs/AI_START_HERE.md |
| 46 | baf38e1 | 2026-10-28 12:00:29 | Fix event bus thread safety and consecutive failure counting | 3 | 84 | 781 | Kids_Motion_Game_Plan.pdf, core/event_bus.py, tests/test_event_bus.py |
| 47 | 878a92e | 2026-10-28 11:00:42 | Delete Kids_Motion_Game_Plan.pdf | 1 | 0 | 729 | Kids_Motion_Game_Plan.pdf |
| 48 | 3c06ffc | 2026-10-27 23:26:43 | Certify Module 3 (Keyboard Input Adapter) and complete Phase A (Foundation) [100% tests passing] | 5 | 310 | 15 | core/input_keyboard.py, docs/master_ai_handoff.md, docs/progress_tracker.md, docs/project_directory_structure.md, tests/test_input_keyboard.py |
| 49 | 1a5690e | 2026-10-27 23:21:05 | Automate project directory tree generator and certify Module 2 (Event Bus) | 6 | 382 | 42 | docs/issues_and_resolutions.md, docs/master_ai_handoff.md, docs/progress_tracker.md, docs/project_directory_structure.md, tests/test_event_bus.py, tools/show_tree.py |
| 50 | 2f206ad | 2026-10-27 23:08:35 | Implement Module 2: Complete EventBus dispatcher covering use cases 02.01 to 02.11 | 2 | 255 | 2 | core/event_bus.py, docs/master_ai_handoff.md |
| 51 | d85db6c | 2026-10-27 23:04:42 | Implement Module 2 piece 1: Event Catalogue and immutable Event data model (UC 02.05) | 1 | 88 | 0 | core/events.py |
| 52 | d659e34 | 2026-10-27 23:00:53 | Add project directory structure documentation | 1 | 38 | 0 | docs/project_directory_structure.md |
| 53 | 697ecae | 2026-10-27 22:56:54 | Add complete unabridged game plan (Parts 1-5) and full use case catalogue (Part 6, 235 cases) | 2 | 990 | 0 | docs/full_game_plan.md, docs/use_case_catalogue.md |
| 54 | 2325318 | 2026-10-27 22:51:38 | Add project documentation: full game plan, progress tracker, issue log, and AI handoff | 4 | 111 | 0 | docs/full_game_plan.md, docs/issues_and_resolutions.md, docs/master_ai_handoff.md, docs/progress_tracker.md |
| 55 | f43647e | 2026-10-27 22:45:27 | Add unit tests verifying Module 1 Config (UC 01.01-01.06) | 2 | 64 | 0 | tests/__init__.py, tests/test_config.py |
| 56 | f54862b | 2026-10-27 22:42:09 | Implement Module 1: Config and Logging | 6 | 1135 | 0 | Kids_Motion_Game_Plan.pdf, config.json, core/__init__.py, core/config.py, core/logger.py, main.py |
| 57 | 57a67c7 | 2026-10-27 21:58:52 | Add gitignore | 1 | 7 | 0 | .gitignore |
