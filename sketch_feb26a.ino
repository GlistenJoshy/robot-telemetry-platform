#include <WiFi.h>
#include <WebServer.h>

// Replace with your network credentials
const char* ssid     = "IQOO";
const char* password = "hello123";

WebServer server(80);

// Motor 1
int motor1Pin1 = 27; 
int motor1Pin2 = 26; 
int enable1Pin = 14;

// Motor 2
int motor2Pin1 = 33; 
int motor2Pin2 = 25; 
int enable2Pin = 32;

// PWM settings
const int freq = 30000;
const int resolution = 8;

const int pwmChannel1 = 0;
const int pwmChannel2 = 1;

int dutyCycle = 0;
String valueString = String(0);

void handleRoot() {
  const char html[] PROGMEM = R"rawliteral(
  <!DOCTYPE HTML><html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      html { font-family: Helvetica; text-align: center; }
      .button { background-color: #4CAF50; border: none; color: white; padding: 12px 28px; font-size: 22px; margin: 4px; cursor: pointer; }
      .stop { background-color: #555555; }
    </style>
    <script>
      function cmd(c) { fetch('/' + c); }
      function speed(val) { 
        document.getElementById('speedVal').innerHTML = val;
        fetch('/speed?value=' + val);
      }
    </script>
  </head>
  <body>
    <h2>ESP32 Robot Control</h2>
    <p><button class="button" onclick="cmd('forward')">FORWARD</button></p>
    <p>
      <button class="button" onclick="cmd('left')">LEFT</button>
      <button class="button stop" onclick="cmd('stop')">STOP</button>
      <button class="button" onclick="cmd('right')">RIGHT</button>
    </p>
    <p><button class="button" onclick="cmd('reverse')">REVERSE</button></p>
    <p>Speed: <span id="speedVal">0</span></p>
    <input type="range" min="0" max="100" step="25" value="0" oninput="speed(this.value)">
  </body>
  </html>)rawliteral";

  server.send(200, "text/html", html);
}

void handleForward() {
  digitalWrite(motor1Pin1, LOW);
  digitalWrite(motor1Pin2, HIGH); 
  digitalWrite(motor2Pin1, LOW);
  digitalWrite(motor2Pin2, HIGH);
  server.send(200);
}

void handleLeft() {
  digitalWrite(motor1Pin1, LOW); 
  digitalWrite(motor1Pin2, LOW); 
  digitalWrite(motor2Pin1, LOW);
  digitalWrite(motor2Pin2, HIGH);
  server.send(200);
}

void handleRight() {
  digitalWrite(motor1Pin1, LOW); 
  digitalWrite(motor1Pin2, HIGH); 
  digitalWrite(motor2Pin1, LOW);
  digitalWrite(motor2Pin2, LOW);
  server.send(200);
}

void handleReverse() {
  digitalWrite(motor1Pin1, HIGH);
  digitalWrite(motor1Pin2, LOW); 
  digitalWrite(motor2Pin1, HIGH);
  digitalWrite(motor2Pin2, LOW);
  server.send(200);
}

void handleStop() {
  digitalWrite(motor1Pin1, LOW); 
  digitalWrite(motor1Pin2, LOW); 
  digitalWrite(motor2Pin1, LOW);
  digitalWrite(motor2Pin2, LOW);
  ledcWrite(pwmChannel1, 0);
  ledcWrite(pwmChannel2, 0);
  server.send(200);
}

void handleSpeed() {
  if (server.hasArg("value")) {
    int value = server.arg("value").toInt();

    if (value == 0) {
      ledcWrite(pwmChannel1, 0);
      ledcWrite(pwmChannel2, 0);
    } else {
      dutyCycle = map(value, 25, 100, 200, 255);
      ledcWrite(pwmChannel1, dutyCycle);
      ledcWrite(pwmChannel2, dutyCycle);
    }
  }
  server.send(200);
}

void setup() {
  Serial.begin(115200);

  pinMode(motor1Pin1, OUTPUT);
  pinMode(motor1Pin2, OUTPUT);
  pinMode(motor2Pin1, OUTPUT);
  pinMode(motor2Pin2, OUTPUT);

  // Proper PWM setup
  ledcSetup(pwmChannel1, freq, resolution);
  ledcAttachPin(enable1Pin, pwmChannel1);

  ledcSetup(pwmChannel2, freq, resolution);
  ledcAttachPin(enable2Pin, pwmChannel2);

  ledcWrite(pwmChannel1, 0);
  ledcWrite(pwmChannel2, 0);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/forward", handleForward);
  server.on("/left", handleLeft);
  server.on("/right", handleRight);
  server.on("/reverse", handleReverse);
  server.on("/stop", handleStop);
  server.on("/speed", handleSpeed);

  server.begin();
}

void loop() {
  server.handleClient();
}