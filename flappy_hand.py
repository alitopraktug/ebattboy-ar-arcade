import cv2
import pygame
import sys
import math
import random
import numpy as np
import os
import hand_tracking_module as htm
from oyun_araclari import OyunYoneticisi 

# --- SETTINGS ---
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
GRAVITY = 0.5
JUMP_STRENGTH = -8
PIPE_SPEED = 5
PIPE_GAP = 160
FINGER_DISTANCE_THRESHOLD = 30
BASE_HEIGHT = 100        

# --- FILE PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "assets", "images")
SND_DIR = os.path.join(BASE_DIR, "assets", "sounds")

# --- START PYGAME ---
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Flappy Hand AR")
clock = pygame.time.Clock()

# --- UPLOAD IMAGE ---
def load_image(name, width, height):
    try:
        path = os.path.join(IMG_DIR, name)
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (width, height))
    except Exception as e:
        print(f"Uyarı: {name} bulunamadı.")
        return None

# UPLOAD ENTITIES
bird_down = load_image("yellowbird-downflap.png", 50, 40)
bird_mid = load_image("yellowbird-midflap.png", 50, 40)
bird_up = load_image("yellowbird-upflap.png", 50, 40)
pipe_img = load_image("pipe.png", 80, 400)
bg_img = load_image("background.png", WINDOW_WIDTH, WINDOW_HEIGHT)
base_img = load_image("base.png", WINDOW_WIDTH, BASE_HEIGHT)

# --- UPLOAD BACKGROUND FOR PYGAME ---
bg_cv2_path = os.path.join(IMG_DIR, "background.png")
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

# --- UPLOAD SOUNDS ---
def load_sound(name):
    try:
        return pygame.mixer.Sound(os.path.join(SND_DIR, name))
    except:
        return None

jump_sound = load_sound("jump.wav")
crash_sound = load_sound("crash.wav")
point_sound = load_sound("point.wav")

# --- CLASSES ---
class Bird:
    def __init__(self):
        self.x = 100
        self.y = WINDOW_HEIGHT // 2
        self.velocity = 0
        self.width = 50
        self.height = 40
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.angle = 0 
        self.images = [bird_down, bird_mid, bird_up]
        self.index = 0
        self.image = self.images[self.index]
        self.counter = 0

    def move(self, jump=False, play_sound=True):
        if jump:
            self.velocity = JUMP_STRENGTH
            if jump_sound and play_sound: jump_sound.play()
            self.angle = 25
            self.counter = 0
        
        self.velocity += GRAVITY
        self.y += self.velocity
        
        if self.velocity <= 0: self.angle = 25
        else:
            if self.angle > -90: self.angle -= 3 

        if self.angle > -80:
            self.counter += 1
            if self.counter >= 5:
                self.index += 1
                if self.index >= 3: self.index = 0
                self.counter = 0
        else: self.index = 1 

        self.image = self.images[self.index]
        if self.y < 0: self.y = 0
        self.rect.y = int(self.y)

    def draw(self, surface):
        if self.image:
            rotated_image = pygame.transform.rotate(self.image, self.angle)
            new_rect = rotated_image.get_rect(center=self.rect.center)
            surface.blit(rotated_image, new_rect.topleft)
        else:
            pygame.draw.rect(surface, (255, 0, 0), self.rect)

class Pipe:
    def __init__(self, x):
        self.x = x
        self.width = 80
        playable_height = WINDOW_HEIGHT - BASE_HEIGHT
        self.gap_start = random.randint(50, playable_height - PIPE_GAP - 50)
        
        self.rect_top = pygame.Rect(self.x, 0, self.width, self.gap_start)
        self.rect_bottom = pygame.Rect(self.x, self.gap_start + PIPE_GAP, self.width, WINDOW_HEIGHT)
        self.passed = False

    def move(self):
        self.x -= PIPE_SPEED
        self.rect_top.x = int(self.x)
        self.rect_bottom.x = int(self.x)

    def draw(self, surface):
        if pipe_img:
            pipe_top_img = pygame.transform.flip(pipe_img, False, True)
            surface.blit(pipe_top_img, (self.x, self.gap_start - 400))
            surface.blit(pipe_img, (self.x, self.gap_start + PIPE_GAP))
        else:
            pygame.draw.rect(surface, (0, 255, 0), self.rect_top)
            pygame.draw.rect(surface, (0, 255, 0), self.rect_bottom)

# --- MAIN LOOP ---
def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, WINDOW_WIDTH)
    cap.set(4, WINDOW_HEIGHT)
    
    detector = htm.HandDetector(detection_con=0.7)
    yonetici = OyunYoneticisi(WINDOW_WIDTH, WINDOW_HEIGHT)
    
    STATE_START = 0
    STATE_GAME = 1
    STATE_MENU = 2
    STATE_GAMEOVER = 3
    state = STATE_START
    
    bird = Bird()
    pipes = [Pipe(WINDOW_WIDTH + 200)]
    score = 0
    font = pygame.font.Font(None, 50)
    game_over = False
    base_x = 0

    while True:
        success, img = cap.read()
        if not success: continue

        # 1. CAMERA MIRROR
        img = cv2.flip(img, 1)
        
        # 2. HAND DETECTION
        img = detector.find_hands(img)
        lm_list = detector.find_position(img, draw=False)

        # Background copy (to hide the face)
        display_img = bg_cv2.copy() 

        mouse_pos = (0, 0)
        pinch = False
        jump_cmd = False

        if len(lm_list) != 0:
            x1, y1 = lm_list[4][1], lm_list[4][2] 
            x2, y2 = lm_list[8][1], lm_list[8][2] 
            mouse_pos = (x2, y2)
            
            length = math.hypot(x2 - x1, y2 - y1)
            
            # draw cursor
            if length < FINGER_DISTANCE_THRESHOLD:
                cv2.circle(display_img, mouse_pos, 15, (0, 255, 0), cv2.FILLED) 
                jump_cmd = True
                pinch = True
            else:
                cv2.circle(display_img, mouse_pos, 15, (0, 0, 255), cv2.FILLED) 

        # --- STATUS ---
        
        # START SCREEN
        if state == STATE_START:
            basladi = yonetici.beat_saber_buton(display_img, "HOLD TO PLAY", 
                                                WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 50, 
                                                300, 100, mouse_pos)
            if basladi:
                bird = Bird()
                pipes = [Pipe(WINDOW_WIDTH + 200)]
                score = 0
                game_over = False
                state = STATE_GAME
            
            menu_rect = yonetici.sag_ust_menu_ikonu(display_img)
            mx, my, mw, mh = menu_rect
            if (mx < mouse_pos[0] < mx + mw) and (my < mouse_pos[1] < my + mh):
                if pinch: state = STATE_MENU

        # GAME MODE
        elif state == STATE_GAME:
            if not game_over:
                # BIRD MOVEMENT
                bird.move(jump_cmd, play_sound=yonetici.ses_aktif)
                
                if bird.rect.bottom >= WINDOW_HEIGHT - BASE_HEIGHT + 10:
                    if crash_sound and yonetici.ses_aktif: crash_sound.play()
                    game_over = True
                    state = STATE_GAMEOVER 
                
                if pipes[-1].x < WINDOW_WIDTH - 300:
                    pipes.append(Pipe(WINDOW_WIDTH))

                for pipe in pipes:
                    pipe.move()
                    if bird.rect.colliderect(pipe.rect_top) or bird.rect.colliderect(pipe.rect_bottom):
                        if crash_sound and yonetici.ses_aktif: crash_sound.play()
                        game_over = True
                        state = STATE_GAMEOVER 

                    if not pipe.passed and pipe.x < bird.x:
                        score += 1
                        if point_sound and yonetici.ses_aktif: point_sound.play()
                        pipe.passed = True
                
                if pipes[0].x < -100: pipes.pop(0)
                
                base_x -= PIPE_SPEED
                if base_x <= -WINDOW_WIDTH: base_x = 0

            mx, my, mw, mh = WINDOW_WIDTH - 80, 20, 60, 60
            if (mx < mouse_pos[0] < mx + mw) and (my < mouse_pos[1] < my + mh):
                 if pinch: state = STATE_MENU

        # MENU MODE
        elif state == STATE_MENU:
            komut = yonetici.menuyu_ciz_ve_yonet(display_img, mouse_pos, pinch)
            if komut == "BACK":
                state = STATE_GAME if not game_over else STATE_START
            elif komut == "EXIT":
                cap.release()
                cv2.destroyAllWindows()
                return 

        # GAME OVER MOD
        elif state == STATE_GAMEOVER:
            komut = yonetici.game_over_menusu(display_img, mouse_pos, pinch)
            if komut == "RETRY":
                bird = Bird()
                pipes = [Pipe(WINDOW_WIDTH + 200)]
                score = 0
                game_over = False
                state = STATE_GAME
            elif komut == "EXIT":
                cap.release()
                cv2.destroyAllWindows()
                return
        
        # 1. DRAW THE MENUS
        if state != STATE_GAME:
            img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            img_rgb = np.transpose(img_rgb, (1, 0, 2))
            
            img_surface = pygame.surfarray.make_surface(img_rgb)
            screen.blit(img_surface, (0,0))

        # 2. GAME GRAPHICS
        if state == STATE_GAME or state == STATE_GAMEOVER:
            if bg_img: screen.blit(bg_img, (0,0))
            
            bird.draw(screen)
            for pipe in pipes: pipe.draw(screen)
            
            if base_img:
                screen.blit(base_img, (base_x, WINDOW_HEIGHT - BASE_HEIGHT))
                screen.blit(base_img, (base_x + WINDOW_WIDTH, WINDOW_HEIGHT - BASE_HEIGHT))
            else:
                pygame.draw.rect(screen, (200, 200, 100), (0, WINDOW_HEIGHT - BASE_HEIGHT, WINDOW_WIDTH, BASE_HEIGHT))

            score_text = font.render(f"{score}", True, (255, 255, 255))
            screen.blit(score_text, (WINDOW_WIDTH//2, 50))
            
            # In-game cursor and menu button
            if state == STATE_GAME:
                cursor_color = (0, 255, 0) if pinch else (0, 0, 255)
                pygame.draw.circle(screen, cursor_color, mouse_pos, 15)
                
                mx, my, mw, mh = WINDOW_WIDTH - 80, 20, 60, 60
                pygame.draw.rect(screen, (100, 100, 100), (mx, my, mw, mh))
                pygame.draw.line(screen, (255,255,255), (mx+10, my+15), (mx+mw-10, my+15), 3)
                pygame.draw.line(screen, (255,255,255), (mx+10, my+30), (mx+mw-10, my+30), 3)
                pygame.draw.line(screen, (255,255,255), (mx+10, my+45), (mx+mw-10, my+45), 3)

        if state == STATE_GAMEOVER:
             img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
             img_rgb = np.transpose(img_rgb, (1, 0, 2))
             img_surface = pygame.surfarray.make_surface(img_rgb)
             screen.blit(img_surface, (0,0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        pygame.display.update()
        clock.tick(30)

if __name__ == "__main__":
    main()