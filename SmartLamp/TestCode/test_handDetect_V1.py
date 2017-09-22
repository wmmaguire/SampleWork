import numpy as np
import cv2

roiPts = []
track_mode = False
termination = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
roiBox = None
kernel = np.ones((5, 5), np.uint8)
frame_width_in_px = 640
number_of_histogram_elements=16

def selectROI(event, x,y,flags,param):
    global track_mode, roiPts

    if (event == cv2.EVENT_LBUTTONDOWN) and (len(roiPts)==4): #reselecting ROI points so take out of tracking mode and empty current roipoints
        roiPts=[]
        track_mode = False
    if (event==cv2.EVENT_LBUTTONDOWN) and (len(roiPts) < 4): #ROI point selection
        roiPts.append([x, y])
        print(roiPts)

cap = cv2.VideoCapture(0)
cv2.namedWindow("frame")
cv2.setMouseCallback("frame", selectROI)

while True:
    ret, frame = cap.read()

    if len(roiPts)<=4 and len(roiPts)>0:
        for x,y in roiPts:
            cv2.circle(frame, (x,y), 4, (0, 255, 0), 1)  # draw small circle for each roi click

    if len(roiPts)==4 and track_mode==False: #initialize the camshift
        # convert the selected points to a box shape
        roiBox = np.array(roiPts, dtype=np.int32)
        s = roiBox.sum(axis=1)
        tl = roiBox[np.argmin(s)]
        br = roiBox[np.argmax(s)]

        #extract the roi from the image and calculate the histograme
        roi = frame[tl[1]:br[1], tl[0]:br[0]]
        roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV) #
        roiHist = cv2.calcHist([roi], [0], None, [number_of_histogram_elements], [0, 180])
        roiHist = cv2.normalize(roiHist, roiHist, 0, 255, cv2.NORM_MINMAX)
        roiBox = (tl[0], tl[1], br[0], br[1])
        track_mode = True #ready for camshift

    if track_mode == True: #tracking mode
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        backProj = cv2.calcBackProject([hsv], [0], roiHist, [0, 180], 1)
        #perfrom some noise reduction and smoothing
        erosion = cv2.erode(backProj, kernel, iterations=2)
        dilate = cv2.dilate(erosion, kernel, iterations=2)
        (r, roiBox) = cv2.CamShift(dilate, roiBox, termination) #this takes prev roiBox and calculates the new roiBox
        pts = np.int0(cv2.boxPoints(r))
        cv2.polylines(frame, [pts], True, (0, 255, 0), 2) #tracking box
        cv2.polylines(backProj, [pts], True, (0, 255, 0), 2) #tracking box
        cv2.polylines(dilate, [pts], True, (0, 255, 0), 2) #tracking box
        cv2.polylines(hsv, [pts], True, (0, 255, 0), 2) #tracking box

        # plot histogram polyline across the windows
        x = np.linspace(0,640,number_of_histogram_elements,dtype=np.int32)
        y = roiHist.flatten().astype(np.int32, copy=False)-255 #note frame height needs to be greater than 255 which is the max histo value
        y=np.absolute(y)
        pts2 = np.stack((x, y), axis=1)
        cv2.polylines(frame, [pts2], False, (0, 255, 0), 2)
        cv2.polylines(hsv, [pts2], False, (0, 255, 0), 2)

        #cv2.imshow("backproject", backProj)
        #cv2.imshow("dilate", dilate)
        #cv2.imshow("hsv", hsv)

    cv2.imshow("frame", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
