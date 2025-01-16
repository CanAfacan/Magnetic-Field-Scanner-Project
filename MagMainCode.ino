
#include <Servo.h>
#include <Wire.h>
#include <QMC5883LCompass.h>

Servo myServo;

const int joystickXPin = A0; 
const int joystickYPin = A1; 

const int servoPin = 9;       
const int servoCenter = 90;    
const int servoRange = 90;     

// Deadzone angle for servo
const int deadzone = 5;

QMC5883LCompass compass;

// initial offset
float initialX = 0.0;
float initialY = 0.0;
float initialZ = 0.0;

void setup() {
  myServo.attach(servoPin);
  myServo.write(servoCenter);
  Serial.begin(9600);
  Wire.begin();
  compass.init();
  calibrate();
}

void loop() {
  int joystickX = analogRead(joystickXPin);
  int joystickY = analogRead(joystickYPin); 
  int servoAngle = map(joystickX, 0, 1023, servoCenter - servoRange, servoCenter + servoRange);

  if (abs(joystickX - 512) < deadzone) {
    servoAngle = myServo.read(); 
  }
  myServo.write(servoAngle);

  // Allegro Hall effect switch sensor control
  int sensorValue = analogRead(A3);
  float voltage = sensorValue * (5.0 / 1023.0);

  compass.read();
  int x = compass.getX();
  int y = compass.getY();
  int z = compass.getZ();

  // units are in µT
  float xMag = x / 100.0 - initialX;
  float yMag = y / 100.0 - initialY;
  float zMag = z / 100.0 - initialZ;

  // Hall Switch checks if B-field is significant
  bool magneticFieldDetected = voltage < 4.5;

  Serial.print("JoystickX: "); Serial.print(joystickX);
  Serial.print(", JoystickY: "); Serial.print(joystickY);
  Serial.print(", Voltage: "); Serial.print(voltage, 3);
  if (magneticFieldDetected) {
    Serial.print(", XMag: "); Serial.print(xMag, 2);
    Serial.print(", YMag: "); Serial.print(yMag, 2);
    Serial.print(", ZMag: "); Serial.print(zMag, 2);
  } else {
    Serial.print(", No magnetic field detected");
  }
  Serial.println();

  delay(100);
}

void calibrate() {
  int x, y, z;
  compass.read();
  x = compass.getX();
  y = compass.getY();
  z = compass.getZ();
  initialX = x / 100.0;
  initialY = y / 100.0;
  initialZ = z / 100.0;
  Serial.print("Calibration values: ");
  Serial.print("X: "); Serial.print(initialX, 2);
  Serial.print(" µT   Y: "); Serial.print(initialY, 2);
  Serial.print(" µT   Z: "); Serial.println(initialZ, 2);
}
