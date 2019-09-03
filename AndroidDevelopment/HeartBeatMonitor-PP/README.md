Author: Max Maguire
Description: Heart Beat Monitor PP

-  This submission includes:
a. STL : PrintV3.zip
b. Particle Source Code: HeartRateSensor.ino
c. Android Source Code: MyParticlePhotonApp
d. Video: HeartRateMonitor_Demo

This is a pulse sensor that works as a wearable device that you strap to your fingertip.
Within the 3d printed casing (a) is a switch that can be used to turn on the particle photon.  
Upon start-up: the RGB LED will flash Red, Green and Blue then begin to track user heart rate.  
The RGB LED flashes every time that a pulse is detected.  It can also "pulsate" given a minor 
change to (b).  The Android app communicates (c) with the particle photon by receiving BPM values
that are process on the particle photon and displaying the value on the screen.  Furthermore, 
it can transmit commands to change the RGB value that flashes to inform the user of a heart beat.