# 🧤 GuardianWalk

<p align="center">
  <img src="banner.png" alt="GuardianWalk Banner" width="100%">
</p>

<p align="center">
  <strong>AI-Powered Wearable Navigation System for Visually Impaired Individuals</strong>
</p>

<p align="center">
An intelligent wearable assistive device that combines <b>Artificial Intelligence</b>, <b>Computer Vision</b>, and <b>Embedded Systems</b> to provide real-time obstacle detection, directional navigation, and voice guidance for visually impaired users.
</p>

---

# 📖 Overview

**GuardianWalk** is an AI-powered wearable navigation system designed to improve the mobility, independence, and safety of visually impaired individuals.

The system uses an **ESP32-CAM** mounted on a wearable glove to continuously capture images of the surrounding environment. These images are transmitted wirelessly to a **Python AI server**, where a **YOLOv8 object detection model** identifies nearby obstacles in real time.

After processing the scene, the AI determines the location of detected objects and provides intuitive navigation feedback through:

- 📳 Dual vibration motors for left and right directional guidance.
- 🎧 Bluetooth voice assistance for spoken navigation instructions.

The vibration intensity automatically increases as obstacles become closer, allowing users to understand both the **direction** and **distance** of nearby objects without requiring visual information.

GuardianWalk combines **Artificial Intelligence, Computer Vision, IoT, Embedded Systems, and Assistive Technology** into a lightweight wearable solution that enhances independent mobility.

---

# 🎯 Project Objective

The objective of GuardianWalk is to develop an affordable AI-powered wearable navigation device that assists visually impaired individuals by detecting obstacles in real time and providing intuitive directional feedback through vibration and Bluetooth voice guidance.

---

# ✨ Features

- 🧤 Wearable glove-based navigation system
- 📷 Real-time image capture using ESP32-CAM
- 🤖 YOLOv8 AI object detection
- 📡 Wireless communication over Wi-Fi
- 📳 Dual coin vibration motors
- 🎧 Bluetooth voice navigation
- 📏 Distance-aware vibration intensity
- ⚡ Lightweight and rechargeable
- ♿ Designed specifically for visually impaired users
- 🚶 Real-time obstacle avoidance

---

# 🧠 System Architecture

```text
                  +----------------+
                  |   ESP32-CAM    |
                  | Capture Images |
                  +--------+-------+
                           |
                           | Wi-Fi
                           ▼
                +----------------------+
                | Python AI Server     |
                | Flask + YOLOv8       |
                +----------+-----------+
                           |
                           ▼
                +----------------------+
                | Object Detection     |
                | Position & Distance  |
                +----------+-----------+
                           |
                           ▼
               +------------------------+
               | Navigation Decision    |
               +----------+-------------+
                          |
                          ▼
                 +----------------------+
                 | ESP32 Controller     |
                 +----------+-----------+
                            |
          +-----------------+------------------+
          |                                    |
          ▼                                    ▼
 Left Coin Vibration                  Right Coin Vibration
          │                                    │
          └──────────────┬─────────────────────┘
                         ▼
              Bluetooth Voice Guidance
```

---

# ⚙️ Working Principle

1. The ESP32-CAM continuously captures images of the user's surroundings.
2. Images are transmitted to the AI server through Wi-Fi.
3. The AI server processes every frame using the YOLOv8 object detection model.
4. Objects are identified along with their relative position and estimated distance.
5. The safest navigation direction is determined.
6. Commands are transmitted back to the ESP32.
7. Directional vibration and Bluetooth voice guidance assist the user in avoiding obstacles.

---

# 📳 Navigation Feedback System

GuardianWalk provides intuitive feedback using two vibration motors and Bluetooth voice guidance.

## Left Obstacle

- Left vibration motor activates.
- Bluetooth announces the obstacle on the left.
- Vibration becomes stronger as the obstacle gets closer.

---

## Right Obstacle

- Right vibration motor activates.
- Bluetooth announces the obstacle on the right.
- Stronger vibration indicates reduced distance.

---

## Obstacle in Front

- Both vibration motors activate simultaneously.
- Bluetooth warns the user that an obstacle is directly ahead.
- Continuous strong vibration indicates immediate danger.

---

## Clear Path

- No vibration.
- Bluetooth may provide navigation instructions or indicate that the path is clear.

---

# 📏 Distance-Based Feedback

GuardianWalk adjusts vibration intensity according to the detected object's distance.

| Estimated Distance | Feedback |
|-------------------|----------|
| Greater than 2 m | No vibration or light pulse |
| 1–2 m | Medium vibration |
| Less than 1 m | Strong vibration |
| Very Close | Continuous strong vibration + immediate voice warning |

This allows users to understand not only the direction of obstacles but also how close they are.

---

# 🎯 AI Detection Capabilities

GuardianWalk is capable of detecting various everyday objects, including:

- 🚶 Person
- 🚗 Car
- 🚌 Bus
- 🏍 Motorcycle
- 🚲 Bicycle
- 🪑 Chair
- 🛋 Sofa
- 🚪 Door
- 🪜 Stairs
- 🌳 Tree
- 🧱 Wall
- 📦 Box
- 🪧 Signboard
- 🛒 Shopping Cart
- 🐕 Animals
- Other common obstacles supported by YOLOv8

---

# 🔧 Hardware Components

| Component | Description |
|-----------|-------------|
| ESP32-CAM | Image acquisition |
| Left Coin Vibration Motor | Indicates obstacles on the left |
| Right Coin Vibration Motor | Indicates obstacles on the right |
| Bluetooth Audio Module | Voice guidance |
| Rechargeable Lithium-ion Battery | Portable power |
| Wearable Glove | Device mounting |
| Connecting Wires | Hardware connections |

---

# 💻 Software Stack

| Technology | Purpose |
|-----------|---------|
| Python | AI Processing |
| YOLOv8 (Ultralytics) | Object Detection |
| OpenCV | Image Processing |
| Flask | API Communication |
| Arduino IDE | ESP32 Programming |
| Git & GitHub | Version Control |

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/joshua14134/GuardianWalk.git

cd GuardianWalk
```

---

## Install Python Packages

```bash
pip install -r server/requirements.txt
```

---

## Start AI Server

```bash
python server/guardianwalk_server.py
```

---

## Upload ESP32 Firmware

1. Open Arduino IDE.
2. Open the **esp32** folder.
3. Select the ESP32-CAM board.
4. Upload the firmware.
5. Connect the ESP32-CAM to the same Wi-Fi network as the AI server.

---

# 🔄 Complete Workflow

```text
ESP32-CAM
      │
      ▼
Capture Image
      │
      ▼
Send Image via Wi-Fi
      │
      ▼
Python Flask Server
      │
      ▼
YOLOv8 Detection
      │
      ▼
Determine Position
      │
      ▼
Estimate Distance
      │
      ▼
Generate Navigation
      │
      ▼
ESP32 Controller
      │
      ├── Left Vibration
      ├── Right Vibration
      └── Bluetooth Voice Output
```

---

# 📸 Project Demonstration

<p align="center">
<img src="banner.png" width="100%">
</p>

The demonstration above showcases the complete GuardianWalk system, including the wearable glove prototype, ESP32-CAM, AI processing workflow, object detection, directional navigation, and Bluetooth voice guidance.

---

# 💡 Applications

- Smart Assistive Technology
- Wearable AI Devices
- Navigation Assistance
- Healthcare Technology
- Embedded AI Systems
- Computer Vision Research
- IoT Applications
- Accessibility Solutions

---

# 🚀 Future Enhancements

- 📏 Monocular depth estimation
- 🗺 GPS-assisted outdoor navigation
- 📱 Android companion application
- ☁ Cloud synchronization
- 🧠 Edge AI processing using Raspberry Pi
- 🎙 Advanced voice assistant
- 🔋 Longer battery life
- 🦯 Smart cane integration
- 🌍 Offline object detection

---

# 📚 Learning Outcomes

This project demonstrates practical implementation of:

- Artificial Intelligence
- Deep Learning
- Computer Vision
- Object Detection
- Embedded Systems
- ESP32 Development
- OpenCV
- Flask API Development
- Python Programming
- IoT Communication
- Wearable Computing
- Human-Centered Assistive Technology

---

# 👥 Team Project

GuardianWalk was developed as a collaborative academic project focused on designing an affordable AI-powered wearable navigation system for visually impaired individuals. The project integrates Artificial Intelligence, Embedded Systems, IoT, and Computer Vision to deliver real-time obstacle detection and intuitive navigation assistance.

---

# 📈 Future Scope

Future versions of GuardianWalk can integrate advanced depth estimation, GPS navigation, indoor mapping, SLAM, cloud connectivity, mobile applications, and edge AI processing to improve navigation accuracy and create a completely standalone wearable navigation system.

---

# 👨‍💻 Developer

**Joshua Greg Colaco**

GitHub: **https://github.com/joshua14134**

---

# 📄 License

This project is licensed under the **MIT License**.

---

<p align="center">
❤️ Built to improve accessibility through Artificial Intelligence and Assistive Technology.
</p>

<p align="center">
⭐ If you found this project useful, consider giving it a <b>Star</b> on GitHub.
</p>
