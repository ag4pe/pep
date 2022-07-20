import RPi.GPIO as GPIO
import time
import stepper
import threading
import math
import PIL.Image,PIL.ImageDraw,PIL.ImageTk


GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
lim_pin=18 #gantry limit switch
hall_pin=12 #blade shaft encoder (1 blip per rev)
ena_pin=16 #stepper motor enable, 1=disable to keep temps down
GPIO.setup(lim_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP) 
GPIO.setup(hall_pin,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ena_pin,GPIO.OUT)
pep=stepper.motor(33,29)
tturn=stepper.motor(11,15)
ttran=stepper.motor(21,23)
tlift=stepper.motor(38,40)

pep_ratio=1600*14/18  #steps/bladerev
ttran_ratio=200*16    #steps/transrev
tturn_ratio=200*8     #steps/tablerev
tlift_ratio=200*8  #steps/rev (12mm pitch)
n=0
shutdown=0

#***********************MechanicalFunctions******************************#   
def in2step(inch,pulleydiam=1.337):
    return int(inch*ttran_ratio/(3.14159*pulleydiam)) #Convert distance to steps on motor
def home():
    GPIO.output(ena_pin,GPIO.LOW)
    ttran.turn(12000)
    while GPIO.input(lim_pin): time.sleep(.03)
    ttran.stop()
def hallblip(x):
    global n
    n+=1
def lift(size=14):
    if size<0:
        size=-size
        reverse=1
    else: reverse=-1
    m={14:1000,12:2000,10:3000,7:4000}
    tlift.step(reverse*m[size],15000)
def centercal(center=-6.5):
    ttran.step(in2step(center),12000)
    time.sleep(3)
    home()
def stop():
    shutdown=1
    pep.stop()
    tturn.stop()
    ttran.stop()
    GPIO.remove_event_detect(hall_pin)
    GPIO.output(ena_pin,GPIO.HIGH)
    try:
        for window in root.winfo_children():
            window.destroy()
        homescreen()
    except Exception as e: print('returning to home screen but',e)
def demo(size=7,qty=15,pps=3,margin=.1,center=-6.5,rpep=17):
    r=(size/2-margin)*25.4-rpep
    xdim=360
    ydim=180
    im=PIL.Image.new('RGB',(xdim*2,ydim*2),(200,200,200))
    draw=PIL.ImageDraw.Draw(im)
    draw.ellipse((xdim-size*12.7,ydim-size*12.7,xdim+size*12.7,ydim+size*12.7),fill=(255,219,112),outline='brown')
    dr=math.sqrt(math.pi*r*r/(.0003172*qty*qty+.8365*qty-3.9))
    npep=[]
    for m in range(math.ceil(r/dr)):
        npep.append(round((r-m*dr)*2*math.pi/dr))
    try: npep.remove(0)
    except ValueError: pass
    if npep[-1]>4:npep.append(1)
    for i in npep:
        dTheta=2*math.pi/i
        for j in range(i):
            x=math.cos(j*dTheta)*r+xdim
            y=math.sin(j*dTheta)*r+ydim
            draw.ellipse((x-rpep,y-rpep,x+rpep,y+rpep),fill='red',outline='black')
        r-=dr
    #TkInter stuff:
    global algimg
    algimg=Toplevel(root)
    algimg.overrideredirect(1)
    algimg.geometry('800x480')
    Label(algimg, text='TestLabel:', font=font).place(x=75,y=0)
    Button(algimg, text="X", font=font,bg="red", fg="white", command=killscreen,height=1, width=1).place(x=0, y=0)
    Button(algimg,text="HOME",font=font,command=home,height=2,width=10).place(x=100,y=400)
    Button(algimg,text="STOP",font=font,bg="red",fg="white",command=stop,height=2,width=10).place(x=300,y=400)
    global algim
    algim=PIL.ImageTk.PhotoImage(im)
    Label(algimg,image=algim).place(x=30,y=40)
    
    process=threading.Thread(target=daemo,args=(size,qty,pps,margin,center,))
    process.start()
#     process.join()
def daemo(size=7,qty=15,pps=3,margin=1.6,center=-6.5):#pps changes speed of the whole script
    global shutdown
    shutdown=0
    global n #blade encoder interrupt counter global var
    rpep=.7 #pepperoni radius
    pizzaTime=time.time() #start timer
    #row location and quantity parameters
    if qty<4.654: #algorithm minimum
        qty=5
    r=round((size-margin-rpep)/2,2) #radius, distance from center to middle of outside row
    dr=round(math.sqrt(math.pi*r*r/(0.0003172*qty*qty+.8365*qty-3.9)),2) #delta radius, distance between rows and peps in a row
    nr=math.ceil(r/dr) #number of rows
    #print(r,dr)
    row_ct=[] #stepper instructions for how far to move to each row
    pep_ct=[] #stepper instructions for how fast to rotate table relative to blade speed
    for m in range(nr): #for each row calculate...
        pep_ct.insert(0,round((r-m*dr)*2*math.pi/dr)) #number of peps in row
        row_ct.insert(0,round(center+r-m*dr,2)) #distance from home position
    if pep_ct[0]==0:pep_ct[0]=1 #force center row to round up to 1
    if pep_ct[0]>4: #add center pep if there is space
        nr+=1
        pep_ct.insert(0,1)
        row_ct.insert(0,center)
    for m in range(nr-1,0,-1): #convert row locations from absolute to relative
        row_ct[m]=round(row_ct[m]-row_ct[m-1],2)
    
    print(pep_ct,row_ct)

#Script   
    GPIO.output(ena_pin,GPIO.LOW)
    home()
    translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[0]),24000))
    GPIO.add_event_detect(hall_pin,GPIO.FALLING,callback=hallblip,bouncetime=round(1000/pps))
    if pep_ct[0]<4 and len(pep_ct)>1: #slow down blade and table for lower counts
        rotate=threading.Thread(target=tturn.ramp,args=(pps*tturn_ratio/pep_ct[1],))
    else: rotate=threading.Thread(target=tturn.ramp,args=(pps*tturn_ratio/pep_ct[0],))
    translate.start()
    rotate.start()
    translate.join()
    rotate.join()
    n=1
    pep.ramp(pps*pep_ratio,.5)
    
    print('[',end='')
    for i in range(len(pep_ct)): #the business end
        try:
            if i and GPIO.input(lim_pin): #prevent duplicate initial index and overlimit movement
                translate=threading.Thread(target=ttran.step,args=(in2step(row_ct[i]),24000,))
                translate.start()
            if pep_ct[i]>1:
                w_rot=pps*tturn_ratio/pep_ct[i]
                tturn.stop()
#                 tturn.step(.95*tturn_ratio,w_rot)
                rotate=threading.Thread(target=tturn.step,args=(.95*tturn_ratio,w_rot,),daemon=True)
                rotate.start()
                while rotate.is_alive():
                    if shutdown: raise Exception('shutdown')
                    time.sleep(.01) #allow time for translate.run()
                tturn.turn(w_rot/2)
            print(n,' ',end='',flush=True)
            n=0
            m=0
            while m==n:pass
        except KeyboardInterrupt:
            print('cancel')
            break
        except Exception as e:
            print(e)
            break
    print(n,']',end='  ')
    stop()
    GPIO.remove_event_detect(hall_pin)
    GPIO.output(ena_pin,GPIO.LOW)
    GPIO.output(ena_pin,GPIO.HIGH)
    home()
    print(round(time.time()-pizzaTime,2),'sec')
    


#***********************UIFunctions******************************#
from tkinter import *
root=Tk() #Create a window

bold=font.Font(family='Helvetica', size=50, weight='bold')
font=font.Font(family='Helvetica', size=20, weight='normal')
preset={1:{'name':'7\nFull','size':7,'qty':25},
        2:{'name':'10\nFull','size':10,'qty':48},
        3:{'name':'12\nFull','size':12,'qty':75},
        4:{'name':'14\nFull','size':14,'qty':102},
        5:{'name':'7\nLess','size':7,'qty':16},
        6:{'name':'10\nLess','size':10,'qty':31},
        7:{'name':'12\nLess','size':12,'qty':46},
        8:{'name':'14\nLess','size':14,'qty':61},}

def killscreen():   #Program kills main window
    root.destroy()
def homescreen():
    root.overrideredirect(1) #Full screen if uncommented
    root.geometry('640x480')
    root.title("Sm^rt Pep")
    namelabel=Label(root, text="Welcome to   SM^RT PEPP   by Agàpe Automation", font=font).place(x=75,y=0)

    fnoption=[None]*9
    fnoption[1]=Button(root,text=preset[1]['name'],font=bold,bg='green',fg='white',command=lambda:demo(preset[1]['size'],preset[1]['qty']),height=2,width=3)
    fnoption[2]=Button(root,text=preset[2]['name'],font=bold,bg='green',fg='white',command=lambda:demo(preset[2]['size'],preset[2]['qty']),height=2,width=3)
    fnoption[3]=Button(root,text=preset[3]['name'],font=bold,bg='green',fg='white',command=lambda:demo(preset[3]['size'],preset[3]['qty']),height=2,width=3)
    fnoption[4]=Button(root,text=preset[4]['name'],font=bold,bg='green',fg='white',command=lambda:demo(preset[4]['size'],preset[4]['qty']),height=2,width=3)
    fnoption[5]=Button(root,text=preset[5]['name'],font=bold,bg='green',fg='white',command=lambda:demo(preset[5]['size'],preset[5]['qty']),height=2,width=3)
    fnoption[6]=Button(root,text=preset[6]['name'],font=bold,bg='green',fg='white',command=lambda:demo(preset[6]['size'],preset[6]['qty']),height=2,width=3)
    fnoption[7]=Button(root,text=preset[7]['name'],font=bold,bg='green',fg='white',command=lambda:demo(preset[7]['size'],preset[7]['qty']),height=2,width=3)
    fnoption[8]=Button(root,text=preset[8]['name'],font=bold,bg='green',fg='white',command=lambda:demo(preset[8]['size'],preset[8]['qty']),height=2,width=3)
    fnlocx=[None]+[30,180,330,480]*2
    fnlocy=[None]+[40]*4+[220]*4
    for i in range(1,len(fnoption)):              
        fnoption[i].place(x=fnlocx[i],y=fnlocy[i])
    fnedit=Button(root,text='EDIT',font=font,command=fn_edit1,height=2,width=10).place(x=500,y=400)
    Button(root, text="X", font=font,bg="red", fg="white", command=killscreen,height=1, width=1).place(x=0,y=0)
    Button(root,text="HOME",font=font,command=home,height=2,width=10).place(x=100,y=400)
    Button(root,text="STOP",font=font,bg="red",fg="white",command=stop,height=2,width=10).place(x=300,y=400)

def fn_edit1():
    global fnedit1
    global n
    fnedit1=Toplevel(root)
    fnedit1.overrideredirect(1)
    fnedit1.geometry('640x480')
    Label(fnedit1, text='Select which preset to edit:', font=font).place(x=75,y=0)                
    fnoption=[None]*9
    fnlocx=[None]+[30,180,330,480]*2
    fnlocy=[None]+[40]*4+[220]*4
    for i in range(1,len(fnoption)):
        fnoption[i]=Button(fnedit1,text=preset[i]['name'],font=bold,bg='green',fg='white',command=lambda:fn_edit2(i),height=2,width=4)
        fnoption[i].place(x=fnlocx[i],y=fnlocy[i])
    print(dir(fnoption[1]))
    Button(fnedit1,text='BACK',font=font,command=fnedit1.destroy,height=2,width=10).place(x=500,y=400)
    Button(fnedit1, text="X", font=font,bg="red", fg="white", command=killscreen,height=1, width=1).place(x=0, y=0)
def fn_edit2(m):
    global fnedit2
    fnedit2=Toplevel(fnedit1)
    fnedit2.overrideredirect(1)
    fnedit2.geometry('640x480')
    Label(fnedit2, text='Edit parameters for:', font=font).place(x=75,y=10) 
    Button(fnedit2,text=preset[m]['name'],font=font,bg='green',fg='white',height=4,width=10).place(x=100,y=50)
    
    Label(fnedit2, text='_Pepp Quantity:', font=font).place(x=300,y=120)  
    qbox=Spinbox(fnedit2,from_=5,to=150,increment=1,font=bold,width=3,command=lambda:fn_edit3(m,'qty',qbox.get()))
    qbox.delete(0,'end')
    qbox.insert(0,str(preset[m]['qty']))
    qbox.place(x=500,y=100)
    
    Label(fnedit2, text='____Pizza Size:', font=font).place(x=300,y=220)
    sbox=Spinbox(fnedit2,values=[7,10,12,14],font=bold,wrap=True,width=3,command=lambda:fn_edit3(m,'size',sbox.get()))
    sbox.delete(0,'end')
    sbox.insert(0,str(preset[m]['size']))
    sbox.place(x=500,y=200)
    
    Label(fnedit2, text='__Crust Margin:', font=font).place(x=300,y=320)
    mbox=Spinbox(fnedit2,from_=0,to=3,increment=.1,font=bold,wrap=True,width=3,command=lambda:fn_edit3(m,'size',sbox.get()))
    mbox.delete(0,'end')
    mbox.insert(0,str(preset[m]['size']))
    mbox.place(x=500,y=200)
    
    Button(fnedit2,text='BACK',font=font,command=fnedit2.destroy,height=2,width=10).place(x=500,y=400)
    Button(fnedit2, text="X", font=font,bg="red", fg="white", command=killscreen,height=1, width=1).place(x=0, y=0)
def fn_edit3(m,n,amt):
    preset[m][n]=int(amt)

homescreen()
root.mainloop()        
