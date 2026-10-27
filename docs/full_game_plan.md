# Kids Motion Game
## Requirements, Hardware and Module Plan

A camera-tracked, full-body interactive game platform for the family: kids jump, duck and lean in the room, and the game responds on the TV with score, health, power-ups and sound. Built as reusable modules so every new game reuses most of what already exists.

- **Document status:** Draft for review (discussion stage, no code yet)
- **Purpose:** Agree requirements, hardware, module list and build sequence before writing use cases
- **Next document:** Full use-case catalogue: every success, failure and edge case per module
- **Tech baseline:** Python and VS Code on a ThinkPad (i5 12th gen, 8 GB RAM); OpenCV, MediaPipe, pygame

---

## Part 1: Requirements

### 1.1 Vision
Turn a normal room into a game console. A child stands on marked floor tiles in front of the TV. A camera watches the child's body. When the child jumps, ducks or leans, the on-screen character does the same. The TV shows the road, obstacles, power-ups, score and a health bar, and the TV speakers play sound effects. The same platform later runs many different games (runner, floor is lava, balloon pop, freeze dance) and finally moves the play surface from the TV to a projected floor.

### 1.2 Goals
- Play a runner-style game with the whole body: jump over obstacles, duck under others, lean to change lanes.
- Reward success with points, power-ups and speed increases; punish contact with health loss and sound.
- Recognise each child, remember their body measurements and avatar, and use the same profile in every game.
- Make adding a new game cheap: a new game should mostly be new rules and art, not new plumbing.
- Be safe, forgiving and fun for children first, and a good engineering project for the parent second.
- Grow in stages: TV first, then floor projection, without rewriting the core.

### 1.3 Functional requirements

#### A. Gameplay
- **FR-A1:** A scrolling world with a character, obstacles and collectibles.
- **FR-A2:** Actions: jump, duck, lean left, lean right (and later: step, hands up, pose match).
- **FR-A3:** Points for each obstacle cleared; bonus for streaks.
- **FR-A4:** Health bar that drops by a small amount on obstacle contact; game over at zero.
- **FR-A5:** Power-ups on the road (for example shield, slow-down, double points, health refill) with clear on-screen feedback and a time limit where relevant.
- **FR-A6:** Speed ramps gradually with progress, with a cap so the game stays playable.
- **FR-A7:** States: menu, profile select, calibration, countdown, playing, paused, game over, results.
- **FR-A8:** Local high scores per profile and per game.

#### B. Sound
- **FR-B1:** Distinct sounds for jump, landing, movement or running loop, obstacle hit, power-up pickup, health low, game over, menu clicks and a countdown.
- **FR-B2:** Sound plays through the TV speakers via HDMI (no extra speakers owned).
- **FR-B3:** Sound latency must be low enough that a jump sound feels simultaneous with the jump.

#### C. Body tracking and action detection
- **FR-C1:** Detect a person from a camera and extract body landmarks in real time.
- **FR-C2:** Lock on to one player; ignore other people walking through the frame.
- **FR-C3:** Detect JUMP, DUCK, LEAN_LEFT, LEAN_RIGHT reliably with smoothing to suppress jitter and false triggers.
- **FR-C4:** Use per-child thresholds (height, jump baseline) so detection is fair for a small child and an adult.
- **FR-C5:** Know the play zone (tile boundary) and react when the player steps outside it (pause or warn).
- **FR-C6:** Work with one camera; improve with two or three (front, side, laptop).

#### D. Profiles and identity
- **FR-D1:** Create a profile with a name, avatar choices and body measurements captured by the camera.
- **FR-D2:** Load a saved profile at the start of any game so the character looks and scales the same.
- **FR-D3:** Re-measure on demand, since children grow.
- **FR-D4:** One universal profile file per person, shared across all games, including per-game high scores.
- **FR-D5:** Face detection is allowed as a helper (for example to confirm someone is present and facing the camera); face recognition (automatically knowing who it is) is optional and deferred. Default selection is by choosing a name on the TV.
- **FR-D6:** Store numbers and settings, not face photos.

#### E. Setup, testing and diagnostics
- **FR-E1:** Every game must be playable with the keyboard, so games can be built and tested without cameras.
- **FR-E2:** Live debug view showing camera frame, skeleton overlay, detected events and frame rate.
- **FR-E3:** Record and replay tracking sessions to reproduce and fix detection problems.
- **FR-E4:** One configuration file for thresholds, camera assignments, display and audio settings.
- **FR-E5:** Logs that explain what happened and why when something fails.

### 1.4 Non-functional requirements

| Area | Requirement |
|---|---|
| **Latency** | Camera-to-reaction under about 150 ms for wired cameras (target); games are forgiving so up to about 250 ms is still playable. |
| **Frame rate** | Game runs at 60 FPS on the TV; tracking runs at 20 to 30 FPS independently and must never slow the game. |
| **Resources** | Must run on 8 GB RAM, integrated graphics. Game renders at 1080p even though the TV is 4K. |
| **Reliability** | Camera disconnects, tracking loss and crashes must degrade gracefully (pause, message, recover), never freeze the screen. |
| **Safety** | Short sessions, a clear zone, soft landings, no obstacles near the play area, and a pause on leaving the zone. |
| **Privacy** | No images stored by default. Profiles hold numbers and names only. Debug recordings are opt-in and kept local. |
| **Reusability** | New game requires changes only in the Mechanics Library and a new game module. |
| **Maintainability** | Modules talk only through the Event Bus and shared data structures; no module reaches into another's internals. |
| **Usability** | A child can start a game alone: walk up, pick own name, stand on the centre tile, see a countdown, play. |

### 1.5 Constraints and assumptions
- Single laptop does everything: capture, tracking, game and display.
- TV is 4K 43 inch, on a stand against a wall, connected by HDMI through the USB-C hub, used as an extended display.
- Cameras are consumer phones via webcam apps (Iriun or DroidCam) plus the laptop webcam. Phone-as-webcam quality, latency and multi-phone support must be tested early.
- Indoor lighting is reasonably even; no strong window light behind the player.
- Players are children, so unpredictable movement, differing sizes and short attention spans are normal.
- No code is written until requirements, modules and use cases are agreed.

### 1.6 Out of scope for now
- Floor projection (planned later as a new output stage).
- Apple Watch or phone motion sensors as input.
- Online play, accounts, leaderboards across devices.
- Face recognition login.
- Multi-player simultaneous tracking (designed for later; one active player first).

### 1.7 Success criteria

| Milestone | How we know it works |
|---|---|
| **M1 Keyboard game** | Family can play the runner with the keyboard: score, health, power-ups, speed ramp, sounds all working. |
| **M2 Body control** | A child jumps and the character jumps, with fewer than about 1 false trigger per minute and most real jumps detected. |
| **M3 Profiles** | A child picks their name, is measured once, and the same character and thresholds come back next day. |
| **M4 Better cameras** | Front phone camera at 9 to 10 ft gives noticeably steadier tracking than the laptop webcam. |
| **M5 Second & third game** | A new game is built mostly from existing modules in a fraction of the first game's effort. |
| **M6 Floor ready** | Output module can target a projector and calibrate to the floor without changing the games. |

---

## Part 2: Hardware

### 2.1 What you already own and its role

| Device | Specification | Role in the system |
|---|---|---|
| **Laptop** | ThinkPad, Intel i5 12th gen, 8 GB RAM, Python and VS Code installed | The brain: runs camera capture, pose tracking, game logic, audio and display. Webcam doubles as a camera. |
| **TV** | Xiaomi TV A Pro 2025, 43 inch, 4K | Main game screen and sound output. Use Game Mode. Game renders at 1080p. |
| **USB-C hub** | Selore S Global: HDMI (4K), USB-A, USB-C, LAN, serial, 3.5 mm jack | Connects TV (HDMI) and cameras (USB). Shares bandwidth, so test under load. |
| **Phone 1** | Xiaomi Poco X6 Pro (proposed) | Front camera on a tripod by the TV, portrait: main player tracking. |
| **Phone 2** | Xiaomi Poco X3 NFC (proposed) | Side camera mid-zone: jump height and landing confirmation (optional at first). |
| **Laptop webcam** | Built into the ThinkPad | Development, profile setup at close range, menu navigation, backup angle. |
| **Cables** | HDMI, many USB-C cables | HDMI laptop to TV via hub; USB-C for phones. Keep runs under about 3 m. |
| **Floor tiles** | 2 ft x 2 ft tiles | Zone marking and a real-world scale reference for measurements. |
| **Spare devices** | Galaxy Tab S9, iPhone 16 Pro, Apple Watch Series 10 | Not used initially. Possible later as extra cameras or sensors. |

### 2.2 Room layout (proposed)
- The TV stand (about 2 ft deep) is against one wall. The opposite wall is about 24 ft away, leaving about 22 ft of usable depth.
- **Play zone:** 3 tiles wide by 2 tiles deep (6 ft x 4 ft), marked with coloured tape, with a distinct centre start tile. Jump games use the centre tile; lane games use all three columns.
- **Distance:** centre of the zone about 9 to 10 ft from the TV. That keeps the 43 inch screen readable and gives the front camera room to see a whole jumping child.
- **Clearance:** about 3 ft free on each side of the zone and roughly 12 ft behind it.
- **Front camera:** on a small tripod directly below or beside the TV, portrait orientation.
- **Side camera (later):** about 8 to 10 ft to the side of the zone, mid-depth, at roughly waist to chest height.
- **Laptop:** beside the TV stand, close to the front camera so USB cables stay short.
- **Lighting:** even light on the player from the front or above; no window or bright lamp behind the player.
- **Floor:** non-slippery; socks with grip or barefoot on a safe surface; nothing breakable nearby.

### 2.3 Possible purchases (not needed to start)

| Item | Why | Rough cost (AED, verify before buying) |
|---|---|---|
| Phone tripod or stand (x2) | Stable, aimable camera mounts. Needed once phones replace the laptop webcam. | 30 to 120 each |
| Longer or better USB cable | For the side camera if it sits beyond about 3 m | 20 to 80 |
| Small speaker (wired) | Only if TV audio proves laggy or weak | 80 to 250 |
| Floor projector | Stage 2: projected road and lava on the floor | 1,000 to 2,000 for a sensible model |
| Ceiling or shelf mount | Hold the projector pointing down | 50 to 150 |
| Coloured floor tape | Zone marking | 10 to 30 |

### 2.4 Software baseline
- Python (Python 3.12 verified).
- OpenCV for camera access and image handling.
- MediaPipe for body pose (and face landmarks if we use them).
- pygame for the game window, input, sprites and audio.
- Iriun or DroidCam for phone-as-webcam. Test with one phone first, then two.
- A simple local file format (JSON) for profiles, config and recordings.

### 2.5 Known hardware risks to test first
- Whether two phones can run as webcams at once on this laptop and hub.
- USB bandwidth and heat on the hub with two cameras and HDMI together.
- Wireless phone camera latency (100 to 300 ms); prefer USB.
- Whether a portrait phone at 9 to 10 ft frames a whole child plus jump headroom.
- Whether the laptop's integrated graphics keeps 60 FPS while tracking runs.
- Whether the TV's Game Mode removes noticeable audio and video delay.

---

## Part 3: Architecture

### 3.1 Data flow
Camera Manager -> Pose Tracker -> Player Lock -> Zone and Calibration -> Action Detector -> Event Bus -> Game Engine and Game -> Display and UI, Audio Manager.
The keyboard adapter publishes the same events into the same Event Bus, so the game cannot tell whether a jump came from a key or a child.

### 3.2 Design principles
- **Events, not calls:** Modules publish and subscribe to events on the Event Bus instead of calling each other directly.
- **Separation of input and game:** The game never knows about cameras. It sees only events such as JUMP.
- **Independent loops:** Capture and tracking run at their own pace; the game loop always renders smoothly.
- **Replaceable parts:** A camera source, a tracker or a display can be swapped (phone for laptop webcam, TV for projector) without touching the rest.
- **Config over constants:** Thresholds and settings live in one file so tuning does not mean editing code.
- **Fail soft:** Every module defines what it does when its input is missing or bad.
- **Observable:** Everything important is logged and visible in the debug view.

### 3.3 Draft event catalogue

| Group | Events |
|---|---|
| **Player actions** | JUMP, LAND, DUCK, STAND, LEAN_LEFT, LEAN_RIGHT, LEAN_CENTER, HANDS_UP, STEP_LEFT, STEP_RIGHT, POSE_MATCHED |
| **Player state** | PLAYER_DETECTED, PLAYER_LOST, PLAYER_LOCKED, PLAYER_IN_ZONE, PLAYER_OUT_OF_ZONE, MULTIPLE_PEOPLE |
| **Camera** | CAMERA_CONNECTED, CAMERA_LOST, CAMERA_LOW_FPS, CAMERA_SWITCHED |
| **Game flow** | GAME_START, GAME_PAUSE, GAME_RESUME, GAME_OVER, STATE_CHANGED, COUNTDOWN_TICK |
| **Gameplay** | OBSTACLE_CLEARED, OBSTACLE_HIT, POWERUP_COLLECTED, POWERUP_EXPIRED, HEALTH_CHANGED, SCORE_CHANGED, SPEED_CHANGED, STREAK_CHANGED |
| **Profile** | PROFILE_SELECTED, PROFILE_CREATED, PROFILE_UPDATED, MEASUREMENT_STARTED, MEASUREMENT_DONE, MEASUREMENT_FAILED |
| **System** | CONFIG_LOADED, ERROR, WARNING, DEBUG_TOGGLED |

### 3.4 Core shared data (conceptual)
- **Landmarks:** a timestamped list of body points per frame, per camera.
- **Player state:** position in zone, standing baseline, current posture.
- **Profile:** name, avatar options, measurements, jump baseline, thresholds, high scores per game.
- **Game state:** current state machine state, score, health, speed, active power-ups.
- **Config:** all tunable numbers, camera mapping, display and audio settings.

---

## Part 4: Modules in Build Order

The order below is deliberate. Each phase ends with something that runs, so you get a working result early and every later step can be tested against it.

### 1. Config and Logging (Phase A: Foundation)
- **Purpose:** One place for every tunable setting and one place where every module reports what it is doing.
- **Inputs:** Settings file, command-line overrides.
- **Outputs:** Settings available to all modules; log file and console output.
- **Depends on:** Nothing.
- **Responsibilities:**
  - Load a single settings file at startup with sensible defaults when values are missing.
  - Validate values (ranges, types) and report clearly when something is wrong.
  - Provide named settings: camera assignments, thresholds, display index, audio volume, debug flags.
  - Provide logging with levels (info, warning, error) to screen and to a file.
  - Rotate or limit log files so they never fill the disk.
- **Why it is at this position:** Every later module needs settings and logs. Building it first means no module ever hard-codes a number or hides a failure, and tuning later is editing a file instead of code.
- **Main risks:** Settings sprawl if not organised by module from day one; silent defaults hiding a typo in the file.
- **Done when:** Any module can read a setting by name, a bad setting gives a clear error, and logs show up in a file with timestamps.

### 2. Event Bus (Phase A: Foundation)
- **Purpose:** The shared messenger. It defines every event, who may publish it and who may listen.
- **Inputs:** Events from any module.
- **Outputs:** Events delivered to subscribers; optional event log.
- **Depends on:** Config and Logging.
- **Responsibilities:**
  - Publish and subscribe with named events and a small data payload (timestamp, source, values).
  - Define and document the event catalogue as the contract between modules.
  - Deliver events without one slow listener blocking the others.
  - Support a debug tap that shows or records every event.
  - Guard against unknown event names and bad payloads.
- **Why it is at this position:** It is the spine of the architecture. Every other module is written against it, so it must exist and be stable before anything else is built.
- **Main risks:** Overly chatty events hurting performance; ordering problems when events arrive from different threads.
- **Done when:** A test publisher and a test subscriber exchange events reliably, including when one subscriber is slow or crashes.

### 3. Input Adapter (Keyboard) (Phase A: Foundation)
- **Purpose:** A stand-in player. It turns key presses into the same events the camera will later produce.
- **Inputs:** Keyboard state.
- **Outputs:** Player action events on the Event Bus.
- **Depends on:** Event Bus, Config.
- **Responsibilities:**
  - Map keys to events (space to jump, down to duck, left and right to lean).
  - Support press and release, so duck can be held.
  - Make the key map configurable.
  - Stay available permanently as a testing and fallback input.
- **Why it is at this position:** It lets the whole game be built and tested before any computer vision exists. It also remains a safety net: if tracking misbehaves you can still play.
- **Main risks:** Keyboard feel (instant, perfect timing) hides timing problems that cameras will later expose; later phases must test with real latency.
- **Done when:** Pressing keys produces the exact events the game will later receive from the Action Detector.

### 4. Display and UI (Phase B: Playable game with keyboard)
- **Purpose:** Everything the family sees on the TV: window, full-screen on the second display, game HUD and menus.
- **Inputs:** Game state and events.
- **Outputs:** Pixels on the TV.
- **Depends on:** Config, Event Bus.
- **Responsibilities:**
  - Open a full-screen window on the TV (extended display) at 1080p.
  - Draw the HUD: score, health bar, speed, active power-ups, streak.
  - Draw menus: main menu, profile select, pause, game over, results.
  - Draw feedback: hit flash, power-up pop, low-health warning.
  - Provide a drawing layer abstraction so a projector floor view can be added later as another output.
- **Why it is at this position:** Nothing can be judged without seeing it. Building the display early lets us design the HUD and menus while there is no tracking noise to confuse the picture.
- **Main risks:** Wrong display chosen or resolution mismatch on the 4K TV; tearing or low frame rate on integrated graphics.
- **Done when:** A full-screen window appears on the TV, runs at a steady 60 FPS and a test HUD updates from events.

### 5. Audio Manager (Phase B: Playable game with keyboard)
- **Purpose:** Plays every sound effect and music track in response to events.
- **Inputs:** Events; sound files.
- **Outputs:** Audio output on the TV.
- **Depends on:** Event Bus, Config.
- **Responsibilities:**
  - Map events to sounds (jump, land, hit, pickup, low health, game over, click, countdown).
  - Handle overlapping sounds, volume levels and mute.
  - Loop a running or background sound and stop it cleanly.
  - Preload sounds so there is no delay on first play.
  - Use the TV speakers through HDMI.
- **Why it is at this position:** Sound is half of the game feel and is cheap to add once events exist. Testing it before tracking separates audio delay from tracking delay.
- **Main risks:** TV audio latency; verify with Game Mode; sounds clipping or cutting each other off.
- **Done when:** Every mapped event plays its sound instantly, overlapping sounds mix cleanly and volume is adjustable.

### 6. Game Engine Core (Phase B: Playable game with keyboard)
- **Purpose:** The reusable heart of every game: loop, state machine, timing and difficulty ramp.
- **Inputs:** Events, config.
- **Outputs:** State changes and game ticks.
- **Depends on:** Event Bus, Display, Audio, Config.
- **Responsibilities:**
  - Run a fixed-timestep game loop independent of camera speed.
  - Manage game states (menu, profile select, calibration, countdown, playing, paused, game over, results) and legal transitions.
  - Provide timers, countdowns and a difficulty curve (speed over time or distance).
  - Handle pause and resume, including auto-pause when the player leaves the zone.
  - Expose a simple game interface that each game implements (setup, update, draw, on_event, teardown).
- **Why it is at this position:** It is the part reused by every future game, so it should be built once, cleanly, before the first game's specific rules.
- **Main risks:** Letting game-specific logic leak into the engine, which kills reuse.
- **Done when:** A blank game can move through all states, pause and resume, and a difficulty value rises smoothly over time.

### 7. Game Mechanics Library (Phase B: Playable game with keyboard)
- **Purpose:** Reusable gameplay building blocks that any game can combine.
- **Inputs:** Game state, player action events.
- **Outputs:** Gameplay events and drawable objects.
- **Depends on:** Game Engine Core, Event Bus.
- **Responsibilities:**
  - Health and damage with invulnerability frames after a hit.
  - Score, streaks and multipliers.
  - Obstacle spawning, movement, patterns and removal.
  - Collision checks with forgiving hitboxes.
  - Power-up types, pickup, duration and expiry.
  - Scrolling background and speed scaling.
  - Event emission for every outcome (cleared, hit, collected).
- **Why it is at this position:** This is where the long-term payoff sits. Games 2 and 3 should be mostly different combinations of these blocks, so they are built before the first game consumes them.
- **Main risks:** Hitboxes too strict for kids (make forgiveness a setting); spawn patterns that are impossible to clear.
- **Done when:** Blocks work together in a throwaway test scene: spawn, clear, hit, collect, ramp speed.

### 8. Game 1: Runner (Phase B: Playable game with keyboard)
- **Purpose:** The first complete game: a scrolling road, jump and duck obstacles, lane changes, power-ups, health, score and speed ramp.
- **Inputs:** Player action events from the keyboard adapter.
- **Outputs:** A complete playable game.
- **Depends on:** Modules 1 to 7.
- **Responsibilities:**
  - Define the road, character, obstacle set and power-ups.
  - Tune difficulty for children.
  - Wire events to sounds and HUD.
  - Provide a results screen with score and personal best.
- **Why it is at this position:** It proves the architecture and the fun. If the game is not fun with a keyboard, cameras will not fix it, so we find out before the hard part.
- **Main risks:** Game feels too easy or too hard; needs playtesting with the kids.
- **Done when:** MILESTONE M1: the family can play start to finish with keys.

### 9. Camera Manager (Phase C: Eyes / tracking)
- **Purpose:** Finds, opens and supervises every camera and hands frames to the rest of the system.
- **Inputs:** Camera devices, config.
- **Outputs:** Timestamped frames; camera status events.
- **Depends on:** Config, Event Bus.
- **Responsibilities:**
  - List available cameras and map them to roles (front, side, laptop) from config.
  - Open cameras at the configured resolution and frame rate.
  - Run capture in its own thread so a slow camera never freezes the game.
  - Detect disconnects and slow frames; publish camera events; attempt reconnect.
  - Provide the latest frame with a timestamp on request.
  - Start with the laptop webcam only; add phones later without changing callers.
- **Why it is at this position:** Everything in the vision chain starts with a reliable frame. Starting with the laptop webcam removes phone-app uncertainty from the first tracking work.
- **Main risks:** Camera index changes after reboot or replug; two cameras on one hub exceeding bandwidth; webcam app quirks with phones.
- **Done when:** The laptop camera streams steadily, and unplugging it produces a clear event and a clean recovery.

### 10. Debug and Replay Tools (Phase C: Eyes / tracking)
- **Purpose:** Lets us see what the tracker sees and replay problems instead of recreating them.
- **Inputs:** Frames, landmarks, events.
- **Outputs:** Overlay window; recording files.
- **Depends on:** Camera Manager, Event Bus.
- **Responsibilities:**
  - Show the camera view with skeleton overlay, zone outline and detected events.
  - Show frame rate, latency and key signals (hip height, shoulder tilt) as live graphs or numbers.
  - Record landmark data (not video by default) from a session and play it back through the Action Detector.
  - Toggle on and off with a key.
  - Allow optional video recording that is local only and off by default.
- **Why it is at this position:** Tracking problems are impossible to fix blind. Having this before the tracker means every later module is built with visibility.
- **Main risks:** Overlay slowing the system; make it lightweight and optional.
- **Done when:** A recorded jump session can be replayed and produces the same events each time.

### 11. Pose Tracker (Phase C: Eyes / tracking)
- **Purpose:** Turns a camera frame into body landmarks.
- **Inputs:** Frames.
- **Outputs:** Landmarks with confidence per frame.
- **Depends on:** Camera Manager.
- **Responsibilities:**
  - Run pose detection on frames at a steady 20 to 30 FPS.
  - Output normalised landmarks with confidence values.
  - Handle no person, partial body and low confidence.
  - Choose a model size that suits the laptop.
  - Prepare for multiple cameras, each with its own landmark stream.
- **Why it is at this position:** The Action Detector, Zone and Player Lock all need landmarks. Debug tools come first so we can see this module's output the moment it exists.
- **Main risks:** CPU load on 8 GB RAM (reduce resolution if needed); reduced accuracy on small bodies and in loose clothing; library and Python version compatibility.
- **Done when:** A person in front of the laptop produces a stable skeleton at the target frame rate.

### 12. Zone and Calibration (Phase C: Eyes / tracking)
- **Purpose:** Knows where the play zone is and how image pixels relate to real distances.
- **Inputs:** Landmarks, frames, config.
- **Outputs:** Zone geometry, scale factors, in-zone state events.
- **Depends on:** Pose Tracker, Camera Manager.
- **Responsibilities:**
  - Define the tile zone from the camera view using marked reference points or tile corners.
  - Convert pixel positions to approximate floor positions and real size using the 2 ft tiles as scale.
  - Decide whether the player is inside, at the edge, or outside the zone.
  - Save calibration per camera and per room setup.
  - Offer a simple guided calibration routine.
- **Why it is at this position:** Jump and lean thresholds only mean something once position and scale are known, so this must come before action detection.
- **Main risks:** Camera moved after calibration (detect and ask for recalibration); perspective error from a low camera angle.
- **Done when:** The system correctly reports inside, edge and outside as a child steps around the tiles.

### 13. Player Lock (Phase C: Eyes / tracking)
- **Purpose:** Chooses one person as the player and keeps tracking that person.
- **Inputs:** Landmarks (possibly several people), zone.
- **Outputs:** Single-player landmark stream; lock events.
- **Depends on:** Pose Tracker, Zone and Calibration.
- **Responsibilities:**
  - Pick the player: the person standing in the zone, nearest the centre tile, for a set time.
  - Ignore other people and objects.
  - Keep identity through brief occlusion and crossings.
  - Release the lock when the player leaves, and allow a new lock.
  - Report multiple-people situations.
- **Why it is at this position:** With kids and parents moving in a room, a wrong person controlling the game is the most visible failure. It sits right before the detector so the detector sees only the player.
- **Main risks:** Sibling stands next to the player and swaps the lock; parent walks through the zone.
- **Done when:** A second person passing the camera does not disturb the game.

### 14. Action Detector (Phase C: Eyes / tracking)
- **Purpose:** Converts the player's landmarks into game events.
- **Inputs:** Locked player landmarks, zone, profile thresholds.
- **Outputs:** Player action events.
- **Depends on:** Pose Tracker, Zone and Calibration, Player Lock, Event Bus.
- **Responsibilities:**
  - Detect JUMP and LAND from vertical motion relative to a standing baseline.
  - Detect DUCK, LEAN_LEFT, LEAN_RIGHT from body geometry.
  - Smooth signals and apply debounce so jitter does not cause false events.
  - Use per-profile thresholds when available, defaults otherwise.
  - Avoid double-firing and handle rapid sequences.
  - Publish the same events as the keyboard adapter.
- **Why it is at this position:** It is last in the vision chain because it relies on everything before it. It is the module whose results the kids actually feel.
- **Main risks:** Latency making jumps feel late; false jumps from camera noise; different children needing different thresholds.
- **Done when:** MILESTONE M2: the kid jumps, the runner jumps, with very few false triggers.

### 15. Profile Manager (Phase D: Identity / profiles)
- **Purpose:** Creates, stores, selects and updates the universal player profiles.
- **Inputs:** User choices, measurement results.
- **Outputs:** Profile data; profile events.
- **Depends on:** Config, Event Bus, Display and UI.
- **Responsibilities:**
  - Create, rename, duplicate-check and delete profiles.
  - Store name, avatar choices, measurements, jump baseline, thresholds and per-game high scores.
  - Load the selected profile and broadcast it so the game and detector use it.
  - Keep the file format versioned so old profiles survive changes.
  - Protect against corrupt files with automatic backup.
- **Why it is at this position:** Profiles are useful only once there are measurements to store and thresholds to improve, so they follow a working detector.
- **Main risks:** Profile file corruption; name collisions between siblings.
- **Done when:** A profile survives restart and the same character and thresholds are applied in the game.

### 16. Measurement Capture (Phase D: Identity / profiles)
- **Purpose:** The guided routine that measures a child and fills a new profile.
- **Inputs:** Landmarks, zone, scale, UI.
- **Outputs:** Measurements stored in the profile.
- **Depends on:** Pose Tracker, Zone and Calibration, Profile Manager, Display and UI.
- **Responsibilities:**
  - Guide the child to the start tile and a standard pose (stand tall, arms out).
  - Measure height, shoulder width, limb proportions and standing baseline using the tile scale.
  - Run a short test jump to set a personal jump baseline.
  - Optionally use face landmarks as a helper for presence and facing direction.
  - Validate quality and retry with plain instructions on failure.
  - Let the parent type in true height to improve scale.
- **Why it is at this position:** It needs a stable tracker and a place to store results, so it comes right after the Profile Manager.
- **Main risks:** Child will not stand still; camera too close or too far gives bad numbers.
- **Done when:** MILESTONE M3: measured once, recognised and tuned the next day.

### 17. Phone Cameras Integration (Phase E: Better cameras and more games)
- **Purpose:** Brings the Xiaomi phones into the Camera Manager as front and side cameras.
- **Inputs:** Phone video streams.
- **Outputs:** Multi-camera landmark streams.
- **Depends on:** Camera Manager, Pose Tracker, Action Detector.
- **Responsibilities:**
  - Register each phone as a camera source with a role.
  - Use the front phone as the primary tracker; keep the laptop webcam for setup and menus.
  - Use the side phone to confirm jump height and landing.
  - Fuse cameras: combine evidence from front and side and fall back to one if the other fails.
  - Compare latency and accuracy between cameras and record the findings.
- **Why it is at this position:** It is a quality upgrade, not a prerequisite. Everything works with one camera first, so adding phones later cannot break the base system.
- **Main risks:** Webcam app limitations with two phones; network or USB latency and bandwidth; fusion rules adding complexity.
- **Done when:** MILESTONE M4: the front phone at 9 to 10 ft is steadier than the laptop camera, and the system survives a camera dropping out.

### 18. Games 2 and 3 (Phase E: Better cameras and more games)
- **Purpose:** The real test of reusability: two more games built from the same parts.
- **Inputs:** Existing action events.
- **Outputs:** New games.
- **Depends on:** Mechanics Library, Engine, tracking chain.
- **Responsibilities:**
  - Game 2: lane switch (lean left, centre, right) using the same tracker and mechanics.
  - Game 3: freeze dance or balloon pop with hands, or the TV version of floor is lava.
  - Measure how much new code each game needed.
  - Feed lessons back into the Mechanics Library.
- **Why it is at this position:** Doing this after the first game and tracking proves the design. If it is painful, the module boundaries need adjusting.
- **Main risks:** Hidden coupling between Game 1 and the engine.
- **Done when:** MILESTONE M5: each new game takes a fraction of Game 1's effort.

### 19. Floor Projection Preparation (Phase E: Better cameras and more games)
- **Purpose:** Adds a second output target: a projector painting the road and lava on the floor.
- **Inputs:** Game state, calibrations.
- **Outputs:** Projected floor image.
- **Depends on:** Display and UI, Zone and Calibration, a projector purchase.
- **Responsibilities:**
  - Add a projector display target to Display and UI.
  - Calibrate camera to projector so objects appear where the child stands.
  - Handle keystone, brightness, shadows and dim-room requirements.
  - Keep health and score on the TV (hybrid mode).
  - Add a floor-based game mode where obstacles approach in floor space.
- **Why it is at this position:** It needs a mature tracker and a good game first. Spending money before the game is proven would be premature.
- **Main risks:** Projector brightness in a lit room; camera and projector calibration drift.
- **Done when:** MILESTONE M6: the same game runs on the floor with a one-time calibration.

---

## Part 5: Sequence Summary, Milestones and Review Checklist

### 5.1 Build sequence at a glance

| # | Module | Phase | Needs | Result you can see |
|---|---|---|---|---|
| 1 | Config and Logging | A | - | Settings file and a log |
| 2 | Event Bus | A | 1 | Test events flow |
| 3 | Input Adapter (Keyboard) | A | 1, 2 | Keys become events |
| 4 | Display and UI | B | 1, 2 | Full-screen TV window and HUD |
| 5 | Audio Manager | B | 1, 2 | Sounds on events |
| 6 | Game Engine Core | B | 1 to 5 | States, loop, difficulty |
| 7 | Game Mechanics Library | B | 2, 6 | Obstacles, health, power-ups |
| 8 | Game 1: Runner | B | 1 to 7 | M1: playable with keyboard |
| 9 | Camera Manager | C | 1, 2 | Steady laptop camera |
| 10 | Debug and Replay Tools | C | 2, 9 | Skeleton overlay, replays |
| 11 | Pose Tracker | C | 9 | Live skeleton |
| 12 | Zone and Calibration | C | 9, 11 | Inside or outside the tiles |
| 13 | Player Lock | C | 11, 12 | One player only |
| 14 | Action Detector | C | 11 to 13 | M2: jump controls the game |
| 15 | Profile Manager | D | 1, 2, 4 | Saved profiles |
| 16 | Measurement Capture | D | 11, 12, 15 | M3: measured, remembered |
| 17 | Phone Cameras Integration | E | 9, 11, 14 | M4: better tracking |
| 18 | Games 2 and 3 | E | 6, 7, 14 | M5: reuse proven |
| 19 | Floor Projection Prep | E | 4, 12 | M6: floor-ready |

### 5.2 Why this order, in one paragraph
Foundation first so nothing is hard-coded. Then a full game with the keyboard, so fun and architecture are proven without computer vision. Then the vision chain, in the order a frame travels (camera, debug view, pose, zone, player lock, actions), because each stage needs the one before it. Then identity, which needs a working detector to have anything to store. Finally the upgrades (phones, more games, floor), which are improvements on a system that already works and cannot break it.

### 5.3 Review checklist
- Are the 19 modules the right split, or should any be merged or split further?
- Is the keyboard-first order acceptable, or do you want tracking work to start earlier?
- Camera roles: front phone as main tracker, side phone for jump height, laptop for setup and menus. Agree?
- Play zone: 3 tiles wide by 2 deep, centre tile as start. Agree, or prefer a different size?
- Profiles: store numbers and avatar choices only, no face photos, choose name on the TV rather than face recognition. Agree?
- Is one active player at a time acceptable for the first versions (two players later)?
- Sessions and safety rules: should the game enforce a time limit or break reminder?
- Which game should be Game 2 and Game 3?
- Do you want a parent mode (settings, recalibration, profile management) protected from the kids?
- Any missing requirement, module or sequence you want added?