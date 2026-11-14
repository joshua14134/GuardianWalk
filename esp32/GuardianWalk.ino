#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// =========================================================
// WIFI + SERVER
// =========================================================
const char* WIFI_SSID = "JOSH";
const char* WIFI_PASSWORD = "joshuaqqq";

const char* SERVER_URL = "http://172.20.10.4:5000/detect";

// =========================================================
// HAPTIC / BUZZER PINS
// NOTE: GPIO 12 is a strapping pin. Make sure the driver
// circuit does not pull it HIGH during boot/reset
// (use a pulldown, e.g. 10k to GND).
// =========================================================
#define LEFT_VIB   12
#define RIGHT_VIB  13
#define BUZZER     14

// =========================================================
// CAMERA PIN MAPPING (AI Thinker ESP32-CAM)
// =========================================================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// =========================================================
// TIMING
// =========================================================
unsigned long lastCaptureTime = 0;
const unsigned long CAPTURE_INTERVAL = 150;   // upper bound; real rate depends on server speed
unsigned long alertOffAt = 0;

// =========================================================
// HTTP (kept open between frames to cut lag)
// =========================================================
WiFiClient client;
HTTPClient http;
bool httpStarted = false;

// =========================================================
// CONNECT WIFI
// =========================================================
void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);              // disable WiFi power saving: lower latency
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to WiFi");

  unsigned long startTime = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - startTime < 20000) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected!");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi connection failed.");
  }
}

// =========================================================
// CAMERA SETUP
// =========================================================
bool startCamera() {
  camera_config_t config = {};   // zero-init: no garbage fields

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;

  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.fb_location  = CAMERA_FB_IN_PSRAM;
    config.frame_size   = FRAMESIZE_QVGA;       // 320x240
    config.jpeg_quality = 12;                   // lower number = better quality
    config.fb_count     = 2;
    config.grab_mode    = CAMERA_GRAB_LATEST;   // always the newest frame
  } else {
    config.fb_location  = CAMERA_FB_IN_DRAM;
    config.frame_size   = FRAMESIZE_QQVGA;      // 160x120
    config.jpeg_quality = 15;
    config.fb_count     = 1;
    config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
  }

  esp_err_t err = esp_camera_init(&config);

  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return false;
  }

  sensor_t *sensor = esp_camera_sensor_get();
  if (sensor != nullptr) {
    sensor->set_brightness(sensor, 1);   // optional slight boost
  }

  Serial.println("Camera initialized.");
  return true;
}

// =========================================================
// HAPTIC OUTPUT (non-blocking)
// =========================================================
void stopAlerts() {
  digitalWrite(LEFT_VIB, LOW);
  digitalWrite(RIGHT_VIB, LOW);
  digitalWrite(BUZZER, LOW);
}

void handleDecision(String decision, int strength) {
  if (decision == "CLEAR") return;

  stopAlerts();

  if (decision == "LEFT") {
    digitalWrite(LEFT_VIB, HIGH);
  }
  else if (decision == "RIGHT") {
    digitalWrite(RIGHT_VIB, HIGH);
  }
  else if (decision == "CENTER") {
    digitalWrite(LEFT_VIB, HIGH);
    digitalWrite(RIGHT_VIB, HIGH);
    digitalWrite(BUZZER, HIGH);
  }

  alertOffAt = millis() + 180;   // turned off in loop(), no delay()
}

// =========================================================
// SEND FRAME TO SERVER
// =========================================================
void sendFrame(camera_fb_t *fb) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    if (httpStarted) {
      http.end();
      httpStarted = false;
    }
    connectWiFi();
    return;
  }

  if (!httpStarted) {
    http.setReuse(true);               // keep-alive
    http.setConnectTimeout(3000);
    http.setTimeout(5000);

    if (!http.begin(client, SERVER_URL)) {
      Serial.println("Could not start HTTP connection.");
      return;
    }

    http.addHeader("Content-Type", "image/jpeg");
    httpStarted = true;
  }

  int httpCode = http.POST(fb->buf, fb->len);

  if (httpCode > 0) {
    String response = http.getString();

    String decision = "CLEAR";
    int strength = 0;

    if (response.indexOf("\"decision\":\"LEFT\"") >= 0) {
      decision = "LEFT";
    }
    else if (response.indexOf("\"decision\":\"RIGHT\"") >= 0) {
      decision = "RIGHT";
    }
    else if (response.indexOf("\"decision\":\"CENTER\"") >= 0) {
      decision = "CENTER";
    }

    int strengthPos = response.indexOf("\"strength\":");
    if (strengthPos >= 0) {
      strength = response.substring(strengthPos + 11).toInt();
    }

    handleDecision(decision, strength);
    // No http.end() here: the connection stays open for the next frame.
  }
  else {
    Serial.printf("HTTP request failed: %d\n", httpCode);
    Serial.println("Check PC IP, Flask server, WiFi and firewall.");
    http.end();
    httpStarted = false;               // reconnect on next frame
  }
}

// =========================================================
// SETUP
// =========================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(LEFT_VIB, OUTPUT);
  pinMode(RIGHT_VIB, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  stopAlerts();

  Serial.printf("PSRAM: %s\n", psramFound() ? "yes" : "no");
  Serial.printf("Free heap before camera: %u\n", ESP.getFreeHeap());

  // Camera FIRST, while internal RAM is still free
  if (!startCamera()) {
    Serial.println("Restarting in 5 seconds...");
    delay(5000);
    ESP.restart();
  }

  // WiFi AFTER camera
  connectWiFi();

  Serial.println("GuardianWalk ESP32 started.");
}

// =========================================================
// LOOP
// =========================================================
void loop() {
  // Turn off haptics/buzzer after the pulse, without blocking
  if (alertOffAt && millis() > alertOffAt) {
    stopAlerts();
    alertOffAt = 0;
  }

  if (millis() - lastCaptureTime >= CAPTURE_INTERVAL) {
    lastCaptureTime = millis();

    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      return;
    }

    if (fb->format == PIXFORMAT_JPEG && fb->len > 0) {
      sendFrame(fb);
    }

    esp_camera_fb_return(fb);
  }
}
