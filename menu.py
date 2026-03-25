import pygame
import cv2
import mediapipe as mp
import sys
import os
import subprocess
import numpy as np

# --- SETTINGS ---
GENISLIK, YUKSEKLIK = 1000, 700
FPS = 30
KAMERA_NO = 0

# Colors
SIYAH = (10, 10, 20)
NEON_MAVI = (0, 200, 255)
NEON_YESIL = (0, 255, 100)
NEON_PEMBE = (255, 0, 127)
BEYAZ = (255, 255, 255)
GRİ = (50, 50, 50)
KIRMIZI = (255, 50, 50) 

# File Paths
MAIN_MUSIC = 'assets/sounds/main_menu_theme.mp3'
GAMES = [
    {'id': 'flappy', 'title': 'Flappy Hand', 'script': 'flappy_hand.py', 'img': 'assets/images/logo_flappy.png', 'sound': 'assets/sounds/flappy_theme.mp3', 'pos': (50, 200)},
    {'id': 'ninja',  'title': 'Fruit Ninja', 'script': 'fruit_ninja.py', 'img': 'assets/images/logo_ninja.png',  'sound': 'assets/sounds/ninja_theme.mp3',  'pos': (280, 200)},
    {'id': 'goal',   'title': 'Goal Keeper', 'script': 'virtual_goalkeeper.py','img': 'assets/images/logo_goal.png', 'sound': 'assets/sounds/goal_theme.mp3',   'pos': (510, 200)},
    {'id': 'neon',   'title': 'Neon Rhythm', 'script': 'neon_rhythm.py', 'img': 'assets/images/logo_neon.png',  'sound': 'assets/sounds/neon_theme.mp3',  'pos': (740, 200)},
]

# --- START ---
pygame.init()
pygame.mixer.init()
ekran = pygame.display.set_mode((GENISLIK, YUKSEKLIK))
pygame.display.set_caption("EBATTBOY™ ARCADE")
saat = pygame.time.Clock()
font_baslik = pygame.font.SysFont("Arial Black", 50)
font_alt = pygame.font.SysFont("Arial", 20)

# --- MENÜ STATES ---
DURUM_ANA = 0
DURUM_OYUNLAR = 1
DURUM_AYARLAR = 2
aktif_durum = DURUM_ANA

# --- SETTING VARIABLES ---
ses_duzeyi = 0.5
tam_ekran = False
pygame.mixer.music.set_volume(ses_duzeyi)
calan_muzik = "" 

# --- MEDIAPIPE ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
cap = cv2.VideoCapture(KAMERA_NO)
cap.set(3, 640)
cap.set(4, 480)

# --- UPLOAD IMAGES ---
def resim_yukle(path, size):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        s = pygame.Surface(size); s.fill(GRİ); return s

# Prapare game cards
KART_BOYUT = (200, 250)
KART_BUYUK = (220, 270)
for game in GAMES:
    game['surf_normal'] = resim_yukle(game['img'], KART_BOYUT)
    game['surf_hover'] = resim_yukle(game['img'], KART_BUYUK)
    game['rect'] = game['surf_normal'].get_rect(topleft=game['pos'])

# --- FUNCTIONS ---
def muzik_yonet(hedef_muzik):
    global calan_muzik
    if calan_muzik != hedef_muzik:# Only play if it changes
        try:
            pygame.mixer.music.load(hedef_muzik)
            pygame.mixer.music.play(-1)
            calan_muzik = hedef_muzik
        except: pass

def oyunu_baslat(script_path):
    global cap, calan_muzik
    
    # Stop the music and put down the camera.
    pygame.mixer.music.stop()
    calan_muzik = ""
    if cap.isOpened(): cap.release()
    cv2.destroyAllWindows()
    
    ekran.fill(SIYAH)
    yazi = font_baslik.render("OYUN BAŞLIYOR...", True, NEON_YESIL)
    ekran.blit(yazi, (GENISLIK//2 - yazi.get_width()//2, YUKSEKLIK//2))
    pygame.display.update()

    # RETRY LOOP
    devam_et = True
    while devam_et:
        try:
            python_exe = sys.executable
            kod = subprocess.call([python_exe, script_path]) 
            if kod != 1:
                devam_et = False
            else:
                print("Oyun yeniden başlatılıyor...")
        except Exception as e:
            print("Hata:", e)
            devam_et = False

    cap = cv2.VideoCapture(KAMERA_NO)
    cap.set(3, 640); cap.set(4, 480)
    muzik_yonet(MAIN_MUSIC)

# --- BUTON CLASS ---
class Buton:
    def __init__(self, text, x, y, w, h, renk):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.renk = renk
        self.orj_renk = renk
    
    def ciz(self, ekran, hover=False):
        renk = NEON_YESIL if hover else self.renk
        pygame.draw.rect(ekran, renk, self.rect, border_radius=15)
        pygame.draw.rect(ekran, BEYAZ, self.rect, 2, border_radius=15)
        txt = font_alt.render(self.text, True, SIYAH if hover else BEYAZ)
        ekran.blit(txt, txt.get_rect(center=self.rect.center))

# Interface Buttons
btn_games = Buton("GAMES", 300, 280, 400, 60, NEON_MAVI)
btn_settings = Buton("SETTINGS", 300, 380, 400, 60, NEON_PEMBE)
btn_exit = Buton("EXIT TO DESKTOP", 300, 480, 400, 60, KIRMIZI) 

btn_back = Buton("BACK", 50, 50, 100, 40, GRİ)
btn_fullscreen = Buton("TAM EKRAN: KAPALI", 300, 200, 400, 50, NEON_MAVI)

# Slider
slider_rect = pygame.Rect(300, 350, 400, 20)
slider_knob = pygame.Rect(300 + int(ses_duzeyi*400), 340, 20, 40)

# --- MAIN LOOP ---
running = True
sanal_mouse = (0, 0)
tiklama_zamani = 0
aktif_hover = None
muzik_yonet(MAIN_MUSIC)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
    success, img = cap.read()
    if not success: break
    img = cv2.flip(img, 1)
    results = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    
    pinch = False
    if results.multi_hand_landmarks:
        lm = results.multi_hand_landmarks[0].landmark
        ix, iy = int(lm[8].x * GENISLIK), int(lm[8].y * YUKSEKLIK) 
        bx, by = int(lm[4].x * GENISLIK), int(lm[4].y * YUKSEKLIK) 
        sanal_mouse = (ix, iy)
        if ((ix-bx)**2 + (iy-by)**2)**0.5 < 40: 
            if pygame.time.get_ticks() - tiklama_zamani > 500: 
                pinch = True
                tiklama_zamani = pygame.time.get_ticks()

    ekran.fill(SIYAH)
    baslik = font_baslik.render("EBATTBOY™", True, NEON_MAVI)
    ekran.blit(baslik, (GENISLIK//2 - baslik.get_width()//2, 50))

    if aktif_durum == DURUM_ANA:
        muzik_yonet(MAIN_MUSIC)
        
        # Buttons
        btn_games.ciz(ekran, btn_games.rect.collidepoint(sanal_mouse))
        btn_settings.ciz(ekran, btn_settings.rect.collidepoint(sanal_mouse))
        btn_exit.ciz(ekran, btn_exit.rect.collidepoint(sanal_mouse)) 
        
        if pinch:
            if btn_games.rect.collidepoint(sanal_mouse): aktif_durum = DURUM_OYUNLAR
            elif btn_settings.rect.collidepoint(sanal_mouse): aktif_durum = DURUM_AYARLAR
            elif btn_exit.rect.collidepoint(sanal_mouse): 
                running = False 

    elif aktif_durum == DURUM_AYARLAR:
        btn_back.ciz(ekran, btn_back.rect.collidepoint(sanal_mouse))
        
        # Full Screen Button
        btn_fullscreen.text = "TAM EKRAN: " + ("ACIK" if tam_ekran else "KAPALI")
        btn_fullscreen.ciz(ekran, btn_fullscreen.rect.collidepoint(sanal_mouse))
        
        # Sound Slider
        pygame.draw.rect(ekran, GRİ, slider_rect, border_radius=10)
        pygame.draw.rect(ekran, NEON_YESIL, (slider_rect.x, slider_rect.y, slider_knob.centerx - slider_rect.x, 20), border_radius=10)
        pygame.draw.rect(ekran, BEYAZ, slider_knob, border_radius=5)
        yazi_ses = font_alt.render(f"SES: %{int(ses_duzeyi*100)}", True, BEYAZ)
        ekran.blit(yazi_ses, (720, 345))

        # Logic
        if slider_rect.collidepoint(sanal_mouse) and pinch:
             new_x = max(slider_rect.left, min(sanal_mouse[0], slider_rect.right))
             ses_duzeyi = (new_x - slider_rect.left) / slider_rect.width
             pygame.mixer.music.set_volume(ses_duzeyi)
             slider_knob.centerx = new_x
        
        if pinch:
            if btn_back.rect.collidepoint(sanal_mouse): aktif_durum = DURUM_ANA
            if btn_fullscreen.rect.collidepoint(sanal_mouse):
                tam_ekran = not tam_ekran
                if tam_ekran: pygame.display.set_mode((GENISLIK, YUKSEKLIK), pygame.FULLSCREEN)
                else: pygame.display.set_mode((GENISLIK, YUKSEKLIK))

    elif aktif_durum == DURUM_OYUNLAR:
        btn_back.ciz(ekran, btn_back.rect.collidepoint(sanal_mouse))
        if pinch and btn_back.rect.collidepoint(sanal_mouse): aktif_durum = DURUM_ANA

        # Cards
        yeni_hover = None
        for game in GAMES:
            hover = game['rect'].collidepoint(sanal_mouse)
            if hover: yeni_hover = game['id']
            
            # Drawing
            img = game['surf_hover'] if hover else game['surf_normal']
            rect = img.get_rect(center=game['rect'].center) if hover else game['rect']
            ekran.blit(img, rect)
            if hover: pygame.draw.rect(ekran, NEON_YESIL, rect, 3, border_radius=15)
            
            # Title
            txt = font_alt.render(game['title'], True, NEON_YESIL if hover else GRİ)
            ekran.blit(txt, (rect.centerx - txt.get_width()//2, rect.bottom + 10))

        # Music and Click
        if yeni_hover: muzik_yonet([g['sound'] for g in GAMES if g['id'] == yeni_hover][0])
        else: muzik_yonet(MAIN_MUSIC)

        if pinch and yeni_hover:
             oyunu_baslat([g['script'] for g in GAMES if g['id'] == yeni_hover][0])

    # Draw Mouse
    pygame.draw.circle(ekran, NEON_MAVI, sanal_mouse, 10)
    if pinch: pygame.draw.circle(ekran, NEON_PEMBE, sanal_mouse, 15, 2)

    pygame.display.update()
    saat.tick(FPS)

cap.release()
cv2.destroyAllWindows()
pygame.quit()