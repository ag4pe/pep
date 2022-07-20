from PIL import Image, ImageDraw
import math

def xy(xcenter,ycenter,radius=0):
    return (xcenter-radius,ycenter-radius,xcenter+radius,ycenter+radius)
def edgesize(pt1,pt2,radius):
    pass

def demoeq(q=100,size=14,overlay=False,margin=.1,rpep=17):
    r=(size/2-margin)*25.4-rpep
    im=Image.new('RGB',(400,400),(128,128,128))
    draw=ImageDraw.Draw(im)
    dough=[]
    dr=math.sqrt(math.pi*r*r/(.0003172*q*q+.8365*q-3.9)) #***error calibrated pep center dist eqn***
    margin=0
    rows=[margin+rpep]
    print('start')
    
    for i in range(22): #dough outline
        theta=i*math.pi/21+math.pi/2 #iterate theta angle pi/2 to 3pi/2
        #r=12**(theta/2)-130*math.cos(1.1*theta)
        r=9.5**(theta/2)-100*math.cos(1.05*theta+.6)+50*math.sin(theta/2) #half cardioid equation
        dough.append((round(r*math.sin(theta+math.pi/2))+200,round(r*math.cos(theta+math.pi/2))+200)) #xy coord conversion
    dough.extend([(200*2-i,j) for (i,j) in dough[::-1]]) #mirror cardioid
    draw.polygon(dough,fill=(255,219,112))
    while rows[-1]<9.5**(math.pi/4)-100*math.cos(1.05*math.pi/2+.6)+50*math.sin(math.pi/4): #set row spacing
        rows.append(round(rows[-1]+dr))
    peps=[]
    for i in range(len(rows)): #for each row
        pepct=20-4.5*i #number of peps in this row (change eventually?)
        for j in range(round(pepct)+1): #for each pep in row
            theta=j*math.pi/pepct+math.pi/2
            r=9.5**(theta/2)-100*math.cos(1.05*theta+.6)+50*math.sin(theta/2)-rows[i]
            pepx=round(r*math.sin(theta+math.pi/2))+200
            pepy=round(r*math.cos(theta+math.pi/2))+200
            peps[i].append((pepx,pepy))
        peps[i].extend([(200*2-i,j) for (i,j) in peps[i][::-1]])
        for j in peps[i]:
            draw.ellipse(xy(j[0],j[1],rpep),fill='red',outline='black')
        draw.polygon(peps[i],outline=(0,0,0))
        peps.append([])
    im.save('Pep_algorithm_test.jpg')
    
    
def demobez(q=100,size=14,overlay=False,margin=.1,rpep=17):
    #rpep = 17 = 34mm/2 = 0.67in
    r=(size/2-margin)*25.4-rpep
    xdim=200 #round(2*r)
    ydim=xdim
    dim=round(size*25.4/2)
    im = Image.new('RGB', (xdim*2,ydim*2), (128, 128, 128))
    draw = ImageDraw.Draw(im)
    
    ts = [t/100.0 for t in range(101)]
    xys = [(xdim,ydim-2*dim/3),(xdim-3*dim/5,ydim-3*dim/2),(xdim-2*dim,ydim-dim/2),(xdim,dim+ydim)]
    #xys = [(xdim,ydim/3),(3*xdim/5,-ydim/2),(-xdim,ydim/2),(xdim,2*ydim)]
    bezier = make_bezier(xys)
    points = bezier(ts)
    points.extend([(xdim*2-i,j) for (i,j) in points])
    draw.polygon(points, fill=(255,219,112)) #draw crust with cheese

    dim-=30
    xys = [(xdim,ydim-2*dim/3),(xdim-3*dim/5,ydim-3*dim/2),(xdim-2*dim,ydim-dim/2),(xdim,dim+ydim)]
    bezier = make_bezier(xys)
    points = bezier([t/15 for t in range(16)])
    points.extend([(xdim*2-i,j) for (i,j) in points[::-1]])
    draw.polygon(points, outline=(0,0,0)) #draw crust with cheese
    for (i,j) in points:
        draw.ellipse(xy(i,j,rpep),fill='red',outline='black')

    dim-=50
    xys = [(xdim,ydim-2*dim/3),(xdim-3*dim/5,ydim-3*dim/2),(xdim-2*dim,ydim-dim/2),(xdim,dim+ydim)]
    bezier = make_bezier(xys)
    points = bezier([t/9 for t in range(10)])
    points.extend([(xdim*2-i,j) for (i,j) in points[::-1]])
    draw.polygon(points, outline=(0,0,0)) #draw crust with cheese
    for (i,j) in points:
        draw.ellipse(xy(i,j,rpep),fill='red',outline='black')

    dim-=50
    xys = [(xdim,ydim-2*dim/3),(xdim-3*dim/5,ydim-3*dim/2),(xdim-2*dim,ydim-dim/2),(xdim,dim+ydim)]
    bezier = make_bezier(xys)
    points = bezier([t/4 for t in range(5)])
    points.extend([(xdim*2-i,j) for (i,j) in points[::-1]])
    draw.polygon(points, outline=(0,0,0)) #draw crust with cheese
    for (i,j) in points:
        draw.ellipse(xy(i,j,rpep),fill='red',outline='black')
        
##    dr=math.sqrt(math.pi*r*r/(.0003172*q*q+.8365*q-3.9)) #***error calibrated pep center dist eqn***
##    npep=[]
##    for m in range(math.ceil(r/dr)): #for each row:
##        npep.append(round((r-m*dr)*2*math.pi/dr))   #add pep qty for each row increasing by 2*pi
##    try: npep.remove(0)   #if any row gives 0, delete
##    except ValueError: pass
##    if npep[-1]>4:npep.append(1)    #if center row leaves a gap in the middle, add an extra row with 1 in it
##    for i in npep:  #for each row's pep qty
##        dTheta=2*math.pi/i #determine angle between each pep
##        for j in range(i): #for each pep in row, draw circle
##            if i==1:
##                draw.ellipse(xy(xdim,ydim,rpep),fill='red',outline='black')
##            else:
##                x=math.cos(j*dTheta)*r+xdim
##                y=math.sin(j*dTheta)*r+ydim
##                draw.ellipse(xy(x,y,rpep),fill='red',outline='black')
##        r-=dr #move to next row inward
##    print('dr =',dr/25.4,'in, Np =',npep,', total =',sum(npep)) #print stats
    im.save('Pep_algorithm_test.jpg', quality=95)

def make_bezier(xys):
    # xys should be a sequence of 2-tuples (Bezier control points)
    n = len(xys)
    combinations = pascal_row(n-1)
    def bezier(ts):
        # This uses the generalized formula for bezier curves
        # http://en.wikipedia.org/wiki/B%C3%A9zier_curve#Generalization
        result = []
        for t in ts:
            tpowers = (t**i for i in range(n))
            upowers = reversed([(1-t)**i for i in range(n)])
            coefs = [c*a*b for c, a, b in zip(combinations, tpowers, upowers)]
            result.append(
                tuple(sum([coef*p for coef, p in zip(coefs, ps)]) for ps in zip(*xys)))
        return result
    return bezier

def pascal_row(n, memo={}):
    # This returns the nth row of Pascal's Triangle
    if n in memo:
        return memo[n]
    result = [1]
    x, numerator = 1, n
    for denominator in range(1, n//2+1):
        # print(numerator,denominator,x)
        x *= numerator
        x /= denominator
        result.append(x)
        numerator -= 1
    if n&1 == 0:
        # n is even
        result.extend(reversed(result[:-1]))
    else:
        result.extend(reversed(result))
    memo[n] = result
    return result

    
