import cv2
import pygame
import sys
import math
import random
import os
import numpy as np
import hand_tracking_module as htm
from oyun_araclari import OyunYoneticisi

# --- CONFIGURATION ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
UI_HEIGHT = 80 
GAME_HEIGHT = WINDOW_HEIGHT - UI_HEIGHT 
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 215, 0)
GREEN = (0, 255, 0)
UI_BG_COLOR = (20, 20, 35) 
UI_BORDER_COLOR = (255, 215, 0) 

# File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "assets", "images")
SND_DIR = os.path.join(BASE_DIR, "assets", "sounds")

# Init Pygame & Mixer
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 512) 
pygame.mixer.init()

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Virtual Goalkeeper: Arcade UI")
clock = pygame.time.Clock()

# Fonts
score_font = pygame.font.Font(None, 60)
label_font = pygame.font.Font(None, 30)

# --- HELPER FUNCTIONS ---
def load_image(name, size=None):
    """Loads an image from assets and optionally resizes it."""
    try:
        path = os.path.join(IMG_DIR, name)
        if not os.path.exists(path): return None
        img = pygame.image.load(path).convert_alpha()
        if size: img = pygame.transform.smoothscale(img, size)
        return img
    except: return None

def load_sound(name, vol=0.5):
    """Loads a sound from assets."""
    try:
        path = os.path.join(SND_DIR, name)
        if not os.path.exists(path): return None
        snd = pygame.mixer.Sound(path)
        snd.set_volume(vol)
        return snd
    except: return None

# --- ASSETS ---
ball_img_orig = load_image("football.png") 

# Gloves
glove_right_img = load_image("glove.png", (130, 130))
if glove_right_img:
    glove_left_img = pygame.transform.flip(glove_right_img, True, False)
else:
    glove_left_img = None

# Background (Game Area)
bg_img = load_image("stadium.jpg", (WINDOW_WIDTH, GAME_HEIGHT))

# Background (Menu / OpenCV)
bg_cv2_path = os.path.join(IMG_DIR, "stadium.jpg")
bg_cv2 = None
if os.path.exists(bg_cv2_path):
    try:
        img_array = np.fromfile(bg_cv2_path, dtype=np.uint8)
        bg_cv2 = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        bg_cv2 = cv2.resize(bg_cv2, (WINDOW_WIDTH, WINDOW_HEIGHT))
    except:
        bg_cv2 = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), dtype=np.uint8)
else:
    bg_cv2 = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), dtype=np.uint8)

# Life Icon
heart_img = load_image("heart.png", (40, 40))

# Sounds
save_sound = load_sound("save.wav", 0.7)
whistle_sound = load_sound("whistle.wav", 0.6)
crowd_sound = load_sound("crowd.wav", 0.3)

# --- BALL CLASS ---
class Ball:
    def __init__(self, speed_mult=1.0):
        self.start_x = WINDOW_WIDTH // 2
        self.start_y = UI_HEIGHT + (GAME_HEIGHT // 2) - 30
        
        # Target is random point on screen
        self.target_x = random.randint(50, WINDOW_WIDTH - 50)
        self.target_y = random.randint(UI_HEIGHT + 50, WINDOW_HEIGHT - 50)
        
        self.x = self.start_x
        self.y = self.start_y
        
        self.scale = 0.05 
        self.growth_speed = 0.015 * speed_mult 
        
        self.active = True
        self.current_radius = 10

    def update(self):
        self.scale += self.growth_speed
        
        # Linear interpolation from start to target
        self.x = self.start_x + (self.target_x - self.start_x) * self.scale
        self.y = self.start_y + (self.target_y - self.start_y) * self.scale
        
        self.current_radius = int(60 * self.scale) 
        
        if self.scale >= 1.0:
            return "goal"
        return "incoming"

    def draw(self, surface):
        if not self.active: return
        
        if ball_img_orig:
            size = int(120 * self.scale) 
            if size < 5: size = 5
            scaled_ball = pygame.transform.smoothscale(ball_img_orig, (size, size))
            rect = scaled_ball.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(scaled_ball, rect)
        else:
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.current_radius)
            pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.current_radius, 2)

# --- UI DRAWING ---
def draw_ui(surface, score, lives):
    pygame.draw.rect(surface, UI_BG_COLOR, (0, 0, WINDOW_WIDTH, UI_HEIGHT))
    pygame.draw.line(surface, UI_BORDER_COLOR, (0, UI_HEIGHT), (WINDOW_WIDTH, UI_HEIGHT), 5)
    
    # Score
    score_label = label_font.render("SCORE", True, (150, 150, 150))
    score_val = score_font.render(str(score), True, WHITE)
    surface.blit(score_label, (WINDOW_WIDTH//2 - score_label.get_width()//2, 10))
    surface.blit(score_val, (WINDOW_WIDTH//2 - score_val.get_width()//2, 35))
    
    # Lives
    start_x = WINDOW_WIDTH - 50
    for i in range(3): 
        pos_x = start_x - (i * 50)
        pos_y = 20
        
        if i < lives: 
            if heart_img:
                surface.blit(heart_img, (pos_x, pos_y))
            else:
                pygame.draw.circle(surface, RED, (pos_x + 20, pos_y + 20), 15)
        else: 
            pygame.draw.circle(surface, (50, 50, 50), (pos_x + 20, pos_y + 20), 15, 2)

    # Title
    title = label_font.render("GOALKEEPER", True, UI_BORDER_COLOR)
    surface.blit(title, (20, 30))

# --- MAIN LOOP ---
def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    detector = htm.HandDetector(detection_con=0.7, max_hands=2)
    yonetici = OyunYoneticisi(WINDOW_WIDTH, WINDOW_HEIGHT)
    
    # Game States
    STATE_START = "START"
    STATE_GAME = "GAME"
    STATE_SETTINGS = "SETTINGS"
    STATE_GAMEOVER = "GAMEOVER"
    game_state = STATE_START
    last_state = STATE_START
    
    balls = []
    spawn_timer = 0
    score = 0
    lives = 3
    difficulty = 1.0
    
    # Sound State Variable
    is_crowd_playing = False
    
    while True:
        success, img = cap.read()
        if not success: continue
        
        # 1. Flip Camera 
        img = cv2.flip(img, 1)
        
        # 2. Detect Hands
        img = detector.find_hands(img)
        lm_list1 = detector.find_position(img, hand_no=0, draw=False)
        lm_list2 = detector.find_position(img, hand_no=1, draw=False)
        
        display_img = bg_cv2.copy()
        
        hands_data = [] 
        finger_pos = None 
        pinch = False
        
        # Hand 1 Data
        if len(lm_list1) != 0:
            x, y = lm_list1[9][1], lm_list1[9][2] 
            ix, iy = lm_list1[8][1], lm_list1[8][2] 
            bx, by = lm_list1[4][1], lm_list1[4][2] 
            
            gx = int((x / 1280) * WINDOW_WIDTH)
            gy = int((y / 720) * WINDOW_HEIGHT)
            
            # Use Index Finger for Menu Cursor
            finger_pos = (int((ix / 1280) * WINDOW_WIDTH), int((iy / 720) * WINDOW_HEIGHT))
            
            # Pinch Check
            dist = math.hypot(ix - bx, iy - by)
            if dist < 60: pinch = True 
            
            side = 'Right' if gx > WINDOW_WIDTH // 2 else 'Left'
            hands_data.append((gx, gy, side))
            
        # Hand 2 Data (Only for Gameplay)
        if len(lm_list2) != 0:
            x, y = lm_list2[9][1], lm_list2[9][2]
            gx = int((x / 1280) * WINDOW_WIDTH)
            gy = int((y / 720) * WINDOW_HEIGHT)
            side = 'Right' if gx > WINDOW_WIDTH // 2 else 'Left'
            hands_data.append((gx, gy, side))

        # Draw Cursor on Menu
        if finger_pos:
            col = (0, 255, 0) if pinch else (0, 255, 255)
            cv2.circle(display_img, finger_pos, 15, col, -1)


        # --- SOUND LOGIC FIX ---
        if crowd_sound:
            if yonetici.ses_aktif:
                if not is_crowd_playing:
                    crowd_sound.play(-1)
                    is_crowd_playing = True
            else:
                if is_crowd_playing:
                    crowd_sound.stop()
                    is_crowd_playing = False

        # STATE 1: START MENU
        if game_state == STATE_START:
            f_pos = finger_pos if finger_pos else (0,0)
            
            # Hold to Play Button
            basladi = yonetici.beat_saber_buton(display_img, "HOLD TO PLAY", 
                                                WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 50, 
                                                300, 100, f_pos)
            if basladi:
                game_state = STATE_GAME
                score = 0
                lives = 3
                difficulty = 1.0
                balls.clear()

            # Settings Icon
            menu_rect = yonetici.sag_ust_menu_ikonu(display_img)
            mx, my, mw, mh = menu_rect
            if (mx < f_pos[0] < mx + mw) and (my < f_pos[1] < my + mh):
                if pinch: 
                    last_state = STATE_START
                    game_state = STATE_SETTINGS

        # STATE 2: GAMEPLAY
        elif game_state == STATE_GAME:
            difficulty += 0.0005 
            spawn_timer += 1
            spawn_threshold = max(30, 80 - int(difficulty * 10))
            
            if spawn_timer > spawn_threshold:
                spawn_timer = 0
                balls.append(Ball(difficulty))

            # Update Balls
            for ball in balls[:]:
                status = ball.update()
                
                # Check for Save
                if ball.scale > 0.65: 
                    for hx, hy, side in hands_data:
                        dist = math.hypot(hx - ball.x, hy - ball.y)
                        if dist < ball.current_radius + 50:
                            if save_sound and yonetici.ses_aktif: save_sound.play()
                            score += 1
                            balls.remove(ball)
                            break
                
                if status == "goal":
                    if whistle_sound and yonetici.ses_aktif: whistle_sound.play()
                    lives -= 1
                    balls.remove(ball)
                    if lives <= 0: game_state = STATE_GAMEOVER
            
            # Menu Interaction
            f_pos = finger_pos if finger_pos else (0,0)
            mx, my, mw, mh = WINDOW_WIDTH - 80, 90, 60, 60 
            if (mx < f_pos[0] < mx + mw) and (my < f_pos[1] < my + mh):
                 if pinch: 
                     last_state = STATE_GAME
                     game_state = STATE_SETTINGS

            # STATE 3: SETTINGS MENU
        elif game_state == STATE_SETTINGS:
            f_pos = finger_pos if finger_pos else (0,0)
            komut = yonetici.menuyu_ciz_ve_yonet(display_img, f_pos, pinch)
            
            if komut == "BACK":
                game_state = last_state
            elif komut == "EXIT":
                cap.release()
                cv2.destroyAllWindows()
                return

        # STATE 4: GAME OVER MENU
        elif game_state == STATE_GAMEOVER:
            f_pos = finger_pos if finger_pos else (0,0)
            komut = yonetici.game_over_menusu(display_img, f_pos, pinch)
            
            if komut == "RETRY":
                game_state = STATE_GAME
                score = 0
                lives = 3
                difficulty = 1.0
                balls.clear()
            elif komut == "EXIT":
                cap.release()
                cv2.destroyAllWindows()
                return

        # DRAWING PHASE

        # 1. Draw Menus (OpenCV based)
        if game_state != STATE_GAME:
            img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            img_rgb = np.transpose(img_rgb, (1, 0, 2))
            img_surface = pygame.surfarray.make_surface(img_rgb)
            screen.blit(img_surface, (0,0))
            
            if game_state == STATE_GAMEOVER:
                sc_text = score_font.render(f"Score: {score}", True, WHITE)
                sc_rect = sc_text.get_rect(center=(WINDOW_WIDTH // 2, 150))
                screen.blit(sc_text, sc_rect)

        # 2. Draw Game (Pygame based)
        if game_state == STATE_GAME:
            # UI
            draw_ui(screen, score, lives)
            # Background
            if bg_img: screen.blit(bg_img, (0, UI_HEIGHT))
            else: pygame.draw.rect(screen, (0, 100, 0), (0, UI_HEIGHT, WINDOW_WIDTH, GAME_HEIGHT))   
            # Balls
            for ball in balls: ball.draw(screen)
            # Gloves
            for hx, hy, side in hands_data:
                img_to_draw = glove_right_img if side == 'Right' else glove_left_img
                if img_to_draw:
                    rect = img_to_draw.get_rect(center=(hx, hy))
                    screen.blit(img_to_draw, rect)
                else:
                    col = YELLOW if side == 'Right' else (255, 140, 0)
                    pygame.draw.circle(screen, col, (hx, hy), 40, 5)
            
            # Cursor
            if finger_pos:
                col = GREEN if pinch else (0, 255, 255)
                pygame.draw.circle(screen, col, finger_pos, 10)
            # Menu Icon
            mx, my, mw, mh = WINDOW_WIDTH - 80, 90, 60, 60 
            pygame.draw.rect(screen, (100, 100, 100), (mx, my, mw, mh))
            pygame.draw.line(screen, WHITE, (mx+10, my+15), (mx+mw-10, my+15), 3)
            pygame.draw.line(screen, WHITE, (mx+10, my+30), (mx+mw-10, my+30), 3)
            pygame.draw.line(screen, WHITE, (mx+10, my+45), (mx+mw-10, my+45), 3)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()