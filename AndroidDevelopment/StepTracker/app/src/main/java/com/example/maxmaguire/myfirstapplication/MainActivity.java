package com.example.maxmaguire.myfirstapplication;

import android.graphics.Color;
import android.os.Environment;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;

import com.androidplot.xy.BoundaryMode;
import com.androidplot.xy.LineAndPointFormatter;
import com.androidplot.xy.SimpleXYSeries;
import com.androidplot.xy.XYPlot;

import android.hardware.SensorManager;
import android.hardware.SensorEventListener;
import android.hardware.SensorEvent;
import android.hardware.Sensor;
import android.widget.RadioButton;
import android.widget.TextView;

import java.util.Arrays;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.lang.Math;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class MainActivity extends AppCompatActivity implements SensorEventListener {
    public String TAG = "Assign1";
    // GUI interfaces
    private static double[] dvBoundaries = {0.5,1.5};
    private static double[] tvBoundaries = {-10,10,-10,10};
    Button submitButton;
    TextView directionView;
    TextView stepCounterView;
    XYPlot myplot;
    private boolean dynamicView = true;
    // Sensors handles/data structures
    private SensorManager mSensorManager;
    private Sensor AccSensor;
    private Sensor MagSensor;
    float[] mGravity;
    float[] mGeomagnetic;
    // Variables for data processing
    static int BUFFER_SIZE  = 10;
    static int SIGNAL_SIZE  = 100;
    private int SAMPLE_FREQ = 100;
    private static int stepCount = 0;
    private static Number sysStartTime;
    // Filtering coefficients
    static final float ALPHA = 0.386f;
    static final float DELTA = 0.06f;
    static final float THRESHOLD = 1.1f;
    static final float TIMEDELAY = 0.3f;
    private static int bufferIndex  = 0;
    private static Number[] signal_ts    = new Number[SIGNAL_SIZE];
    private static Number[] signal       = new Number[SIGNAL_SIZE];
    private static Number[] direction    = new Number[SIGNAL_SIZE];
    private static Number[] filt_signal  = new Number[SIGNAL_SIZE];
    private static Number[] dataBuffer   = new Number[BUFFER_SIZE];
    private static Number[] timeBuffer   = new Number[BUFFER_SIZE];
    private static Number[] dirBuffer    = new Number[BUFFER_SIZE];
    private static LinkedList<Number> stepTime  = new LinkedList<>();
    private static LinkedList<Number> stepDirX  = new LinkedList<>();
    private static LinkedList<Number> stepDirY  = new LinkedList<>();
    private static float yaw;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.d(TAG, "Created");
        // Initialize Variables
        sysStartTime = System.currentTimeMillis();
        Arrays.fill(filt_signal, 1);
        stepDirX.addFirst(0);
        stepDirY.addFirst(0);
        setContentView(R.layout.activity_main);
        // Return GUI objects
        submitButton    = (Button) findViewById(R.id.newTrialButton);
        directionView   = (TextView) findViewById(R.id.directiontxt);
        stepCounterView = (TextView) findViewById(R.id.stepCntr);
        myplot          = (XYPlot) findViewById(R.id.plot);
        // Obtain sensors
        mSensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (mSensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER) != null) {
            Log.d(TAG, "Accessing Accelerometer");
            AccSensor = mSensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
            mSensorManager.registerListener(this, AccSensor, SAMPLE_FREQ*100); // Used to change sampling rate
        }
        if (mSensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD) != null) {
            MagSensor = mSensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD);
            mSensorManager.registerListener(this, MagSensor, SAMPLE_FREQ*100); // Used to change sampling rate
            Log.d(TAG, "Accessing Magnometer");
        }
    }
    @Override
    protected void onStart() {
        super.onStart();
        Log.d(TAG, "Application started");
    }

    @Override
    protected void onResume() {
        super.onResume();
        Log.d(TAG, "Application resumed");
    }

    @Override
    protected void onPause() {
        super.onPause();
        Log.d(TAG, "Application paused");
    }

    public void ClearTrialData(View view) {
        Log.d(TAG, "Start of new Trial");
        stepCount = 0;
        // Set origin to current position
        Double newxOrigin = stepDirX.getLast().doubleValue();
        Double newyOrigin = stepDirY.getLast().doubleValue();
        // Reset step counters
        stepTime  = new LinkedList<>();
        stepDirX  = new LinkedList<>();
        stepDirY  = new LinkedList<>();
        stepDirX.addFirst(newxOrigin);
        stepDirY.addFirst(newyOrigin);
        stepCounterView.setText("STEP COUNT:        " + String.valueOf(stepCount));
    }
    @Override
    public void onSensorChanged(SensorEvent SensorEvent) {
        // For accelerometer readings
        if (SensorEvent.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
            mGravity = SensorEvent.values.clone();
        }
        // For Magnometer readings
        if (SensorEvent.sensor.getType() == Sensor.TYPE_MAGNETIC_FIELD) {
            mGeomagnetic = SensorEvent.values.clone();
            Number timestamp = System.currentTimeMillis();
        }
        if (mGravity != null && mGeomagnetic != null) {
            float R[] = new float[9];
            float I[] = new float[9];
            boolean success = SensorManager.getRotationMatrix(R, I, mGravity, mGeomagnetic);
            if (success) {
                float orientation[] = new float[3];
                SensorManager.getOrientation(R, orientation);
                yaw = ((float) Math.toDegrees(orientation[0]) + 360) % 360; // orientation contains: azimut, pitch and roll
                dirBuffer[bufferIndex] = yaw;
                directionView.setText("DIRECTION:        " + String.format("%.0f",yaw));
            }
            Number timestamp = System.currentTimeMillis();
            String newData = new String(String.valueOf(mGravity[0]) + ";" + String.valueOf(mGravity[1]) + ";" + String.valueOf(mGravity[2]));
            // print raw data to log
            Log.d(TAG, "\t" + newData);
            // Computing magnitude of Accelerometer data
            Double magnitude = Math.pow(mGravity[0], 2) + Math.pow(mGravity[1], 2) + Math.pow(mGravity[2], 2);
            dataBuffer[bufferIndex] = Math.sqrt(magnitude / Math.pow(9.8, 2));
            timeBuffer[bufferIndex] = (timestamp.doubleValue() - sysStartTime.doubleValue()) / 1000;
            bufferIndex++;
            // Update graph if new buffer if filled
            if (bufferIndex == dataBuffer.length) {
                bufferIndex = 0;
                SetPlotter(dataBuffer, timeBuffer, dirBuffer);
            }
        }

    }
    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
    }
    // ERROR DOESN'T WORK WITH PHONE-->  DON"T USE!
    private void FileWrite(String myData) {
        File root  = Environment.getExternalStorageDirectory();
        File path  = new File(root.getAbsolutePath(),"DataFolder2");
        if (!path.exists()) {
            if (!path.mkdirs()) {
                Log.d(TAG, "Path not created!!");
            }
        }
        File logFile = new File(path,"Data.txt");
        Log.d(TAG, logFile.toString());
        if (!logFile.exists()) {
            try {
                Log.d(TAG, "Creating File");
                logFile.createNewFile();
            } catch (IOException e1) {
                e1.printStackTrace();
            }
        }
        try {
            //BufferedWriter for performance, true to set append to file flag
            Log.d(TAG, "Writing to File");
            BufferedWriter buf = new BufferedWriter(new FileWriter(logFile, true));
            Long ts = System.currentTimeMillis();
            buf.append(ts.toString() + "\t");
            buf.append(myData + "\n");
            buf.close();
        } catch (IOException e1) {
            e1.printStackTrace();
        }
    }

    /* Checks if external storage is available for read and write */
    public boolean isExternalStorageWritable() {
        String state = Environment.getExternalStorageState();
        if (Environment.MEDIA_MOUNTED.equals(state)) {
            return true;
        }
        return false;
    }
    private void SetPlotter(Number[] dataBuffer, Number[] timeBuffer, Number[] dirBuffer) {
        // clear plot
        myplot.clear();
        List<List<Number>> sensorData = UpdateSeries(dataBuffer, timeBuffer, dirBuffer);
        StepDetection(sensorData);
        if (dynamicView) {
            // create series x = time in seconds, y = accelerometer magnitude
            SimpleXYSeries bufferedData = new SimpleXYSeries(sensorData.get(0), sensorData.get(1), "Acc");
            SimpleXYSeries filteredData = new SimpleXYSeries(sensorData.get(0), sensorData.get(2), "Filt Acc");
            LineAndPointFormatter lineFormat1 = new LineAndPointFormatter(Color.RED, null, null, null);
            LineAndPointFormatter lineFormat2 = new LineAndPointFormatter(Color.GREEN, null, null, null);
            // label plot
            myplot.addSeries(bufferedData, lineFormat1);
            myplot.addSeries(filteredData, lineFormat2);
            myplot.setDomainLabel("Time (ms)");
            myplot.getDomainTitle().pack();
            myplot.setRangeBoundaries(dvBoundaries[0], dvBoundaries[1], BoundaryMode.FIXED);
            myplot.setDomainBoundaries(-10, 10, BoundaryMode.AUTO);
            myplot.setRangeLabel("Accelerometer Data");
            myplot.getRangeTitle().pack();
        } else {
            SimpleXYSeries trajectorySeries = new SimpleXYSeries(stepDirX, stepDirY, "Trajectory");
            LineAndPointFormatter lineFormat3 = new LineAndPointFormatter(Color.BLUE, Color.WHITE, null, null);
            myplot.addSeries(trajectorySeries, lineFormat3);
            myplot.setDomainLabel("Step Units");
            myplot.setDomainBoundaries(tvBoundaries[0], tvBoundaries[1] , BoundaryMode.FIXED);
            myplot.getDomainTitle().pack();
            myplot.setRangeLabel("Step Units");
            myplot.setRangeBoundaries(tvBoundaries[2], tvBoundaries[3], BoundaryMode.FIXED);
            myplot.getRangeTitle().pack();
        }
        myplot.redraw();
    }
    public void onRadioButtonClicked(View view) {
        // Is the button now checked?
        boolean checked = ((RadioButton) view).isChecked();
        // Check which radio button was clicked
        switch(view.getId()) {
            case R.id.AccView:
                if (checked)
                    dynamicView = true;
                    break;
            case R.id.TrajView:
                if (checked)
                    dynamicView = false;
                    break;
        }
    }
    private List<List<Number>> UpdateSeries(Number[] dataBuffer,Number[] timeBuffer,Number[] dirBuffer) {
        // Update Data Series
        System.arraycopy(signal, dataBuffer.length, signal, 0, signal.length-dataBuffer.length);
        System.arraycopy(dataBuffer, 0, signal, signal.length-dataBuffer.length, dataBuffer.length);
        // Update Time Series
        System.arraycopy(signal_ts, timeBuffer.length, signal_ts, 0, signal_ts.length-timeBuffer.length);
        System.arraycopy(timeBuffer, 0, signal_ts, signal_ts.length-timeBuffer.length, timeBuffer.length);
        // Update Direction Series
        System.arraycopy(direction, dirBuffer.length, direction, 0, direction.length-dirBuffer.length);
        System.arraycopy(dirBuffer, 0, direction, direction.length-dirBuffer.length, dirBuffer.length);
        // Low pass filter
        int i;
        for ( i=0; i<signal.length-1; i++ ) {
            if (signal[i] == null) {
                break;
            }
            filt_signal[i+1] = DELTA*signal[i+1].floatValue() + (1.0-DELTA)*filt_signal[i].floatValue();
        }
        // Cast into nested list
        List<Number> new_sig      = Arrays.asList(signal);
        List<Number> new_ts       = Arrays.asList(signal_ts);
        List<Number> filt_sig2    = Arrays.asList(filt_signal);
        List<Number> dir_data     = Arrays.asList(direction);
        List<List<Number>> result = new ArrayList<>();
        result.add(new_ts);
        result.add(new_sig);
        //result.add(filt_sig);
        result.add(filt_sig2);
        result.add(dir_data);
        return result;
    }
    public void StepDetection(List<List<Number>> sensorData) {
        List<Number> ts  = sensorData.get(0);
        List<Number> dir = sensorData.get(3);
        List<Number> filteredSensorData = sensorData.get(2);
        for(int ind = 0; ind < ts.size(); ind++) {
            if (filteredSensorData.get(ind).floatValue() > THRESHOLD) {
                if (stepTime.isEmpty() || ts.get(ind).floatValue() > (TIMEDELAY + stepTime.getLast().floatValue())) {
                    // Increment step count
                    stepCount++;
                    //Update step linked list
                    stepTime.addLast(ts.get(ind));
                    double xStep = Math.cos(Math.toRadians(dir.get(ind).doubleValue()));
                    double yStep = Math.sin(Math.toRadians(dir.get(ind).doubleValue()));
                    stepDirX.addLast(stepDirX.getLast().doubleValue() + xStep);
                    stepDirY.addLast(stepDirY.getLast().doubleValue() + yStep);
                    // Display Direction in degrees
                    stepCounterView.setText("STEP COUNT:        " + String.valueOf(stepCount));
                    // Update xlim of Trajectory view
                    tvBoundaries[0] = tvBoundaries[0] + xStep;
                    tvBoundaries[1] = tvBoundaries[1] + xStep;
                    // Update ylim of Trajectory view
                    tvBoundaries[2] = tvBoundaries[2] + yStep;
                    tvBoundaries[3] = tvBoundaries[3] + yStep;
                }
            }
        }

    }
}
