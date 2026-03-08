#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ================= WIFI =================
const char* ssid = "JOSH";
const char* password = "joshuaqqq";
const char* serverUrl = "http://172.20.10.3:5000/detect";

// ================= PINS =================
#define LEFT_VIB   12
#define RIGHT_VIB  13
#define BUZZER_PIN 14

#define CAPTURE_INTERVAL 200

unsigned long lastCapture = 0;

// ================= BUZZER =================
unsigned long buzzerStart = 0;
bool buzzerActive = false;
int buzzerDuration = 0;

// ================= MOTOR INIT =================
void motorInit() {

  ledcAttach(LEFT_VIB, 5000, 8);
  ledcAttach(RIGHT_VIB, 5000, 8);
  ledcAttach(BUZZER_PIN, 3000, 8);

  ledcWrite(LEFT_VIB, 0);
  ledcWrite(RIGHT_VIB, 0);
  ledcWrite(BUZZER_PIN, 0);
}

// ================= BUZZER =================
void startBuzzer(int duration) {
  ledcWrite(BUZZER_PIN, 180);
  buzzerStart = millis();
  buzzerDuration = duration;
  buzzerActive = true;
}

void updateBuzzer() {
  if (buzzerActive && millis() - buzzerStart > buzzerDuration) {
    ledcWrite(BUZZER_PIN, 0);
    buzzerActive = false;
  }
}

// ================= DECISION HANDLER =================
void handleDecision(String decision, int strength) {

  decision.toUpperCase();

  // Safety clamp
  strength = constrain(strength, 0, 255);

  if (decision == "LEFT") {

    ledcWrite(LEFT_VIB, strength);
    ledcWrite(RIGHT_VIB, 0);
  }

  else if (decision == "RIGHT") {

    ledcWrite(RIGHT_VIB, strength);
    ledcWrite(LEFT_VIB, 0);
  }

  else if (decision == "CENTER") {

    ledcWrite(LEFT_VIB, strength);
    ledcWrite(RIGHT_VIB, strength);

    if (strength > 200) {
      startBuzzer(300);
    }
  }

  else {  // CLEAR

    ledcWrite(LEFT_VIB, 0);
    ledcWrite(RIGHT_VIB, 0);
  }

  Serial.print("Decision: ");
  Serial.print(decision);
  Serial.print(" Strength: ");
  Serial.println(strength);
}

// ================= CAMERA INIT =================
void startCamera() {

  camera_config_t config;

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;

  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;

  config.pin_xclk = 0;
  config.pin_pclk = 22;
  config.pin_vsync = 25;
  config.pin_href  = 23;
  config.pin_sccb_sda = 26;
  config.pin_sccb_scl = 27;
  config.pin_pwdn = 32;
  config.pin_reset = -1;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 15;
  config.fb_count = 2;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed");
    ESP.restart();
  }
}

// ================= SETUP =================
void setup() {

  Serial.begin(115200);
  motorInit();

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.println(WiFi.localIP());

  startCamera();
}

// ================= LOOP =================
void loop() {

  updateBuzzer();

  if (WiFi.status() != WL_CONNECTED) return;
  if (millis() - lastCapture < CAPTURE_INTERVAL) return;

  lastCapture = millis();

  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) return;

  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "image/jpeg");

  int code = http.POST(fb->buf, fb->len);

  if (code == 200) {

    String response = http.getString();

    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, response);

    if (!error) {

      String decision = doc["decision"] | "CLEAR";
      int strength = doc["strength"] | 0;

      handleDecision(decision, strength);
    }
  }
  else {
    ledcWrite(LEFT_VIB, 0);
    ledcWrite(RIGHT_VIB, 0);
  }

  http.end();
  esp_camera_fb_return(fb);
}