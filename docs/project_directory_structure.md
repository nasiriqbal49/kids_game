# Project Directory Structure

**Last Updated:** Phase A (Module 1 certified, Module 2 in progress)

This document maps the project file tree, distinguishing what is currently implemented from what is planned.

---

## Current Active Tree

```text
kids_game/
│
├── .venv/                         # Python 3.12 virtual environment (gitignored)
├── logs/                          # Runtime log outputs (gitignored)
│   └── kidsgame.log               # Auto-rotated execution logs
│
├── core/                          # Foundation engine modules (Phase A)
│   ├── __init__.py                # Core package marker
│   ├── logger.py                  # Rotating logger (Module 1)
│   └── config.py                  # JSON config loader & validator (Module 1)
│
├── docs/                          # Master design & tracking documentation
│   ├── full_game_plan.md          # Complete unabridged specification (Parts 1–5)
│   ├── use_case_catalogue.md      # All 235 use cases & severity rules (Part 6)
│   ├── progress_tracker.md        # Live status, timestamps & use-case completions
│   ├── issues_and_resolutions.md  # Hurdle & bug resolution log
│   ├── master_ai_handoff.md       # Context snapshot for AI resumption
│   └── project_directory_structure.md # This file
│
├── tests/                         # Automated test suite
│   ├── __init__.py                # Tests package marker
│   └── test_config.py             # Unit tests for Module 1 (UC 01.01–01.06)
│
├── .gitignore                     # Git exclusion rules
├── config.json                    # Active system configuration
├── Kids_Motion_Game_Plan.pdf      # Source plan PDF
└── main.py                        # Test runner & entry point