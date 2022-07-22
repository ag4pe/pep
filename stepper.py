import RPi.GPIO as GPIO
import time
import math


class motor(object):
    freq=0
    def __init__(self,clkpin,dirpin,maxspeed=20000):
        #pass __init__ args into object vars
        self.clk_pin=clkpin #pulse output pin, can be BOARD or BCM depending on how the importing code defines it
        self.dir_pin=dirpin #direction output pin
        self.maxspeed=maxspeed #N/A, possibly a default speed for each function
        
        #setup GPIOs
        GPIO.setup(clkpin,GPIO.OUT)
        GPIO.setup(dirpin,GPIO.OUT)
        GPIO.output(clkpin,0)
        GPIO.output(dirpin,0)
        self.pwm=GPIO.PWM(clkpin,100) #build PWM object for use in stepper.turn
        
    def turn(self,freq): #run motor at specified frequency; does not require threading
        GPIO.output(self.dir_pin,GPIO.LOW) #default direction
        if freq<0: #negative frequency swaps direction
            GPIO.output(self.dir_pin,GPIO.HIGH)
        freq=int(abs(freq)) #frequency to positive integer to keep stuff from breaking
        try:
            self.pwm.ChangeFrequency(freq) #set frequency
            self.pwm.start(50) #begin signal output
            self.freq=freq #set object variable for reference by other functions
        except ValueError: #pwm doesn't like 0 frequency, so change the duty cycle to 0 instead
            self.pwm.start(0)
            
    def ramp(self,freq,dur=1): #increase motor speed to specified frequency over specified duration
        freq=int(freq)
        increment=int((freq-self.freq)/(dur*10)) #define size of 10 increments to ramp
        for i in range(self.freq,freq+increment,increment): 
            if i<0: #change direction mid-ramp if necessary
                i=abs(i)
                GPIO.output(self.dir_pin,GPIO.HIGH)
            else: GPIO.output(self.dir_pin,GPIO.LOW)
            try:
                self.pwm.ChangeFrequency(i)
                self.pwm.start(50) 
            except ValueError:
                self.pwm.start(0)
            time.sleep(dur/10)
        self.freq=freq
        
    def step(self,steps,freq): #run motor a specified number of steps at a specified frequency
        GPIO.output(self.dir_pin,GPIO.LOW)
        if steps<0 or freq<0:
            GPIO.output(self.dir_pin,GPIO.HIGH)
        freq=int(abs(freq))
        steps=int(abs(steps))
        
        self.freq=freq
        for i in range(steps): #signal output
            GPIO.output(self.clk_pin,1)
            time.sleep(1/freq)
            GPIO.output(self.clk_pin,0)
            time.sleep(1/freq)
        self.freq=0
        
    def accel(self,steps,freq,dur=0): #run motor a specified number of steps at a specified frequency with bookend ramps of specified duration
        GPIO.output(self.dir_pin,GPIO.LOW)
        if steps<0 or freq<0:
            GPIO.output(self.dir_pin,GPIO.HIGH)
            
        freq=int(abs(freq))
        steps=int(abs(steps))
        freqs=[0] #each frequency in this list is run for one step for smooth ramp
        if dur > 0: #optional ramp
            i=0
            while freqs[-1]<freq: #calculate ramp frequencies
                i+=1
                increment=math.sqrt(i*2*(freq-self.freq)/dur)
                freqs.append(increment)
            
            dist=0
            for i in freqs: #signal output
                if i==0: continue
                GPIO.output(self.clk_pin,1)
                time.sleep(1/i)
                GPIO.output(self.clk_pin,0)
                time.sleep(1/i)
                dist+=1
                if dist>=steps/2-steps%2-2: #stop ramp just before halfway to allow time for deceleration
                    freq=i
                    break
#             print('accel steps:',steps,'=',dist, end='')
        
        self.freq=freq
        for steady in range(steps-dist*2): #run at constant frequency, accounting for ramp steps
            GPIO.output(self.clk_pin,1)
            time.sleep(1/freq)
            GPIO.output(self.clk_pin,0)
            time.sleep(1/freq)
#         print(' +',steps-dist*2, end='')
            
        if dur > 0:
            i=0
            freqs.reverse()
            freqs=[i for i in freqs if i<=freq] #trim frequencies above what was actually reached
            
            dist=0
            for i in freqs: #signal output
                if i==0: continue
                GPIO.output(self.clk_pin,1)
                time.sleep(1/i)
                GPIO.output(self.clk_pin,0)
                time.sleep(1/i)
                dist+=1
                if dist>=steps/2-steps%2-2:
                    freq=i
                    break
#             print(' +',dist)
            
        self.freq=0
    def stop(self):
        self.pwm.stop()
        self.freq=0
