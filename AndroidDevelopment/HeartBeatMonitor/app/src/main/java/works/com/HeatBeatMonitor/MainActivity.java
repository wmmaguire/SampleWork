package works.com.HeatBeatMonitor;

import com.androidplot.xy.LineAndPointFormatter;
import com.androidplot.xy.SimpleXYSeries;
import com.androidplot.xy.XYPlot;
import android.graphics.Color;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorManager;
import android.hardware.SensorEventListener;
import android.os.Bundle;
import android.os.Environment;
import android.support.v7.app.ActionBarActivity;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.MotionEvent;
import android.view.SubMenu;
import android.view.SurfaceView;
import android.view.View;
import android.view.WindowManager;
import android.view.View.OnTouchListener;
import android.widget.TextView;

import org.opencv.android.BaseLoaderCallback;
import org.opencv.android.CameraBridgeViewBase;
import org.opencv.android.LoaderCallbackInterface;
import org.opencv.android.OpenCVLoader;
import org.opencv.core.Core;
import org.opencv.core.Mat;
import org.opencv.highgui.Highgui;

import java.util.*;
import java.text.SimpleDateFormat;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

public class MainActivity extends ActionBarActivity implements OnTouchListener, SensorEventListener,
        CameraBridgeViewBase.CvCameraViewListener2 {
    private final String TAG = "APP";
    private static File path;
    private CameraView mOpenCvCameraView;
    private SubMenu mColorEffectsMenu;
    TextView heartmonitorView;
    TextView rgbVal;
    float lastTouchY=0;
    int cannyThreshold=50;
    // Sensors handles/data structures
    private SensorManager mSensorManager;
    private Sensor shakeSensor;
    XYPlot myplot;
    // Hardcoded variables containing thresholds/buffer size/ sample freq
    private final int SAMPLE_FREQ         = 60;
    private static final int SIGNAL_SIZE  = 80;
    private static final double DELTA     = .045; // for ACC filter
    private static final int PROCESS_DUR  = 10;
    private static final int WINDOW        = 12; // for signal filter
    private static final double ACC_THRESHOLD = 1;
    private static final int PXL_THRESHOLD = 190;
    private static final double[] HEARTBEATRANGE = {40,200};
    // Variables for Counters/System time/previous recordings
    private static double prev_accMag = 0;
    private static double pxlFlag_ts = 0;
    private static double accFlag_ts = 0;
    private static double accMag = 0;
    private static double beatsPerMinute;
    private static int cntr = 0;
    private static double sysStartTime_PXL;
    // Lists to hold frame time/ pixel values/ heartbeat data
    private static LinkedList<Number> frameTime_PXL = new LinkedList<>();
    private static LinkedList<Number> redList   = new LinkedList<>();
    private static LinkedList<Number> fredList  = new LinkedList<>();
    private static LinkedList<Number> filteredPxlVal  = new LinkedList<>();
    private static LinkedList<Number> heartBeatTime = new LinkedList<>();
    private static LinkedList<Number> heartBeatVal = new LinkedList<>();
    private static int heartBeatInd = 0;
    private String fileTimeStamp;

    private BaseLoaderCallback mLoaderCallback = new BaseLoaderCallback(this) {
        @Override
        public void onManagerConnected(int status) {
            switch (status) {
                case LoaderCallbackInterface.SUCCESS:
                {
                    Log.i(TAG, "OpenCV loaded successfully");
                    mOpenCvCameraView.enableView();

                } break;
                default:
                {
                    super.onManagerConnected(status);
                } break;
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // Start timer
        super.onCreate(savedInstanceState);
        Log.d(TAG, "called onCreate");
        //To create a new directory for saving img data (if doesn't exist)
        CreateNewFolder("HeartMonitor/trial");
        // keeps the screen on
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        setContentView(R.layout.activity_vision);
        heartmonitorView = (TextView) findViewById(R.id.heartmonitor);
        // set camera on
        mOpenCvCameraView = (CameraView) findViewById(R.id.HelloOpenCvView);
        mOpenCvCameraView.setVisibility(SurfaceView.VISIBLE);
        mOpenCvCameraView.setCvCameraViewListener(this);
        // Obtain Sensor
        mSensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (mSensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION) != null) {
            Log.d(TAG, "Accessing Significant Motion sensor");
            shakeSensor = mSensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION);
            mSensorManager.registerListener(this, shakeSensor, SAMPLE_FREQ*100); // Used to change sampling rate
        }
        fileTimeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
        // obtain GUI handles
        rgbVal = (TextView) findViewById(R.id.rgbVal);
        myplot = (XYPlot) findViewById(R.id.plot);
    }
    // Turn camera back on when the app is resumed
    @Override
    public void onResume() {
        super.onResume();
        OpenCVLoader.initAsync(OpenCVLoader.OPENCV_VERSION_2_4_6, this, mLoaderCallback);
    }
    // turn camera inactive when the app is paused
    @Override
    public void onPause() {
        super.onPause();
        if (mOpenCvCameraView != null)
            mOpenCvCameraView.disableView();
    }
    // release camera on destroy
    public void onDestroy() {
        super.onDestroy();
        if (mOpenCvCameraView != null)
            mOpenCvCameraView.disableView();
    }
    // enable flash option in menu
    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        mColorEffectsMenu = menu.addSubMenu("Flash On");
        mColorEffectsMenu = menu.addSubMenu("Flash Off");
        return true;
    }
    // Turning flash on/off via menu
    public boolean onOptionsItemSelected(MenuItem item) {
        Log.i(TAG, "called onOptionsItemSelected; selected item: " + item);
        if (item.toString().equals("Flash On")) {
            mOpenCvCameraView.setFlashOn();
        } else if (item.toString().equals("Flash Off")) {
            mOpenCvCameraView.setFlashOff();
        }
        return true;
    }

    @Override
    public void onCameraViewStarted(int width, int height) {
    }

    @Override
    public void onCameraViewStopped() {
    }
    // Runs everytime you get a new frame
    @Override
    public Mat onCameraFrame(CameraBridgeViewBase.CvCameraViewFrame inputFrame) {
        Mat currentFrame = inputFrame.rgba();
        List<Mat> rawrgb = new ArrayList<>(3);
        Core.split(currentFrame,rawrgb);//split source
        if(frameTime_PXL.isEmpty()) {
            sysStartTime_PXL = Core.getTickCount();
        }
        double redValues = Core.mean(rawrgb.get(0)).val[0]; //r
        double tempval   = (Core.getTickCount()-sysStartTime_PXL)/Core.getTickFrequency();
        frameTime_PXL.addLast(tempval);
        redList.addLast(redValues);
        // Method 1: Low Pass Filter
        if (fredList.isEmpty()) {
            fredList.addLast(redValues);
        } else {
            double filteredVal = DELTA*redList.getLast().doubleValue() + (1.0-DELTA)*redList.get(redList.size()-2).doubleValue();
            fredList.addLast(filteredVal);
        }
        // Keep fixed signal frame
        if(frameTime_PXL.size() > SIGNAL_SIZE) {
            redList.removeFirst();
            frameTime_PXL.removeFirst();
            fredList.removeFirst();
            // Keep heartbeat list in same frame as pixel values
            if (!heartBeatTime.isEmpty() && heartBeatTime.get(0).doubleValue() < frameTime_PXL.get(0).floatValue()) {
                heartBeatTime.removeFirst();
                heartBeatVal.removeFirst();
            }
        }
        // only using red values
        String newData = String.format("%f ; %f ; %f ; %f ",frameTime_PXL.getLast(),redList.getLast(),accFlag_ts,accMag);
        if (isExternalStorageWritable()) {
            FileWrite(newData);
        }
        cntr++;
        if (cntr == PROCESS_DUR) {
            ProcessData();
            SetPlotter();
            HeartMonitor();
            cntr = 0;
        }
        return currentFrame;
    }

    //Detects every time you touch the screen
    @Override
    public boolean onTouchEvent(MotionEvent e) {
        // MotionEvent reports input details from the touch screen
        // and other input controls. In this case, you are only
        // interested in events where the touch position changed.
        float y = e.getY();
        // adjust threshold based on touch scrolling
        if (e.getAction() == MotionEvent.ACTION_MOVE) {
            if (lastTouchY > y)
                cannyThreshold += 5;
            else
                cannyThreshold -= 5;
            lastTouchY = y;
        }

        if (e.getAction() == MotionEvent.ACTION_UP)
            lastTouchY = 0;
        return true;
    }
    private void CreateNewFolder(String basefolder) {
        File root  = Environment.getExternalStorageDirectory();
        path = new File(root.getAbsolutePath(), basefolder);
        if (!path.exists()) {
            if (!path.mkdirs()) {
                Log.d(TAG, "Path not created!!");
                return;
            }
            Log.d(TAG, "Path not created!!");
        }
    }
    // To write images to external png file
    private void imgFileWrite(Mat myData) {
        // Get the absolute file path and create a new folder (StepDetection)
        String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
        String logFile   = new String(path.toString()+"/test_image_" + timeStamp + ".png");
        Highgui.imwrite(logFile,myData);
    }
    // To write data to external txt file
    private void FileWrite(String myData) {
        File logFile = new File(path,"Image_Data" + fileTimeStamp + ".txt");
        if (!logFile.exists()) {
            try {
                Log.d(TAG, "Creating File: " + logFile.toString());
                logFile.createNewFile();
            } catch (IOException e1) {
                e1.printStackTrace();
            }
        }
        try {
            //BufferedWriter for performance, true to set append to file flag
            BufferedWriter buf = new BufferedWriter(new FileWriter(logFile, true));
            Long ts = System.currentTimeMillis();
            buf.append(ts.toString() + ";");
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
    // Method 2: Low pass filter (rolling avg window)
    private void ProcessData() {
        LinkedList<Number> pxlVals = new LinkedList<>();
        double mean;
        int  frameInd = 0;
        for (int mvind = 0; mvind < redList.size(); mvind++) {
            mean = 0;
            for (int pxlind = mvind; pxlind < mvind + WINDOW; pxlind++) {
                // padding
                if (pxlind < WINDOW) {
                    mean += redList.getFirst().doubleValue();
                    continue;
                } else if (pxlind > redList.size() + WINDOW) {
                    mean += redList.getLast().doubleValue();
                    continue;
                } else {
                    frameInd = pxlind - WINDOW;
                    mean += redList.get(frameInd).doubleValue();
                }
            }
            mean /= WINDOW;
            // Finger Detection (inform user)
            if (mean < PXL_THRESHOLD) {
                pxlFlag_ts = frameTime_PXL.get(mvind).doubleValue();
                runOnUiThread(new Runnable() {
                    public void run() {
                        heartmonitorView.setTextColor(Color.RED);
                        heartmonitorView.setText("FINGER CANNOT BE DETECTED");
                    }
                });
            }
            pxlVals.addLast(mean);
        }
        filteredPxlVal = pxlVals;
    }
    private void SetPlotter() {
        // clear plot
        myplot.clear();
        SimpleXYSeries redVals  = new SimpleXYSeries(frameTime_PXL, redList,"raw");
        SimpleXYSeries fpxlseries = new SimpleXYSeries(frameTime_PXL,filteredPxlVal,"filtered data");
        LineAndPointFormatter lineFormat1 = new LineAndPointFormatter(Color.RED, null, null, null);
        LineAndPointFormatter lineFormat2 = new LineAndPointFormatter(Color.BLUE, null, null, null);
        // label plot
        myplot.addSeries(redVals, lineFormat1);
        myplot.addSeries(fpxlseries, lineFormat2);
        if(!heartBeatTime.isEmpty()) {
            SimpleXYSeries beatIndicator = new SimpleXYSeries(heartBeatTime, heartBeatVal, "Heart Beat");
            LineAndPointFormatter lineFormat3 = new LineAndPointFormatter(null, Color.WHITE, null, null);
            myplot.addSeries(beatIndicator, lineFormat3);
        }
        myplot.setDomainLabel("Time (ms)");
        myplot.setRangeLabel("Avg Red Pixel Value per Frame");
        myplot.redraw();
    }
    public void HeartMonitor() {
        // Retrieve data
        // Initialize instance variables
        double prev_val = filteredPxlVal.getFirst().doubleValue();
        double cur_dt   = 0;
        double prev_dt;
        // Evaluate signal for heart beat
        for (int ind = 1; ind < filteredPxlVal.size()-1; ind++) {
            prev_dt = cur_dt;
            cur_dt = prev_val - filteredPxlVal.get(ind).doubleValue();
            prev_val = filteredPxlVal.get(ind).doubleValue();
            // evaluate derivative of filteredPXL value to find local minima
            if (ind > 0 && cur_dt < 0 && prev_dt > 0) {
                heartBeatInd = ind;
                // Make sure that the detected heart beat is not logged if the finger isn't detected
                if (pxlFlag_ts >= frameTime_PXL.get(heartBeatInd).doubleValue()) {
                    Log.d(TAG, String.format("Exceeded pixel value threshold: %f", pxlFlag_ts));
                    continue;
                }
                // Make sure that the detected heart beat is not logged if the phone is unsteady
                if (accFlag_ts >= frameTime_PXL.get(heartBeatInd).doubleValue()) {
                    Log.d(TAG, String.format("Exceeded Acc value threshold: %f", accFlag_ts));
                    continue;
                }
                // if conditions are met, log heart beat value/time stamp and compute frequency between most recent
                // detected heart beats.  Use this frequency to compute BPM
                if (heartBeatTime.isEmpty() ||
                        heartBeatTime.getLast().doubleValue() < frameTime_PXL.get(heartBeatInd).doubleValue()) {
                    heartBeatTime.addLast(frameTime_PXL.get(heartBeatInd));
                    heartBeatVal.addLast(redList.get(heartBeatInd));
                    if (heartBeatTime.size() > 1) {
                        double prev_beatsPerMinute = beatsPerMinute;
                        beatsPerMinute  = 60.0/(heartBeatTime.getLast().doubleValue() - heartBeatTime.get(heartBeatTime.size()-2).doubleValue());
                        // If the computed BPM exceeded higher limits of expected range (40-200), discard it
                        if (beatsPerMinute > HEARTBEATRANGE[1]) {
                            //Log.d(TAG, String.format("Logging Band Pass Catcher 1: %f", beatsPerMinute));
                            heartBeatVal.removeLast();
                            heartBeatTime.removeLast();
                            beatsPerMinute = prev_beatsPerMinute;
                           continue;
                        }
                        if (beatsPerMinute > HEARTBEATRANGE[0]) {
                            //Log.d(TAG, String.format("Logging Catcher 2: %f", beatsPerMinute));
                            if (heartBeatTime.size() > 1) {
                                runOnUiThread(new Runnable() {
                                    public void run() {
                                        heartmonitorView.setTextColor(Color.BLUE);
                                        heartmonitorView.setText(String.format("BPM: %f", beatsPerMinute));
                                    }
                                });
                            }
                        }
                    }
                }
            }
        }
    }
    @Override
    public boolean onTouch(View view, MotionEvent motionEvent) {
        return false;
    }

    @Override
    public void onSensorChanged(SensorEvent sensorEvent) {
        // Read Accelerometer and notify user if significant shake is detected
        if (sensorEvent.sensor.getType() == Sensor.TYPE_LINEAR_ACCELERATION) {
            double x = sensorEvent.values[0];
            double y = sensorEvent.values[1];
            double z = sensorEvent.values[2];
            double cur_accMag  = Math.sqrt(x * x + y * y + z * z);
            accMag = DELTA*cur_accMag + (1.0-DELTA)*prev_accMag;
            prev_accMag = cur_accMag;
            if (accMag > ACC_THRESHOLD) {
                if (frameTime_PXL.isEmpty()) {
                    accFlag_ts = sysStartTime_PXL;
                } else {
                    accFlag_ts = frameTime_PXL.getLast().doubleValue();
                }
                runOnUiThread(new Runnable() {
                    public void run() {
                        heartmonitorView.setText("PLEASE STEADY PHONE!");
                        heartmonitorView.setTextColor(Color.RED);
                    }
                });
            }
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int i) {

    }
}