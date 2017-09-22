import time
import paho.mqtt.client as mqtt
from datetime import datetime
import threading
# Subscribing as paho client
USERNAME = 'marisamaxmaayan' 
PASSWORD = '6226622662'
BROKER   = 'broker.shiftr.io'
class Servo():
    
    # Servo setup    
    def __init__(self,chan,pwm,mid):
        self.mid     = mid
        client = mqtt.Client()
        client.mid    = mid
        client.servo  = self 
        client.on_connect = onConnect
        client.on_message = whenMessageRecieved
        client.username_pw_set(USERNAME, PASSWORD)
        client.connect(BROKER)
        client.loop_start()
        self.pwmObj    = pwm
        self.channel   = chan
        self.pos       = 0
        self.running   = True
        self.thread    = None
        #if not running:    
        #    self.thread = threading.Thread(target=self._thread)
        #    self.thread.start()
            
    def initialize(self):
        if self.thread is None:
            # start background servo thread
            now = datetime.now()
            ts  = now.strftime("%B%d_%H%M")
            #Servo.thread = threading.Thread(target=self._thread)
            #Servo.thread.start()
            
    # Move servos immediately to a specified x, y position
    def moveTo(self,pos):
        spos     = 200*pos
        self.set_servo_pulse(float(spos / 1000.0))
        self.pos = spos

    def moveToSpeed(pos,steps):
        dpos = pos / float(steps)
        for s in range(0,steps,1):
            pos += dpos
            self.moveTo(pos)
            
    def get_servoinfo(self):
        self.last_access = time.time()
        self.initialize()
        return self.channel,self.pos
    
    def servoControl(self,on,off):
        if self.pwmObj is not None:
            self.pwmObj.set_pwm(self.channel,on,off)
            self.pos = off
        else:
            print('Servo not available')
        
    # Helper function to make setting a servo pulse width simpler.
    def set_servo_pulse(self,pulse):
        pulse_length = 1000000    # 1,000,000 us per second
        pulse_length //= 60       # 60 Hz
        #print('{0}us per period'.format(pulse_length))
        pulse_length //= 4096     # 12 bits of resolution
        #print('{0}us per bit'.format(pulse_length))
        pulse *= 1000
        pulse //= pulse_length
        #print(int(pulse))
        self.servoControl(0,int(pulse))

def onConnect(client, userdata, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(client.mid)
    
def whenMessageRecieved(client, userdata, msg):
    payload = str(msg.payload)
    print(client.servo.channel,"Payload Message: ",client.mid,payload)

