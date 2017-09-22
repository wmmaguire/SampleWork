package works.com.HeatBeatMonitor;

import org.opencv.android.JavaCameraView;
import android.content.Context;
import android.hardware.Camera;
import android.util.AttributeSet;
// Sets view of android camera
public class CameraView extends JavaCameraView {

    public CameraView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    public void setFlashOn() {
        Camera.Parameters params = mCamera.getParameters();
        params.setFlashMode(Camera.Parameters.FLASH_MODE_TORCH);
        mCamera.setParameters(params);
    }

    public void setFlashOff() {
        Camera.Parameters params = mCamera.getParameters();
        params.setFlashMode(Camera.Parameters.FLASH_MODE_OFF);
        mCamera.setParameters(params);
    }
}
