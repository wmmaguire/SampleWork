import time
from datetime import datetime
import io
import threading
import picamera
import cv2
import numpy as np
import math
datadir = "/home/pi/Desktop/TestFiles/"
#Load a cascade file for detecting faces
face_cascade = cv2.CascadeClassifier(datadir + 'Classifiers/haarcascade_frontalface_default.xml')
# Hand detection variables
number_of_histogram_elements=16
minFingerLen = 70
hsvSatThresh = 30
hsvValThresh = 75

class Camera(object):
    # Camera setup
    thread = None  # background thread that reads frames from camera
    frame  = None  # current frame is stored here by background thread
    faces  = []    # update if face is detected
    skinHist    = None # update skinhistogram from face ROI for hand detection
    last_access = 0     # time of last client access to the camera
    resolution  = (320,240)
    framerate   = 25
    vname       = ''
    # Face Detection info
    facepos     = []
    # Occupancy Detection variables
    refFrame = None
    occupied = False
    movepos  = None
    # Hand Gesture info
    hand_gesture_mode = True
    minArea  = 500
    fingerAngles = []   # finger angles
    fingerDir    = []   # finger directions
    handGesIter  = 5    # frames to skip before running hand gesture algorithm
#    contours     = []
    
    def initialize(self):
        if Camera.thread is None:
            # start background frame thread
            now = datetime.now()
            ts  = now.strftime("%B%d_%H%M")
            vname = datadir + "DataFolder/video_log" + ts + ".h264"
            Camera.vname  = vname
            Camera.thread = threading.Thread(target=self._thread)
            Camera.thread.start()

            # wait until frames start to be available
            while self.frame is None:
                time.sleep(0)

    def get_frame(self):
        Camera.last_access = time.time()
        self.initialize()
        return self.frame

    @classmethod
    def _thread(cls):  
        with picamera.PiCamera() as camera:
            stream = io.BytesIO()
            camera.resolution = cls.resolution
            camera.framerate  = cls.framerate
            camera.start_preview()
            camera.start_recording(cls.vname)
            
            # let camera warm up
            time.sleep(2)
            for foo in camera.capture_continuous(stream, 'jpeg',
                                                 use_video_port=True):
                # store frame
                stream.seek(0)
                #cls.frame = stream.read()
                inputStream = stream.getvalue()
                ## image processing
                cls  = img_processor(cls,inputStream)
                #cls.faces    = Camera.faces
                #cls.frame    = Camera.frame
                # reset stream for next frame
                stream.seek(0)
                stream.truncate()

                # if there hasn't been any clients asking for frames in
                # the last 5 seconds stop the thread
                if time.time() - cls.last_access > 5:
                    break
        cls.thread = None

# Image processing helper functions
def img_processor(Camera,inputStream):
    # Convert the picture into a numpy array
    buff = np.fromstring(inputStream, dtype=np.uint8)
    #Now creates an OpenCV image
    image = cv2.imdecode(buff, 1)
    gray  = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Occupancy detection (2 methods)
    Camera,image = OccupancyDetection1(Camera,gray,image)
    Camera,image = FaceDetection(Camera,gray,image)
    if Camera.skinHist is not None and Camera.hand_gesture_mode:
        # Hand Gestures
#        print("Entering Hand Gestures")
        if Camera.handGesIter == 0:
            Camera,image = handGestures(Camera,image)
            Camera.handGesIter = 2
        else:
            Camera.handGesIter = Camera.handGesIter - 1 
    # Add ccupancy state text to image
    if Camera.occupied:
        state = "occupied"
	printcolor = (0,0,255)
    else:
        state = "unoccupied"
        printcolor = (0,255,0)
    cv2.putText(image, "Room Status: {}".format(state), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, printcolor, 2)
    # Add time-stamp text to image
    cv2.putText(image, datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
        (10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
    # Add finger count text to image
    cv2.putText(image, "Finger Count: {}".format(str(len(Camera.fingerDir))),
        (10, image.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
    #convert image back to bytes
    ret, frame = cv2.imencode('.jpg', image)
    Camera.frame = frame.tostring()
    return Camera

## Occupancy Detection Method1: difference in Reference frame 
def OccupancyDetection1(Camera,gray,image):
    ## OccupancyDetection vars
    maxmov          = 0
    cntrpoint       = None
    Camera.movepos  = None
    Camera.occupied = False 
    # Denoise gray image
    denoisedgray = cv2.GaussianBlur(gray, (21, 21), 0)
    # if the ref frame is None, initialize it and end processing
    if Camera.refFrame is None:
        print("Defining RefFrame")
        Camera.refFrame = denoisedgray
        # convert image back to bytes
        ret, frame    = cv2.imencode('.jpg', image)
        Camera.faces    = []
        return Camera,image
    # compute the absolute difference between the current frame and ref frame
    frameDelta = cv2.absdiff(Camera.refFrame, denoisedgray)
    thresh     = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
 
    # dilate the thresholded image, then find contours on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)
    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)
    # loop over the contours and store in class object
    for c in cnts:
	# if the contour is too small, ignore it
	if cv2.contourArea(c) < Camera.minArea:
	    continue
        # compute the bounding box for the contour and draw it on the frame
	(x, y, w, h) = cv2.boundingRect(c)
	xdisp = Camera.resolution[0]/2 - (x+w/2)
        ydisp = Camera.resolution[1]/2 - (y+h/2)
	c = math.sqrt((xdisp)**2 + (ydisp)**2)
	# To visualize (center of frame)
#	cv2.circle(image,(int(Camera.resolution[0]/2),int(Camera.resolution[1]/2)),5,[255,255,255],2)
	if (c > maxmov):
            maxmov  = c
            Camera.movepos = (int(xdisp),int(ydisp))
            cntrpoint = (x+w/2,y+h/2)
        # Update Frame
	Camera.occupied = True
    # To visualize (center of movement)
#    if cntrpoint is not None:
#        cv2.circle(image,(x+w/2,y+h/2),5,[0,0,255],2)     
    return Camera,image

## Occupancy Detection Method2: Adaptive foreground analysis 
def OccupancyDetection2(Camera,gray,image):
    ## OccupancyDetection
    maxmov          = 0
    cntrpoint       = None
    Camera.movpos   = None
    Camera.occupied = False
    state           = "unoccupied"
    printcolor      = (0,255,0)
    # Apply GMM mask
    fgmask = fgbg.apply(image,learningRate = 0.01)
    # dilate the thresholded image, then find contours on thresholded image
    thresh = cv2.dilate(fgmask, None, iterations=2)
    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)
    # loop over the contours and store in class object
    Camera.contours = cnts
    for c in cnts:
	# if the contour is too small, ignore it
	if cv2.contourArea(c) < Camera.minArea:
	    continue
            # compute the bounding box for the contour and draw it on the frame
	(x, y, w, h) = cv2.boundingRect(c)
	xdisp = Camera.resolution[0]/2 - (x+w/2)
        ydisp = Camera.resolution[1]/2 - (y+h/2)
	c = math.sqrt((xdisp)**2 + (ydisp)**2)
	# plot center of frame for visualization
#	cv2.circle(image,(int(Camera.resolution[0]/2),int(Camera.resolution[1]/2)),5,[255,255,255],2)
	if (c > maxmov):
            maxmov = c
            cntrpoint = (x+w/2,y+h/2)
            Camera.movepos = (int(xdisp),int(ydisp))
        # Update Frame
	Camera.occupied = True
	state           = "occupied"
	printcolor      = (0,0,255)
    # plot center of movement for visualization
    #if cntrpoint is not None:
        #cv2.circle(image,(x+w/2,y+h/2),5,[0,0,255],2)
    Camera.movepos = movepos
    cv2.putText(image, "Room Status: {}".format(state), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, printcolor, 2)
    return Camera,image

## Face Detection
def FaceDetection(Camera,gray,image):
    #Look for faces in the image using the loaded cascade file
    facepos = []
    faces   = face_cascade.detectMultiScale(gray, 1.2, 5)
    #Draw a rectangle around every found face
    Camera.faces = faces
    for (x,y,w,h) in faces:
#        print("Face Detected")
        cv2.rectangle(image,(x,y),(x+w,y+h),(255,255,0),2)
        # To visualize (plot center of frame and center of face)
        cv2.circle(image,(int(Camera.resolution[0]/2),int(Camera.resolution[1]/2)),5,[255,255,0],2)
        cv2.circle(image,(x+w/2,y+h/2),5,[255,0,0],2)
        xdisp = Camera.resolution[0]/2 - x+w/2
        ydisp = Camera.resolution[1]/2 - y+h/2
        facepos.append((xdisp,ydisp))
    Camera.facepos = facepos
    if len(faces) == 1:
#        print(Camera.facepos)
        Camera = SkinMap(faces,image)     
    return Camera,image

## Skin Map: Create Hue histogram of face that is detected (2 methods)
def SkinMap(faces,img):
    # Method 1: Use face to characterize skin and develop Mask
    hist_flat = None
#   print('_________Skin Mapping_______')
    # Adaptive skin color mapping
    for (x,y,w,h) in faces:
        # for visulization (Draw rectancle around face and sub-region for skin mapping)
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,255,0),2)
        cv2.rectangle(img,(int(x+w/5),int(y+h/2)),(int(x+4*w/5),int(y+2*h/3)),(255,255,255),2)
        # Masking of ROI (capture nose region for skin extraction)
        roi      = img[int(y+h/2):int(y+2*h/3), int(x+w/5):int(x+4*w/5)]
        hsv_roi  = cv2.cvtColor(roi,cv2.COLOR_BGR2HSV)
        # Calculate histogram (Normalize)
        hist_mask_hue  = cv2.calcHist([hsv_roi],[0],None,[number_of_histogram_elements],[0,180])
        nhist_mask_hue = cv2.normalize(hist_mask_hue,0,255,cv2.NORM_MINMAX)
        # Use hue histogram to backproject and map out skin tone
        hist_flat = nhist_mask_hue.reshape(-1)
    Camera.skinHist   = hist_flat
    return Camera
    
def handGestures(Camera,img):
    hsv      = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Method 1: Adaptive, backprojection from normalize hue hist
    hist_flat = Camera.skinHist
    thresh    = cv2.calcBackProject([hsv], [0], hist_flat , [0, 180], 1)
    # Create kernel and apply erosion/dilation and denoising filters to skin mask
    kernel       = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
    erosion      = cv2.erode(thresh,kernel,iterations = 4)
    dilate       = cv2.dilate(erosion,kernel,iterations = 4)
    skinThresh   = cv2.GaussianBlur(dilate,(3,3),0)
    # To visualize (skinMask)
#    skinMask    = cv2.bitwise_and(img,img,mask=skinthresh)
    # Apply skinthreshold to image
    # look for contours in image (representing skin outline)
    contours, hierarchy = cv2.findContours(skinThresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE) # Method 1
    max_area=0
    ci = 1
    fingerAngles = []
    fingerDir    = []
    for i in range(len(contours)):
        cnt=contours[i]
        area = cv2.contourArea(cnt)
        if(area > max_area):
            max_area=area
            ci=i
        cnt=contours[ci]
        hull = cv2.convexHull(cnt)
        moments = cv2.moments(cnt)
        # Find center of hand and draw
        if moments['m00']!=0:
            cx = int(moments['m10']/moments['m00']) # cx = M10/M00
            cy = int(moments['m01']/moments['m00']) # cy = M01/M00             
        centr=(cx,cy)
        #...        
        cnt  = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)
        hull = cv2.convexHull(cnt,returnPoints = False)
        # Look for hull/convex points to denote fingers
        defects = cv2.convexityDefects(cnt,hull)
        mind=0
        maxd=0
        count_defects = 0
        if defects is None:
            continue
        for j in range(defects.shape[0]):
            s,e,f,d = defects[j,0]
            start = tuple(cnt[s][0]) # contour pt 1
            end = tuple(cnt[e][0])   # contour pt 2
            far = tuple(cnt[f][0])   # convex point
            # Draw triangle between two convex points and convex points
            a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
            c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
            # Compute angle between two fingers
            angle = math.acos((b**2 + c**2 - a**2)/(2*b*c)) * 57.3
            # Calculate finger lengths
            fin1dir = (centr[0] - start[0],centr[1] - start[1])
            fin2dir = (centr[0] - end[0],centr[1] - end[1])
            fin1len = math.sqrt((fin1dir[0])**2 + (fin1dir[1])**2)
            fin2len = math.sqrt((fin2dir[0])**2 + (fin2dir[1])**2)
            # Evaluate conditions to classify valid finger (finger angles/length)
            if ((angle <= 90) & (angle not in fingerAngles) &
                (fin1len > minFingerLen) & (fin2len > minFingerLen) ):
                # Log Finger data (angle/Dir)
                fingerAngles.append(angle)
                fingerDir.append(fin1dir)
                fingerDir.append(fin2dir)
                count_defects += 1
                ##Draw center of hand
                cv2.circle(img,centr,5,[0,0,255],2) 
                ## Draw circle at dip between fingers  
                cv2.circle(img,far,5,[255,0,0],-1)
                ## Draw Triangle between fingers
                cv2.line(img,far,start,[255,255,255],2)
                cv2.line(img,far,end,[255,255,255],2) 
                cv2.line(img,start,end,[0,255,0],2)
#    print("")
#    print("finger Distances: ",list(set(fingerDir)))
#    print("finger Angles: ",fingerAngles)
    Camera.fingerAngles = fingerAngles
    Camera.fingerDir    = fingerDir
    return Camera,img
