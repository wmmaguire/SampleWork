import cv2
import numpy as np

# Load face cascade
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
# Load eye cascade
eye_cascade = cv2.CascadeClassifier('harcascade_eye.xml')
# Start video object using openCV
cap = cv2.VideoCapture(0)

while True:
    # Read image
    ret, img = cap.read()
    # Convert to gray scale
    gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Detect Face within img
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)  
    for (x,y,w,h) in faces:
        # draw blue box to capture all faces
        cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)
        # define region of image (where face is)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = img[y:y+h, x:x+w]
        # look for eyes in ROI
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex,ey,ew,eh) in eyes:
            # draw green box to capture all in face eyes
            cv2.rectangle(roi_color, (ex,ey), (ex+ew,ey+eh), (0,255,0),2)
        # Display color image
        cv2.imshow('img',img)
        # If escape key is pressed, break out of loop
        k = cv2.waitKet(30) & 0xff
        if k == 27:
            break
# Proper shut-down
cap.release()
cv2.destroyAllWindows()
