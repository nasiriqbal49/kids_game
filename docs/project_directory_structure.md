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
│   ├── full_game_plan.md
│   ├── issues_and_resolutions.md
│   ├── master_ai_handoff.md
│   ├── progress_tracker.md
│   ├── project_directory_structure.md
│   └── use_case_catalogue.md
├── logs
│   └── kidsgame.log
├── tests
│   ├── __init__.py
│   ├── test_config.py
│   └── test_event_bus.py
├── tools
│   └── show_tree.py
├── .gitignore
├── config.json
├── Kids_Motion_Game_Plan.pdf
└── main.py
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
