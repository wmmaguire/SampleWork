import cv2
import numpy as np
import math

fname = '/Users/maxmaguire/Desktop/Grad School/CMU/Semester-2/UserSensorSystems/Final Project/TestFiles/ImgProcessing/images/hand4.jpg'
fname1 = '/Users/maxmaguire/Desktop/Grad School/CMU/Semester-2/UserSensorSystems/Final Project/TestFiles/ImgProcessing/images/face4.jpg'
#Load a cascade file for detecting faces
face_cascade = cv2.CascadeClassifier('/Users/maxmaguire/Desktop/Grad School/CMU/Semester-2/UserSensorSystems/Final Project/TestFiles/Classifiers/haarcascade_frontalface_default.xml')
# load hand/face image
img  = cv2.imread(fname)
img1 = cv2.imread(fname1)
## Filter 1 ##
minFingerLen = 50
hsvSatThresh = 30
hsvValThresh = 75
# resize, convert to gray scale, apply gaussian denoising
img  = cv2.resize(img,(320,240))
img1 = cv2.resize(img1,(320,240))
hsv  = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
## Filter 2 ##
#  Step1: Detect face (ROI)
gray1 = cv2.cvtColor(img1,cv2.COLOR_BGR2GRAY)
#Look for faces in the image using the loaded cascade file
faces = face_cascade.detectMultiScale(gray1, 1.1, 5)
#  Step2: Draw a rectangle around face (ROI) and extract hist mapping
mask  = np.zeros(img1.shape[:2],np.uint8)
for (x,y,w,h) in faces:
    print('')
    print('_________face detected_______')
    cv2.rectangle(img1,(x,y),(x+w,y+h),(255,255,0),2)
    # Masking of ROI
    hsv2       = cv2.cvtColor(img1,cv2.COLOR_BGR2HSV)
    masked_img = cv2.inRange(hsv2, np.array((0., 30., 70.)), np.array((26., 255., 255.)))
    # capture nose region for skin extraction
    hsv_roi = hsv2[int(y+h/2):int(y+2*h/3), int(x+w/5):int(x+4*w/5)]
    mask_roi = masked_img[int(y+h/2):int(y+2*h/3), int(x+w/5):int(x+4*w/5)]
    # Calculate histogram (Normalize)
    #M = cv2.calcHist([hsv_roi],[0,1],mask_roi,[180,180],[0,180,0,180])
    #M = cv2.normalize(M,0,180,cv2.NORM_MINMAX) # should be used?
    #################### Method 2 ############################
    hist_mask_hue  = cv2.calcHist([hsv_roi],[0],mask_roi,[180],[0,180])
    nhist_mask_hue = cv2.normalize(hist_mask_hue,0,180,cv2.NORM_MINMAX) # should be used?
    #################### Method 1 ############################
    hist_mask_sat  = cv2.calcHist([hsv_roi],[1],mask_roi,[255],[0,255])
    hist_mask_val  = cv2.calcHist([hsv_roi],[2],mask_roi,[255],[0,255])
    nhist_mask_hue = cv2.normalize(hist_mask_hue,0,180,cv2.NORM_MINMAX) # should be used?
    nhist_mask_sat = cv2.normalize(hist_mask_sat,0,255,cv2.NORM_MINMAX)
    nhist_mask_val = cv2.normalize(hist_mask_val,0,255,cv2.NORM_MINMAX)
    # smooth histogram and find index of first local max
    N1 = 7
    N2 = 5
    nhue  = np.convolve(nhist_mask_hue[:,0],np.ones((N1,))/N1,mode='same')
    nsat  = np.convolve(nhist_mask_sat[:,0],np.ones((N1,))/N1,mode='same')
    nval  = np.convolve(nhist_mask_val[:,0],np.ones((N1,))/N1,mode='same')
    dnhue = np.convolve(np.gradient(nhue),np.ones((N1,))/N1,mode='same')
    dnsat = np.convolve(np.gradient(nsat),np.ones((N1,))/N1,mode='same')
    dnval = np.convolve(np.gradient(nval),np.ones((N1,))/N1,mode='same')
    # Show hsv hist
    cv2.imshow('face_mask2',hsv_roi)
    hsvHueThresh = np.where(dnhue < 0)[0][0]
    hsvSatThresh = np.where(dnsat < 0)[0][0]
    hsvValThresh = np.where(dnval < 0)[0][0]
    print("Hue Value: ",hsvHueThresh)
    print("Saturation Value: ",hsvSatThresh)
    print("Intensity Value: ",hsvValThresh)
# Method 1 (Apply backprojection for hue)
hist_flat = nhist_mask_hue.reshape(-1) # Normalized vs hist?
dst  = cv2.calcBackProject([hsv,cv2.cvtColor(img, cv2.COLOR_BGR2HSV)], [0], hist_flat, [0, 180], 1)
disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
cv2.filter2D(dst,-1,disc,dst)
ret,thresh = cv2.threshold(dst,50,255,0)
# apply erosion/dilation filter to mask and denoise
kernel   = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
thresh = cv2.erode(thresh,kernel,iterations = 3)
thresh = cv2.dilate(thresh,kernel,iterations = 2)
thresh = cv2.GaussianBlur(thresh,(3,3),0)
skinMask2  = cv2.bitwise_and(img,img,mask=thresh)
# Method 2 (Create thre   
# threshold range for skin color from SV values ** DOUBLE CHECK
lower = np.array([0,hsvSatThresh,hsvValThresh],dtype = "uint8")
upper = np.array([20,255,255],dtype = "uint8")
# Create a skin mask
skinMask = cv2.inRange(hsv,lower,upper)
# apply erosion/dilation filter to mask
kernel   = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
skinMask = cv2.erode(skinMask,kernel,iterations = 2)
skinMask = cv2.dilate(skinMask,kernel,iterations = 2)
# denoise mask, then apply mask to original image
skinMask = cv2.GaussianBlur(skinMask,(3,3),0)
skin     = cv2.bitwise_and(img,img, mask = skinMask)
## Compare filter methods
_, contours2, hierarchy2 = cv2.findContours(skinMask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE) # Method 2
_, contours1, hierarchy1 = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE) # Method 1
contours = contours1
drawing = np.zeros(img.shape,np.uint8)
max_area=0
ci = 1
print('')
print("_________Number of Contours ",len(contours),"_______")
fingerAngles = []
fingerDist   = []
for i in range(len(contours)):
    cnt=contours[i]
    area = cv2.contourArea(cnt)
    if(area>max_area):
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
    cv2.circle(img,centr,5,[0,0,255],2) #Draw center of hand

    cv2.drawContours(drawing,[cnt],0,(0,255,0),2) 
    cv2.drawContours(drawing,[hull],0,(0,0,255),2) 
    # What does this do?          
    cnt  = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)
    hull = cv2.convexHull(cnt,returnPoints = False)
    # Look for hull/convex points to denote fingers
    if(1):
        # What does this do?
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
            # finger is valid if angle is less than 90 degrees
            fin1disp = (centr[0] - start[0],centr[1] - start[1])
            fin2disp = (centr[0] - end[0],centr[1] - end[1])
            fin1len = math.sqrt((fin1disp[0])**2 + (fin1disp[1])**2)
            fin2len = math.sqrt((fin2disp[0])**2 + (fin2disp[1])**2)
            if ((angle <= 90) & (angle not in fingerAngles) &
                (fin1len > minFingerLen) & (fin2len > minFingerLen) ):
                fingerAngles.append(angle)
                fingerDist.append(fin1disp)
                fingerDist.append(fin2disp)
                count_defects += 1
                cv2.circle(skin,far,5,[0,255,0],-1)
                cv2.circle(img,far,5,[255,0,0],-1)
                cv2.line(img,far,start,[255,255,255],2)
                cv2.line(img,far,end,[255,255,255],2) 
            #dist = cv2.pointPolygonTest(cnt,centr,True)
                cv2.line(img,start,end,[0,255,0],2)
                #print("   1st Finger dir: ",fin1disp[0],fin1disp[1])
                #print("   2nd Finger dir: ",fin2disp[0],fin2disp[1])
                #print("       Finger Angle: ",angle)
                #print("Number of Fingers: ",count_defects+1)
                #print("i: ",i,"j :",j)
print("finger Distances: ",list(set(fingerDist)))
print("finger Angles: ",fingerAngles)
# plot images
skinMask   = cv2.merge((skinMask,skinMask,skinMask))
thresh     = cv2.merge((thresh,thresh,thresh))
cv2.imshow('contour drawing',drawing)
cv2.imshow("Method 2",np.hstack([img,skin,skinMask])) # Using S & V
cv2.imshow("Method 1",np.vstack((img,thresh,skinMask2))) # Using H,S,V
cv2.waitKey(0)
