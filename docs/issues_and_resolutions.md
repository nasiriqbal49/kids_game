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



---

### Issue #005: Test 02.11 never ran; Phase A status was over-claimed
- **Module:** Module 2 (Event Bus tests) and project docs
- **Symptom:** The handoff and tracker claimed "24 tests passing, 100% certified", but only 23 tests actually ran.
- **Root Cause:** `test_02_11_shutdown_flushes_and_stops_acceptance` was indented at column 0, outside the test class, so `unittest` never discovered it. Tests for 01.05, 01.07, 01.08 and 03.06 did not exist but were marked Pass.
- **Resolution:** Indented the method into the class (24 tests ran). Added the missing tests. Rewrote handoff and tracker so "Pass" requires a real, running test.
- **Lesson:** After adding tests, confirm the total count increased by the expected number.
- **Status:** **Resolved & Verified**

---

### Issue #006: Event Bus thread safety and failure counting
- **Module:** Module 2 (UC 02.03, 02.04, 02.07, 02.11)
- **Symptom:** `post()` congestion path could crash with concurrent threads; a subscriber was silenced forever after 5 total errors in a session; a lock object existed but was never used.
- **Resolution:** Real `threading.Lock` around the queue in `post()`, `drain()` and `shutdown()`; failure count resets after a successful call (consecutive failures). Added `test_02_12` (failure reset) and `test_02_13` (concurrent posting guard).
- **Incident:** The first attempt placed the `else:` branch aligned with the `for` loop instead of the `try`, which reset the count on every publish. Test `test_02_03` caught it. Correct placement: `else:` at the same indentation as `try:`.
- **Status:** **Resolved & Verified**

---

### Issue #007: Keyboard latency simulation published from a background thread
- **Module:** Module 3 (UC 03.09)
- **Symptom:** The delayed-event thread called `bus.publish()` directly, breaking the cross-thread rule.
- **Resolution:** The delayed thread now calls `bus.post()`; the event is created at key-press time so its timestamp is real; the test drains the bus. 
- **Status:** **Resolved & Verified**

---

### Issue #008: Logging settings in config.json were ignored
- **Module:** Module 1 (UC 01.07, 01.08)
- **Symptom:** `main.py` hard-coded DEBUG; `logging.level`, `max_bytes`, `backup_count` did nothing. Old file handlers were not closed on reconfigure. Warnings emitted before the file handler existed never reached the log file.
- **Resolution:** Added `configure_from(cfg)`; `main.py` starts logging with defaults, loads config, then reapplies logging from config. Handlers are closed when replaced; warnings are emitted after all handlers exist. Added `tests/test_logger.py` (5 tests).
- **Status:** **Resolved & Verified**

---

### Issue #009: Keyboard tests read the real config.json
- **Module:** Module 3 tests
- **Symptom:** `setUp` created the adapter with the real project config, so editing key bindings could break tests.
- **Resolution:** Tests now use a `FakeConfig`. Rule added to AI_START_HERE: tests never touch real `config.json`, `profiles/` or `logs/`.
- **Status:** **Resolved & Verified**

---

### Issue #010: Config loader weaknesses
- **Module:** Module 1 (UC 01.03, 01.04, 01.06, 05.06)
- **Symptoms:** JSON that is valid but not an object was silently ignored; `true` accepted for number settings; CLI overrides skipped after a broken file; a typo like `--display.fullscreen=flase` became False; volume could exceed the volume cap.
- **Resolution:** Non-object JSON treated as malformed (backed up to `.bad`); bool rejected for number settings; overrides always applied; strict bool parsing; volume lowered to the cap. 5 tests added.
- **Status:** **Resolved & Verified**

---

### Issue #011: Push rejected after the PDF was deleted on GitHub
- **Module:** Setup / Version Control
- **Symptom:** `git push` rejected (`fetch first`).
- **Root Cause:** The owner deleted `Kids_Motion_Game_Plan.pdf` on GitHub, creating a commit not present locally.
- **Resolution:** `git pull --no-rebase --no-edit origin main`, then `git push`. The PDF deletion is intentional; the `.md` plan files are now the source of truth.
- **Status:** **Resolved**

---

### Issue #012: Missing pygame import and uninitialized video driver in test_display.py
- **Module:** Module 4 (Display and UI tests, Use Case 04.13)
- **Symptom:** `NameError: name 'pygame' is not defined` during execution of `test_04_13_focus_loss_dispatches_pause`.
- **Root Cause:** `import pygame` was omitted from the top-level imports in `tests/test_display.py`. Additionally, because `tearDown()` shuts down pygame video via `close()`, `process_window_events()` returned early on `pygame.get_init() == False`.
- **Resolution:** Added `import pygame` at the top of `tests/test_display.py` and ensured `pygame.init()` is active in `test_04_13`.
- **Status:** **Resolved & Verified**

---

### Issue #013: Focus-loss pause used the wrong pygame event
- **Module:** Module 4 (UC 04.13)
- **Symptom:** Alt+Tab did not pause the game, but moving the mouse pointer out of the window did.
- **Root Cause:** The code checked `ACTIVEEVENT` with `state == 1`, which is mouse focus in pygame (input focus is 2). The test used a fake event with the same wrong value, so it passed while the real behaviour was wrong. In pygame 2 the correct event is `WINDOWFOCUSLOST`.
- **Resolution:** Handle `pygame.WINDOWFOCUSLOST`; added a test that mouse-leave does not pause.
- **Lesson:** A test that fakes the input proves nothing unless the fake matches what the real system sends.
- **Status:** **Resolved & Verified**

---

### Issue #014: Display swallowed keyboard events; window close published a pause
- **Module:** Module 4 / Module 3 integration
- **Symptom:** `process_window_events()` read every pygame event, so key presses would never reach the keyboard adapter. Closing the window published `GAME_PAUSE` with a reason (`window_close`) that is not in the event contract.
- **Resolution:** `process_window_events(events)` handles only window events and returns all other events to the main loop. Window close sets `quit_requested`. Four tests added. Rule recorded as gap G10: the main loop owns the pygame event pump.
- **Status:** **Resolved & Verified**

---

### Issue #015: Module 4 status over-claimed; housekeeping files broken
- **Module:** Docs and project hygiene
- **Symptom:** The tracker marked 04.07, 04.10 and 04.12 as Pass on constants-only, flag-only or helper-only tests, and still listed gap G3 as open after the contracts were written. `docs/project_directory_structure.md` was empty (0 bytes). `requirements.txt` was saved as UTF-16 (shown as a binary file on GitHub).
- **Resolution:** Tracker and handoff rewritten to show 6 verified, 4 partial, 3 not started. Directory doc regenerated with `python tools/show_tree.py --update`; `requirements.txt` re-saved as plain text. Both housekeeping fixes to be confirmed with `git show --stat HEAD`.
- **Status:** **Resolved (housekeeping to be confirmed)**

---

### Issue #016: Gap G11: Pause event payload missing 'reason' contract key
- **Module:** Module 3 / Module 6 integration
- **Symptom:** `input_keyboard.py` dispatched `GAME_PAUSE` with payload `{"action": "toggle"}` which lacked the contract-mandated `"reason"` key required by `docs/event_contracts.md`.
- **Root Cause:** Input adapter was created in Phase A before the event contracts were formalized in Phase B.
- **Resolution:** Updated `core/input_keyboard.py` to dispatch `{"reason": "parent_key", "action": "toggle"}`. Conforms to `event_contracts.md` while preserving unpause toggle capability in `GameEngine`.
- **Status:** **Resolved & Verified**