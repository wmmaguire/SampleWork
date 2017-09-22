#!/usr/bin/env python
from __future__ import division
from datetime import datetime
import os
# Used for python networking
from flask import Flask, render_template, Response
# Raspberry Pi camera module (requires picamera package)
from camera_pi_V2 import Camera

# Data directory [hardcoded]
datadir = "/home/pi/Desktop/TestFiles/DataFolder/"
# Initialize servo channels
from ServoClass import Servo
Chan1 = 0
Chan2 = 1
Chan3 = 2
servoControl = False
if servoControl:
    # Used for Servo control
    import Adafruit_PCA9685
    # Initialise the PCA9685 using the default address (0x40).
    pwm = Adafruit_PCA9685.PCA9685()
    # Set frequency to 60hz, good for servos.
    pwm.set_pwm_freq(60)
else:
    pwm = None
    
servo1 = Servo(Chan1,pwm,"head")
servo2 = Servo(Chan2,pwm,"body")
servo3 = Servo(Chan3,pwm,"shoulder")
print(servo1.mid)
print(servo2.mid)
print(servo3.mid)
    
app = Flask(__name__)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        #log_data(camera)        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def log_data(camera):
    fid.write(str(camera.last_access) + ";" + str(camera.occupied))
    if servoControl:
        s1chan,s1pos = servo1.get_servoinfo()
        s2chan,s2pos = servo2.get_servoinfo()
        s3chan,s3pos = servo3.get_servoinfo()
        fid.write(";" + str(s1pos))
        fid.write(";" + str(s2pos))
        fid.write(";" + str(s3pos))
    fid.write(";[")
    for c in camera.contours:
        fid.write(str(c))
    fid.write("];[")
    for face in camera.faces:
        fid.write(str(face))
    fid.write("];\n")

if __name__ == '__main__':
    # Initialize data logging files (csv and avi)
    now = datetime.now()
    ts  = now.strftime("%B%d_%H%M")
    fname = datadir + "data_log" + str(ts) + ".csv"
    fid = open(fname,"w+")
    if os.stat(fname).st_size == 0:
        if servoControl:
            fid.write("Time,occupied,s1pos,s2pos,s3pos,s4pos,contours,FacePos" + "\n")
        else:
            fid.write("Time,occupied,contours,FacePos" + "\n")
    app.run(host='0.0.0.0', debug=True, threaded=True)
