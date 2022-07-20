from PIL import Image, ImageDraw
import math

def xy(xcenter,ycenter,radius):
    return (xcenter-radius,ycenter-radius,xcenter+radius,ycenter+radius)

            
def demo(scale=1):
    r=round(14*25.4*scale/2)
    xdim=round(200*scale)
    ydim=xdim
    im = Image.new('RGB', (xdim*2,ydim*2), (128, 128, 128))
    draw = ImageDraw.Draw(im)
    draw.ellipse(xy(xdim,ydim,r),fill=(255,219,112),outline='brown') #draw crust with cheese
    draw.ellipse(xy(xdim,ydim,round(13.7*25.4*scale/2)),fill='red',outline='white')
    draw.ellipse(xy(xdim,ydim,round(11.7*25.4*scale/2)),fill='red',outline='white')
    draw.ellipse(xy(xdim,ydim,round(9.7*25.4*scale/2)),fill='red',outline='white')
    draw.ellipse(xy(xdim,ydim,round(6.7*25.4*scale/2)),fill='red',outline='white')
    rad=.3
    pt1=(xdim,ydim-r+2)
    pt2=(xdim+r*math.sin(rad),ydim-r*math.cos(rad)+2)
    draw.polygon(((xdim,ydim),pt1,pt2),fill=(255,219,112))
    im.save('pizzadrawing.jpg', quality=95)

##draw.ellipse((100, 100, 150, 200), fill=(255, 0, 0), outline=(0, 0, 0))
##draw.rectangle((200, 100, 300, 200), fill=(0, 192, 192), outline=(255, 255, 255))
##draw.line((350, 200, 450, 100), fill=(255, 255, 0), width=10)


