import math
import time
import pygame
from typing import Dict, List, Optional, Tuple, Any
from core.events import EventType
from vision.pose_tracker import PoseResult

# Master Control Matrix mapping Gestures -> Hardware Keys -> Web Games
MASTER_CONTROL_MATRIX = [
    ("Air Mouse Move", "Point right index finger", "Windows Mouse Cursor", "All Web & PC Games", "Touchless cursor movement"),
    ("Air Mouse Click", "Quick pinch (Thumb + Index)", "Left Mouse Click", "All Menus & Replay", "Start game, select level, Play Again"),
    ("Air Mouse Drag", "Hold pinch while moving", "Left Mouse Hold & Drag", "Puzzle & Card Games", "Drag items, sliders, and windows"),
    ("Air Mouse Right-Click", "Thumb touches Pinky", "Right Mouse Click", "PC & Strategy Games", "Open context menus & secondary actions"),
    ("Air Mouse Scroll", "Left hand: Point UP or DOWN", "Mouse Scroll Wheel", "Web Pages & Catalogs", "Scroll game catalogs & pages smoothly"),
    ("Real Jump", "Leap in the air", "Spacebar / Up Arrow", "Subway Surfers, Temple Run 2", "Jump over trains, roots, pits"),
    ("Real Crouch", "Duck low / crouch", "Down Arrow", "Subway Surfers, Temple Run 2", "Slide under overhead barriers"),
    ("Body Lean", "Tilt body Left / Right", "Left / Right Arrow", "Subway Surfers, Slope 3D", "Slalom between lanes"),
    ("Steering Wheel", "Hold plate/wheel & rotate", "Left / Right Arrow", "Madalin Stunt Cars, Drift Hunters", "Steer cars left and right (Continuous Hold)"),
    ("Nerf Gun Recoil", "Aim toy gun, upward jerk", "Left Mouse Click + Space", "Zombie Derby, Stupid Zombies", "Fire weapon / shoot lasers"),
    ("Boxing Punch", "Punch fist forward", "F key / Z key", "Iron Snout, Stickman Fighter", "Punch enemies & smash crates"),
    ("Karate Kick", "Kick leg forward", "K key / X key", "Iron Snout, Fighting games", "High kick enemies"),
    ("Chicken Flap", "Flap elbows like wings", "W key", "Flappy Dunk, Wing Gliders", "Glide in mid-air"),
    ("Flamingo Balance", "Lift 1 foot for 1 second", "L key", "Balance Challenges, Yoga", "Unlock rainbow bonus coins")
]

TUTORIAL_LESSONS = [
    {
        "id": "AIR_MOUSE",
        "title": "AIR MOUSE (TOUCHLESS HAND CONTROLLER)",
        "toy": "Your Right Hand (and Left Hand to Scroll)",
        "mode": "SEATED DESK or COUCH (2 to 8 ft)",
        "how": "Point your right index to move cursor. Pinch thumb+index to Click or Drag. Touch thumb+pinky for Right-Click. Left index UP/DOWN to Scroll!",
        "action": "AIR_MOUSE",
        "keys": "Mouse Move, Left Click, Drag, Right Click, Scroll",
        "games": "Poki, CrazyGames, Temple Run 2, Subway Surfers (Play Again & Menus)"
    },
    {
        "id": "STEERING",
        "title": "STEERING WHEEL (CARS & KARTS)",
        "toy": "Paper Plate, Frisbee, or Toy Wheel",
        "mode": "COUCH / SEATED (4 to 6 ft from TV)",
        "how": "Hold plate at 9 and 3 o'clock. Rotate left or right like a real racecar driver! (Continuous hold)",
        "action": "STEER",
        "keys": "Left / Right Arrow (Held while turned)",
        "games": "Madalin Stunt Cars 2, Drift Hunters, Zombie Derby"
    },
    {
        "id": "JUMP",
        "title": "JUMP OVER HURDLES",
        "toy": "Your Body",
        "mode": "STANDING (8 to 10 ft from TV)",
        "how": "Bend your knees and jump up in the air! Leaps over hurdles and pits.",
        "action": "JUMP",
        "keys": "Spacebar / Up Arrow",
        "games": "Subway Surfers, Temple Run 2, Parkour Run"
    },
    {
        "id": "DUCK",
        "title": "DUCK & SLIDE",
        "toy": "Your Body",
        "mode": "STANDING (8 to 10 ft from TV)",
        "how": "Crouch down low to slide under high overhead bars.",
        "action": "DUCK",
        "keys": "Down Arrow",
        "games": "Subway Surfers, Temple Run 2"
    },
    {
        "id": "NERF_GUN",
        "title": "NERF / TOY GUN SHOOTING",
        "toy": "Toy Nerf Gun, Water Gun, or Two Hands",
        "mode": "COUCH / SEATED (4 to 6 ft from TV)",
        "how": "Hold toy gun pointing at screen. Pull trigger with upward recoil jerk to fire!",
        "action": "SHOOT",
        "keys": "Left Click / Spacebar",
        "games": "Zombie Derby, Stupid Zombies, Venge.io"
    },
    {
        "id": "LEAN_LEFT",
        "title": "LEAN LEFT",
        "toy": "Your Body",
        "mode": "SEATED or STANDING",
        "how": "Tilt your upper body to the left, then return to center.",
        "action": "LEAN_LEFT",
        "keys": "Left Arrow",
        "games": "Subway Surfers, Slope 3D"
    },
    {
        "id": "LEAN_RIGHT",
        "title": "LEAN RIGHT",
        "toy": "Your Body",
        "mode": "SEATED or STANDING",
        "how": "Tilt your upper body to the right, then return to center.",
        "action": "LEAN_RIGHT",
        "keys": "Right Arrow",
        "games": "Subway Surfers, Slope 3D"
    },
    {
        "id": "PUNCH",
        "title": "BOXING PUNCH",
        "toy": "Your Fists / Boxing Gloves",
        "mode": "STANDING or SEATED",
        "how": "Punch fist straight forward towards the screen to smash wooden crates!",
        "action": "PUNCH",
        "keys": "F key / Z key",
        "games": "Iron Snout, Stickman Fighter, Boxing Stars"
    },
    {
        "id": "CHICKEN_FLAP",
        "title": "CHICKEN FLAP (WINGS GLIDE)",
        "toy": "Your Arms & Elbows",
        "mode": "STANDING (8 to 10 ft from TV)",
        "how": "Flap elbows rapidly up and down like a chicken to glide over huge pits!",
        "action": "CHICKEN_FLAP",
        "keys": "W key",
        "games": "Flappy Dunk, Wing Gliders, Jetpack"
    },
    {
        "id": "FLAMINGO",
        "title": "FLAMINGO 1-LEG BALANCE",
        "toy": "Your Leg",
        "mode": "STANDING (8 to 10 ft from TV)",
        "how": "Lift one foot off the floor and balance for 1 second to unlock rainbow coins!",
        "action": "FLAMINGO_BALANCE",
        "keys": "L key",
        "games": "Balance Challenges, Yoga Games"
    }
]


class TutorialAcademy:
    """
    Interactive On-Screen Tutorial & Motion Academy.
    Features animated demonstrations, live match accuracy (0-100%),
    and the [Tab] Universal Web Game Controls Cheat Sheet.
    """

    def __init__(self):
        self.selected_lesson_idx: int = 0
        self.verified_lessons: Dict[str, bool] = {}
        self.show_cheat_sheet: bool = False

    def toggle_cheat_sheet(self) -> None:
        self.show_cheat_sheet = not self.show_cheat_sheet

    def get_current_lesson(self) -> Dict[str, Any]:
        return TUTORIAL_LESSONS[self.selected_lesson_idx]

    def next_lesson(self) -> None:
        self.selected_lesson_idx = (self.selected_lesson_idx + 1) % len(TUTORIAL_LESSONS)

    def prev_lesson(self) -> None:
        self.selected_lesson_idx = (self.selected_lesson_idx - 1) % len(TUTORIAL_LESSONS)

    @staticmethod
    def evaluate_camera_framing(pose: Optional[PoseResult], mode: str) -> Tuple[str, str, Tuple[int, int, int]]:
        if not pose or not pose.has_person or not pose.landmarks:
            return "NO PLAYER DETECTED", "Step in front of the camera so we can see you!", (231, 76, 60)

        lms = pose.landmarks
        nose = lms.get("nose")
        l_ankle = lms.get("left_ankle")
        r_ankle = lms.get("right_ankle")

        if not nose:
            return "HEAD OUT OF FRAME", "Tilt camera slightly up or step back!", (231, 76, 60)

        if nose.y < 0.06:
            return "HEAD TOO CLOSE TO TOP", "Step back or tilt camera up!", (231, 76, 60)

        if "STANDING" in mode:
            if pose.is_partial or not (l_ankle or r_ankle):
                return "FEET CUT OFF AT BOTTOM", "Tilt camera down or step back to 8-10 ft!", (241, 196, 15)
            ankle_y = (l_ankle.y if l_ankle else r_ankle.y)
            span = abs(ankle_y - nose.y)
            if span < 0.25:
                return "TOO FAR AWAY (> 12 FT)", "Step closer to the 8-10 ft marker!", (241, 196, 15)
            elif span > 0.85:
                return "TOO CLOSE (< 6 FT)", "Step back to 8-10 ft for jumping!", (241, 196, 15)
            else:
                return "PERFECT STANDING ZONE!", "Optimal ~8.5 ft! Mark your floor tape here!", (46, 204, 113)
        else:
            return "PERFECT DESK / COUCH ZONE!", "Optimal 2 to 6 ft! Ready for mouse & driving!", (52, 152, 219)

    def calculate_match_percentage(self, lesson_id: str, last_action: str,
                                   pose: Optional[PoseResult]) -> int:
        if not pose or not pose.has_person or not pose.landmarks:
            return 0

        lms = pose.landmarks
        r_wrist = lms.get("right_wrist")
        r_index = lms.get("right_index")

        # Look up target action by lesson_id rather than assuming selected index
        lesson = next((l for l in TUTORIAL_LESSONS if l["id"] == lesson_id), None)
        target_action = lesson["action"] if lesson else TUTORIAL_LESSONS[self.selected_lesson_idx]["action"]

        if last_action and (target_action in last_action or last_action in target_action):
            return 100

        if lesson_id == "AIR_MOUSE":
            if r_wrist and r_index and r_wrist.visibility > 0.4 and r_index.visibility > 0.4:
                return 100 if last_action == "AIR_MOUSE" else 85
            return 20

        elif lesson_id == "STEERING":
            l_wrist = lms.get("left_wrist")
            if l_wrist and r_wrist:
                tilt = abs(l_wrist.y - r_wrist.y)
                if tilt > 0.075:
                    return 100
                elif abs(l_wrist.x - r_wrist.x) > 0.12:
                    return 50
            return 20

        elif lesson_id == "NERF_GUN":
            l_wrist = lms.get("left_wrist")
            if l_wrist and r_wrist:
                dist = abs(l_wrist.x - r_wrist.x)
                if dist < 0.15:
                    return 75 if "SHOOT" in last_action else 50
                return 25

        elif lesson_id == "FLAMINGO":
            l_ankle = lms.get("left_ankle")
            r_ankle = lms.get("right_ankle")
            if l_ankle and r_ankle:
                split = abs(l_ankle.y - r_ankle.y)
                if split > 0.08:
                    return 85
                elif split > 0.04:
                    return 50
            return 15

        elif lesson_id == "CHICKEN_FLAP":
            l_elbow = lms.get("left_elbow")
            r_elbow = lms.get("right_elbow")
            if l_elbow and r_elbow and abs(l_elbow.x - r_elbow.x) > 0.25:
                return 60
            return 20

        return 10

    def draw(self, surface: pygame.Surface, last_action: str = "",
             pose: Optional[PoseResult] = None) -> None:
        """Renders Tutorial Academy or the Master Controls Matrix."""
        if self.show_cheat_sheet:
            self._draw_cheat_sheet(surface)
            return

        sw = surface.get_width()
        sh = surface.get_height()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 14, 26, 245))
        surface.blit(overlay, (0, 0))

        font_title = pygame.font.Font(None, 48)
        font_header = pygame.font.Font(None, 32)
        font_body = pygame.font.Font(None, 24)
        font_desc = pygame.font.Font(None, 20)

        title = font_title.render("MOTION ACADEMY & GESTURE TUTORIAL", True, (241, 196, 15))
        surface.blit(title, (sw // 2 - title.get_width() // 2, 30))

        sub = font_desc.render("[Left / Right] Browse Lessons  |  [Tab] View Full Key Cheat Sheet  |  [Esc] Menu", True, (0, 255, 200))
        surface.blit(sub, (sw // 2 - sub.get_width() // 2, 80))

        card = self.get_current_lesson()

        # Left Panel: Text & Instructions
        panel_x, panel_y, panel_w, panel_h = 60, 120, int(sw * 0.52), 480
        pygame.draw.rect(surface, (20, 26, 42), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(surface, (52, 152, 219), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        t_surf = font_header.render(f"LESSON {self.selected_lesson_idx + 1}/{len(TUTORIAL_LESSONS)}: {card['title']}", True, (255, 255, 255))
        surface.blit(t_surf, (panel_x + 25, panel_y + 20))

        toy_label = font_body.render(f"EQUIPMENT: {card['toy']}", True, (0, 255, 200))
        surface.blit(toy_label, (panel_x + 25, panel_y + 65))

        mode_label = font_body.render(f"SETUP: {card['mode']}", True, (241, 196, 15))
        surface.blit(mode_label, (panel_x + 25, panel_y + 105))

        how_label = font_body.render("HOW TO DO IT:", True, (255, 255, 255))
        surface.blit(how_label, (panel_x + 25, panel_y + 145))
        how_val = font_desc.render(card["how"], True, (210, 225, 240))
        surface.blit(how_val, (panel_x + 25, panel_y + 175))

        key_label = font_desc.render(f"Signals Sent: [{card['keys']}]", True, (241, 196, 15))
        surface.blit(key_label, (panel_x + 25, panel_y + 230))

        games_label = font_desc.render(f"Web Games: {card['games']}", True, (0, 255, 200))
        surface.blit(games_label, (panel_x + 25, panel_y + 265))

        # Live Real-Time Match Percentage Bar
        match_pct = self.calculate_match_percentage(card["id"], last_action, pose)
        if match_pct >= 80:
            self.verified_lessons[card["id"]] = True

        bar_x, bar_y, bar_w, bar_h = panel_x + 25, panel_y + 320, panel_w - 50, 36
        pygame.draw.rect(surface, (30, 35, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        fill_w = int(bar_w * (match_pct / 100.0))
        fill_col = (46, 204, 113) if match_pct >= 75 else ((241, 196, 15) if match_pct >= 40 else (231, 76, 60))
        pygame.draw.rect(surface, fill_col, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)

        pct_txt = font_body.render(f"LIVE GESTURE ACCURACY: {match_pct}%", True, (255, 255, 255))
        surface.blit(pct_txt, (bar_x + 15, bar_y + 7))

        is_done = self.verified_lessons.get(card["id"], False)
        status_msg = "MASTERED! YOU DID IT!" if is_done else f"IMITATE THE STICKMAN! (Detected: {last_action or 'Waiting...'})"
        msg_col = (46, 204, 113) if is_done else (241, 196, 15)
        msg_surf = font_header.render(status_msg, True, msg_col)
        surface.blit(msg_surf, (panel_x + 25, panel_y + 380))

        # Right Panel: Animated Cartoon Figure
        anim_x = panel_x + panel_w + 30
        anim_y = panel_y
        anim_w = sw - anim_x - 60
        anim_h = panel_h

        pygame.draw.rect(surface, (18, 22, 34), (anim_x, anim_y, anim_w, anim_h), border_radius=10)
        pygame.draw.rect(surface, (241, 196, 15), (anim_x, anim_y, anim_w, anim_h), 2, border_radius=10)

        fig_title = font_body.render("ANIMATED DEMONSTRATION", True, (241, 196, 15))
        surface.blit(fig_title, (anim_x + anim_w // 2 - fig_title.get_width() // 2, anim_y + 15))

        self._draw_animated_stickman(surface, card["id"], anim_x + anim_w // 2, anim_y + 240)

        # Bottom Bar: Live Distance & Camera Framing Advisor
        stat_tag, advice_msg, badge_color = self.evaluate_camera_framing(pose, card["mode"])
        bot_bar_y = sh - 110
        bot_rect = (sw // 2 - 450, bot_bar_y, 900, 65)

        pygame.draw.rect(surface, (20, 24, 38), bot_rect, border_radius=8)
        pygame.draw.rect(surface, badge_color, bot_rect, 3, border_radius=8)

        tag_surf = font_header.render(f"[ {stat_tag} ]", True, badge_color)
        adv_surf = font_desc.render(advice_msg, True, (255, 255, 255))
        surface.blit(tag_surf, (bot_rect[0] + 25, bot_rect[1] + 10))
        surface.blit(adv_surf, (bot_rect[0] + 25, bot_rect[1] + 38))

    def _draw_cheat_sheet(self, surface: pygame.Surface) -> None:
        """Draws the Master Control Matrix table."""
        sw = surface.get_width()
        sh = surface.get_height()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((8, 12, 22, 250))
        surface.blit(overlay, (0, 0))

        font_title = pygame.font.Font(None, 44)
        font_header = pygame.font.Font(None, 22)
        font_row = pygame.font.Font(None, 20)

        title = font_title.render("UNIVERSAL MOTION CONTROLLER - MASTER CHEAT SHEET", True, (0, 255, 200))
        surface.blit(title, (sw // 2 - title.get_width() // 2, 20))

        sub = font_header.render("Controls Poki, CrazyGames & PC Games!  |  [Tab] Return to Lessons", True, (241, 196, 15))
        surface.blit(sub, (sw // 2 - sub.get_width() // 2, 65))

        table_x, start_y = 50, 105
        col_widths = [190, 250, 220, 330, 290]
        headers = ["GESTURE / ACTION", "HOW TO DO IT", "SIGNALS SENT", "SUPPORTED GAMES", "GAME FUNCTION"]

        cur_x = table_x
        for i, h in enumerate(headers):
            h_surf = font_header.render(h, True, (241, 196, 15))
            surface.blit(h_surf, (cur_x, start_y))
            cur_x += col_widths[i]

        pygame.draw.line(surface, (52, 152, 219), (table_x, start_y + 25), (sw - 50, start_y + 25), 2)

        row_y = start_y + 35
        for row in MASTER_CONTROL_MATRIX:
            cur_x = table_x
            for i, val in enumerate(row):
                color = (0, 255, 200) if i == 0 else ((255, 255, 255) if i == 2 else (205, 215, 225))
                cell_surf = font_row.render(val, True, color)
                surface.blit(cell_surf, (cur_x, row_y))
                cur_x += col_widths[i]
            row_y += 32

    def _draw_animated_stickman(self, surface: pygame.Surface, lesson_id: str,
                                cx: int, cy: int) -> None:
        ticks = pygame.time.get_ticks()
        t = ticks / 1000.0

        col_body = (0, 255, 220)
        col_prop = (241, 196, 15)
        head_radius = 24
        torso_len = 80

        if lesson_id == "AIR_MOUSE":
            # Animated stickman pointing right arm forward at a floating cursor with click ripples
            head_y = cy - torso_len - 20
            pygame.draw.circle(surface, col_body, (cx, head_y), head_radius)
            pygame.draw.line(surface, col_body, (cx, head_y + head_radius), (cx, cy), 5)
            # Legs (seated or standing)
            pygame.draw.line(surface, col_body, (cx, cy), (cx - 20, cy + 55), 5)
            pygame.draw.line(surface, col_body, (cx, cy), (cx + 20, cy + 55), 5)

            # Left arm (relaxed)
            pygame.draw.line(surface, col_body, (cx, head_y + head_radius + 15), (cx - 25, cy - 5), 4)

            # Right arm pointing forward
            hand_x = cx + 65
            hand_y = cy - 35
            pygame.draw.line(surface, col_prop, (cx, head_y + head_radius + 15), (cx + 35, cy - 15), 5)
            pygame.draw.line(surface, col_prop, (cx + 35, cy - 15), (hand_x, hand_y), 5)
            # Pointing index finger
            pygame.draw.line(surface, (255, 255, 255), (hand_x, hand_y), (hand_x + 18, hand_y - 12), 4)

            # Floating cursor dot moving in a circle
            cur_x = hand_x + 50 + int(math.sin(t * 2.5) * 40)
            cur_y = hand_y - 20 + int(math.cos(t * 2.5) * 25)

            # Draw cursor arrow
            pygame.draw.polygon(surface, (255, 255, 255), [
                (cur_x, cur_y),
                (cur_x + 14, cur_y + 10),
                (cur_x + 6, cur_y + 12),
                (cur_x + 10, cur_y + 20),
                (cur_x + 4, cur_y + 22),
                (cur_x, cur_y + 14)
            ])

            # Periodic click ripple animation
            pulse = math.sin(t * 3.5)
            if pulse > 0.5:
                r_size = int((pulse - 0.5) * 35)
                pygame.draw.circle(surface, (0, 255, 200), (cur_x, cur_y), r_size, 2)
                f_click = pygame.font.Font(None, 22)
                c_txt = f_click.render("CLICK!", True, (0, 255, 200))
                surface.blit(c_txt, (cur_x + 18, cur_y - 15))

        elif lesson_id == "JUMP":
            jump_offset = int(max(0.0, math.sin(t * 3.5)) * 60)
            head_y = cy - torso_len - 30 - jump_offset
            torso_bot_y = head_y + torso_len
            pygame.draw.circle(surface, col_body, (cx, head_y), head_radius)
            pygame.draw.line(surface, col_body, (cx, head_y + head_radius), (cx, torso_bot_y), 5)
            pygame.draw.line(surface, col_body, (cx, torso_bot_y), (cx - 25, torso_bot_y + 50), 5)
            pygame.draw.line(surface, col_body, (cx, torso_bot_y), (cx + 25, torso_bot_y + 50), 5)

        elif lesson_id == "DUCK":
            phase = math.sin(t * 2.5) * 0.5 + 0.5
            squat = int(phase * 48)
            hip_y = cy + squat
            head_y = hip_y - 100
            foot_y = cy + 55
            knee_y = (hip_y + foot_y) // 2
            knee_out = 12 + int(phase * 30)

            pygame.draw.circle(surface, col_body, (cx, head_y), head_radius)
            pygame.draw.line(surface, col_body, (cx, head_y + head_radius), (cx, hip_y), 5)
            pygame.draw.line(surface, col_body, (cx, hip_y), (cx - knee_out, knee_y), 5)
            pygame.draw.line(surface, col_body, (cx, hip_y), (cx + knee_out, knee_y), 5)
            pygame.draw.line(surface, col_body, (cx - knee_out, knee_y), (cx - 22, foot_y), 5)
            pygame.draw.line(surface, col_body, (cx + knee_out, knee_y), (cx + 22, foot_y), 5)

        elif lesson_id == "STEERING":
            angle = math.sin(t * 3.0) * 0.5
            head_y = cy - torso_len - 20
            pygame.draw.circle(surface, col_body, (cx, head_y), head_radius)
            pygame.draw.line(surface, col_body, (cx, head_y + head_radius), (cx, cy), 5)
            wheel_w = 40
            wx1 = cx - int(math.cos(angle) * wheel_w)
            wy1 = cy - 30 - int(math.sin(angle) * wheel_w)
            wx2 = cx + int(math.cos(angle) * wheel_w)
            wy2 = cy - 30 + int(math.sin(angle) * wheel_w)
            pygame.draw.circle(surface, col_prop, (cx, cy - 30), wheel_w, 4)
            pygame.draw.line(surface, col_body, (cx - 20, cy - 45), (wx1, wy1), 4)
            pygame.draw.line(surface, col_body, (cx + 20, cy - 45), (wx2, wy2), 4)

        elif lesson_id == "NERF_GUN":
            recoil = int(max(0.0, math.sin(t * 4.0) ** 3) * 20)
            head_y = cy - torso_len - 20
            pygame.draw.circle(surface, col_body, (cx, head_y), head_radius)
            pygame.draw.line(surface, col_body, (cx, head_y + head_radius), (cx, cy), 5)
            gun_x = cx + 45
            gun_y = cy - 35 - recoil
            pygame.draw.rect(surface, (255, 60, 60), (cx + 10, gun_y, 45, 16), border_radius=3)
            if recoil > 10:
                pygame.draw.circle(surface, (255, 255, 0), (gun_x + 15, gun_y + 8), 12)

        elif lesson_id in ("LEAN_LEFT", "LEAN_RIGHT"):
            direction = -1 if lesson_id == "LEAN_LEFT" else 1
            lean = int(max(0.0, math.sin(t * 2.5)) * 45) * direction
            head_x = cx + lean
            head_y = cy - torso_len - 20
            pygame.draw.circle(surface, col_body, (head_x, head_y), head_radius)
            pygame.draw.line(surface, col_body, (head_x, head_y + head_radius), (cx, cy), 5)
            pygame.draw.line(surface, col_body, (cx, cy), (cx - 20, cy + 55), 5)
            pygame.draw.line(surface, col_body, (cx, cy), (cx + 20, cy + 55), 5)

        elif lesson_id == "PUNCH":
            thrust = int(max(0.0, math.sin(t * 5.0)) * 70)
            head_y = cy - torso_len - 20
            shoulder_y = head_y + head_radius + 18
            pygame.draw.circle(surface, col_body, (cx, head_y), head_radius)
            pygame.draw.line(surface, col_body, (cx, head_y + head_radius), (cx, cy), 5)
            fist_x = cx + 25 + thrust
            pygame.draw.line(surface, col_prop, (cx, shoulder_y), (fist_x, shoulder_y + 2), 6)
            pygame.draw.circle(surface, (255, 80, 80), (fist_x + 6, shoulder_y + 2), 12)

        elif lesson_id == "CHICKEN_FLAP":
            flap = int(math.sin(t * 8.0) * 25)
            head_y = cy - torso_len - 20
            pygame.draw.circle(surface, col_body, (cx, head_y), head_radius)
            pygame.draw.line(surface, col_body, (cx, head_y + head_radius), (cx, cy), 5)
            pygame.draw.line(surface, col_prop, (cx - 15, cy - 45), (cx - 45, cy - 35 - flap), 6)
            pygame.draw.line(surface, col_prop, (cx + 15, cy - 45), (cx + 45, cy - 35 - flap), 6)

        elif lesson_id == "FLAMINGO":
            head_y = cy - torso_len - 20
            pygame.draw.circle(surface, col_body, (cx, head_y), head_radius)
            pygame.draw.line(surface, col_body, (cx, head_y + head_radius), (cx, cy), 5)
            pygame.draw.line(surface, col_body, (cx, cy), (cx - 10, cy + 60), 5)
            pygame.draw.line(surface, (255, 100, 150), (cx, cy), (cx + 30, cy + 25), 5)

        else:
            head_y = cy - torso_len - 20
            pygame.draw.circle(surface, col_body, (cx, head_y), head_radius)
            pygame.draw.line(surface, col_body, (cx, head_y + head_radius), (cx, cy), 5)
            pygame.draw.line(surface, col_body, (cx, cy), (cx - 20, cy + 55), 5)
            pygame.draw.line(surface, col_body, (cx, cy), (cx + 20, cy + 55), 5)