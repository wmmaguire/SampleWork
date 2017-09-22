Step Detection Description:

I developed an android app to detect the steps that the user has taken.  Upon, connecting to the phones 3-axis accelerometer sensors, the step detection protocol works via a three-step process:

    Compute the magnitude of the 3-axis accelerometer data by taking its Euclidean norm and dividing by the gravitational constant.
    Smoothing the magnitude data with a low-pass filter the data by running it through an exponentially weighted moving average.

            y_i= ∝x_i+(1-∝) y_(i-1)

                    RC=  1/(2πf_c )

                    ∝ =  ∆t/(RC+ ∆t)

    The sampling rate (1/( ∆t)) of the system was 100hz and a cutoff frequency of 1Hz was selected, which yielded a smoothing factor (∝) of 0.06.
    Applying the smoothed magnitude data to a Step Detection threshold (10% above its baseline signal) and a blanking window (0.3s).
    Smoothed magnitude readings that crossed the step detection threshold were classified as steps.  Subsequent magnitude readings within the blanking window following a step were disregarded as noise or a signal associated with the recorded step.

Although the step detection algorithm can function in any phone orientation, an additional feature has been added to the app that makes it more appealing to use by holding it parallel to the ground.  The application also subscribes to the magnetic field sensor to extract the phone’s yaw.  The phones orientation is stored into a temporary list during each step, which is then used to record and display the users trajectory.  The trajectory of the user can be visualized on the main plot by switching the selected button in the radio button group.

Lastly, the user can clear the step history and start a new trial by clicking the button “Start new trial”.
