Author: Max Maguire, 2017

Description: Ana-Lamp is a user sensor system that operates as an assistive, interactive desktop lamp.

Folder Contents:
Flask:  This contains all the software components to run/control Ana-Lamp
   -  App_V2.py:        Main application
   -  campera_pi_V2.py: Camera class
   -  ServoClass_V2.py: Servo class
   -  requirements.txt: list of dependencies
   -  templates:        web app html/css files
DataFolder: directory where data is logged
Classifiers: Contains xml files for Haar Cascade object detection
   -  haarcascade_eye.xml - eye feature set
   - haarcascade_frontalface_default.xml - frontal face feature set
Adafruit_Python_PCA9685: library to interface servo hat with raspberry pi


Helpful Resources:

[Configuring OpenCV/Python for RasPI](http://www.pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python/):  This is a step-by-step tutorial on how to configure your raspberry pi to use OpenCV.

[FLASK](https://blog.miguelgrinberg.com/post/video-streaming-with-flask):   This is a helpful blog to explain how flask works (the python library that is used to post motion jpegs to the web)

[Haar Cascades Classifiers (Face Detection)](https://pythonprogramming.net/haar-cascade-face-eye-detection-python-opencv-tutorial/):  This is a python/openCV tutorial on how to implement Haar Cascades for face detection.  Can also be used for other objects (eyes, ears, keys etc..).  There is also information on how to create your own Haar Cascade xml file.
