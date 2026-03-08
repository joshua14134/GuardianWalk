# GuardianWalk

![Python](https://img.shields.io/badge/Python-3.10-blue)
![YOLOv8](https://img.shields.io/badge/YOLOv8-AI-red)
![ESP32](https://img.shields.io/badge/ESP32-CAM-green)
![Flask](https://img.shields.io/badge/Flask-API-black)

AI-powered wearable navigation system for visually impaired individuals using **YOLOv8 + ESP32-CAM**.

---

## System Architecture

![Architecture](docs/architecture.png)

---

## How It Works

1. ESP32-CAM captures an image.
2. Image is sent to the AI server.
3. YOLOv8 detects obstacles.
4. AI decides safe direction.
5. ESP32 activates vibration motors.
6. Buzzer warns if obstacle is too close.

---

## Hardware Used

* ESP32-CAM
* Vibration Motors
* Buzzer
* Battery Pack
* Camera Module

---

## Software Stack

* Python
* YOLOv8
* Flask
* OpenCV
* Arduino IDE

---

## Project Structure

GuardianWalk/

server/ → AI detection server
esp32/ → ESP32 firmware
docs/ → diagrams and demo images

---

## Future Improvements

* Depth detection using MiDaS
* Offline Raspberry Pi processing
* GPS outdoor navigation
* Smart cane integration

---

## Author
group project

AI & Computer Vision Project
