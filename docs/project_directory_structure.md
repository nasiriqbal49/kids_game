# Project Directory Structure

**Last Updated:** Phase A (Automated)

---

## Current Active Tree

```text
kids_game/
├── core
│   ├── __init__.py
│   ├── config.py
│   ├── event_bus.py
│   ├── events.py
│   ├── input_keyboard.py
│   └── logger.py
├── docs
│   ├── AI_START_HERE.md
│   ├── change.md
│   ├── event_contracts.md
│   ├── full_game_plan.md
│   ├── git_commits.md
│   ├── issues_and_resolutions.md
│   ├── master_ai_handoff.md
│   ├── progress_tracker.md
│   ├── project_directory_structure.md
│   └── use_case_catalogue.md
├── engine
│   ├── games
│   │   ├── __init__.py
│   │   └── runner.py
│   ├── mechanics
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   └── manager.py
│   ├── __init__.py
│   ├── audio.py
│   ├── display.py
│   ├── event_pump.py
│   └── game_engine.py
├── identity
│   ├── __init__.py
│   ├── measurement_capture.py
│   └── profile_manager.py
├── logs
│   └── kidsgame.log
├── tests
│   ├── __init__.py
│   ├── test_action_detector.py
│   ├── test_audio.py
│   ├── test_camera_manager.py
│   ├── test_camera_supervisor.py
│   ├── test_config.py
│   ├── test_debug_tools.py
│   ├── test_display.py
│   ├── test_event_bus.py
│   ├── test_event_pump.py
│   ├── test_game_engine.py
│   ├── test_game_runner.py
│   ├── test_input_keyboard.py
│   ├── test_logger.py
│   ├── test_measurement_capture.py
│   ├── test_mechanics.py
│   ├── test_player_lock.py
│   ├── test_pose_tracker.py
│   ├── test_profile_manager.py
│   └── test_zone_calibration.py
├── tools
│   ├── extract_module.py
│   ├── inspect_cameras.py
│   ├── make_session_diff.py
│   ├── show_tree.py
│   └── update_git_commits.py
├── user_data
│   ├── profiles.json
│   └── profiles.json.bak
├── vision
│   ├── __init__.py
│   ├── action_detector.py
│   ├── camera_manager.py
│   ├── camera_supervisor.py
│   ├── debug_tools.py
│   ├── player_lock.py
│   ├── pose_tracker.py
│   └── zone_calibration.py
├── .gitignore
├── .gitingestignore
├── config.json
├── main.py
├── module_10_spec.md
├── requirements.txt
└── session_diff.txt
```

---

## Target Project Tree (Full Build Roadmap)

```text
kids_game/
├── core/                          # Architecture foundation (Phase A)
│   ├── logger.py                  # Module 1: Logging
│   ├── config.py                  # Module 1: Settings
│   ├── events.py                  # Module 2: Event catalogue & dataclass
│   ├── event_bus.py               # Module 2: Pub/Sub message broker
│   └── input_keyboard.py          # Module 3: Keyboard input adapter
├── engine/                        # Game Engine & Mechanics (Phase B)
│   ├── display.py                 # Module 4: Pygame second-screen display & HUD
│   ├── audio.py                   # Module 5: Sound & music manager
│   ├── game_engine.py             # Module 6: State machine & fixed timestep loop
│   ├── mechanics/                 # Module 7: Reusable gameplay blocks
│   └── games/                     # Module 8 & 18: Runner, Lane Switch, Freeze Dance
├── vision/                        # Computer Vision & Tracking (Phase C & E)
├── identity/                      # Player Profiles & Calibration (Phase D)
├── projection/                    # Projector Output (Phase E)
├── assets/                        # Art, sounds and fonts
├── docs/                          # Comprehensive documentation & logs
├── tests/                         # Module unit tests
└── main.py                        # Game startup script
```
