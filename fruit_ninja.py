import cv2
import pygame
import sys
import math
import random
import os
import numpy as np
import hand_tracking_module as htm
from oyun_araclari import OyunYoneticisi

# --- SETTINGS & CONSTANTS ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
GRAVITY = 0.25 

# Audio Configuration
pygame.mixer.pre_init(44100, -16, 2, 512) 
pygame.init()
pygame.mixer.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BUTTON_COLOR = (255, 140, 0) 
BUTTON_HOVER = (255, 165, 50)

FRUIT_COLORS = {
    'elma': (255, 0, 0),    # Apple
    'karpuz': (0, 255, 0),  # Watermelon
    'muz': (255, 255, 0)    # Banana
}

# File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "assets", "images")
SND_DIR = os.path.join(BASE_DIR, "assets", "sounds")

# Pygame Setup
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Fruit Ninja: Complete Game")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 40)
score_font = pygame.font.Font(None, 80)

# --- HELPER FUNCTIONS ---
def load_image(name, size=None):
    """Loads an image from the assets folder and handles scaling."""
    try:
        path = os.path.join(IMG_DIR, name)
        if not os.path.exists(path): return None
        img = pygame.image.load(path).convert_alpha()
        if size: 
            if isinstance(size, int):
                img = pygame.transform.smoothscale(img, (size, size))
            else:
                img = pygame.transform.smoothscale(img, size)
        return img
    except: return None

def load_sound(name, volume=0.5):
    """Loads a sound file from the assets folder."""
    try:
        path = os.path.join(SND_DIR, name)
        if not os.path.exists(path): return None
        snd = pygame.mixer.Sound(path)
        snd.set_volume(volume)
        return snd
    except: return None

# --- LOAD ASSETS ---
# 1. Menu Assets
logo_img = load_image("logo.png", (400, 200)) 
play_btn_img = load_image("play_btn.png", (200, 100)) 

# Background (OpenCV)
bg_cv2_path = os.path.join(IMG_DIR, "arka_plan.png")
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

# Background Music
music_path = os.path.join(SND_DIR, "menu_music.wav")

# 2. Game Assets
bg_img = load_image("arka_plan.png", (WINDOW_WIDTH, WINDOW_HEIGHT))
spawn_sound = load_sound("spawn.wav", 0.4)      
slice_sound = load_sound("slice.wav", 0.7)      
explosion_sound = load_sound("explosion.wav", 0.8) 
fuse_sound = load_sound("fuse.wav", 0.6)        

# Prepare Fruits (Slicing Logic)
def load_and_slice(name, size):
    """Loads a fruit image and creates two halves for the slicing effect."""
    path = os.path.join(IMG_DIR, name)
    if not os.path.exists(path): return None
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (size, size))
        w, h = img.get_size()
        left = img.subsurface((0, 0, w//2, h)).copy()
        right = img.subsurface((w//2, 0, w//2, h)).copy()
        return {'whole': img, 'h1': left, 'h2': right}
    except: return None

fruit_types = ['elma', 'karpuz', 'muz'] 
loaded_fruits = {}
for f in fruit_types:
    data = load_and_slice(f"{f}.png", 90)
    if data:
        data['score'] = 10
        loaded_fruits[f] = data
    else:
        # Fallback to colored circles if images are missing
        loaded_fruits[f] = {'score': 10, 'color': FRUIT_COLORS.get(f, WHITE)}

bomb_img = load_image("bomba.png", 90)

# --- CLASSES ---
class Fruit:
    def __init__(self, name):
        self.name = name
        self.data = loaded_fruits[name]
        self.is_image = 'whole' in self.data
        self.x = random.randint(100, WINDOW_WIDTH - 100)
        self.y = WINDOW_HEIGHT + 50
        # Physics setup
        if self.x < WINDOW_WIDTH // 2: self.speed_x = random.randint(2, 5)
        else: self.speed_x = random.randint(-5, -2)
        self.speed_y = random.randint(-17, -13)
        self.rotation = 0
        self.rot_speed = random.randint(-5, 5)

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += GRAVITY
        self.rotation += self.rot_speed
        if self.y > WINDOW_HEIGHT + 100: return "missed"
        return "active"

    def draw(self, surface):
        if self.is_image:
            img = self.data['whole']
            rot_img = pygame.transform.rotate(img, self.rotation)
            rect = rot_img.get_rect(center=(self.x, self.y))
            surface.blit(rot_img, rect)
        else:
            col = self.data.get('color', WHITE)
            pygame.draw.circle(surface, col, (int(self.x), int(self.y)), 45)

class Bomb:
    def __init__(self):
        self.x = random.randint(100, WINDOW_WIDTH - 100)
        self.y = WINDOW_HEIGHT + 50
        if self.x < WINDOW_WIDTH // 2: self.speed_x = random.randint(2, 5)
        else: self.speed_x = random.randint(-5, -2)
        self.speed_y = random.randint(-16, -13)
        self.rotation = 0

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += GRAVITY
        self.rotation += 2
        if self.y > WINDOW_HEIGHT + 100: return "missed"
        return "active"

    def draw(self, surface):
        if bomb_img:
            rot_img = pygame.transform.rotate(bomb_img, self.rotation)
            rect = rot_img.get_rect(center=(self.x, self.y))
            surface.blit(rot_img, rect)
        else:
            pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), 40)
            pygame.draw.line(surface, RED, (self.x-20, self.y-20), (self.x+20, self.y+20), 5)

class SlicedPiece:
    def __init__(self, asset, x, y, speed_x, rotation, is_image=True):
        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = -3
        self.rotation = rotation
        self.asset = asset
        self.is_image = is_image

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += GRAVITY + 0.1
        self.rotation += random.randint(-3, 3)

    def draw(self, surface):
        if self.is_image:
            rot_img = pygame.transform.rotate(self.asset, self.rotation)
            rect = rot_img.get_rect(center=(self.x, self.y))
            surface.blit(rot_img, rect)
        else:
            pygame.draw.circle(surface, self.asset, (int(self.x), int(self.y)), 25)

# --- MENU FUNCTIONS ---
def draw_main_menu_buttons(surface, finger_pos):
    # Draw Logo
    if logo_img:
        logo_rect = logo_img.get_rect(center=(WINDOW_WIDTH//2, 150))
        surface.blit(logo_img, logo_rect)
    else:
        title = score_font.render("FRUIT NINJA", True, GREEN)
        surface.blit(title, (WINDOW_WIDTH//2 - 180, 100))

    # Play Button Area
    btn_rect = pygame.Rect(0, 0, 250, 100)
    btn_rect.center = (WINDOW_WIDTH//2, 400)
    
    hover = False
    if finger_pos:
        if btn_rect.collidepoint(finger_pos):
            hover = True
    
    # Draw Button
    if play_btn_img:
        if hover:
            scaled_btn = pygame.transform.scale(play_btn_img, (220, 110))
            btn_rect = scaled_btn.get_rect(center=(WINDOW_WIDTH//2, 400))
            surface.blit(scaled_btn, btn_rect)
        else:
            surface.blit(play_btn_img, btn_rect)
    else:
        col = BUTTON_HOVER if hover else BUTTON_COLOR
        pygame.draw.rect(surface, col, btn_rect, border_radius=20)
        pygame.draw.rect(surface, WHITE, btn_rect, 5, border_radius=20)
        txt = font.render("PLAY", True, WHITE)
        txt_rect = txt.get_rect(center=btn_rect.center)
        surface.blit(txt, txt_rect)
    
    hint = font.render("Touch to Start", True, WHITE)
    surface.blit(hint, (WINDOW_WIDTH//2 - 100, 500))
    
    return hover

# --- MAIN GAME LOOP ---
def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    detector = htm.HandDetector(detection_con=0.7, max_hands=1)
    
    # Initialize Game Manager
    yonetici = OyunYoneticisi(WINDOW_WIDTH, WINDOW_HEIGHT)
    
    # States
    STATE_MAIN_MENU = "MAIN_MENU" 
    STATE_GAME = "GAME"
    STATE_SETTINGS = "SETTINGS"
    STATE_GAMEOVER = "GAMEOVER"
    
    game_state = STATE_MAIN_MENU
    last_state = STATE_MAIN_MENU
    
    # Start Music
    if os.path.exists(music_path):
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play(-1) 
        pygame.mixer.music.set_volume(0.5)
    
    # Game Variables
    fruits = []       
    sliced_pieces = [] 
    bombs = []        
    spawn_timer = 0
    score = 0
    lives = 3
    trail_points = []
    is_fuse_playing = False
    
    menu_click_timer = 0 
    
    while True:
        success, img = cap.read()
        if not success: continue
        
        # 1. Flip Camera
        img = cv2.flip(img, 1)
        
        # 2. Hand Detection
        img = detector.find_hands(img)
        lm_list = detector.find_position(img, draw=False)
        
        display_img = bg_cv2.copy()
        
        finger_pos = None
        pinch = False
        
        if len(lm_list) != 0:
            x, y = lm_list[8][1], lm_list[8][2] 
            bx, by = lm_list[4][1], lm_list[4][2] 
            
            # Map coordinates to window size
            game_x = int((x / 1280) * WINDOW_WIDTH)
            game_y = int((y / 720) * WINDOW_HEIGHT)
            finger_pos = (game_x, game_y)
            
            trail_points.append(finger_pos)
            if len(trail_points) > 10: trail_points.pop(0)

            # Check Pinch (Click)
            dist = math.hypot(x - bx, y - by)
            if dist < 60: 
                pinch = True
                cv2.circle(display_img, finger_pos, 15, (0, 255, 0), cv2.FILLED)
            else:
                cv2.circle(display_img, finger_pos, 15, (0, 0, 255), cv2.FILLED)
        else:
            trail_points.clear()

        # --- SOUND CONTROL FIX ---
        # Dynamically adjust music volume based on settings
        target_volume = 0.5 if yonetici.ses_aktif else 0.0
        pygame.mixer.music.set_volume(target_volume)
        
        # STATE 1: MAIN MENU 
        if game_state == STATE_MAIN_MENU:
            f_pos = finger_pos if finger_pos else (0,0)
            menu_rect = yonetici.sag_ust_menu_ikonu(display_img)
            mx, my, mw, mh = menu_rect
            
            if (mx < f_pos[0] < mx + mw) and (my < f_pos[1] < my + mh):
                if pinch: 
                    last_state = STATE_MAIN_MENU 
                    game_state = STATE_SETTINGS

            # Prepare Background and Menu UI
            img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            img_rgb = np.transpose(img_rgb, (1, 0, 2))
            img_surface = pygame.surfarray.make_surface(img_rgb)
            screen.blit(img_surface, (0,0))

            # Draw Custom Menu Buttons
            is_hovering = draw_main_menu_buttons(screen, finger_pos)
            
            # Draw Cursor
            if finger_pos:
                col = GREEN if pinch else (0, 255, 255)
                pygame.draw.circle(screen, col, finger_pos, 15)

            # Button Interaction Logic
            if is_hovering:
                menu_click_timer += 1
                if finger_pos:
                    pygame.draw.circle(screen, WHITE, finger_pos, 15 + menu_click_timer, 2)
                
                if menu_click_timer > 30: 
                    game_state = STATE_GAME
                    last_state = STATE_GAME
                    score = 0
                    lives = 3
                    fruits.clear(); sliced_pieces.clear(); bombs.clear()
            else:
                menu_click_timer = 0

        # STATE 2: GAMEPLAY
        elif game_state == STATE_GAME:
            spawn_timer += 1
            if spawn_timer > 50:
                spawn_timer = 0
                if spawn_sound and yonetici.ses_aktif: spawn_sound.play()
                
                if random.random() < 0.2: bombs.append(Bomb())
                else:
                    f_name = random.choice(list(loaded_fruits.keys()))
                    fruits.append(Fruit(f_name))

            # Fuse Sound Logic
            if len(bombs) > 0 and yonetici.ses_aktif:
                if fuse_sound and not is_fuse_playing:
                    fuse_sound.play(loops=-1)
                    is_fuse_playing = True
            else:
                if fuse_sound and is_fuse_playing:
                    fuse_sound.stop()
                    is_fuse_playing = False

            # Update Bombs
            for b in bombs[:]:
                status = b.update()
                if status == "missed": bombs.remove(b)
                else:
                    if finger_pos:
                        dist = math.hypot(finger_pos[0]-b.x, finger_pos[1]-b.y)
                        if dist < 45:
                            if explosion_sound and yonetici.ses_aktif: explosion_sound.play()
                            game_state = STATE_GAMEOVER

            # Update Fruits
            for f in fruits[:]:
                status = f.update()
                if status == "missed":
                    lives -= 1
                    if lives <= 0: game_state = STATE_GAMEOVER
                    fruits.remove(f)
                else:
                    if finger_pos:
                        dist = math.hypot(finger_pos[0]-f.x, finger_pos[1]-f.y)
                        if dist < 50:
                            if slice_sound and yonetici.ses_aktif: slice_sound.play()
                            score += f.data['score']
                            
                            # Create Sliced Pieces
                            if f.is_image:
                                p1 = SlicedPiece(f.data['h1'], f.x, f.y, -5, f.rotation)
                                p2 = SlicedPiece(f.data['h2'], f.x, f.y, 5, f.rotation)
                            else:
                                col = f.data.get('color', WHITE)
                                p1 = SlicedPiece(col, f.x, f.y, -5, 0, False)
                                p2 = SlicedPiece(col, f.x, f.y, 5, 0, False)
                            sliced_pieces.append(p1); sliced_pieces.append(p2)
                            fruits.remove(f)

            # Update Sliced Pieces
            for p in sliced_pieces[:]:
                p.update()
                if p.y > WINDOW_HEIGHT + 100: sliced_pieces.remove(p)

            # Menu Interaction within Game
            f_pos = finger_pos if finger_pos else (0,0)
            mx, my, mw, mh = WINDOW_WIDTH - 80, 20, 60, 60
            if (mx < f_pos[0] < mx + mw) and (my < f_pos[1] < my + mh):
                 if pinch: 
                     last_state = STATE_GAME 
                     game_state = STATE_SETTINGS

            # Rendering
            if bg_img: screen.blit(bg_img, (0,0))
            else: screen.fill((50, 50, 50))
            
            if len(trail_points) > 1:
                pygame.draw.lines(screen, (200, 255, 255), False, trail_points, 5)
            
            for b in bombs: b.draw(screen)
            for f in fruits: f.draw(screen)
            for p in sliced_pieces: p.draw(screen)
            
            sc = score_font.render(f"{score}", True, (255, 255, 0))
            screen.blit(sc, (30, 30))
            life_txt = font.render("X " * lives, True, RED)
            screen.blit(life_txt, (WINDOW_WIDTH - 150, 30))
            
            if finger_pos:
                col = GREEN if pinch else (0, 255, 255)
                pygame.draw.circle(screen, col, finger_pos, 15)
            
            # Draw Menu Icon
            pygame.draw.rect(screen, (100, 100, 100), (mx, my, mw, mh))
            pygame.draw.line(screen, WHITE, (mx+10, my+15), (mx+mw-10, my+15), 3)
            pygame.draw.line(screen, WHITE, (mx+10, my+30), (mx+mw-10, my+30), 3)
            pygame.draw.line(screen, WHITE, (mx+10, my+45), (mx+mw-10, my+45), 3)

        # STATE 3: SETTINGS MENU 
        elif game_state == STATE_SETTINGS:
            f_pos = finger_pos if finger_pos else (0,0)
            
            # Using compatibility layer for old function names
            komut = yonetici.menuyu_ciz_ve_yonet(display_img, f_pos, pinch)
            
            if komut == "BACK":
                game_state = last_state 
            elif komut == "EXIT":
                cap.release()
                cv2.destroyAllWindows()
                return

            img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            img_rgb = np.transpose(img_rgb, (1, 0, 2))
            img_surface = pygame.surfarray.make_surface(img_rgb)
            screen.blit(img_surface, (0,0))

        # STATE 4: GAME OVER MENU
        elif game_state == STATE_GAMEOVER:
            if is_fuse_playing and fuse_sound:
                fuse_sound.stop()
                is_fuse_playing = False
                
            f_pos = finger_pos if finger_pos else (0,0)
            komut = yonetici.game_over_menusu(display_img, f_pos, pinch)
            
            if komut == "RETRY":
                game_state = STATE_GAME
                score = 0
                lives = 3
                fruits.clear(); sliced_pieces.clear(); bombs.clear()
            elif komut == "EXIT":
                cap.release()
                cv2.destroyAllWindows()
                return

            # Rendering
            img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            img_rgb = np.transpose(img_rgb, (1, 0, 2))
            img_surface = pygame.surfarray.make_surface(img_rgb)
            screen.blit(img_surface, (0,0))
            
            sc_text = score_font.render(f"Score: {score}", True, WHITE)
            sc_rect = sc_text.get_rect(center=(WINDOW_WIDTH // 2, 100)) 
            screen.blit(sc_text, sc_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()