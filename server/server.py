from ultralytics import YOLO
from flask import Flask, request, jsonify, Response
import cv2
import numpy as np
import threading
import time
import torch
import pyttsx3
import queue

try:
    import winsound
except ImportError:
    winsound = None


# =========================================================
# CONFIG
# =========================================================
MODEL_PATH = "yolov8m.pt"
CONFIDENCE = 0.40

# Processing dimensions
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480

MIN_AREA = 1800
SPEAK_INTERVAL = 2.0

DANGEROUS = [
    "person", "chair", "dining table", "couch",
    "bed", "tv", "laptop", "car", "bus", "truck",
    "motorbike", "bicycle"
]


# =========================================================
# DEVICE + MODEL
# =========================================================
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

print("Loading YOLO model...")
model = YOLO(MODEL_PATH)
model.to(device)
print("YOLO model loaded.")


# =========================================================
# FLASK
# =========================================================
app = Flask(__name__)


# =========================================================
# SHARED STATE
# =========================================================
state_lock = threading.Lock()

latest_frame = None
latest_frame_id = 0
processed_frame_id = 0
latest_display_frame = None

latest_result = {
    "decision": "CLEAR",
    "strength": 0,
    "label": None,
    "location": None,
    "danger_level": "LOW",
    "approaching": False,
    "updated": time.time()
}

previous_area = {}
last_speak_time = 0

frame_available = threading.Event()


# =========================================================
# VOICE SYSTEM
# =========================================================
speech_queue = queue.Queue(maxsize=5)


def speech_worker():
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
    except Exception as e:
        print("TTS initialization error:", e)
        return

    while True:
        text = speech_queue.get()

        try:
            if text:
                engine.say(text)
                engine.runAndWait()
        except Exception as e:
            print("TTS error:", e)

        speech_queue.task_done()


def speak(text):
    try:
        if speech_queue.full():
            try:
                speech_queue.get_nowait()
                speech_queue.task_done()
            except queue.Empty:
                pass

        speech_queue.put_nowait(text)

    except queue.Full:
        pass


threading.Thread(
    target=speech_worker,
    daemon=True
).start()


# =========================================================
# OVERLAY DRAWING HELPERS (readable text on the live video)
# =========================================================
FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_text(img, text, org, scale=0.6, color=(255, 255, 255), thickness=2):
    """Text with a black outline so it's readable on any background."""
    x, y = org
    cv2.putText(img, text, (x, y), FONT, scale, (0, 0, 0),
                thickness + 3, cv2.LINE_AA)          # outline
    cv2.putText(img, text, (x, y), FONT, scale, color,
                thickness, cv2.LINE_AA)              # fill


def draw_label(img, text, x, y, box_color=(0, 255, 0), scale=0.6):
    """Label chip: solid colored background + dark text, sits above the box."""
    (tw, th), base = cv2.getTextSize(text, FONT, scale, 2)
    top = max(0, y - th - base - 8)
    cv2.rectangle(img, (x, top), (x + tw + 10, top + th + base + 8),
                  box_color, -1)
    cv2.putText(img, text, (x + 5, top + th + 3), FONT, scale,
                (0, 0, 0), 2, cv2.LINE_AA)


def draw_bottom_bar(img, text, color=(0, 255, 255)):
    """Semi-transparent bar at the bottom with auto-fitting text."""
    h, w = img.shape[:2]
    bar_h = 40
    overlay = img.copy()
    cv2.rectangle(overlay, (0, h - bar_h), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)

    scale = 0.75
    while scale > 0.4:
        (tw, _), _ = cv2.getTextSize(text, FONT, scale, 2)
        if tw <= w - 20:
            break
        scale -= 0.05
    draw_text(img, text, (10, h - 13), scale=scale, color=color)


def danger_color(area):
    """Box color by size: red = very close, orange = medium, green = far."""
    if area > 100000:
        return (0, 0, 255)
    if area > 50000:
        return (0, 165, 255)
    return (0, 255, 0)


# =========================================================
# DETECTION / DECISION LOGIC
# =========================================================
def process_frame(frame):
    global previous_area

    img = cv2.resize(
        frame,
        (IMAGE_WIDTH, IMAGE_HEIGHT),
        interpolation=cv2.INTER_CUBIC
    )

    # Mild image adjustment to avoid over-brightening
    img = cv2.convertScaleAbs(
        img,
        alpha=1.05,
        beta=5
    )

    h, w = img.shape[:2]
    start_time = time.time()

    results = model.predict(
        source=img,
        conf=CONFIDENCE,
        imgsz=IMAGE_WIDTH,
        device=device,
        verbose=False
    )

    best_object = None
    largest_area = 0
    detections = []

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]

            if label not in DANGEROUS:
                continue

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            x1 = max(0, min(x1, w - 1))
            x2 = max(0, min(x2, w - 1))
            y1 = max(0, min(y1, h - 1))
            y2 = max(0, min(y2, h - 1))

            area = max(0, x2 - x1) * max(0, y2 - y1)

            if area < MIN_AREA:
                continue

            cx = (x1 + x2) // 2

            if cx < w * 0.33:
                location = "left"
            elif cx > w * 0.66:
                location = "right"
            else:
                location = "center"

            detections.append({
                "label": label,
                "area": area,
                "location": location,
                "box": [x1, y1, x2, y2]
            })

            if area > largest_area:
                largest_area = area
                best_object = detections[-1]

            # Readable box + label chip (colored by danger)
            box_color = danger_color(area)
            cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 3)
            draw_label(img, f"{label} ({location})", x1, y1,
                       box_color=box_color)

    decision_out = "CLEAR"
    strength = 0
    voice_output = "Path clear."
    danger_level = "LOW"
    approaching = False

    if best_object:
        label = best_object["label"]
        area = best_object["area"]
        location = best_object["location"]

        if area > 100000:
            strength = 255
            danger_level = "HIGH"
        elif area > 50000:
            strength = 220
            danger_level = "MEDIUM"
        else:
            strength = 150
            danger_level = "LOW"

        if label in previous_area:
            if area > previous_area[label] * 1.2:
                approaching = True

        previous_area[label] = area

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
            elif approaching:
                voice_output = "Object approaching. Slow down."
            else:
                voice_output = f"{label.capitalize()} ahead."

    elapsed = max(time.time() - start_time, 0.001)
    fps = int(1 / elapsed)

    draw_text(img, f"FPS: {fps}", (15, 32), scale=0.8, color=(0, 255, 0))
    draw_bottom_bar(img, voice_output)

    result_data = {
        "decision": decision_out,
        "strength": int(strength),
        "label": best_object["label"] if best_object else None,
        "location": best_object["location"] if best_object else None,
        "danger_level": danger_level,
        "approaching": approaching,
        "updated": time.time()
    }

    return img, result_data, voice_output


# =========================================================
# BACKGROUND YOLO WORKER
# =========================================================
def inference_worker():
    global processed_frame_id
    global latest_display_frame
    global latest_result
    global last_speak_time

    while True:
        frame_available.wait()
        frame_available.clear()

        with state_lock:
            if latest_frame is None:
                continue

            frame = latest_frame.copy()
            current_id = latest_frame_id

        try:
            display_frame, result_data, voice_output = process_frame(frame)

            with state_lock:
                latest_display_frame = display_frame.copy()
                latest_result = result_data
                processed_frame_id = current_id

            now = time.time()

            if now - last_speak_time >= SPEAK_INTERVAL:
                speak(voice_output)
                last_speak_time = now

            if (
                winsound
                and result_data["decision"] == "CENTER"
                and result_data["danger_level"] == "HIGH"
            ):
                try:
                    winsound.Beep(2000, 200)
                except Exception:
                    pass

            print(
                f"Decision={result_data['decision']} | "
                f"Object={result_data['label']} | "
                f"Strength={result_data['strength']}"
            )

        except Exception as e:
            print("Inference error:", e)


threading.Thread(
    target=inference_worker,
    daemon=True
).start()


# =========================================================
# ESP32 ROUTE
# =========================================================
@app.route("/detect", methods=["POST"])
def detect():
    global latest_frame
    global latest_frame_id

    if not request.data:
        return jsonify({"error": "No image received"}), 400

    np_img = np.frombuffer(request.data, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "Invalid image"}), 400

    with state_lock:
        latest_frame = img
        latest_frame_id += 1
        received_id = latest_frame_id
        response = dict(latest_result)

    frame_available.set()

    response["status"] = "received"
    response["received_frame"] = received_id

    return jsonify(response), 200


# =========================================================
# STATUS ROUTE
# =========================================================
@app.route("/status", methods=["GET"])
def status():
    with state_lock:
        response = dict(latest_result)

    response["server"] = "running"
    return jsonify(response)


# =========================================================
# VIDEO STREAM
# =========================================================
def generate():
    while True:
        with state_lock:
            if latest_display_frame is not None:
                frame = latest_display_frame.copy()
            else:
                frame = None

        if frame is None:
            time.sleep(0.05)
            continue

        ret, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        )

        if not ret:
            time.sleep(0.03)
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )

        time.sleep(0.03)


@app.route("/video")
def video():
    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# =========================================================
# GUARDIANWALK DASHBOARD  (single-screen, no-scroll on desktop)
# =========================================================
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GuardianWalk | Safety Dashboard</title>

<style>
:root {
  --bg:#080d16; --panel:#111b2a; --panel2:#0b1421; --line:#26364b;
  --text:#eef4fb; --muted:#a8bad0; --blue:#38bdf8; --green:#22c55e;
  --yellow:#fbbf24; --red:#f87171;
}
* { box-sizing:border-box; }
html { height:100%; }
body {
  margin:0; min-height:100%; background:var(--bg); color:var(--text);
  font-family:Segoe UI,Arial,sans-serif; font-size:14px; line-height:1.4;
}

header {
  display:flex; justify-content:space-between; align-items:center; gap:16px;
  padding:10px clamp(16px,3vw,36px); background:#0c1421;
  border-bottom:1px solid var(--line); flex-wrap:wrap;
}
.brand { display:flex; align-items:center; gap:12px; }
.logo {
  display:grid; place-items:center; width:38px; height:38px; border-radius:11px;
  background:#12324a; color:var(--blue); font-size:22px;
}
h1 { font-size:18px; letter-spacing:1.2px; margin:0; }
.sub { color:var(--muted); font-size:11px; margin-top:2px; }
.connection { display:flex; align-items:center; gap:9px; font-size:13px; color:var(--green); }
.dot { width:9px; height:9px; border-radius:50%; background:var(--green); box-shadow:0 0 10px currentColor; }

main { width:min(1600px,100%); margin:0 auto; padding:18px clamp(16px,3vw,36px); }
.intro { margin-bottom:14px; }
.intro h2 { font-size:clamp(20px,2vw,26px); margin:0 0 4px; }
.intro p { color:var(--muted); font-size:13px; margin:0; }

.layout {
  display:grid; grid-template-columns:minmax(0,1.55fr) minmax(330px,1fr);
  gap:14px; align-items:start;
}

.panel {
  background:var(--panel); border:1px solid var(--line); border-radius:14px;
  overflow:hidden; min-width:0;
}
.panel-head {
  display:flex; justify-content:space-between; align-items:center;
  padding:10px 16px; border-bottom:1px solid var(--line); gap:12px;
}
.panel-head h3 { font-size:14px; margin:0; }
.live { color:var(--red); font-size:12px; font-weight:800; letter-spacing:1px; }

.feed {
  background:#05080d; min-height:240px; aspect-ratio:4/3;
  display:flex; align-items:center; justify-content:center; overflow:hidden;
}
.feed img { width:100%; height:100%; display:block; object-fit:contain; }
.feed-placeholder { padding:40px 20px; text-align:center; color:var(--muted); }
.feed-placeholder strong { display:block; color:var(--text); margin-bottom:8px; }

.panel-foot {
  display:flex; justify-content:space-between; gap:10px; padding:8px 16px;
  color:var(--muted); font-size:12px; flex-wrap:wrap;
}

.side { display:grid; gap:10px; min-width:0; }
.card { padding:14px; }

.decision-label { font-size:11px; color:var(--muted); letter-spacing:1.2px; }
.decision-value { font-size:clamp(26px,2.4vw,34px); font-weight:800; margin:4px 0 2px; line-height:1.1; }
.decision-message { font-size:13px; color:var(--muted); }

.section-title { font-size:12px; font-weight:700; letter-spacing:.8px; margin:0 0 9px; color:var(--muted); }

.metrics { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }
.metric { background:var(--panel2); border:1px solid var(--line); border-radius:10px; padding:9px 10px; }
.metric-label { font-size:11px; color:var(--muted); }
.metric-value { font-size:17px; font-weight:700; margin-top:3px; word-break:break-word; line-height:1.2; }

.direction { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:6px; }
.direction div {
  padding:10px 2px; text-align:center; background:var(--panel2);
  border:1px solid var(--line); border-radius:9px; color:var(--muted); font-size:12px;
}
.direction .active { border-color:var(--blue); color:var(--blue); background:#0e2a3b; }

.voice-box { background:var(--panel2); border:1px solid var(--line); padding:10px; border-radius:10px; }
.voice-title { font-size:11px; color:var(--muted); margin-bottom:5px; }
.voice-text { font-size:14px; line-height:1.4; overflow-wrap:anywhere; }

.status-line {
  display:flex; justify-content:space-between; gap:12px; font-size:13px;
  padding:6px 0; border-bottom:1px solid var(--line);
}
.status-line:last-child { border-bottom:0; }
.status-value { font-weight:700; text-align:right; }

.footer { text-align:center; color:#71839a; font-size:12px; padding:14px 10px; }

/* =====================================================
   DESKTOP: lock to one screen, nothing scrolls
   ===================================================== */
@media (min-width:901px) and (min-height:560px) {
  html, body { height:100%; overflow:hidden; }
  body { display:flex; flex-direction:column; }

  header { flex:0 0 auto; }
  .intro, .footer { display:none; }

  main {
    flex:1 1 auto; min-height:0; width:min(1700px,100%);
    padding:14px clamp(16px,2vw,28px);
    display:flex; flex-direction:column;
  }

  .layout {
    flex:1 1 auto; min-height:0; align-items:stretch;
    grid-template-columns:minmax(0,1.5fr) minmax(380px,1fr);
  }

  /* Camera panel fills full height */
  .cam { display:flex; flex-direction:column; min-height:0; }
  .cam .feed { flex:1 1 auto; min-height:0; aspect-ratio:auto; }
  .cam .panel-head, .cam .panel-foot { flex:0 0 auto; }

  /* Right column: 2-col compact grid, fills height */
  .side {
    min-height:0; height:100%;
    grid-template-columns:repeat(2,minmax(0,1fr));
    grid-auto-rows:min-content;
    align-content:stretch;
    overflow:hidden;
  }
  .side > .span2 { grid-column:span 2; }
  .side > .card { display:flex; flex-direction:column; justify-content:center; min-height:0; padding:12px 14px; }

  .metrics { grid-template-columns:repeat(4,minmax(0,1fr)); }
  .metric-value { font-size:15px; }
}

/* Short desktop windows: tighten further */
@media (min-width:901px) and (max-height:760px) {
  header { padding:6px 24px; }
  .logo { width:32px; height:32px; font-size:18px; }
  .sub { display:none; }
  main { padding:10px 18px; }
  .layout, .side { gap:8px; }
  .side > .card { padding:9px 12px; }
  .decision-value { font-size:24px; margin:2px 0; }
  .section-title { margin-bottom:6px; }
  .metric { padding:6px 8px; }
  .direction div { padding:7px 2px; }
  .status-line { padding:4px 0; }
}

/* Tablet / mobile: normal page scrolling */
@media (max-width:900px) {
  main { padding:16px 12px; }
  .layout { grid-template-columns:1fr; }
  .side { grid-template-columns:repeat(2,minmax(0,1fr)); align-items:start; }
  .side > .span2 { grid-column:span 2; }
}
@media (max-width:520px) {
  header { padding:10px 14px; }
  h1 { font-size:16px; }
  .side { grid-template-columns:1fr; }
  .side > .span2 { grid-column:auto; }
  .decision-value { font-size:28px; }
}
</style>
</head>

<body>
<header>
  <div class="brand">
    <div class="logo">◈</div>
    <div>
      <h1>GUARDIANWALK</h1>
      <div class="sub">AI-POWERED WALKING ASSISTANCE SYSTEM</div>
    </div>
  </div>

  <div class="connection" id="connection">
    <span class="dot"></span>
    <span>CONNECTING TO SERVER</span>
  </div>
</header>

<main>
  <section class="intro">
    <h2>Safety Monitoring Dashboard</h2>
    <p>Live obstacle detection, direction guidance, and voice alerts.</p>
  </section>

  <div class="layout">
    <section class="panel cam">
      <div class="panel-head">
        <h3>ESP32-CAM Live Feed</h3>
        <span class="live">● LIVE</span>
      </div>

      <div class="feed">
        <img
          src="/video"
          alt="GuardianWalk live camera feed"
          onerror="this.style.display='none';document.getElementById('placeholder').style.display='block'"
        >
        <div class="feed-placeholder" id="placeholder" style="display:none">
          <strong>Camera feed unavailable</strong>
          Check the server and ESP32-CAM connection.
        </div>
      </div>

      <div class="panel-foot">
        <span>YOLO OBJECT DETECTION</span>
        <span id="lastUpdate">Waiting for frames...</span>
      </div>
    </section>

    <div class="side">
      <section class="panel card span2">
        <div class="decision-label">MOVEMENT GUIDANCE</div>
        <div class="decision-value" id="decision">CLEAR</div>
        <div class="decision-message" id="decisionMessage">Path appears clear.</div>
      </section>

      <section class="panel card span2">
        <h3 class="section-title">DETECTION METRICS</h3>
        <div class="metrics">
          <div class="metric">
            <div class="metric-label">Detected Object</div>
            <div class="metric-value" id="object">None</div>
          </div>
          <div class="metric">
            <div class="metric-label">Danger Level</div>
            <div class="metric-value" id="danger">LOW</div>
          </div>
          <div class="metric">
            <div class="metric-label">Strength</div>
            <div class="metric-value" id="strength">0 / 255</div>
          </div>
          <div class="metric">
            <div class="metric-label">Approaching</div>
            <div class="metric-value" id="approaching">NO</div>
          </div>
        </div>
      </section>

      <section class="panel card">
        <h3 class="section-title">DIRECTION</h3>
        <div class="direction">
          <div id="left">← LEFT</div>
          <div id="center">↑ CENTER</div>
          <div id="right">RIGHT →</div>
        </div>
      </section>

      <section class="panel card">
        <h3 class="section-title">VOICE ALERT</h3>
        <div class="voice-box">
          <div class="voice-title">LATEST SPOKEN INSTRUCTION</div>
          <div class="voice-text" id="voiceText">Waiting for detection...</div>
        </div>
      </section>

      <section class="panel card span2">
        <h3 class="section-title">SYSTEM STATUS</h3>
        <div class="status-line">
          <span>Flask Server</span>
          <span class="status-value" id="serverStatus">Checking...</span>
        </div>
        <div class="status-line">
          <span>Detection Updates</span>
          <span class="status-value" id="detectionStatus">Waiting</span>
        </div>
        <div class="status-line">
          <span>Last Update</span>
          <span class="status-value" id="statusTime">--</span>
        </div>
      </section>
    </div>
  </div>
</main>

<div class="footer">
  GUARDIANWALK · AI ASSISTIVE WALKING SYSTEM · LIVE MONITORING
</div>

<script>
const $ = id => document.getElementById(id);

function setDirection(value) {
  ["left", "center", "right"].forEach(id => $(id).classList.remove("active"));
  const normalized = (value || "").toLowerCase();
  if (normalized === "left") $("left").classList.add("active");
  else if (normalized === "right") $("right").classList.add("active");
  else if (normalized === "center") $("center").classList.add("active");
}

function updateDashboard(data) {
  const decision = data.decision || "CLEAR";
  const danger = data.danger_level || "LOW";
  const label = data.label || "None";
  const location = data.location || "";
  const approaching = data.approaching ? "YES" : "NO";
  const strength = Number(data.strength || 0);

  $("decision").textContent = decision;
  $("object").textContent = label;
  $("danger").textContent = danger;
  $("strength").textContent = strength + " / 255";
  $("approaching").textContent = approaching;

  let message = "Path appears clear.";
  if (decision === "LEFT") {
    message = "Obstacle on the left. Move right.";
  } else if (decision === "RIGHT") {
    message = "Obstacle on the right. Move left.";
  } else if (decision === "CENTER") {
    message = danger === "HIGH"
      ? "Obstacle very close. Stop immediately."
      : "Obstacle ahead. Move carefully.";
  }
  $("decisionMessage").textContent = message;

  let voice = "Path clear.";
  if (label !== "None") {
    if (decision === "LEFT") voice = label + " on left. Move right.";
    else if (decision === "RIGHT") voice = label + " on right. Move left.";
    else if (danger === "HIGH") voice = "Emergency stop. Obstacle very close.";
    else if (approaching === "YES") voice = "Object approaching. Slow down.";
    else voice = label + " ahead.";
  }
  $("voiceText").textContent = voice;
  setDirection(location || decision);

  const updated = data.updated
    ? new Date(data.updated * 1000).toLocaleTimeString()
    : new Date().toLocaleTimeString();

  $("lastUpdate").textContent = "Updated: " + updated;
  $("statusTime").textContent = updated;
  $("detectionStatus").textContent = data.label ? "Object detected" : "Monitoring";
}

async function fetchStatus() {
  try {
    const response = await fetch("/status", { cache: "no-store" });
    if (!response.ok) throw new Error("Server response error");
    const data = await response.json();

    $("connection").innerHTML =
      '<span class="dot"></span><span>SERVER CONNECTED</span>';
    $("serverStatus").textContent = "ONLINE";
    updateDashboard(data);
  } catch (error) {
    $("connection").innerHTML =
      '<span style="color:#f87171">●</span>' +
      '<span style="color:#f87171">SERVER OFFLINE</span>';
    $("serverStatus").textContent = "OFFLINE";
    $("detectionStatus").textContent = "No connection";
  }
}

fetchStatus();
setInterval(fetchStatus, 500);
</script>
</body>
</html>
"""

# =========================================================
# START SERVER
# =========================================================
if __name__ == "__main__":
    print("GuardianWalk server starting...")
    print("Dashboard: http://127.0.0.1:5000")
    print("ESP32 endpoint: http://YOUR_PC_IP:5000/detect")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )
