#!/usr/bin/env python
from __future__ import division
from datetime import datetime
import time,os,math
# Used for python networking
from flask import Flask, render_template, Response
# Raspberry Pi camera module
from camera_pi_V2 import Camera
# Initialize servo channels
import Adafruit_PCA9685 # Used for Servo control
from ServoClass_V2 import Servo
# User for Paho client communication
import paho.mqtt.client as mqtt

###  Initialize global class to hold system info ##########
class systemInfo():
    scanDir             = 1
    camera_prevaccessTS = 0
    lampMoveTS          = 0
    # Web app messages
    UserMode = 0
    payload  = None
    topic    = None
    # Hand Tracking
    gestureToggle = -2 # gesture state -2,-1,0,1 (setup,facetrack,static,search)
sysInfo = systemInfo()
    
###############################################################
############  PAHO Communication ##############################
#  version 2 (1 thread that reads all tasks)
def onConnect(client, userdata, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("head")
    client.subscribe("body")
    client.subscribe("rotation")
    client.subscribe("mode")
    
def whenMessageRecieved(client, userdata, msg):
    if len(msg.payload) > 0:
        payload = int(msg.payload)
        topic   = str(msg.topic)
        sysInfo.payload = payload
        if topic == 'mode':
            sysInfo.mode = topic
            modehandler()
        else:
            sysInfo.topic = topic
###############################################################
###########  Global Variables   ###############################
# Data directory [hardcoded]
datadir = "/home/pi/Desktop/TestFiles/DataFolder/"
# Subscribing as paho client
USERNAME = 'USER_DEFINED'
PASSWORD = 'USER_DEFINED'
BROKER   = 'broker.shiftr.io'
# Servos
Chan1 = 0
Chan2 = 1
Chan3 = 2
servoControl = True
#Initialize Paho client
client = mqtt.Client()
client.on_connect = onConnect
client.on_message = whenMessageRecieved
client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER)
client.loop_start()

#Initialize Servo classes
if servoControl:
    # Initialise the PCA9685 using the default address (0x40).
    pwm = Adafruit_PCA9685.PCA9685()
    # Set frequency to 60hz, good for servos.
    pwm.set_pwm_freq(60)
else:
    pwm = None 
servo1 = Servo(Chan1,pwm,"head")
servo2 = Servo(Chan2,pwm,"body")
servo3 = Servo(Chan3,pwm,"rotation")
# set servo limits
ServoLimits = [(0,180),(80,180),(71,169)]
# initialization pos
InitPos1 = 90   
InitPos2 = 169  
InitPos3 = 130
# Hand-Gesture pos
HandPos1  = 90    
HandPos2  = 82
HandPos3  = 169
# Shut-down pos
FinPos1   = 90    
FinPos2   = 35
FinPos3   = 95
###############################################################
############# Flask FUNCTIONS #################################
app = Flask(__name__)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen(camera):
    global sysInfo,servo1,servo2,servo3
    """Video streaming generator function."""
    while True:     
        #camera = setCameraState(camera) # evaluate lamp state to toggle modes for camera
        frame  = camera.get_frame()
        # web-app
        if sysInfo.UserMode == 1:
            camera.set_faceDetectionMode(False)
            camera.set_HandGestureMode(False)
            WebControl()
        # face tracking
        if sysInfo.UserMode == 2:
            camera.set_faceDetectionMode(True)
            camera.set_HandGestureMode(False)
            camera = FaceTracking(camera)
        # Hand Tracking
        if sysInfo.UserMode == 3:
            camera.reset_OccupancyDetectionMode()
            camera = HandTracking(camera)
        # occupancy detection
        if sysInfo.UserMode == 4:
            camera.set_faceDetectionMode(False)
            camera.set_HandGestureMode(False)
            camera = MotionTracking(camera)
                
        log_data(camera)        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
###############################################################
########## HELPER FUNCTIONS ###################################
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
    
def modehandler():
    global sysInfo
    print("Entering Mode handler",sysInfo.payload)
    # web control
    if (sysInfo.payload == 1):
        sysInfo.UserMode = 1
        wakeup()
        print("    web control")
        return
    # face focus
    if (sysInfo.payload == 22):
        print("    face focus")
        sysInfo.UserMode = 2
        wakeup()
        return
    # working with hands
    if (sysInfo.payload == 333):
        print("    hand tracking")
        sysInfo.UserMode = 3
        sysInfo.gestureToggle = -2
        wakeup()
        return
    # occupancy
    if (sysInfo.payload == 4444):
        print("    occupancy detection")
        sysInfo.UserMode = 4
        wakeup()
        return
    # sleep
    if (sysInfo.payload == 55555):
        print("    sleep")
        sysInfo.UserMode = 5
        sleep()
        return
# Function to evaluate lamp state to toggle modes for camera
def setCameraState(camera):
    global sysInfo
    usermode  = sysInfo.UserMode
    movetime  = sysInfo.lampMoveTS
    curtime   = time.time()
    return camera
    
def HandTracking(camera):
    global servo1,servo2,sysInfo
    # Step coefficients
    xstep = 1
    ystep = 1
    stepspeedCoeff  = 0.07
    # Search for face 
    if sysInfo.gestureToggle == -2:
        camera.set_faceDetectionMode(True)
        camera.set_HandGestureMode(False)
        sysInfo.gestureToggle = -1
        print("HandGesture mode",camera.hand_gesture_mode,"FaceDetection mode",camera.faceDetectionMode)
    # Begin gesture tracking
    if sysInfo.gestureToggle == -1:
        if len(camera.facepos) == 1:
            sysInfo.gestureToggle = 1
            camera.set_HandGestureMode(True)
            camera.set_faceDetectionMode(False)
            trackHands()
            print("Beginning Hand search")
        return camera      
    # Stay
    if sysInfo.gestureToggle == 0:
        print("Stay")
        return camera
    # Track
    if sysInfo.gestureToggle == 1:
        xpos = servo1.pos
        ypos = servo2.pos
        sumfingAngles  = sum(camera.fingerAngles)
        sumXfingDirs   = sum([xdir[0] for xdir in camera.fingerDir])
        sumYfingDirs   = sum([ydir[0] for ydir in camera.fingerDir])
        if sumfingAngles > 80:
            if(sumXfingDirs == 0):
                xstep = 0
            if(sumXfingDirs < 0):
                xstep = -1
            if(sumYfingDirs == 0):
                ystep = 0
            if(sumYfingDirs < 0):
                ystep = -1
        return camera
    return camera
    
def WebControl():
    global servo1,servo2,servo3,sysInfo
    stepspeedCoeff = 0.3
    sysInfo.topic
    sysInfo.payload
    if sysInfo.topic == "rotation":
        safeMovement(servo1,sysInfo.payload,stepspeedCoeff)
    if sysInfo.topic == "head":
        safeMovement(servo2,sysInfo.payload,stepspeedCoeff)
    if sysInfo.topic == "body":
        safeMovement(servo3,sysInfo.payload,stepspeedCoeff)
    
def MotionTracking(camera):
    global servo1,servo2,sysInfo
    # limits for center of frame
    xcenter = 30
    zcenter = 20
    # Step coefficients
    zstepSizeCoeff  = 0.5
    xstepSizeCoeff  = 0.1
    zstepspeedCoeff = 0.07
    xstepspeedCoeff = 0.05
    # timing variables
    processingRate = 0.5
    scanRate       = 3
    scanStepSize   = 10
    scanStepCoeff  = 0.05
    # current x & z servo positions
    xpos = servo1.pos
    zpos = servo2.pos
    newFrame = camera.last_access - sysInfo.camera_prevaccessTS
    if newFrame > processingRate:
        newpos = camera.movepos
        print(newpos)
        if newpos is None:
            lastmoveTS = time.time() - sysInfo.lampMoveTS
            if lastmoveTS > scanRate:
                print("scanning...")
                scan(servo1,scanStepSize,scanStepCoeff)
                camera.reset_OccupancyDetectionMode()
        else:
            xpos = servo1.pos
            zpos = servo2.pos
            print("Something detected")
            xpos_center = math.fabs(newpos[0]) > xcenter
            zpos_center = math.fabs(newpos[1]) > zcenter
            if (xpos_center):
                xstepsize = int(newpos[0]*xstepSizeCoeff)
                safeMovement(servo1,xpos+xstepsize,xstepspeedCoeff)
            if (zpos_center):
                zstepsize = int(newpos[1]*zstepSizeCoeff)
                safeMovement(servo2,zpos+zstepsize,zstepspeedCoeff)
            #if not zpos_center and not xpos_center:   
            camera.reset_OccupancyDetectionMode()
        sysInfo.camera_prevaccessTS = camera.last_access          
    return camera

def FaceTracking(camera):
    global servo1,servo3,sysInfo
    camera.reset_OccupancyDetectionMode()
    # limits for center of frame
    xcenter = 30
    zcenter = 20
    # Step coefficients
    zstepSizeCoeff  = 0.5
    xstepSizeCoeff  = 0.15
    zstepspeedCoeff = 0.1
    xstepspeedCoeff  = 0.05
    # timing variables
    processingRate = 0.5
    # current x & z servo positions
    xpos = servo1.pos
    zpos = servo3.pos
    newFrame = camera.last_access - sysInfo.camera_prevaccessTS
    if newFrame > processingRate:
        if len(camera.facepos) == 1:
            newpos = camera.facepos[0]
            xpos = servo1.pos
            zpos = servo3.pos
            if (math.fabs(newpos[0]) > xcenter):
                xstepsize = int(newpos[0]*xstepSizeCoeff)
                safeMovement(servo1,xpos+xstepsize,xstepspeedCoeff)
            if (math.fabs(newpos[1]) > zcenter):
                zstepsize = int(newpos[1]*zstepSizeCoeff)
                val = safeMovement(servo3,zpos+zstepsize,zstepspeedCoeff)
                #print(val,zpos,zpos+zstepsize)
        sysInfo.camera_prevaccessTS = camera.last_access
    return camera
        
# Function to incrementally move motor and change direction if limit reached
def scan(servo,scanStepSize,stepSpeed):
    global sysInfo
    stepsize = scanStepSize*sysInfo.scanDir
    nextDir  = safeMovement(servo,servo.pos+stepsize,stepSpeed)
    sysInfo.scanDir   = sysInfo.scanDir * nextDir
    
# functions to place lamp at appropriate positions based on mode
def trackHands():
    global servo1,servo2,servo3,sysInfo
    time.sleep(0.1)
    servo1.moveToSpeed(HandPos1,0.3)
    servo2.moveToSpeed(HandPos2,0.3)
    servo3.moveToSpeed(HandPos3,0.3)
    sysInfo.lampMoveTS = time.time()   
    
def wakeup():
    global servo1,servo2,servo3,sysInfo
    servo1.moveToSpeed(InitPos1,0.2)
    servo2.moveToSpeed(InitPos2,0.2)
    servo3.moveToSpeed(InitPos3,0.2)
    sysInfo.lampMoveTS = time.time()   
    
def sleep():
    global servo1,servo2,servo3,sysInfo
    servo1.moveToSpeed(FinPos1,0.2)
    servo2.moveToSpeed(FinPos2,0.2)
    servo3.moveToSpeed(FinPos3,0.2)
    sysInfo.lampMoveTS = time.time()
    
# Function to safely move lamp so that it doesn't exceed servo limits
def safeMovement(servo,pos,speed):
    global sysInfo
    lowerlimit  = ServoLimits[servo.channel][0]
    upperlimit  = ServoLimits[servo.channel][1]
    if (lowerlimit > pos):
        #print("Below lower limit",lowerlimit,pos)
        return -1
    if (upperlimit < pos):
        #print("Above upper limit",upperlimit,pos)
        return -1
    servo.moveToSpeed(pos,0.2)
    sysInfo.lampMoveTS = time.time()
    return 1

################################################        
########### MAIN FUNCTION ######################
if __name__ == '__main__':
    # Initialize servo positions
    wakeup()
    # Initialize data logging files (csv and avi)
    now = datetime.now()
    ts  = now.strftime("%B%d_%H%M")
    fname = datadir + "data_log" + str(ts) + ".csv"
    fid = open(fname,"w+")
    #if os.stat(fname).st_size == 0:
    #    if servoControl:
    #        fid.write("Time,occupied,s1pos,s2pos,s3pos,s4pos,contours,FacePos" + "\n")
    #    else:
    #        fid.write("Time,occupied,contours,FacePos" + "\n")
    app.run(host='0.0.0.0', debug=True, threaded=True)
