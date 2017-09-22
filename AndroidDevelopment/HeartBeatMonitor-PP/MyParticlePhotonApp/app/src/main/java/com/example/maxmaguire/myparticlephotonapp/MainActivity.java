package com.example.maxmaguire.myparticlephotonapp;

import android.graphics.Color;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.os.AsyncTask;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.URL;
import javax.net.ssl.HttpsURLConnection;
import android.widget.EditText;

public class MainActivity extends AppCompatActivity implements View.OnFocusChangeListener {
    // Set actvity name as debug tag

    public static final String TAG = HttpsClient.class.getSimpleName();
    public static final String DEVICE_BASEURL = "https://api.particle.io/v1/devices/";
    private String deviceID =    "300045001547353236343033";
    private String deviceToken = "08c191ebec5bb1071ed074e28094d1832da89574";
    private String[] inputVars = {"bpm"};
    private String[] outputFuncs = {"RGBled"};

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        final EditText redPixelValueEditText   =  (EditText) findViewById(R.id.redValue);
        final EditText greenPixelValueEditText =  (EditText) findViewById(R.id.greenValue);
        final EditText bluePixelValueEditText  =  (EditText) findViewById(R.id.blueValue);

        // Declare and assign our buttons and text
        final Button postButton = (Button) findViewById(R.id.postButton);

        /*
        final Button getButton  = (Button) findViewById(R.id.getButton);
        View.OnClickListener getListener = new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Toast.makeText(MainActivity.this, "GET pub", Toast.LENGTH_SHORT).show();
                new HttpsClient().execute(DEVICE_BASEURL + deviceID + "/" + inputVars[0] +
                                                            "?access_token=" + deviceToken);
            }
        };
        getButton.setOnClickListener(getListener);
        */
        Thread t = new Thread(new Runnable() {
            public void run() {
                try {
                    while (true) {
                        new HttpsClient().execute(DEVICE_BASEURL + deviceID + "/" + inputVars[0] +
                                "?access_token=" + deviceToken);
                        Thread.sleep(500);
                    }
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        });

        t.start();

        View.OnClickListener postListener = new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String params = redPixelValueEditText.getText().toString() + ',' +
                                greenPixelValueEditText.getText().toString() + ',' +
                                bluePixelValueEditText.getText().toString();
                Toast.makeText(MainActivity.this, "Posted new RGB values" + params, Toast.LENGTH_SHORT).show();
                new PostClient().execute(params);
            }
        };
        postButton.setOnClickListener(postListener);

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
    @Override
    protected void onDestroy() {
        super.onDestroy();
        Log.d(TAG, "Application Ended");
    }
    /*
     * ASYNC HTTP GET
     * Must do in Background!
     */
    class HttpsClient extends AsyncTask<String, Void, String> {
        private Exception exception;
        public String doInBackground(String... urls) {

            try {
                // *******************    Open Connection    *****************************");
                URL url = new URL(urls[0]);
                //Log.d(TAG, "Received URL:  " + url);
                HttpsURLConnection con = (HttpsURLConnection) url.openConnection();
                //Log.d(TAG, "Con Status: " + con);
                InputStream in = con.getInputStream();
                //Log.d(TAG, "GetInputStream:  " + in);
                // "*******************    String Builder     *****************************");
                String line = null;

                BufferedReader br = new BufferedReader(new InputStreamReader(in));

                Data data = new Data();
                //Log.d(TAG,br.toString());
                while ((line = br.readLine()) != null) {
                    JSONObject jObject = new JSONObject(line);
                    //Log.d(TAG,jObject.getString("name"));
                    if (jObject.getString("name").equals(inputVars[0])) {
                        //convert to JSON (stripping the beginning "data: "
                        data.setData(jObject.getString("name"), jObject.getInt("result"));
                    }
                    //check if we have all needed data
                    if (data.isReady()) {
                        //exit endless connection
                        // "*******************    Data received    *****************************");
                        break;
                    }
                }

                // Creation of finalized containers for UI usage
                final String respVar = data.getData();
                //Log.d(TAG,data.getData());
                final int respVal = data.getValue();
                // To access the findViewById we need this to runOnUiThread
                runOnUiThread(new Runnable(){
                    public void run() {
                        // *******************    Run UI Thread     *****************************");
                        // Assign and declare
                        final TextView updateGetExample  = (TextView) findViewById(R.id.getTextView);
                        // Update the TextViews
                        // *******************    Update TextView       *************************");
                        updateGetExample.setText("BPM: " + Integer.toString(respVal));
                        if (respVal < 85) {
                            updateGetExample.setTextColor(Color.CYAN);
                        } if (respVal > 85 && respVal < 120) {
                            updateGetExample.setTextColor(Color.GREEN);
                        } if (respVal > 120) {
                            updateGetExample.setTextColor(Color.RED);
                        }

                    }

                });
                // Closing the stream
                // *******************  Stream closed, exiting     ******************************");
                br.close();
            } catch (Exception e) {
                this.exception = e;
                Log.d(TAG,e.getMessage());
                return null;
            }
            return null; }

    }

    /*
     * ASYNC HTTP POST
     * Must do it in background!
     */
    class PostClient extends AsyncTask<String, Void, String> {
        public String doInBackground(String... IO) {

            // Predefine variables
            String io = new String(IO[0]);
            URL url;

            try {
                // Stuff variables
                url = new URL(DEVICE_BASEURL + deviceID +"/" + outputFuncs[0]);
                String param = "access_token=" + deviceToken + "&params=" +io;
                Log.d(TAG, "url: " + url);
                Log.d(TAG, "param: " + param);

                // Open a connection using HttpURLConnection
                HttpsURLConnection con = (HttpsURLConnection) url.openConnection();

                con.setReadTimeout(7000);
                con.setConnectTimeout(7000);
                con.setDoOutput(true);
                con.setDoInput(true);
                con.setInstanceFollowRedirects(false);
                con.setRequestMethod("POST");
                con.setFixedLengthStreamingMode(param.getBytes().length);
                con.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");

                // Send
                PrintWriter out = new PrintWriter(con.getOutputStream());
                out.print(param);
                out.close();

                con.connect();

                BufferedReader in = null;
                if (con.getResponseCode() != 200) {
                    in = new BufferedReader(new InputStreamReader(con.getErrorStream()));
                    Log.d(TAG, "!=200: " + in);
                } else {
                    in = new BufferedReader(new InputStreamReader(con.getInputStream()));
                    Log.d(TAG, "POST request send successful: " + in);
                };


            } catch (Exception e) {
                Log.d(TAG, e.getMessage());
                e.printStackTrace();
                return null;
            }
            // Set null and we're good to go
            return null;
        }
    }

    @Override
    public void onFocusChange(View v, boolean hasFocus) {
        int userInput = 0;
        switch(v.getId()){
            case R.id.redValue:
                EditText redPixelValueEditText   =  (EditText) findViewById(R.id.redValue);
                userInput = Integer.parseInt(redPixelValueEditText.getText().toString());
                Log.d(TAG,String.valueOf(userInput));
                if (userInput < 0 || userInput > 255) {
                    redPixelValueEditText.setText('0');
                }
                break;
            case R.id.blueValue:
                EditText bluePixelValueEditText   =  (EditText) findViewById(R.id.blueValue);
                userInput = Integer.parseInt(bluePixelValueEditText.getText().toString());
                if (userInput < 0 || userInput > 255) {
                    bluePixelValueEditText.setText('0');
                }
                break;
            case R.id.greenValue:
                EditText greenPixelValueEditText   =  (EditText) findViewById(R.id.greenValue);
                userInput = Integer.parseInt(greenPixelValueEditText.getText().toString());
                if (userInput < 0 || userInput > 255) {
                    greenPixelValueEditText.setText('0');
                }
                break;
        }
    }
}
