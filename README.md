# 🎮 EBATTBOY ARCADE

A computer vision-based arcade gaming platform controlled entirely with hand gestures using real-time camera input.

---

## 🚀 Features

* ✋ Hand gesture control using MediaPipe
* 🎯 Multiple mini-games in a single platform
* 🎮 Real-time interaction via webcam
* 🔊 Sound effects and dynamic feedback
* 🧠 Computer vision + game development integration

---

## 🕹️ Included Games

* **Flappy Hand** → Control the bird with finger gestures
* **Fruit Ninja** → Slice fruits using hand movement
* **Neon Rhythm** → React to directional inputs with precision
* **Virtual Goalkeeper** → Save incoming balls using both hands

---

## 🧠 Technologies Used

* Python
* OpenCV
* MediaPipe
* Pygame
* NumPy

---

## 📁 Project Structure

```
.
├── menu.py
├── flappy_hand.py
├── fruit_ninja.py
├── neon_rhythm.py
├── virtual_goalkeeper.py
├── hand_tracking_module.py
├── oyun_araclari.py
│
├── assets/
│   ├── images/
│   └── sounds/
│
└── requirements.txt
```

---

## ▶️ How to Run

1. Clone the repository:

```
git clone https://github.com/yourusername/ebattboy-ar-arcade.git
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Run the project:

```
python menu.py
```


## ⚠️ Requirements

* Webcam (for hand tracking)
* Python 3.9+
* Good lighting for accurate detection

## 💡 How It Works

The system uses MediaPipe to detect hand landmarks in real-time.
Finger positions are processed to detect gestures such as pinch or movement.
These gestures are mapped into in-game controls for interaction.

## 📌 Future Improvements

* More mini-games
* Multiplayer support
* Gesture customization
* Performance optimization

## 👨‍💻 Author

**Ali Toprak Tuğtekin**



