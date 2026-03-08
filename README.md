# 🧤 GuardianWalk

![Python](https://img.shields.io/badge/Python-3.10-blue)
![YOLOv8](https://img.shields.io/badge/YOLOv8-AI-red)
![ESP32](https://img.shields.io/badge/ESP32-CAM-green)
![Flask](https://img.shields.io/badge/Flask-API-black)

GuardianWalk is an **AI-powered wearable navigation system designed to assist visually impaired individuals**.
The system uses **YOLOv8 computer vision with an ESP32-CAM based wearable glove** to detect obstacles and guide the user through **vibration and audio feedback**.

---

## 🧠 System Architecture

![Architecture](docs/architecture.png)

### Processing Pipeline

ESP32-CAM → WiFi → AI Server → YOLOv8 Detection → Navigation Decision → Haptic Feedback

---

## ⚙ How It Works

1. **ESP32-CAM captures an image** of the surrounding environment.
2. The image is **sent to the AI server via WiFi**.
3. **YOLOv8 detects obstacles** such as people, furniture, and vehicles.
4. The system **determines the safest direction to move**.
5. ESP32 **activates vibration motors** to guide the user.
6. A **buzzer alerts the user** if an obstacle is very close.

---

## 🔧 Hardware Used

* ESP32-CAM
* Coin Vibration Motors (2x)
* Buzzer
* Rechargeable Battery (ICR Lithium-ion)
* Wearable Glove Mount

---

## 💻 Software Stack

* Python
* YOLOv8 (Ultralytics)
* Flask API
* OpenCV
* Arduino IDE

---

## 📂 Project Structure

```
GuardianWalk
│
├── server
│   └── AI detection server
│
├── esp32
│   └── ESP32 firmware
│
├── docs
│   └── diagrams and demo images
│
└── README.md
```

---

## 🚀 Installation

Clone the repository

git clone https://github.com/YOURUSERNAME/GuardianWalk.git

Install dependencies

pip install -r server/requirements.txt

Run the AI server

python server/guardianwalk_server.py

Upload the ESP32 firmware using Arduino IDE.

---

## 🔮 Future Improvements

* Depth detection using MiDaS
* Offline AI processing with Raspberry Pi
* GPS outdoor navigation
* Obstacle distance estimation
* Smart cane integration

---

## 👥 Project

This project was **developed as a group project** focusing on AI, computer vision, and embedded systems.

---

## ⭐ Goal

GuardianWalk aims to provide a **low-cost AI-powered wearable assistive technology** that improves mobility and safety for visually impaired individuals.
