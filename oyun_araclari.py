import cv2
import time
import numpy as np

class GameManager:
    def __init__(self, w=1000, h=700):
        self.w = w
        self.h = h
        self.hover_start_time = 0
        self.active_button_key = None 
        self.sound_active = True
        
        # --- BUTTON DEFINITIONS ---
        cx, cy = w // 2, h // 2
        
        self.settings_btns = {
            "main_menu": {"rect": [cx - 150, cy - 60, 300, 60], "text": "MAIN MENU", "color": (0, 0, 255)},
            "sound":     {"rect": [cx - 150, cy + 20, 300, 60], "text": "SOUND: ON", "color": (255, 0, 255)},
            "back":      {"rect": [cx - 150, cy + 100, 300, 60], "text": "BACK TO GAME", "color": (0, 255, 0)}
        }

        self.gameover_btns = {
            "retry": {"rect": [cx - 150, cy - 30, 300, 60], "text": "RETRY", "color": (0, 200, 255)},
            "menu":  {"rect": [cx - 150, cy + 50, 300, 60], "text": "MAIN MENU", "color": (0, 0, 255)}
        }

    def _draw_button(self, img, key, btn, mouse_pos, pinch=False):
        """
        Works with both HOVER (Wait) and PINCH (Click) logic.
        """
        x, y, w, h = btn["rect"]
        text = btn["text"]
        color = btn["color"]
        
        triggered = False
        # Is mouse over the button?
        hover = (x < mouse_pos[0] < x + w) and (y < mouse_pos[1] < y + h)

        if hover:
            # 1. PINCH CHECK
            if pinch:
                triggered = True
                self.hover_start_time = 0
                self.active_button_key = None
            
            # 2. HOVER (WAIT) CHECK
            else:
                if self.active_button_key != key:
                    self.active_button_key = key
                    self.hover_start_time = time.time()
                
                elapsed_time = time.time() - self.hover_start_time
                fill_ratio = min(elapsed_time / 1.5, 1.0) 
                
                # Draw loading bar effect
                cv2.rectangle(img, (x, y), (x + int(w * fill_ratio), y + h), (0, 200, 0), -1)
                
                if fill_ratio >= 1.0:
                    triggered = True
                    self.hover_start_time = 0
                    self.active_button_key = None
        else:
            if self.active_button_key == key:
                self.active_button_key = None
                self.hover_start_time = 0

        # Draw Frame and Text
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 2)
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(text, font, 0.8, 2)[0]
        tx = x + (w - text_size[0]) // 2
        ty = y + (h + text_size[1]) // 2
        text_color = (255, 255, 255) if hover else color
        
        cv2.putText(img, text, (tx, ty), font, 0.8, text_color, 2)
        
        return triggered

    def draw_hold_button(self, img, text, x, y, w, h, mouse_pos):
        dummy_btn = {"rect": [x, y, w, h], "text": text, "color": (255, 255, 255)}
        return self._draw_button(img, "start_btn", dummy_btn, mouse_pos, pinch=False)

    def draw_top_right_menu_icon(self, img):
        x, y, w, h = self.w - 80, 20, 60, 60 
        cv2.rectangle(img, (x, y), (x + w, y + h), (100, 100, 100), -1)
        cv2.line(img, (x+10, y+15), (x+w-10, y+15), (255,255,255), 3)
        cv2.line(img, (x+10, y+30), (x+w-10, y+30), (255,255,255), 3)
        cv2.line(img, (x+10, y+45), (x+w-10, y+45), (255,255,255), 3)
        return [x, y, w, h]

    def manage_settings_menu(self, img, mouse_pos, pinch):
        overlay = img.copy()
        cv2.rectangle(img, (0, 0), (self.w, self.h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)
        
        command = None
        cv2.putText(img, "SETTINGS", (self.w//2 - 100, 100), cv2.FONT_HERSHEY_DUPLEX, 2, (255, 255, 255), 2)

        for key, btn in self.settings_btns.items():
            clicked = self._draw_button(img, key, btn, mouse_pos, pinch)
            
            if clicked:
                if key == "main_menu": command = "EXIT"
                elif key == "back": command = "BACK"
                elif key == "sound":
                    self.sound_active = not self.sound_active
                    btn["text"] = "SOUND: ON" if self.sound_active else "SOUND: OFF"
        return command

    def manage_game_over_menu(self, img, mouse_pos, pinch):
        overlay = img.copy()
        cv2.rectangle(img, (0, 0), (self.w, self.h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)

        command = None
        cx, cy = self.w // 2, self.h // 2
        
        cv2.putText(img, "GAME OVER", (cx - 130, cy - 100), cv2.FONT_HERSHEY_DUPLEX, 2, (255, 255, 255), 3)

        for key, btn in self.gameover_btns.items():
            clicked = self._draw_button(img, key, btn, mouse_pos, pinch)
            
            if clicked:
                if key == "retry": command = "RETRY"
                elif key == "menu": command = "EXIT"
        
        return command

    # --- COMPATIBILITY LAYER ---
    beat_saber_buton = draw_hold_button
    sag_ust_menu_ikonu = draw_top_right_menu_icon
    menuyu_ciz_ve_yonet = manage_settings_menu
    game_over_menusu = manage_game_over_menu
    @property
    def ses_aktif(self): return self.sound_active
    @ses_aktif.setter
    def ses_aktif(self, value): self.sound_active = value
    
OyunYoneticisi = GameManager