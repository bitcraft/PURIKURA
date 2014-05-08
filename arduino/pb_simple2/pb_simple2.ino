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

// 'p' prefix signifies 'protocol'
byte pSwitchTrigger = 0x01;
byte pSetTilt       = 0x80;

int tiltServoPin = 10;
int ledPin = 13;
int triggerState[] = {HIGH, HIGH};
int triggerHeld[] = {0, 0};

int lastTriggerState[] = {HIGH, HIGH};
long lastDebounceTime[] = {0, 0};
long debounceDelay = 100;

Servo tiltServo;
int incomingByte = 0;
int tiltPosNegativeLimit = 20;
int tiltPosPositiveLimit = 160;
int tiltPos = tiltPosNegativeLimit;

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
  
  // sub 2 b/c our inputs begin at 2
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
      Serial.write(pSwitchTrigger);
      Serial.write(pin);
    }
  } 
  else {
    triggerHeld[index] = 0;
  }
  
  lastTriggerState[index] = thisState;
}

void loop() {
  readPin(2);
  readPin(3);
  
  // read a byte from the serial buffer and set the byte value to the
  // servo position.  only the last read byte will change the servo.
  if (Serial.available() > 0) {
    incomingByte = Serial.read();
    if (tiltPosPositiveLimit >= incomingByte >= tiltPosNegativeLimit){
      tiltPos = incomingByte;
    }
  }
  
  // set our position each loop
  // this causes the servo to resist movement
  tiltServo.write(tiltPos);
}
