/*
  AquaSync: Smart Water Level Monitoring System
  
  This firmware reads the water level sensor value from analog pin A0, 
  streams telemetry via serial interface, and controls visual and audible 
  indicators based on exact safety thresholds with clean state transitions.
*/

const int analogInPin = A0;
int sensorValue = 0;

// LED pin definitions for readability
const int LED_LOW_MID = 2; // Green LED (100 - 600)
const int LED_HIGH    = 3; // Yellow LED (601 - 625)
const int LED_FULL_A  = 4; // Red LED 1 (626 - 700)
const int LED_FULL_B  = 5; // Red LED 2 / Buzzer (626 - 700)

void setup() {
  // Initialize digital pins as outputs
  pinMode(LED_LOW_MID, OUTPUT);
  pinMode(LED_HIGH, OUTPUT);
  pinMode(LED_FULL_A, OUTPUT);
  pinMode(LED_FULL_B, OUTPUT);
  
  // Initialize Serial communication
  Serial.begin(9600);
}

void loop() {
  // Read water level sensor
  sensorValue = analogRead(analogInPin);
  
  // Output to Serial (Required by our graphical dashboard!)
  Serial.print("sensor = ");
  Serial.print(sensorValue);
  Serial.print("\n");
  
  delay(2); // Short stabilization delay
  
  // State 1: Low-Medium Level (100 - 600)
  if (sensorValue >= 100 && sensorValue <= 600) {
    digitalWrite(LED_LOW_MID, HIGH);
    digitalWrite(LED_HIGH, LOW);
    digitalWrite(LED_FULL_A, LOW);
    digitalWrite(LED_FULL_B, LOW);
    delay(100);
  }
  // State 2: High Level (601 - 625)
  else if (sensorValue >= 601 && sensorValue <= 625) {
    digitalWrite(LED_LOW_MID, LOW);
    digitalWrite(LED_HIGH, HIGH);
    digitalWrite(LED_FULL_A, LOW);
    digitalWrite(LED_FULL_B, LOW);
    delay(100);
  }
  // State 3: Critical Full Level (626 - 700)
  else if (sensorValue >= 626 && sensorValue <= 700) {
    digitalWrite(LED_LOW_MID, LOW);
    digitalWrite(LED_HIGH, LOW);
    digitalWrite(LED_FULL_A, HIGH);
    digitalWrite(LED_FULL_B, HIGH);
    delay(100);
  }
  // State 4: Empty / Inactive (Below 100 or Above 700)
  else {
    digitalWrite(LED_LOW_MID, LOW);
    digitalWrite(LED_HIGH, LOW);
    digitalWrite(LED_FULL_A, LOW);
    digitalWrite(LED_FULL_B, LOW);
    delay(100);
  }
}
