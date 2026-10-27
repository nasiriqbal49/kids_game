# Issues & Resolutions Log

This document tracks every error, edge-case hurdle, or design correction encountered during development.

---

### Issue #001: Root directory file placement confusion in VS Code
- **Module:** Setup & Module 1 (Foundation)
- **Symptom:** `main.py` was mistakenly created inside `core/` instead of project root `D:\kids_game`.
- **Root Cause:** When a file or folder inside `core` is selected in the VS Code sidebar, clicking "New File" creates it inside that folder.
- **Resolution:** Moved `main.py` to root via PowerShell terminal command (`Move-Item core\main.py .\main.py -Force`). Advised to click outside folders in VS Code before adding root files.
- **Status:** **Resolved**

---

### Issue #002: Git line ending warning (`LF will be replaced by CRLF`)
- **Module:** Setup / Version Control
- **Symptom:** Git warning displayed when adding `Kids_Motion_Game_Plan.pdf`.
- **Root Cause:** Standard Windows vs Linux newline handling in Git.
- **Resolution:** Normal behavior for Windows systems; ignored as it does not affect Python or binary assets.
- **Status:** **Resolved**

---

### Issue #003: Graceful degradation on corrupted `config.json`
- **Module:** Module 1 (Use Case 01.04)
- **Requirement:** Malformed JSON must never crash the game.
- **Resolution:** Implemented `try/except (json.JSONDecodeError, OSError)` block in `core/config.py` that automatically copies the damaged file to `config.json.bad` and falls back to in-memory defaults. Verified with unit test `test_01_04`.
- **Status:** **Resolved & Verified**
---

### Issue #004: Python SyntaxError on invalid walrus operator assignment in test suite
- **Module:** Module 2 (Event Bus tests, Use Case 02.11)
- **Symptom:** `SyntaxError: invalid syntax` on line 166 of `tests/test_event_bus.py`:
  `self.bus.subscribe(EventType.PAUSE := EventType.GAME_PAUSE, ...)`
- **Root Cause:** In Python, the walrus operator (`:=`) cannot be assigned to an attribute or dotted name (`obj.attr := value`). It only accepts a simple identifier.
- **Resolution:** Replaced the line with direct subscription:
  `self.bus.subscribe(EventType.GAME_PAUSE, lambda e: received.append(e.name))`
- **Status:** **Resolved & Verified**