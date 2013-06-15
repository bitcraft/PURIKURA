/*
 Input Pullup Serial
 
 This example demonstrates the use of pinMode(INPUT_PULLUP). It reads a 
 digital input on pin 2 and prints the results to the serial monitor.
 
 The circuit: 
 * Momentary switch attached from pin 2 to ground 
 * Built-in LED on pin 13
 
 Unlike pinMode(INPUT), there is no pull-down resistor necessary. An internal 
 20K-ohm resistor is pulled to 5V. This configuration causes the input to 
 read HIGH when the switch is open, and LOW when it is closed. 
 
 created 14 March 2012
 by Scott Fitzgerald
 
 http://www.arduino.cc/en/Tutorial/InputPullupSerial
 
 This example code is in the public domain
 
 */

int triggerPin = 2;
int ledPin = 13;
int triggerState[] = {HIGH, HIGH};
int triggerHeld[] = {0, 0};

int lastTriggerState[] = {HIGH, HIGH};
long lastDebounceTime[] = {0, 0};
long debounceDelay = 100;


void setup() {
  //start serial connection
  Serial.begin(9600);
  //configure pin2 as an input and enable the internal pull-up resistor
  pinMode(triggerPin, INPUT_PULLUP);
  pinMode(3, INPUT_PULLUP);
  pinMode(ledPin, OUTPUT);

}

void readPin(int pin) {
  //read the pushbutton value into a variable
  int thisState = digitalRead(pin);
  long now = millis();
  
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
      Serial.println(pin);
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
}
