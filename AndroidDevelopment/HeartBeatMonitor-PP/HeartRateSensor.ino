/*
 * Project HeartRateSensor
 * Description:
        Example program to:
 - Measures the heart rate through a pulse Sensor
 and flashes an RGB LED to indicate when a pulse
 has occurred.  This is connected to the Particle Photon
 Sensor App, which displays the BPM and controls the RGB LED color.
 * Author: Max Maguire
 * Date: 04/10/17
 */
 // input pins
 int PulseSensorPurplePin = A1;
 int ai1   = A0; // not used
 // output pins
 int led2  = D7; // not necessary
 int rled  = A4;
 int gled  = A5;
 int bled  = A7;
 // heat beat variables
 double fcoeff   = 0.05;
 double cur_heartBeatTS = 0;
 int cur_dfs        = 0;
 int bpm   = 0;
 int Signal = 0;      // raw signal
 int FiltSignal  = 0; // 1st Layer lp filter
 int FiltSignal2 = 0; // 2nd Layer lp filter
 char respSIG[64];
 bool startFlag  = true;
 int threshold[] = {40,200}; // bpm threshold
 // Initialize rgb led values
 int redValue[]   = {255,0};
 int greenValue[] = {255,255};
 int blueValue[]  = {255,255};
 // not used..
 double danalogvalue = 0;
 int  ianalogvalue = 0;
 char respPOT[64];

 void setup() {

   //Register our Particle function here
   Particle.function("RGBled", RGBledControl);
   //Register our Particle variable here
   //Particle.variable("ianalogvalue", &ianalogvalue,INT);
   Particle.variable("bpm", &bpm, INT);
   Serial.begin(9600);
   // Set outputs
   pinMode(led2,OUTPUT);
   pinMode(rled,OUTPUT);
   pinMode(gled,OUTPUT);
   pinMode(bled,OUTPUT);
   // set inputs
   pinMode(ai1,INPUT);
   // turn rgb led to off state...
   analogWrite( rled, redValue[0]);
   analogWrite( gled, greenValue[0]);
   analogWrite( bled, blueValue[0]);
 }

 void loop() {
   // On First loop, record Signal in filters...
   Signal = analogRead(PulseSensorPurplePin);
   if (startFlag) {
    Serial.println("First Line");
    FiltSignal  = Signal;
    FiltSignal2 = Signal;
    // Signal Beginning of Loop
    // Red first
    analogWrite( rled, 0);
    analogWrite( gled, greenValue[0]);
    analogWrite( bled, blueValue[0]);
    delay(500);
    // Green Second
    analogWrite( rled, redValue[0]);
    analogWrite( gled, 0);
    analogWrite( bled, blueValue[0]);
    delay(500);
    // Blue Last
    analogWrite( rled, redValue[0]);
    analogWrite( gled, greenValue[0]);
    analogWrite( bled, 0);
    delay(500);
   }
   Serial.print(String(millis()));
   // detect heart beat and calculate bpm
   heartBeatDetection();
   sprintf(respSIG, "\tPulseSignal,%d,time,%d,FiltSignal2", Signal,FiltSignal2);
   Serial.println(respSIG);
   // Wait 10 milli-seconds...
   delay(10);
   startFlag = false;
 }
 // Provide String input to change RGB LED
 int RGBledControl( String command )
{
    String colors[3];
    colors[0]="";
    colors[1]="";
    colors[2]="";
    int index = 0;
    for( int i = 0; i < command.length(); i++ )
    {
      if( index < 3 ){
        char c = command.charAt(i);
        colors[index] += c;

        if( c == ',') index++;
      }
    }
    // get the red component...
    redValue[1]   = colors[0].toInt();
    // now green
    greenValue[1] = colors[1].toInt();
    // now blue
    blueValue[1]  = colors[2].toInt();
   // write the mixed color
   return 1;
}
// Process Pulse Sensor Data
void heartBeatDetection() {
    int prev_FiltSignal    = FiltSignal;
    int prev_FiltSignal2   = FiltSignal2;
    int prev_dfs           = cur_dfs;
    // apply 2 layer, low-pass Filter
    FiltSignal  = lpFilter(Signal,prev_FiltSignal);
    FiltSignal2 = lpFilter(FiltSignal,prev_FiltSignal2);
    cur_dfs = FiltSignal2 - prev_FiltSignal2;
    // evaluates local maximum of filtered signal
    if (cur_dfs <= 0 && prev_dfs > 0) {
      double evalcur_heartBeatTS       = double(millis());
      double dt = (evalcur_heartBeatTS - cur_heartBeatTS)/1000.0;
      double temp_bpm = (60.0/dt);
      // Evaluate bpm frequency to fit within range (40-200)
      if (temp_bpm > threshold[1]) {
        return;
      }
      // if below high threshold, store new pulse TS
      cur_heartBeatTS = evalcur_heartBeatTS;
      if (temp_bpm > threshold[0]) {
        bpm = temp_bpm;
        // turn LEDs on
        //rgbpulse();
        analogWrite( rled, redValue[1]);
        analogWrite( gled, greenValue[1]);
        analogWrite( bled, blueValue[1]);
        digitalWrite(led2, HIGH);
        return;
      }
    }
    // turn LEDs off
    analogWrite( rled, redValue[0]);
    analogWrite( gled, greenValue[0]);
    analogWrite( bled, blueValue[0]);
    digitalWrite(led2, LOW);
    return;
}
// Low-Pass Filter
int lpFilter(int Sig,int prev_fSig) {
  int fSignal = int(fcoeff*Sig + (1.0-fcoeff)*prev_fSig);
  return fSignal;
}
// display rgb led Pulse
void rgbpulse() {
  for (int i = 0; i < 255; i++) {
    if (redValue[1] > i) {
      analogWrite( rled, i);
    }
    if (greenValue[1] > i) {
      analogWrite( gled, i);
    }
    if (blueValue[1] > i) {
      analogWrite( bled, i);
    }
    delay(1);
  }
}
