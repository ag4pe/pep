//README: this program pulses two stepper drivers based on user input from a 3-way switch and a potentiometer.
//  Switch up pos runs motor1 cw,down pos runs motor1 ccw, center pos runs both motors at same speed in same direction as before.
//  Potentiometer controls speed from 0-5kHz. 
//Wiring: see pin number variables below.
//  Pot requires 5V,GND, and signal with 10kOhm from signal to ground.
//  Switch requires common GND and two signals using built-in pull-up resistors.

//PIN #s
int gnd=4;
int clk=5;

//VARS
String readString;
int n0 = 0; //initial sleep time (2/frequency)
int i;    //index
int x;    //intermediate sleep time during ramp from n0 to n
int elapse; //stopwatch for rampup
void setup() {
  Serial.begin(9600);
  pinMode(clk,OUTPUT);
}

void loop() {
  if (Serial.available())  {
    char c = Serial.read();  //gets one byte from serial buffer
    if (c == 10) { //if newline, save/print result
      Serial.println(readString);
      int n = readString.toInt();
      if (n > 0) { //zero means stop
        x=n+1;
        i=0;
        elapse = millis();
        while (x > n && Serial.peek() == -1){
          i++;
          x = sqrt(n*150000/i); //linear ramp: sleep_n = sqrt(sleep_target * duration / index)
          digitalWrite(clk,HIGH);
          delayMicroseconds(x);
          digitalWrite(clk,LOW);
          delayMicroseconds(x);
        }
//        Serial.println(millis()-elapse);
        n0 = n;
        while (Serial.peek() == -1){
          digitalWrite(clk,HIGH);
          delayMicroseconds(n);
          digitalWrite(clk,LOW);
          delayMicroseconds(n);
        }
        n0 = 0;
      }
      readString=""; //clears variable for new input
    }  
    else {     
      readString += c; //makes the string readString
    }
  }  
}
