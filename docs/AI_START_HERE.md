# AI START HERE - Kids Motion Game

> **Any AI model (Claude, Gemini, GPT, others) must read this file FIRST, completely, before answering anything or writing any code.**
> This file tells you what to read, in what order, what you must never do, and how to continue exactly where the previous AI stopped.

---

## 1. What this project is (one paragraph)

A camera-tracked, full-body interactive game for the owner's children. A child stands on marked floor tiles in front of a TV. A camera tracks the body; jump, duck and lean become game events. The game runs on the TV (score, health bar, power-ups, sounds). The system is built as 19 reusable modules so new games reuse most parts. Later stage: floor projection. The full detail is in `docs/full_game_plan.md`.

## 2. The person you are working with

- Name: Nasir. Working on a ThinkPad (i5 12th gen, 8 GB RAM), **Windows 11, PowerShell, VS Code**.
- Project folder: `D:\kids_game`. Git repo (private): `https://github.com/nasiriqbal49/kids_game`, branch `main`.
- Python: **3.12** in a virtual environment `.venv` (activate with `.\.venv\Scripts\Activate.ps1`). Do not suggest Python 3.14 (MediaPipe may not support it).
- Experienced data/analytics engineer and comfortable with Python, but wants **slow, small, testable steps**. Mixes English and Urdu; reply in the language he writes in.
- **You cannot see his private repo.** Never claim you read files you were not given. Ask him to paste the file, attach it, or run `git pull origin main`, `git log --oneline`, `git ls-files`, or send a gitingest export or `git archive -o kids_game.zip HEAD`.

## 3. Reading order (do this before working)

Read in exactly this order. Do not skip. Do not skim.

1. `docs/AI_START_HERE.md` (this file).
2. `docs/master_ai_handoff.md` - current state and the NEXT immediate step.
3. `docs/progress_tracker.md` - per-module and per-use-case status. **Treat "Pass" claims as claims, not facts, until verified (see section 6).**
3A. `docs/git_commits.md` — chronological log of recent commits and exact files touched.
4. `docs/issues_and_resolutions.md` - past problems; do not repeat them. Append new ones.
5. `docs/project_directory_structure.md` - where files live and where they will go.
6. `docs/full_game_plan.md` - requirements, hardware, architecture, all 19 modules with purpose, responsibilities, why-in-this-order, risks, "done when". **Read the section of the module you are about to build in full.**
7. `docs/use_case_catalogue.md` - every use case with ID, priority, success criteria, failure/edge condition, handling. **Read every use case of the module you are about to build.** These are the acceptance tests.
8. The code in `core/` (and other folders) that the next module depends on, and its tests in `tests/`.
9. The original PDF plan was removed from the repo by the owner. `docs/full_game_plan.md` and `docs/use_case_catalogue.md` are now the only source of truth. If they look inconsistent or incomplete, stop and ask the owner; never "repair" them from memory.

After reading, state in two or three sentences: which module is next, which use cases it must satisfy, and what you verified. Then begin.

## 3A. NON-NEGOTIABLE RULES (read before touching anything)

### 3.1 Never degrade the documents
- **Never shorten, summarise, reword, reorder, merge, redact or "clean up" `full_game_plan.md` or `use_case_catalogue.md`.** They are frozen reference documents. Every use case ID (for example 14.03) and its text must stay exactly as is.
- If a requirement or use case must change, **ask the owner first**, then record it in a clearly marked `## Change Log` section at the end of that file (date, what changed, why, who approved). Never edit the original text silently.
- Do not delete any file or section of the docs. Append, do not overwrite.
- When updating any doc, change only what is needed. Never re-output a whole doc to make a small edit.

### 3.2 Architecture rules
1. **Events, not calls.** Modules never call each other's internals. They publish and subscribe on the Event Bus (`core/event_bus.py`).
2. **Events must exist in the catalogue** (`core/events.py`). Add new events to the plan's event catalogue (with owner approval) before using them.
3. **Cross-thread rule:** background threads (camera, tracking, latency simulation) must use `bus.post(event)`. Only the main thread calls `bus.publish()` or `bus.drain()`.
4. **The game never knows about cameras.** It sees only events (JUMP, DUCK, ...). The keyboard adapter and the camera pipeline emit the same events.
5. **Decoupled loops:** camera/tracking runs in its own thread (about 30 FPS); the game renders at a steady 60 FPS and is never slowed by tracking.
6. **Config over constants.** No hard-coded thresholds; they live in `config.json` through `core/config.py`.
7. **Fail soft.** No module may crash the game. Every failure has a defined behaviour: log it, tell the parent, degrade safely, never freeze the TV.
8. **Privacy:** no images stored by default; profiles hold numbers and names only.
9. Game renders at 1080p even though the TV is 4K.

### 3.3 Working style rules (the owner's explicit wishes)
- **Small steps.** One small, testable piece at a time. Never dump multiple modules or large multi-file changes in one message.
- **One question per message at most.** Do not ask what you can find in the docs.
- **Exact instructions for Windows PowerShell + VS Code.** Say which file, which line, what to paste. When changing existing code, show the **complete replacement block** (for example a whole method), and state its indentation. Do not give vague "add this near the try" instructions.
- After each step, **ask the owner to run the tests and paste the output**, then read it before moving on.
- Explain briefly *why*, in plain language. No long lectures.
- Do not re-explain or re-create modules already marked DONE.

### 3.4 Honesty rules (these exist because a previous AI over-claimed)
- **Never write "Pass", "verified", "100% complete" or any test count unless it came from actual test output pasted by the owner.** State the real number of tests run.
- A use case counts as verified **only if a test with that use-case ID exists, runs, and passes**.
- A module is **DONE only when every P1 and P2 use case in the catalogue for that module has a passing test** (P3 may be deferred, but the deferral must be listed explicitly in the tracker).
- If you are unsure, or something looks inconsistent, say so and ask. Do not paper over it.
- If you find a bug in earlier code, report it plainly, propose the fix as a small step, and log it in `issues_and_resolutions.md`.

## 4. Test conventions

- Test framework: `unittest`. Run all tests from the project root, with the venv active:
  `python -m unittest discover -s tests -t . -v`
- One test file per module in `tests/` named `test_<module>.py`.
- **Test method names carry the use-case ID:** `test_14_03_walking_does_not_jump`. Docstring starts with `UC 14.03:`.
- Every test method must be **inside a class and indented correctly**; an unindented method silently never runs. After adding tests, confirm the total test count increased by the number you added.
- Tests must not touch the real `config.json`, `profiles/` or `logs/`; use temporary directories.
- Camera-dependent logic must be testable without a camera (recorded landmark files, fake frames).

## 5. Git discipline

- After each working, tested step: `git add .`, `git commit -m "<module>: <what and which use cases>"`, `git push`.
- Never commit `.venv/`, `logs/`, `recordings/`, `profiles/`, `*.bad` (already in `.gitignore`).
- Commit messages must name the module and use-case IDs, for example `Module 2: fix thread safety (02.04, 02.07), consecutive failure count (02.03)`.
- Do not commit with failing tests unless the commit message says so and the tracker records it.

## 6. How to resume safely (when you take over from another AI)

1. Read everything in section 3's reading order.
2. Ask the owner to run:
   ```
   git pull origin main
   git status
   git log --oneline -15
   python -m unittest discover -s tests -t . -v
   ```
3. Compare the **actual** passing tests with the tracker. For each module, list use cases that are claimed but have no test. Report any mismatch plainly before building anything new.
4. Fix mismatches in small steps. Then continue with the first module that is not truly DONE.
5. If the previous AI left unfinished work (half-written files, failing tests), finish or revert it first, and log it.

## 7. How to end every working session (mandatory)

Update these three files with **minimal, append-style edits** and tell the owner what to commit:

1. `docs/progress_tracker.md` - change status only for use cases that have a passing test; update "Last Updated" with the date; add the real test count.
2. `docs/master_ai_handoff.md` - rewrite only section "Current Exact State and Next Immediate Step": what is done (with real test counts), what is half-done, what is next, any open known issues.
3. `docs/issues_and_resolutions.md` - append any new issue: symptom, root cause, resolution, status.

Also run:
- `python tools/show_tree.py --update` to refresh `docs/project_directory_structure.md`.
- `python tools/update_git_commits.py` to refresh `docs/git_commits.md`.

## 8. Module build protocol (repeat for each module, in the order of the plan)

1. Read the module section in the plan and every use case in the catalogue.
2. Propose the file layout and public interface in a few lines; get a quick OK.
3. Write the smallest working slice first; test it; commit.
4. Add the remaining use cases one or two at a time, each with a test carrying its ID.
5. Check failure and edge handling, not just the happy path.
6. When all P1 and P2 use cases pass, update the three tracking docs and commit.
7. Only then start the next module.

Build order (do not reorder without owner approval): 1 Config and Logging, 2 Event Bus, 3 Keyboard Input, 4 Display and UI, 5 Audio, 6 Game Engine Core, 7 Mechanics Library, 8 Game 1 Runner (Milestone M1), 9 Camera Manager, 10 Debug and Replay, 11 Pose Tracker, 12 Zone and Calibration, 13 Player Lock, 14 Action Detector (M2), 15 Profile Manager, 16 Measurement Capture (M3), 17 Phone Cameras (M4), 18 Games 2 and 3 (M5), 19 Floor Projection Prep (M6).

## 9. Known open items (also tracked in the handoff and tracker files)

Phase A cleanup (A1 to A7) is complete as of 2026-10-28, including the event payload contracts in `docs/event_contracts.md`. The live list of gaps (G1 to G10) is in `docs/progress_tracker.md`; keep it current.

Lessons from independent reviews (apply them every time):
- A test that fakes its input proves nothing unless the fake matches what the real system sends (see issue #013).
- A "Pass" backed only by a constants check, a flag, or a helper function that nothing uses is **Partial**, not Pass (see issue #015).
- One component must own each shared resource. The main loop owns the pygame event pump; no module may consume events that belong to another (see issue #014).
- After adding tests, confirm the total count rose by the number added, and check that new files in `docs/` are not empty.

## 10. Things you must not do

- Do not rewrite or re-explain finished modules.
- Do not shorten, summarise, or redact any doc, use case, or requirement.
- Do not skip tests, or mark use cases Pass without a test.
- Do not change the module order, event names, or architecture without owner approval.
- Do not add dependencies without saying why and getting an OK.
- Do not write code that touches hardware (cameras, display) without a keyboard or fake-input fallback.
- Do not give instructions for macOS/Linux; the owner is on Windows 11 PowerShell.
- Do not assume you can access the private GitHub repo.
