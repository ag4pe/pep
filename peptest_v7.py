import RPi.GPIO as GPIO
import time
import stepper
import threading
import math
import serial
import PIL.Image,PIL.ImageDraw,PIL.ImageTk
from tkinter import *


GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
lim_pin=18 #gantry limit switch
hall_pin=8 #blade shaft encoder (1 blip per rev)
ena_pin=12 #stepper motor enable, 1=disable to keep temps down
tube_pin=16
GPIO.setup(lim_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP) 
GPIO.setup(hall_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ena_pin,GPIO.OUT)
GPIO.setup(tube_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP)

#stepper.motor(PUL,DIR)
tturn=stepper.motor(7,11)
ttran=stepper.motor(13,15)
tlift=stepper.motor(38,40)

pep_ratio = -3200*14/19  #steps/bladerev
pep_max = 10000 #blade top speed Hz
ttran_ratio = 1600    #steps/transrev
tturn_ratio = 1600    #steps/tablerev
tturn_max = .8*tturn_ratio #turntable top speed Hz
tlift_ratio = 400/(8/25.4)  #steps/in (0.19196in screw lead)
tlift_max = 1.5 #inch extension

n = 0
shutdown = False

try:
    ser = serial.Serial("/dev/ttyACM0",9600)
    GPIO.setup(37,GPIO.OUT)
    class pep:
        freq = 0
        def stop():
            ser.write(b'0\r\n')
            pep.freq=0
        def turn(freq):
            GPIO.output(37,0)
            if freq == 0:
                pep.stop()
                return
            elif freq < 0:
                GPIO.output(37,1)
                freq=-freq
            freq = int(1000000/(2*freq))
            ser.write(b'%d\r\n' % freq)
            pep.freq=freq
    print('ser to Arduino')
except:
    pep=stepper.motor(35,37)
    print('stepper.motor')

#***********************MechanicalFunctions******************************#   
def in2step(inch,pulleydiam=1.337/20*15):
    return int(inch*ttran_ratio/(3.14159*pulleydiam)) #Convert distance to steps on motor
def home():
    GPIO.output(ena_pin,GPIO.LOW)
    ttran.turn(3*ttran_ratio)
    while GPIO.input(lim_pin): time.sleep(.03)
    ttran.stop()
def hallblip(x):
    global n
    n+=1
    if False:
        global derf
        if 'derf' in globals():
            print(1/(time.time()-derf))
        derf=time.time()
def centercal(center=-8.2):
    ttran.step(in2step(center),12000)
    time.sleep(2)
    home()

def enable():
    GPIO.output(ena_pin,GPIO.LOW)
    
def stop():
    global shutdown
    shutdown=1
    GPIO.output(ena_pin,GPIO.HIGH)
    pep.stop()
    tturn.stop()
    ttran.stop()
    GPIO.remove_event_detect(hall_pin)
    try: pizzadisplay.pack_forget()
    except: pass
#     try:
#         for window in root.winfo_children():
#             window.destroy()
#         homescreen()
#     except Exception as e: print(' and returned to home screen but',e)
def run_pep(size=7, qty=15, lift=0, pps=3 , margin=0, center=-7, rpep=17):
    
    if False: #GPIO.input(tube_pin):
        #print('tube error')
        error_popup()
        return
    #create pizza mockup image then run motors pep_program in thread
    
    #calculate pep pitch circle radius in mm
    r=(size/2-margin)*25.4-rpep
    
    #image dimensions/setup
    xdim=325
    ydim=90
    im=PIL.Image.new('RGB',(xdim*2,ydim*2),(215,215,215))
    draw=PIL.ImageDraw.Draw(im)
    draw.ellipse((xdim-size*12.7,ydim-size*12.7,xdim+size*12.7,ydim+size*12.7),fill=(255,219,112),outline='brown')
    
    #calculate spacing between each row in mm (delta_radius)
    dr=math.sqrt(math.pi*r*r/(.0003172*qty*qty+.8365*qty-3.9))
    
    #calculate the number of peps in each row, with some fudging to get it to look right
    npep=[]
    for m in range(math.ceil(r/dr)):
        npep.append(round((r-m*dr)*2*math.pi/dr))
    try: npep.remove(0)
    except ValueError: pass
    if npep[-1]>4:npep.append(1)
    
    #calculate row_ct and pep_ct for pep_program coordination
    row_ct=[] #how far to move to each row in inches
    pep_ct=[] #number of blade revolutions per table revolution
    nr=math.ceil(r/dr) #Number of Rows
    for m in range(nr): #for each row calculate...
        pep_ct.insert(0, round((r-m*dr) * 2*math.pi / dr)) #number of peps in row
        row_ct.insert(0, round(center + r/25.4 - m*dr/25.4, 2)) #distance from home position
    if pep_ct[0]==0:pep_ct[0]=1 #force center row to round up to 1
    if pep_ct[0]>4: #add center pep if there is space
        nr+=1
        pep_ct.insert(0,1)
        row_ct.insert(0,center)
    for m in range(nr-1,0,-1): #convert row locations from absolute to relative
        row_ct[m]=round(row_ct[m]-row_ct[m-1],2)
    
    
    #for each row; for each pep: draw a red circle
    for row in npep:
        dTheta=2*math.pi/row
        for pep in range(row):
            x=math.cos(pep*dTheta)*r+xdim
            y=math.sin(pep*dTheta)*r+ydim
            draw.ellipse((x-rpep,y-rpep,x+rpep,y+rpep),fill='red',outline='black')
        r-=dr
 
    #TkInter display finalized pep layout image:
    global algim
    algim=PIL.ImageTk.PhotoImage(im)
    global pizzadisplay
    pizzadisplay = Label(root,image=algim)
    pizzadisplay.pack()
    lift_steps = int(lift * tlift_ratio)
    
    #run pep_program with e-stop capability
    print('run_pep:',pep_ct,row_ct, 'pps=',pps, ', tlift=',lift_steps)
    process=threading.Thread(target=pep_program ,args=(row_ct,pep_ct,pps,lift_steps))
    process.start()
    
def pep_program(row_ct,pep_ct,pps,lift_steps): #pps changes speed of the whole script
    global shutdown
    shutdown=0
    global n #blade encoder interrupt counter global var
    pizzaTime=time.time() #start timer
    
    #move gantry and start table
    GPIO.output(ena_pin,GPIO.LOW)
    home()
    
    tturn_steps = int(tturn_ratio * .2*pep_ct[0]) #rotate table 1 pep width less than 1 rev
    tturn_speed = pps*tturn_steps/pep_ct[0]
    pep_speed = pps*pep_ratio #calculate how fast to rotate blade
    if pep_speed > pep_max:
        pep_speed = pep_max
        pps = pps * abs(pep_max/pep_speed)
    tturn_speed = pps*tturn_steps/pep_ct[0]  #fit x peps in that section, assuming bladespeed of pps
    mod = 1
    if abs(tturn_speed) > tturn_max: #slow down blade and table for lower counts
        mod = mod * abs(tturn_max/tturn_speed)
    print(round(mod,2),end='')
    tturn_speed = tturn_speed*mod
    pep_speed = pep_speed*mod

    
    translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[0]),24000))
    rotate=threading.Thread(target=tturn.ramp,args=(tturn_speed,))
    lift = threading.Thread(target=tlift.step,args=(lift_steps,8000,))
    translate.start()
    rotate.start()
    lift.start()
    translate.join()
    #start slicing, count first pep;
    GPIO.add_event_detect(hall_pin,GPIO.FALLING,callback=hallblip,bouncetime=round(800/pps))
    pep.turn(pep_speed)
    rotate.join()
    n = 0 #peps per row on interrupt
    k = n #total peps on pizza compiled at end of loop
    
    print('\t [',end='')
    for i in range(len(pep_ct)): #the business end
        try:
            if i and GPIO.input(lim_pin): #prevent duplicate initial index and overlimit movement
                translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[i]),12000,))
                translate.start()
            if pep_ct[i]>1:
                
                tturn_steps = int(tturn_ratio * (1 - .25 * 2**(-i))) #rotate table 1 pep width less than 1 rev
                tturn_speed = 2*pps*tturn_steps/pep_ct[i] #fit x peps in that section, assuming bladespeed of pps
                pep_speed = pps*pep_ratio #calculate how fast to rotate blade
                
                mod = 1  # default no mod multiplier
                if abs(tturn_speed) > tturn_max: #slow down blade and table for lower counts
                    mod = mod * abs(tturn_max/tturn_speed)
                    print('t',end='')
                if pep_speed > pep_max:
                    mod = mod * abs(pep_max/pep_speed)
                    print('p',end='')
                tturn_speed = tturn_speed*mod
                pep_speed = pep_speed*mod
                tturn.stop() #end previous tturn.turn to start tturn.step thread
                
                rotate=threading.Thread(target=tturn.step,args=(tturn_steps,tturn_speed,))
                slicer=threading.Thread(target=pep.turn,args=(pep_speed,))
                rotate.start()
                slicer.start()
                
                while rotate.is_alive():
                    if shutdown:raise Exception('shutdown')
                    time.sleep(.01) #allow time for threads
                tturn.turn(tturn_speed)
                
            print(n, end=', ', flush=True)
            k += n #compile total pep count
            n=0 #move to new row and reset counter
            while n==0:pass #wait for encoder to trigger before moving on
        except Exception as e:
            print(e,end='')
            break
    print(n,k,']',end='  ')
    
    #stop and clean up
    stop()
    enable()
    lift = threading.Thread(target=tlift.step, args=(-lift_steps,8000,))
    lift.start()
    home()
    stop()
    cycletime=round(time.time()-pizzaTime,2)
    print(cycletime,'sec')
#     
#     global algimg
#     algimg.destroy()
    


#***********************UIFunctions******************************#

root=Tk() #Create a window

bold=font.Font(family='Helvetica', size=50, weight='bold')
norm=font.Font(family='Helvetica', size=20, weight='normal')
preset={1:{'name':'7"','size':7, 'qty':[25,16,9], 'lift':[.75,.7,.65]},
        2:{'name':'10"','size':10, 'qty':[48,31,17], 'lift':[.5,.45,.4]},
        3:{'name':'12"','size':12, 'qty':[75,46,29], 'lift':[.25,.2,.15]},
        4:{'name':'14"','size':14, 'qty':[102,61,41], 'lift':[.25,.125,.0625]}}

def killscreen():   #Program kills main window
    root.destroy()
    
def homescreen():
    #root.overrideredirect(1) #Full screen if uncommented
    root.geometry('650x480')
    root.title("Sm^rt Pep")
    Label(root,text='SM^RTPEP | version b.7.0').place(x=0,y=460)
        
    #Button(root, text="X", font=norm,bg="red", fg="white", command=killscreen,height=1, width=1).place(x=0,y=0)
    frame0=Frame(root)
    Button(frame0,text="STOP",font=norm,bg="red",fg="white",command=stop,height=5,width=9).pack()
    Button(frame0,text="HOME",font=norm,command=home,height=2,width=9).pack()
    frame0.place(x=243,y=200)
    
    frame1=Frame(root,borderwidth=5,relief=SUNKEN)
    lifttk=IntVar()
    lifttk.set(1)
    lifttk0=Radiobutton(frame1,font=norm,variable=lifttk,value=0,indicatoron=0,width=12,height=2,text='THIN')
    lifttk0.pack() #place(x=30,y=180)
    lifttk1=Radiobutton(frame1,font=norm,variable=lifttk,value=1,indicatoron=0,width=12,height=2,text='THICK')
    lifttk1.pack() #place(x=30,y=250)
    lifttk2=Radiobutton(frame1,font=norm,variable=lifttk,value=2,indicatoron=0,width=12,height=2,text='HAND-TOSS')
    lifttk2.pack() #place(x=30,y=320)
    frame1.place(x=30,y=200)
    
    frame2=Frame(root,borderwidth=5,relief=SUNKEN)
    qtytk=IntVar()
    qtytk0=Radiobutton(frame2,font=norm,variable=qtytk,value=0,indicatoron=0,width=12,height=2,text='FULL')
    qtytk0.pack()
    qtytk1=Radiobutton(frame2,font=norm,variable=qtytk,value=1,indicatoron=0,width=12,height=2,text='R4R')
    qtytk1.pack()
    qtytk2=Radiobutton(frame2,font=norm,variable=qtytk,value=2,indicatoron=0,width=12,height=2,text='ADD')
    qtytk2.pack()
    frame2.place(x=425,y=200)
    
    qtytk.set(0)
    lifttk.set(0)
    
    fnoption=[None]*5
    fnlocx=[None]+[30,180,330,480]*2
    fnlocy=[None]+[10]*4+[220]*4
    for i in range(1,len(fnoption)):
        fnoption[i]=Button(root,text=preset[i]['name'],font=bold,bg='green',fg='white',height=2,width=3,
                           command=lambda i=i: run_pep(preset[i]['size'], preset[i]['qty'][qtytk.get()], preset[i]['lift'][lifttk.get()]))
        fnoption[i].place(x=fnlocx[i],y=fnlocy[i])

def error_popup():
    errwin = Tk()
    errwin.wm_title('Error')
    tubeerror = Label(errwin,text='Attach pepperoni holder',font=bold)
    tubeerror.pack(padx=50,pady=30)
    Button(errwin,text='OK',font=bold,command=errwin.destroy,padx=50,pady=30).pack()
    
homescreen()

root.mainloop()        
 
 
 
 