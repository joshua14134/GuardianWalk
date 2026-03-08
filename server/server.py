from ultralytics import YOLO
from flask import Flask, request, jsonify, Response
import cv2
import numpy as np
import threading
import time
import torch
import pyttsx3

try:
    import winsound
except:
    winsound = None

# =============================
# DEVICE
# =============================
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

# =============================
# LOAD YOLOv8m
# =============================
model = YOLO("yolov8m.pt")
model.to(device)

# =============================
# AUDIO SYSTEM
# =============================
def speak(text):
    def run():
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 165)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except:
            pass
    threading.Thread(target=run, daemon=True).start()

# =============================
# GLOBALS
# =============================
app = Flask(__name__)
latest_frame = None
frame_lock = threading.Lock()

last_speak_time = 0
SPEAK_INTERVAL = 2

previous_area = {}

MIN_AREA = 8000

DANGEROUS = [
    "person","chair","dining table","couch",
    "bed","tv","laptop",
    "car","bus","truck","motorbike","bicycle"
]

# =============================
# DETECT ROUTE
# =============================
@app.route("/detect", methods=["POST"])
def detect():

    global latest_frame, last_speak_time, previous_area

    if not request.data:
        return jsonify({"decision": "CLEAR", "strength": 0})

    np_img = np.frombuffer(request.data, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"decision": "CLEAR", "strength": 0})

    img = cv2.resize(img, (416, 320))
    h, w, _ = img.shape

    img = cv2.convertScaleAbs(img, alpha=1.15, beta=20)

    start_time = time.time()

    results = model(img, conf=0.4, verbose=False)

    best_object = None
    largest_area = 0

    for r in results:
        if r.boxes is None:
            continue

        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            if label not in DANGEROUS:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            area = (x2 - x1) * (y2 - y1)

            if area < MIN_AREA:
                continue

            if area > largest_area:
                largest_area = area
                cx = (x1 + x2) // 2

                if cx < w * 0.33:
                    location = "left"
                elif cx > w * 0.66:
                    location = "right"
                else:
                    location = "center"

                best_object = {
                    "label": label,
                    "area": area,
                    "location": location
                }

            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    decision_out = "CLEAR"
    strength = 0
    voice_output = "Path clear."

    if best_object:

        label = best_object["label"]
        area = best_object["area"]
        location = best_object["location"]

        # ===== Distance Scaling =====
        if area > 100000:
            strength = 255
            danger_level = "HIGH"
        elif area > 50000:
            strength = 220
            danger_level = "MEDIUM"
        else:
            strength = 150
            danger_level = "LOW"

        # ===== Motion Prediction =====
        approaching = False
        if label in previous_area:
            if area > previous_area[label] * 1.2:
                approaching = True

        previous_area[label] = area

        # ===== Decision Logic =====
        if location == "left":
            decision_out = "LEFT"
            voice_output = f"{label.capitalize()} on left. Move right."

        elif location == "right":
            decision_out = "RIGHT"
            voice_output = f"{label.capitalize()} on right. Move left."

        else:
            decision_out = "CENTER"

            if danger_level == "HIGH":
                voice_output = "Emergency stop. Obstacle very close."
                if winsound:
                    winsound.Beep(2000, 200)
            elif approaching:
                voice_output = "Object approaching. Slow down."
            else:
                voice_output = f"{label.capitalize()} ahead."

    # ===== Speech Control =====
    if time.time() - last_speak_time > SPEAK_INTERVAL:
        speak(voice_output)
        last_speak_time = time.time()

    fps = int(1 / (time.time() - start_time))
    cv2.putText(img, f"FPS:{fps}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.putText(img, voice_output, (20, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    with frame_lock:
        latest_frame = img.copy()

    return jsonify({
        "decision": decision_out,
        "strength": int(strength)
    })

# =============================
# STREAM
# =============================
def generate():
    global latest_frame
    while True:
        with frame_lock:
            frame = latest_frame
        if frame is None:
            continue

        ret, buffer = cv2.imencode('.jpg', frame,
                                   [int(cv2.IMWRITE_JPEG_QUALITY), 35])

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() + b'\r\n')

@app.route("/video")
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/")
def home():
    return """
    <html>
    <body style="background:#111;color:white;text-align:center;">
    <h1>GuardianWalk </h1>
    <img src="/video" width="850">
    </body>
    </html>
    """

if __name__ == "__main__":
    speak("GuardianWalk .")
    app.run(host="0.0.0.0", port=5000, threaded=True)