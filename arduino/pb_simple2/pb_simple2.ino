/*
 photobooth arduino control
 
 pin 2: switch to start photo session
 pin 3: unused switch
 pin 4: camera tilt servo
 
 protocol: command/argument
 
 outgoing => to host:
 0x00: reserved
 0x01: switch trigger [value: pin number]
 
 incoming => from host:
 0x80: set tilt [value: 0-180 ]
 */

#include <Servo.h>

// protocol declarations
// 'p' prefix signifies 'protocol'
byte pSwitchTrigger = 0x01;
byte pSetTilt       = 0x80;

// pin configuration
int tiltServoPin = 10;
int ledPin = 13;

// define our servo and the physical limits of it
Servo tiltServo;
int tiltPosNegativeLimit = 20;
int tiltPosPositiveLimit = 160;
int tiltPos = tiltPosNegativeLimit;
int servoResetFreq = 500;
long lastServoResetTime = 0;

// incoming protocol buffer
byte serBufferData[2];
byte serBufferIndex = 0;

// debounce on switch pins
int triggerState[] = {HIGH, HIGH};
int triggerHeld[]  = {0, 0};
int lastTriggerState[]  = {HIGH, HIGH};
long lastDebounceTime[] = {0, 0};
long debounceDelay = 100;

void setup() {
  Serial.begin(9600);
  pinMode(2, INPUT_PULLUP);
  pinMode(3, INPUT_PULLUP);
  pinMode(ledPin, OUTPUT);
  tiltServo.attach(tiltServoPin);
}

void readPin(int pin) {
  int thisState = digitalRead(pin);
  long now = millis();

  // subtract 2 b/c our inputs begin at 2 --
  // pins 0 and 1 are reserved for serial communication
  int index = pin;
  index -= 2;

  if (thisState != lastTriggerState[index]) {
    lastDebounceTime[index] = now;
  }

  if ((now - lastDebounceTime[index]) > debounceDelay) {
    triggerState[index] = thisState;
  }

  if (triggerState[index] == LOW) {
    if (triggerHeld[index] == 0) {
      triggerHeld[index] = 1;
      byte out[] = {pSwitchTrigger, pin};
      Serial.write(out, 2);
    }
  } 
  else {
    triggerHeld[index] = 0;
  }

  lastTriggerState[index] = thisState;
}

void setTilt(byte value) {
  if (tiltPosPositiveLimit >= value) {
    if (tiltPosNegativeLimit <= value) {
      tiltPos = (int)value;
    }
  }
}

void loop() {
  readPin(2);
  readPin(3);

  long now = millis();
  if ((now - lastServoResetTime) > servoResetFreq) {
    lastServoResetTime = now;
    tiltServo.write(tiltPos);
  }
}

void serialEvent() {
  byte cmd;
  byte arg;
  boolean complete = false;
  
  while (Serial.available()) {
    serBufferData[serBufferIndex] = (byte)Serial.read();
    cmd = serBufferData[0];

    if (serBufferIndex == 1) {
      arg = serBufferData[1];
      complete = true;
      serBufferIndex = 0;
    } else {
      serBufferIndex += 1;
    }
    
    if (cmd == pSetTilt) {
      if (complete) {
        setTilt(arg);
      }
    } else {
      // this command isn't known, so just ignore everything else
      Serial.flush();
    }
  }
}
