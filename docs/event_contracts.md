# Event Payload Contracts

**Status:** Approved for Phase B (Modules 4–8)
**Reference:** docs/full_game_plan.md Section 3.3 and core/events.py

Every event dispatched across the Event Bus carries an immutable contract:
Event(name: str, payload: dict, source: str, timestamp: float)

Below are the payload schemas for events used in Phase B. All keys are strictly named and typed.

---

## 1. Player Actions (Published by Input Adapter & Action Detector)

### JUMP
- Published by: input_keyboard, action_detector
- Subscribers: game_engine, audio, display
- Payload: {}

### DUCK / STAND
- Published by: input_keyboard, action_detector
- Subscribers: game_engine, display
- Payload: {}

### LEAN_LEFT / LEAN_RIGHT / LEAN_CENTER
- Published by: input_keyboard, action_detector
- Subscribers: game_engine, display
- Payload: {}

---

## 2. Game Flow & State Machine

### STATE_CHANGED
- Published by: game_engine
- Subscribers: display, audio, input_keyboard
- Payload:
  {
    "old_state": "MENU",
    "new_state": "PLAYING"
  }
  (Allowed states: MENU, PROFILE_SELECT, CALIBRATION, COUNTDOWN, PLAYING, PAUSED, GAME_OVER, RESULTS)

### COUNTDOWN_TICK
- Published by: game_engine
- Subscribers: display, audio
- Payload:
  {
    "count": 3
  }
  (count: 3, 2, 1, 0 where 0 = "GO!")

### GAME_PAUSE / GAME_RESUME
- Published by: game_engine, input_keyboard
- Subscribers: display, audio, camera_manager
- Payload:
  {
    "reason": "parent_key"
  }
  (reason: "parent_key", "out_of_zone", "focus_loss", "hdmi_disconnect")

### GAME_OVER (CRITICAL EVENT)
- Published by: game_engine
- Subscribers: display, audio, profile_manager
- Payload:
  {
    "final_score": 1250,
    "obstacles_cleared": 42,
    "longest_streak": 8,
    "run_duration_sec": 145.2
  }

---

## 3. Gameplay Metrics & HUD (Consumed by Display and Audio)

### HEALTH_CHANGED
- Published by: mechanics
- Subscribers: display (HUD & low-health bar), audio (low-health alert, hit SFX)
- Payload:
  {
    "current": 80,
    "max": 100,
    "delta": -20,
    "is_low": false
  }
  (is_low is true when current <= 25, triggering UC 04.06 red bar)

### SCORE_CHANGED
- Published by: mechanics
- Subscribers: display (HUD score animation)
- Payload:
  {
    "score": 450,
    "delta": 50
  }

### SPEED_CHANGED
- Published by: mechanics, game_engine
- Subscribers: display (scrolling world & speedometer)
- Payload:
  {
    "current_speed": 1.25,
    "is_capped": false
  }

### STREAK_CHANGED
- Published by: mechanics
- Subscribers: display (streak counter), audio
- Payload:
  {
    "streak": 5,
    "multiplier": 1.5
  }

### OBSTACLE_HIT
- Published by: mechanics
- Subscribers: display (screen hit flash UC 04.11), audio (hit SFX)
- Payload:
  {
    "obstacle_type": "low_hurdle"
  }
  (obstacle_type: "low_hurdle", "high_bar", "lane_barrier")

### OBSTACLE_CLEARED
- Published by: mechanics
- Subscribers: display, audio
- Payload:
  {
    "obstacle_type": "low_hurdle",
    "points": 50
  }

### POWERUP_COLLECTED
- Published by: mechanics
- Subscribers: display (HUD power-up timer icon), audio (pickup SFX)
- Payload:
  {
    "powerup_type": "shield",
    "duration_sec": 10.0
  }
  (powerup_type: "shield", "slow_down", "double_points", "health_refill")

### POWERUP_EXPIRED
- Published by: mechanics
- Subscribers: display (remove HUD icon), audio
- Payload:
  {
    "powerup_type": "shield"
  }

---

## 4. System & Diagnostics

### DEBUG_TOGGLED
- Published by: input_keyboard (Ctrl+F3)
- Subscribers: display, debug_tools
- Payload: {}