# 🧤 GuardianWalk

<p align="center">
  <img src="banner.png" alt="GuardianWalk Banner" width="100%">
</p>

<p align="center">
  <strong>AI-Powered Wearable Navigation System for Visually Impaired Individuals</strong>
</p>

<p align="center">
  An intelligent wearable glove that combines <b>Computer Vision</b>, <b>Artificial Intelligence</b>, and <b>Embedded Systems</b> to provide real-time obstacle detection and navigation assistance.
</p>

---

# 📖 Overview

**GuardianWalk** is an AI-powered wearable navigation system developed to enhance the mobility, independence, and safety of visually impaired individuals.

The system integrates an **ESP32-CAM**, **YOLOv8 object detection**, and a **Python-based AI server** to identify obstacles in real time. Once an object is detected, the system determines the safest direction and guides the user using **vibration motors** and **audio alerts**.

GuardianWalk demonstrates the practical integration of **Artificial Intelligence, Computer Vision, IoT, Embedded Systems, and Assistive Technology** into a lightweight, wearable solution.

---

# 🎯 Project Objective

The objective of GuardianWalk is to develop an affordable smart wearable device that enables visually impaired users to navigate safely by detecting nearby obstacles and providing intuitive haptic and audio feedback in real time.

---

# ✨ Key Features

- 🧤 Wearable glove-based navigation system
- 📷 Real-time image capture using ESP32-CAM
- 🤖 YOLOv8 AI-powered object detection
- 📡 Wireless communication via Wi-Fi
- 📳 Haptic navigation using vibration motors
- 🔊 Audio alerts using buzzer
- ⚡ Lightweight and portable design
- ♿ Designed specifically for visually impaired users

---

# 🧠 System Architecture

```
                +----------------+
                |   ESP32-CAM    |
                | Capture Images |
                +--------+-------+
                         |
                         | Wi-Fi
                         ▼
               +-------------------+
               |   Python Server   |
               | Flask API + AI    |
               +--------+----------+
                        |
                        ▼
             +----------------------+
             | YOLOv8 Object Model  |
             +----------+-----------+
                        |
                        ▼
            +------------------------+
            | Navigation Decision    |
            +----------+-------------+
                       |
                       ▼
             +----------------------+
             | ESP32 Feedback Unit  |
             +----------+-----------+
                        |
          +-------------+--------------+
          |                            |
          ▼                            ▼
  Vibration Motors                 Buzzer Alert
```

---

# ⚙️ Working Principle

1. The ESP32-CAM captures images continuously.
2. Images are transmitted to the AI server through Wi-Fi.
3. The server processes each image using the YOLOv8 object detection model.
4. Detected objects are classified and analyzed.
5. The safest navigation direction is determined.
6. Commands are sent back to the ESP32.
7. Vibration motors guide the user, while the buzzer warns about nearby obstacles.

---

# 🔧 Hardware Components

| Component | Description |
|-----------|-------------|
| ESP32-CAM | Captures real-time images |
| Coin Vibration Motors (2x) | Directional haptic feedback |
| Buzzer | Audio warning system |
| Rechargeable Lithium-ion Battery | Portable power source |
| Wearable Glove | Device mounting platform |
| Connecting Wires | Circuit connections |

---

# 💻 Software Stack

| Technology | Purpose |
|-----------|---------|
| Python | AI Processing |
| YOLOv8 (Ultralytics) | Object Detection |
| OpenCV | Image Processing |
| Flask | Communication API |
| Arduino IDE | ESP32 Programming |
| Git & GitHub | Version Control |

---

# 🚀 Installation

## Clone the Repository

```bash
git clone https://github.com/joshua14134/GuardianWalk.git

cd GuardianWalk
```

---

## Install Dependencies

```bash
pip install -r server/requirements.txt
```

---

## Start the AI Server

```bash
python server/guardianwalk_server.py
```

---

## Upload ESP32 Firmware

1. Open the **esp32** folder in Arduino IDE.
2. Select the ESP32-CAM board.
3. Connect your ESP32-CAM.
4. Upload the firmware.
5. Ensure both the ESP32 and AI server are connected to the same Wi-Fi network.

---

# 🔄 System Workflow

```
ESP32-CAM
      │
      ▼
Capture Image
      │
      ▼
Send Image via Wi-Fi
      │
      ▼
Flask AI Server
      │
      ▼
YOLOv8 Detection
      │
      ▼
Navigation Decision
      │
      ▼
ESP32 Controller
      │
      ├── Left Motor
      ├── Right Motor
      └── Buzzer
```

---

# 📸 Project Demonstration

<p align="center">
<img src="banner.png" width="100%">
</p>

The banner above showcases the GuardianWalk wearable prototype, system architecture, hardware components, AI object detection, and overall navigation workflow.

---

# 💡 Applications

- Smart Wearable Technology
- Assistive Devices
- AI Navigation Systems
- Computer Vision Projects
- Embedded Systems
- IoT Applications
- Healthcare Technology
- Academic Research

---

# 🚀 Future Enhancements

- 📏 Real-time Distance Estimation
- 🗺 GPS Navigation
- 🧠 Edge AI using Raspberry Pi
- 🎙 Voice Assistant Integration
- 📱 Android & iOS Mobile Application
- ☁ Cloud Monitoring Dashboard
- 🔋 Improved Battery Optimization
- 🦯 Smart Cane Integration
- 🌍 Offline AI Processing

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
- Flask API
- Python Programming
- IoT Communication
- Wearable Device Design
- Human-Centered Assistive Technology

---

# 👥 Team Project

GuardianWalk was developed as a collaborative academic project focused on designing an intelligent wearable navigation system for visually impaired individuals. The project combines AI, embedded systems, and real-time communication to provide an affordable assistive solution that improves user mobility and safety.

---

# 📈 Future Scope

Future versions of GuardianWalk may incorporate advanced depth estimation, simultaneous localization and mapping (SLAM), cloud synchronization, GPS-assisted outdoor navigation, voice interaction, and edge AI processing. These improvements aim to enhance accuracy, reduce latency, and make the system completely standalone for everyday use.

---

# 👨‍💻 Developer

**Joshua Greg Colaco**

GitHub: **https://github.com/joshua14134**

---

# 📄 License

This project is licensed under the **MIT License**.

---

<p align="center">
Made with ❤️ to improve accessibility through Artificial Intelligence.
</p>

<p align="center">
⭐ If you found this project interesting, consider giving it a Star on GitHub.
</p>
