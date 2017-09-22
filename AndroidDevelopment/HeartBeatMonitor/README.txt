Heart Beat Monitor Description:

In this assignment I developed an android app to detect the users heart rate (BPM) by processing Android’s built in camera pixel values using openCV.  I added two additional features (finger detection and shake detection) to account for conditions that may lead to inaccurate readings.
    Finger Detection: This tracks the smoothed red pixel values that are recorded and ensures that BPM calculations are only computed if they cross a threshold value (chosen as 190).
    The timestamp at which Pixel values fail to exceed this threshold are recorded (to prohibit the BPM from being calculated before this time point) and a message is displayed on the screen to inform the user.
    Shake Detection: This tracks the magnitude of the 3-axis accelerometer values that are recorded to ensure that BPM calculation are not computed under unsteady conditions (acceleration magnitude values that cross threshold value chosen as 1).
    The timestamp at which the phone is determined to be unsteady is recorded (to prohibit the BPM from being calculated before this time point) and a message is displayed on the screen to inform the user.

Assuming that these conditions are met, the procedure used to compute the user’s BPM goes as follows:

    Compute the mean of the red pixel value that is recorded for each frame.
    Smoothing the mean red pixel values of each frame with a low-pass filter (linear rolling average over a 12 sample window).
    Find the time stamp associated with the local minima of the smoothed data (denoting the end of one heart beat/ the start of a new heart beat → Systolic peak)
    The local minima can be found by calculating the derivative of the smoothed data and finding the index of 0 threshold crossing where the preceding value is positive.
    Once the time stamps of consecutive heart beats are recorded, the beats per minute is computed using the following formula:
BPM=  (60 (Seconds⁄Minute))/(TS_t-TS_(t-1)  (Seconds⁄Beat))

An additional measure is used to evaluate the BPM calculation by verifying that it falls within an appropriate range [40-200].  If the BPM value is below the lower limit of the appropriate range (40), the heart beat time stamp is recorded however the display is not updated.  If the BPM value is above the higher limit of the appropriate range (possibly due to picking up the diastolic peak) the heart beat time stamp discarded.
