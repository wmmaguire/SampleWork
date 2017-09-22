import time
from datetime import datetime
import io
import threading
import picamera
import cv2
import numpy
import imutils
datadir = "/home/pi/Desktop/TestFiles/"
#Load a cascade file for detecting faces
face_cascade = cv2.CascadeClassifier(datadir + 'Classifiers/haarcascade_frontalface_default.xml')
            
class Camera(object):
    # Camera setup
    thread = None  # background thread that reads frames from camera
    frame  = None  # current frame is stored here by background thread
    faces       = [] # update if face is detected
    last_access = 0  # time of last client access to the camera
    resolution  = (320,240)
    framerate   = 25
    vname       = ''
    # Occupancy Detection variables
    refFrame = None
    occupied = False
    minArea  = 500
    contours = []
    
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
            
            #camera.hflip = True
            #camera.vflip = True
            # let camera warm up
            time.sleep(2)
            for foo in camera.capture_continuous(stream, 'jpeg',
                                                 use_video_port=True):
                # store frame
                stream.seek(0)
                #cls.frame = stream.read()
                inputStream = stream.getvalue()
                ## Face Detection
                cls  = face_detect(cls,inputStream)
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
def face_detect(Camera,inputStream):
    # Convert the picture into a numpy array
    buff = numpy.fromstring(inputStream, dtype=numpy.uint8)
    #Now creates an OpenCV image
    image = cv2.imdecode(buff, 1)
    # convert it to grayscale, and blur it
    gray         = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoisedgray = cv2.GaussianBlur(gray, (21, 21), 0)
    # Time stamp image
    cv2.putText(image, datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
        (10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)    
    #Look for faces in the image using the loaded cascade file
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)
    #Draw a rectangle around every found face
    for (x,y,w,h) in faces:
        cv2.rectangle(image,(x,y),(x+w,y+h),(255,255,0),2)      
    #convert image back to bytes
    ret, frame = cv2.imencode('.jpg', image)
    Camera.frame = frame.tostring()
    return Camera
