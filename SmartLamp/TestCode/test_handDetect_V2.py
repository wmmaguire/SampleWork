import numpy as np
import cv2

track_mode = False
termination = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
roiBox = None
kernel = np.ones((5, 5), np.uint8)
frame_width_in_px = 640
number_of_histogram_elements=16
face_cascade = cv2.CascadeClassifier('/Users/maxmaguire/Desktop/Grad School/CMU/Semester-2/UserSensorSystems/Final Project/TestFiles/Classifiers/haarcascade_frontalface_default.xml')
fgbg = cv2.bgsegm.createBackgroundSubtractorMOG(history=3,nmixtures=2,backgroundRatio=0.001) # python2v3
minArea = 500
def selectROI(event, x,y,flags,param):
    global track_mode

    if (event == cv2.EVENT_LBUTTONDOWN): #reselecting ROI points so take out of tracking mode and empty current roipoints
        track_mode = False

cap = cv2.VideoCapture(0)
cv2.namedWindow("frame")
cv2.setMouseCallback("frame", selectROI)

while True:
    ret, frame = cap.read()
    if not track_mode:
        #  Step1: Detect face (ROI)
        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        #Look for faces in the image using the loaded cascade file
        face = face_cascade.detectMultiScale(gray, 1.1, 5)
        for (x,y,w,h) in face:
            print('_________New face detected_______')
            roiBox = (x,y,x+w,y+h)
            # Define ROI in HSV
            roi      = frame[int(y+h/2):int(y+2*h/3), int(x+w/5):int(x+4*w/5)]
            hsv_roi  = cv2.cvtColor(roi,cv2.COLOR_BGR2HSV)
            cv2.rectangle(frame,(int(x+w/5),int(y+h/2)),(int(x+4*w/5),int(y+2*h/3)),(255,255,255),2)
            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
            #################### Method 1 ############################
            hist_mask_hue  = cv2.calcHist([hsv_roi],[0],None,[number_of_histogram_elements],[0,180])
            nhist_mask_hue = cv2.normalize(hist_mask_hue,hist_mask_hue,0,255,cv2.NORM_MINMAX)
            track_mode = True #ready for camshift

    if track_mode == True: #tracking mode
        fgmask  = np.zeros(frame.shape[:2],np.uint8)
        hsv     = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        backProj = cv2.calcBackProject([hsv], [0], nhist_mask_hue, [0, 180], 1)
        #perfrom some noise reduction and smoothing on skin mask
        erosion  = cv2.erode(backProj, kernel, iterations=2)
        dilate   = cv2.dilate(erosion, kernel, iterations=2)
        skinthresh = cv2.GaussianBlur(dilate,(3,3),0)
        # segment foreground from background 
#        fgthesh  = fgbg.apply(frame)
#        fgthesh  = cv2.dilate(fgthesh, kernel, iterations=6)
#        _,cnts,_ = cv2.findContours(fgthesh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # python2v3
#        for c in cnts:
#            #print(c)
#            # if the contour is too small, ignore it
#            if cv2.contourArea(c) < minArea:
#                continue
#            # compute the bounding box for the contour and draw a mask for it
#            (x, y, w, h) = cv2.boundingRect(c)
#            fgmask[y:y+w,x:x+w] = 255           
#            #cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
#        # combine masks
#        skinMask  = cv2.bitwise_and(skinMask,skinMask,mask=fgmask)
        skinMask  = cv2.bitwise_and(frame,frame,mask=skinthresh)
        (r, roiBox) = cv2.CamShift(dilate, roiBox, termination) #this takes prev roiBox and calculates the new roiBox
        pts = np.int0(cv2.boxPoints(r))
        cv2.polylines(frame, [pts], True, (0, 255, 0), 2) #tracking box
        cv2.polylines(backProj, [pts], True, (0, 255, 0), 2) #tracking box
        cv2.polylines(dilate, [pts], True, (0, 255, 0), 2) #tracking box
        cv2.polylines(hsv, [pts], True, (0, 255, 0), 2) #tracking box

        # plot histogram polyline across the windows
        x = np.linspace(0,640,number_of_histogram_elements,dtype=np.int32)
        y = nhist_mask_hue.flatten().astype(np.int32, copy=False)-255 #note frame height needs to be greater than 255 which is the max histo value
        y = np.absolute(y)
        pts2 = np.stack((x, y), axis=1)
        cv2.polylines(frame, [pts2], False, (0, 255, 0), 2)
        cv2.polylines(hsv, [pts2], False, (0, 255, 0), 2)
        cv2.imshow("skin Mask", skinMask)

    cv2.imshow("frame", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
