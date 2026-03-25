import cv2
import pygame
import sys
import math
import random
import os
import numpy as np
import hand_tracking_module as htm

# --- SETTINGS ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
CUT_SPEED_THRESHOLD = 15
PINCH_THRESHOLD = 40  

# Global Sound Level
MUSIC_VOLUME = 0.5

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)       
MAGENTA = (255, 0, 255)    
YELLOW = (255, 255, 0)     
NEON_GREEN = (57, 255, 20) 
GRAY = (128, 128, 128)     
RED = (255, 50, 50)        
GRID_COLOR = (40, 40, 60)

# Directions
DIR_UP = "UP"; DIR_DOWN = "DOWN"; DIR_LEFT = "LEFT"; DIR_RIGHT = "RIGHT"; DIR_ANY = "ANY"
DIRECTIONS = [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_ANY]

# File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SND_DIR = os.path.join(BASE_DIR, "assets", "sounds")
IMG_DIR = os.path.join(BASE_DIR, "assets", "images")

pygame.mixer.pre_init(44100, -16, 2, 512) 
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Neon Rhythm: Final Edition")
clock = pygame.time.Clock()

# Fonts
title_font = pygame.font.Font(None, 80)
menu_font = pygame.font.Font(None, 50) 
small_font = pygame.font.Font(None, 40)
score_font = pygame.font.Font(None, 60)

# --- AUXILIARY FUNCTIONS ---
def get_path(folder, filename):
    path = os.path.join(folder, filename)
    if os.path.exists(path): return path
    return None

def load_sfx(filename):
    try:
        path = get_path(SND_DIR, filename)
        if path: return pygame.mixer.Sound(path)
    except: return None
    return None

# --- RENDERING BACKGROUND ---
bg_image = None
bg_path = get_path(IMG_DIR, "background_1.png") 

if bg_path:
    bg_image = pygame.image.load(bg_path).convert()
    bg_image = pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
    bg_dark = bg_image.copy()
    dark_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    dark_overlay.fill((0, 0, 0))
    dark_overlay.set_alpha(150)
    bg_dark.blit(dark_overlay, (0,0))
else:
    bg_dark = None

# Sounds
hit_sound = load_sfx("hit.wav") 
if hit_sound: hit_sound.set_volume(0.6)

# Music
MENU_MUSIC = get_path(SND_DIR, "menu.wav")
GAME_MUSIC = {
    'EASY': get_path(SND_DIR, "song_easy.wav"),
    'MEDIUM': get_path(SND_DIR, "song_medium.wav"),
    'HARD': get_path(SND_DIR, "song_hard.wav")
}

# --- DRAWING ARROWS ---
def draw_direction_indicator(surface, color, center, size, direction):
    if direction == DIR_ANY:
        pygame.draw.circle(surface, WHITE, center, int(size * 0.35), 2)
        pygame.draw.circle(surface, color, center, int(size * 0.15))
    else:
        arrow_size = int(size * 0.5) 
        cx, cy = center
        if direction == DIR_UP:
            points = [(cx, cy - arrow_size), (cx - arrow_size//2, cy + arrow_size//2), (cx + arrow_size//2, cy + arrow_size//2)]
        elif direction == DIR_DOWN:
            points = [(cx, cy + arrow_size), (cx - arrow_size//2, cy - arrow_size//2), (cx + arrow_size//2, cy - arrow_size//2)]
        elif direction == DIR_LEFT:
            points = [(cx - arrow_size, cy), (cx + arrow_size//2, cy - arrow_size//2), (cx + arrow_size//2, cy + arrow_size//2)]
        elif direction == DIR_RIGHT:
            points = [(cx + arrow_size, cy), (cx - arrow_size//2, cy - arrow_size//2), (cx - arrow_size//2, cy + arrow_size//2)]
        pygame.draw.polygon(surface, WHITE, points)
        pygame.draw.polygon(surface, color, points, 2)

# --- DRAWING CURSOR---
def draw_cursor(surface, pos, is_pinching=False):
    if pos:
        color = YELLOW if is_pinching else NEON_GREEN
        pygame.draw.circle(surface, color, pos, 15, 3)
        pygame.draw.circle(surface, WHITE, pos, 5)

# --- BOX CLASS ---
class Cube:
    def __init__(self, side, speed_mult):
        self.side = side
        self.color = CYAN if side == 'LEFT' else MAGENTA
        self.direction = random.choice(DIRECTIONS)
        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT // 2
        offset_x = random.randint(60, 130) 
        offset_y = random.randint(30, 90)
        
        if side == 'LEFT': self.target_x = self.center_x - offset_x
        else: self.target_x = self.center_x + offset_x
            
        if random.random() < 0.7: self.target_y = self.center_y + offset_y
        else: self.target_y = self.center_y - offset_y
            
        self.x = self.center_x
        self.y = self.center_y
        self.scale = 0.02
        self.growth_speed = speed_mult
        self.size = 10
        self.active = True

    def update(self):
        self.scale += self.growth_speed
        self.x = self.center_x + (self.target_x - self.center_x) * self.scale
        self.y = self.center_y + (self.target_y - self.center_y) * self.scale
        self.size = int(60 * self.scale)
        if self.scale > 1.3: return "missed"
        return "active"

    def draw(self, surface):
        if not self.active: return
        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = (int(self.x), int(self.y))
        
        glow_size = int(self.size * 1.6)
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*self.color, 50), glow_surf.get_rect(), border_radius=15)
        pygame.draw.rect(glow_surf, (*self.color, 90), glow_surf.get_rect().inflate(-5,-5), border_radius=10)
        surface.blit(glow_surf, (rect.centerx - glow_size//2, rect.centery - glow_size//2))
        
        pygame.draw.rect(surface, self.color, rect, width=int(3 * self.scale) + 2, border_radius=6)
        pygame.draw.rect(surface, WHITE, rect, width=1, border_radius=6)
        draw_direction_indicator(surface, self.color, rect.center, self.size, self.direction)

# --- MENU DRAWING ---
def draw_menu(surface, hand_pos, is_pinching):
    if bg_image:
        surface.blit(bg_image, (0,0))
        dark = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        dark.set_alpha(100)
        surface.blit(dark, (0,0))
    else:
        surface.fill(BLACK)
        
    for i in range(0, WINDOW_HEIGHT, 50):
        pygame.draw.line(surface, (20, 20, 20), (0, i), (WINDOW_WIDTH, i))
    
    title = title_font.render("NEON RHYTHM", True, NEON_GREEN)
    surface.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 40))
    
    # LIST OF BUTTON
    buttons = [
        {"label": "EASY",   "color": CYAN,    "rect": pygame.Rect(WINDOW_WIDTH//2 - 120, 140, 240, 60), "action": "EASY"},
        {"label": "MEDIUM", "color": YELLOW,  "rect": pygame.Rect(WINDOW_WIDTH//2 - 120, 220, 240, 60), "action": "MEDIUM"},
        {"label": "HARD",   "color": MAGENTA, "rect": pygame.Rect(WINDOW_WIDTH//2 - 120, 300, 240, 60), "action": "HARD"},
        {"label": "SETTINGS", "color": GRAY,  "rect": pygame.Rect(WINDOW_WIDTH//2 - 120, 380, 240, 60), "action": "SETTINGS"},
        {"label": "EXIT", "color": RED, "rect": pygame.Rect(WINDOW_WIDTH//2 - 150, 480, 300, 60), "action": "EXIT"}
    ]
    
    selected_action = None
    for btn in buttons:
        color = btn["color"]
        if hand_pos and btn["rect"].collidepoint(hand_pos):
            if btn["action"] in ["SETTINGS", "EXIT"]:
                pygame.draw.rect(surface, color, btn["rect"], border_radius=20)
                text_color = BLACK
                if is_pinching: 
                    selected_action = btn["action"]
            else:
                # Play buttons
                pygame.draw.rect(surface, color, btn["rect"], border_radius=20)
                text_color = BLACK
                selected_action = btn["action"]
        else:
            pygame.draw.rect(surface, color, btn["rect"], width=4, border_radius=20)
            s = pygame.Surface((btn["rect"].width, btn["rect"].height), pygame.SRCALPHA)
            s.fill((0,0,0,150))
            surface.blit(s, (btn["rect"].x, btn["rect"].y))
            text_color = color
            
        text = menu_font.render(btn["label"], True, text_color)
        surface.blit(text, (btn["rect"].centerx - text.get_width()//2, btn["rect"].centery - text.get_height()//2))
    
    draw_cursor(surface, hand_pos, is_pinching)
    return selected_action

# --- SETTINGS DISPLAY ---
def draw_settings_menu(surface, hand_pos, is_pinching):
    global MUSIC_VOLUME
    surface.fill((20, 20, 30))
    
    title = title_font.render("SETTINGS", True, GRAY)
    surface.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 50))
    
    # Sound Bar Control
    vol_text = menu_font.render(f"Music Volume: {int(MUSIC_VOLUME*100)}%", True, WHITE)
    surface.blit(vol_text, (WINDOW_WIDTH//2 - vol_text.get_width()//2, 200))
    
    bar_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, 260, 300, 40)
    
    # Volume Adjustment Logic (if Pinch)
    if hand_pos and is_pinching:
        if bar_rect.inflate(40, 40).collidepoint(hand_pos): 
            relative_x = hand_pos[0] - bar_rect.x
            new_vol = relative_x / bar_rect.width
            MUSIC_VOLUME = max(0.0, min(1.0, new_vol))
            pygame.mixer.music.set_volume(MUSIC_VOLUME)

    pygame.draw.rect(surface, WHITE, bar_rect, 2)
    pygame.draw.rect(surface, NEON_GREEN, (bar_rect.x, bar_rect.y, int(300 * MUSIC_VOLUME), 40))
    
    back_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, 450, 300, 80)
    
    action = None
    if hand_pos and back_rect.collidepoint(hand_pos):
        pygame.draw.rect(surface, WHITE, back_rect, border_radius=20)
        text_color = BLACK
        if is_pinching:
            action = "BACK"
    else:
        pygame.draw.rect(surface, WHITE, back_rect, width=4, border_radius=20)
        text_color = WHITE
    
    back_txt = menu_font.render("MAIN MENU", True, text_color)
    surface.blit(back_txt, (back_rect.centerx - back_txt.get_width()//2, back_rect.centery - back_txt.get_height()//2))
    
    draw_cursor(surface, hand_pos, is_pinching)
    return action

# --- PAUSE (IN-GAME MENU) ---
def draw_pause_menu(surface, hand_pos, is_pinching):
    dark = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    dark.fill(BLACK)
    dark.set_alpha(150)
    surface.blit(dark, (0,0))

    title = title_font.render("PAUSED", True, WHITE)
    surface.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))

    buttons = [
        {"label": "CONTINUE", "color": NEON_GREEN, "rect": pygame.Rect(WINDOW_WIDTH//2 - 120, 220, 240, 70), "action": "CONTINUE"},
        {"label": "RETRY",    "color": YELLOW,     "rect": pygame.Rect(WINDOW_WIDTH//2 - 120, 310, 240, 70), "action": "RETRY"},
        {"label": "MENU",     "color": RED,        "rect": pygame.Rect(WINDOW_WIDTH//2 - 120, 400, 240, 70), "action": "MENU"}
    ]

    selected = None
    for btn in buttons:
        color = btn["color"]
        if hand_pos and btn["rect"].collidepoint(hand_pos):
            pygame.draw.rect(surface, color, btn["rect"], border_radius=20)
            text_color = BLACK
            if is_pinching:
                selected = btn["action"]
        else:
            pygame.draw.rect(surface, color, btn["rect"], width=4, border_radius=20)
            text_color = color
        
        txt = menu_font.render(btn["label"], True, text_color)
        surface.blit(txt, (btn["rect"].centerx - txt.get_width()//2, btn["rect"].centery - txt.get_height()//2))

    draw_cursor(surface, hand_pos, is_pinching)
    return selected


# --- PLAYGROUND DRAWING ---
def draw_game_background(surface):
    if bg_dark: surface.blit(bg_dark, (0,0))
    center = (WINDOW_WIDTH//2, WINDOW_HEIGHT//2)
    pygame.draw.line(surface, GRID_COLOR, center, (150, 0), 2)
    pygame.draw.line(surface, GRID_COLOR, center, (WINDOW_WIDTH-150, 0), 2)
    pygame.draw.line(surface, GRID_COLOR, center, (150, WINDOW_HEIGHT), 2)
    pygame.draw.line(surface, GRID_COLOR, center, (WINDOW_WIDTH-150, WINDOW_HEIGHT), 2)
    pygame.draw.line(surface, GRID_COLOR, center, (WINDOW_WIDTH//2, 0), 1)
    pygame.draw.line(surface, GRID_COLOR, center, (WINDOW_WIDTH//2, WINDOW_HEIGHT), 1)
    pygame.draw.line(surface, GRID_COLOR, center, (0, WINDOW_HEIGHT//2), 1)
    pygame.draw.line(surface, GRID_COLOR, center, (WINDOW_WIDTH, WINDOW_HEIGHT//2), 1)

# --- MAIN PROGRAM ---
def main():
    global MUSIC_VOLUME
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    detector = htm.HandDetector(detection_con=0.7, max_hands=2)
    
    state = "MENU"
    cubes = []
    score = 0
    combo = 0
    lives = 10
    
    spawn_timer = 0
    spawn_rate = 60
    cube_speed = 0.01
    menu_hold_timer = 0
    
    pinch_cooldown = 0
    
    prev_left_hand = None
    prev_right_hand = None
    is_menu_music_playing = False
    
    # To remember the chosen song and the difficulty level.
    current_difficulty = "EASY"
    
    game_settings_rect = pygame.Rect(WINDOW_WIDTH - 90, 20, 70, 50)
    
    while True:
        success, img = cap.read()
        if not success: continue
        img = cv2.flip(img, 1)
        
        img = detector.find_hands(img)
        lm_list1 = detector.find_position(img, hand_no=0, draw=False)
        lm_list2 = detector.find_position(img, hand_no=1, draw=False)
        
        left_hand = None
        right_hand = None
        active_landmarks = [] 
        
        # Hand Coordinates
        if len(lm_list1) > 0:
            cx, cy = lm_list1[8][1], lm_list1[8][2]
            screen_x = int((cx / 1280) * WINDOW_WIDTH)
            screen_y = int((cy / 720) * WINDOW_HEIGHT)
            if screen_x < WINDOW_WIDTH // 2: left_hand = (screen_x, screen_y)
            else: right_hand = (screen_x, screen_y); active_landmarks = lm_list1 

        if len(lm_list2) > 0:
            cx, cy = lm_list2[8][1], lm_list2[8][2]
            screen_x = int((cx / 1280) * WINDOW_WIDTH)
            screen_y = int((cy / 720) * WINDOW_HEIGHT)
            if screen_x < WINDOW_WIDTH // 2: left_hand = (screen_x, screen_y)
            else: right_hand = (screen_x, screen_y); active_landmarks = lm_list2
        
        cursor_pos = right_hand if right_hand else left_hand
        if not right_hand and left_hand and len(lm_list1) > 0:
             if left_hand[0] == int((lm_list1[8][1] / 1280) * WINDOW_WIDTH): active_landmarks = lm_list1
             else: active_landmarks = lm_list2

        # Pinch Control
        is_pinching = False
        if len(active_landmarks) != 0:
            x1, y1 = active_landmarks[4][1], active_landmarks[4][2]
            x2, y2 = active_landmarks[8][1], active_landmarks[8][2]
            sx1, sy1 = int((x1/1280)*WINDOW_WIDTH), int((y1/720)*WINDOW_HEIGHT)
            sx2, sy2 = int((x2/1280)*WINDOW_WIDTH), int((y2/720)*WINDOW_HEIGHT)
            dist = math.hypot(sx2-sx1, sy2-sy1)
            if dist < PINCH_THRESHOLD: is_pinching = True

        left_vel_x, left_vel_y = 0, 0
        right_vel_x, right_vel_y = 0, 0
        if left_hand and prev_left_hand:
            left_vel_x = left_hand[0] - prev_left_hand[0]
            left_vel_y = left_hand[1] - prev_left_hand[1]
        if right_hand and prev_right_hand:
            right_vel_x = right_hand[0] - prev_right_hand[0]
            right_vel_y = right_hand[1] - prev_right_hand[1]

        if pinch_cooldown > 0: pinch_cooldown -= 1

        # --- MENU STATE ---
        if state == "MENU":
            if not is_menu_music_playing and MENU_MUSIC:
                pygame.mixer.music.load(MENU_MUSIC)
                pygame.mixer.music.set_volume(MUSIC_VOLUME)
                pygame.mixer.music.play(-1)
                is_menu_music_playing = True

            action = draw_menu(screen, cursor_pos, is_pinching)
            
            if action:
                if action == "EXIT":
                    if pinch_cooldown == 0:
                        pygame.quit()
                        sys.exit() 
                elif action == "SETTINGS":
                    if pinch_cooldown == 0:
                        state = "SETTINGS"
                        pinch_cooldown = 60
                else:
                    menu_hold_timer += 1
                    if cursor_pos: pygame.draw.circle(screen, WHITE, cursor_pos, 10 + menu_hold_timer, 4)
                    
                    if menu_hold_timer > 45: 
                        state = "GAME"
                        current_difficulty = action
                        if action == "EASY": spawn_rate = 55; cube_speed = 0.015   
                        elif action == "MEDIUM": spawn_rate = 35; cube_speed = 0.025   
                        elif action == "HARD": spawn_rate = 20; cube_speed = 0.040   
                        
                        music_file = GAME_MUSIC[action]
                        if music_file:
                            pygame.mixer.music.load(music_file)
                            pygame.mixer.music.set_volume(MUSIC_VOLUME)
                            pygame.mixer.music.play(-1)
                            is_menu_music_playing = False
                        score = 0; lives = 10; combo = 0; cubes.clear(); menu_hold_timer = 0
            else:
                menu_hold_timer = 0

        # --- SETTINGS STATE ---
        elif state == "SETTINGS":
            action = draw_settings_menu(screen, cursor_pos, is_pinching)
            if action == "BACK":
                 if pinch_cooldown == 0:
                     state = "MENU"
                     pinch_cooldown = 60

        # --- PAUSED STATE ---
        elif state == "PAUSED":
            draw_game_background(screen)
            for cube in cubes: cube.draw(screen)  
            action = draw_pause_menu(screen, cursor_pos, is_pinching)
            if action:
                if pinch_cooldown == 0:
                    if action == "CONTINUE":
                        state = "GAME"
                        pygame.mixer.music.unpause()
                    elif action == "RETRY":
                        state = "GAME"
                        # Reset
                        score = 0; lives = 10; combo = 0; cubes.clear()
                        spawn_timer = 0
                        music_file = GAME_MUSIC[current_difficulty]
                        if music_file:
                            pygame.mixer.music.load(music_file)
                            pygame.mixer.music.set_volume(MUSIC_VOLUME)
                            pygame.mixer.music.play(-1)
                    elif action == "MENU":
                        state = "MENU"
                        is_menu_music_playing = False 
                    
                    pinch_cooldown = 60

        # --- GAME STATE ---
        elif state == "GAME":
            screen.fill(BLACK) 
            draw_game_background(screen)
            
            # PAUSE BUTTON
            if cursor_pos and game_settings_rect.collidepoint(cursor_pos):
                pygame.draw.rect(screen, GRAY, game_settings_rect, border_radius=10)
                if is_pinching: 
                    if pinch_cooldown == 0:
                        state = "PAUSED"
                        pygame.mixer.music.pause() 
                        pinch_cooldown = 60
            else:
                pygame.draw.rect(screen, (50, 50, 50), game_settings_rect, width=2, border_radius=10)

            set_txt = small_font.render("SET", True, WHITE)
            screen.blit(set_txt, (game_settings_rect.centerx - set_txt.get_width()//2, game_settings_rect.centery - set_txt.get_height()//2))

            spawn_timer += 1
            if spawn_timer > spawn_rate:
                spawn_timer = 0
                side = 'LEFT' if random.random() < 0.5 else 'RIGHT'
                cubes.append(Cube(side, cube_speed))
            
            for cube in cubes[:]:
                status = cube.update()
                if status == "missed":
                    lives -= 1; combo = 0; cubes.remove(cube)
                    if lives <= 0:
                        state = "GAMEOVER"; pygame.mixer.music.fadeout(500)
                    continue
                
                cube.draw(screen)
                
                if cube.scale > 0.6:
                    hit = False
                    hand_vel_x, hand_vel_y = 0, 0
                    active_hand = None

                    if cube.side == 'LEFT' and left_hand:
                        dist = math.hypot(left_hand[0] - cube.x, left_hand[1] - cube.y)
                        if dist < cube.size + 45:
                            active_hand = left_hand
                            hand_vel_x, hand_vel_y = left_vel_x, left_vel_y
                    elif cube.side == 'RIGHT' and right_hand:
                        dist = math.hypot(right_hand[0] - cube.x, right_hand[1] - cube.y)
                        if dist < cube.size + 45:
                            active_hand = right_hand
                            hand_vel_x, hand_vel_y = right_vel_x, right_vel_y
                    
                    if active_hand:
                        speed = math.hypot(hand_vel_x, hand_vel_y)
                        correct_direction = False
                        if cube.direction == DIR_ANY:
                            if speed > CUT_SPEED_THRESHOLD: correct_direction = True
                        elif cube.direction == DIR_UP:
                            if hand_vel_y < -CUT_SPEED_THRESHOLD: correct_direction = True
                        elif cube.direction == DIR_DOWN:
                            if hand_vel_y > CUT_SPEED_THRESHOLD: correct_direction = True
                        elif cube.direction == DIR_LEFT:
                            if hand_vel_x < -CUT_SPEED_THRESHOLD: correct_direction = True
                        elif cube.direction == DIR_RIGHT:
                            if hand_vel_x > CUT_SPEED_THRESHOLD: correct_direction = True

                        if correct_direction: hit = True

                    if hit:
                        if hit_sound: hit_sound.set_volume(MUSIC_VOLUME + 0.1); hit_sound.play() # Ses ayarına göre sfx
                        score += 10 + combo; combo += 1; cubes.remove(cube)
                        color = CYAN if cube.side == 'LEFT' else MAGENTA
                        pygame.draw.circle(screen, color, (int(cube.x), int(cube.y)), 60)
                        pygame.draw.circle(screen, WHITE, (int(cube.x), int(cube.y)), 30)

            if left_hand:
                pygame.draw.circle(screen, CYAN, left_hand, 20)
                pygame.draw.circle(screen, (0, 100, 100), left_hand, 30, 2)
            if right_hand:
                pygame.draw.circle(screen, MAGENTA, right_hand, 20)
                pygame.draw.circle(screen, (100, 0, 100), right_hand, 30, 2)
                
            score_txt = score_font.render(f"{score}", True, WHITE)
            screen.blit(score_txt, (20, 20))
            combo_txt = menu_font.render(f"Combo x{combo}", True, YELLOW)
            screen.blit(combo_txt, (20, 80))
            bar_w = 300; life_pct = max(0, lives / 10)
            pygame.draw.rect(screen, (30, 30, 30), (WINDOW_WIDTH - 320, 80, bar_w, 20))
            pygame.draw.rect(screen, NEON_GREEN if lives > 3 else (255, 0, 0), (WINDOW_WIDTH - 320, 80, bar_w * life_pct, 20))

        # --- GAMEOVER STATE ---
        elif state == "GAMEOVER":
            if bg_dark: screen.blit(bg_dark, (0,0))
            else: screen.fill(BLACK)
            
            t1 = title_font.render("GAME OVER", True, (255, 0, 0))
            t2 = menu_font.render(f"Final Score: {score}", True, WHITE)
            t3 = menu_font.render("Hold Center for Menu", True, CYAN)
            screen.blit(t1, (WINDOW_WIDTH//2 - t1.get_width()//2, 200))
            screen.blit(t2, (WINDOW_WIDTH//2 - t2.get_width()//2, 300))
            screen.blit(t3, (WINDOW_WIDTH//2 - t3.get_width()//2, 450))
            
            draw_cursor(screen, cursor_pos, is_pinching) 

            center_area = pygame.Rect(WINDOW_WIDTH//2 - 60, 420, 120, 100)
            if cursor_pos:
                if center_area.collidepoint(cursor_pos):
                    menu_hold_timer += 1
                    pygame.draw.circle(screen, CYAN, cursor_pos, 10 + menu_hold_timer, 2)
                    if menu_hold_timer > 50:
                        state = "MENU"; menu_hold_timer = 0; is_menu_music_playing = False
                else:
                    menu_hold_timer = 0
                    
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        
        prev_left_hand = left_hand
        prev_right_hand = right_hand

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()