# Module 10 Specification

## Game Plan Section
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

## Use Case Catalogue
Module 10 use cases not found in catalogue.
