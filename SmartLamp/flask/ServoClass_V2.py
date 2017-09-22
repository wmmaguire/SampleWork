import time
from datetime import datetime
import math

class Servo():
    
    # Servo setup    
    def __init__(self,chan,pwm,mid):
        self.mid     = mid
        self.pwmObj    = pwm
        self.channel   = chan
        self.pos       = 0
        self.running   = True
        self.thread    = None
            
    def initialize(self):
        if self.thread is None:
            # start background servo thread
            now = datetime.now()
            ts  = now.strftime("%B%d_%H%M")
            
    # Move servos immediately to a specified angle position
    def moveTo(self,pos):
        spos     = 200*pos
        self.set_servo_pulse(float(spos / 1000.0))
        self.pos = pos

    # Move servos to a specificied angle position gradually (step-wise)
    def moveToSpeed(self,newpos,steps):
        curpos = self.pos
        pos    =  newpos - curpos
        if pos < 0:
            steps = -steps
        dpos   = pos / float(steps)
        while newpos != curpos:
            if math.fabs(newpos-curpos) < math.fabs(steps):
                steps = newpos-curpos
            curpos   = curpos + steps
            spos     = 600 + 11.11*curpos
            self.set_servo_pulse(float(spos / 1000.0))
            self.pos = curpos
            
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
        pulse_length //= 4096     # 12 bits of resolution
        pulse *= 1000
        pulse //= pulse_length
        self.servoControl(0,int(pulse))

