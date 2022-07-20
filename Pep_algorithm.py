from PIL import Image, ImageDraw
import math

def xy(xcenter,ycenter,radius):
    return (xcenter-radius,ycenter-radius,xcenter+radius,ycenter+radius)

            
def demo(q=100,size=14,overlay=False,margin=.1,rpep=17):
    #rpep = 17 = 34mm/2 = 0.67in
    r=(size/2-margin)*25.4-rpep
    xdim=200 #round(2*r)
    ydim=xdim
    if overlay: #draw on old image
        im=Image.open('Pep_algorithm_test.jpg')
        draw = ImageDraw.Draw(im)
    else:   #create new image
        im = Image.new('RGB', (xdim*2,ydim*2), (128, 128, 128))
        draw = ImageDraw.Draw(im)
        draw.ellipse(xy(xdim,ydim,round(size*25.4/2)),fill=(255,219,112),outline='brown') #draw crust with cheese
    dr=math.sqrt(math.pi*r*r/(.0003172*q*q+.8365*q-3.9)) #***error calibrated pep center dist eqn***
    npep=[]
    for m in range(math.ceil(r/dr)): #for each row:
        npep.append(round((r-m*dr)*2*math.pi/dr))   #add pep qty for each row increasing by 2*pi
    try: npep.remove(0)   #if any row gives 0, delete
    except ValueError: pass
    if npep[-1]>4:npep.append(1)    #if center row leaves a gap in the middle, add an extra row with 1 in it
    for i in npep:  #for each row's pep qty
        dTheta=2*math.pi/i #determine angle between each pep
        for j in range(i): #for each pep in row, draw circle
            if i==1:
                draw.ellipse(xy(xdim,ydim,rpep),fill='red',outline='black')
            else:
                x=math.cos(j*dTheta)*r+xdim
                y=math.sin(j*dTheta)*r+ydim
                draw.ellipse(xy(x,y,rpep),fill='red',outline='black')
        r-=dr #move to next row inward
    print('dr =',dr/25.4,'in, Np =',npep,', total =',sum(npep)) #print stats
    im.save('Pep_algorithm_test.jpg', quality=95)


def j40():
    q=100
    size=14
    overlay=False
    margin=.9
    rpep=17
    r=(size/2-margin)*25.4-rpep
    xdim=200 #round(2*r)
    ydim=xdim
    im=Image.open('Pep_algorithm_test.jpg')
    draw = ImageDraw.Draw(im)
    dr=40
    npep=[19,13,8]
    if npep[-1]>4:npep.append(1)    #if center row leaves a gap in the middle, add an extra row with 1 in it
    for i in npep:  #for each row's pep qty
        dTheta=2*math.pi/i #determine angle between each pep
        for j in range(i): #for each pep in row, draw circle
            if i==1:
                draw.ellipse(xy(xdim,ydim,rpep),fill='red',outline='black')
            else:
                x=math.cos(j*dTheta+.5)*r+xdim
                y=math.sin(j*dTheta+.5)*r+ydim
                draw.ellipse(xy(x,y,rpep),fill='red',outline='black')
        r-=dr #move to next row inward
    print('dr =',dr/25.4,'in, Np =',npep,', total =',sum(npep)) #print stats
    im.save('Pep_algorithm_test.jpg', quality=95)
##draw.ellipse((100, 100, 150, 200), fill=(255, 0, 0), outline=(0, 0, 0))
##draw.rectangle((200, 100, 300, 200), fill=(0, 192, 192), outline=(255, 255, 255))
##draw.line((350, 200, 450, 100), fill=(255, 255, 0), width=10)
