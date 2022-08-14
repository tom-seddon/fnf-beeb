#!/usr/bin/python3
import tia_palette,argparse,sys,os.path,os,random,math
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../submodules/beeb/bin'))
import png

##########################################################################
##########################################################################

class Image:
    def __init__(self,w,h):
        self._pixels=[]
        for y in range(h): self._pixels.append(w*[(0,0,0)])
        self._border=(0,0,0)

    @property
    def width(self): return len(self._pixels[0])

    @property
    def height(self): return len(self._pixels)

    def getpixel(self,x,y):
        if y>=0 and y<self.height and x>=0 and x<self.width:
            return self._pixels[y][x]
        else: return self._border

    def putpixel(self,x,y,rgb):
        if y>=0 and y<self.height and x>=0 and x<self.width:
            self._pixels[y][x]=(rgb[0],rgb[1],rgb[2])

    def get_widened(self):
        image=Image(self.width*2,self.height)
        for y in range(self.height):
            for x in range(self.width):
                image._pixels[y][x*2+0]=self._pixels[y][x]
                image._pixels[y][x*2+1]=self._pixels[y][x]

        return image

    def save(self,path):
        data=[]
        for row in self._pixels:
            data.append([])
            for pixel in row: data[-1]+=pixel
            
        with open(path,'wb') as f:
            writer=png.Writer(len(self._pixels[0]),
                              len(self._pixels),
                              greyscale=False)
            writer.write(f,data)

##########################################################################
##########################################################################

def get_beeb_rgb(index):
    return (0 if (index&1)==0 else 255,
            0 if (index&2)==0 else 255,
            0 if (index&4)==0 else 255)

##########################################################################
##########################################################################

def main2(options):

    tia_rgbs=[]
    for i in range(128): tia_rgbs.append(tia_palette.get_rgb(i<<1))

    tia_max_rgb=[0,0,0]
    for tia_rgb in tia_rgbs:
        for i in range(3): tia_max_rgb[i]=max(tia_max_rgb[i],tia_rgb[i])

    print(tia_max_rgb)
    
    pc_image=Image(320,256)
    beeb_image=Image(160,256)
    for index in range(128):
        tia_rgb=tia_palette.get_rgb(index<<1)

        for dy in range(16):
            for dx in range(40):
                x=index%8*40
                y=index//8*16
                pc_image.putpixel(x+dx,y+dy,tia_rgb)


        int_rgb=[]
        for x in tia_rgb:
            assert x>=0 and x<=255
            x/=256.0
            #x=math.pow(x,2.2)
            x*=5
            x=int(x)
            assert x>=0 and x<=4
            int_rgb.append(x)

        beeb_colours=[0,0,0,0]
        dest=0
        for i in range(4):
            for j in range(3):
                if int_rgb[j]>i:
                    beeb_colours[dest]|=1<<j
                    dest+=1
                    dest%=len(beeb_colours)

        if ((beeb_colours[0]==beeb_colours[2] and
              beeb_colours[1]!=beeb_colours[3])
            or
            (beeb_colours[1]==beeb_colours[3] and
             beeb_colours[0]!=beeb_colours[2])):
            beeb_colours[0],beeb_colours[1]=beeb_colours[1],beeb_colours[0]

        beeb_rgbs=[get_beeb_rgb(i) for i in beeb_colours]

        # beeb_rgbs=[]
        # for i in range(4):
        #     beeb_colour=0
        #     for j in range(3):
        #         if int_rgb[j]>i: beeb_colour|=1<<j
        #     beeb_rgbs.append(get_beeb_rgb(beeb_colour))
        # # random.shuffle(beeb_rgbs)

        for dy in range(0,16,2):
            for dx in range(0,20,2):
                x=index%8*20
                y=index//8*16

                # 0123 - horizontal lines
                # 0312 - vertical lines
                # 0321 - checquerboard
                
                beeb_image.putpixel(x+dx+0,y+dy+0,beeb_rgbs[0])
                beeb_image.putpixel(x+dx+1,y+dy+0,beeb_rgbs[1])
                beeb_image.putpixel(x+dx+0,y+dy+1,beeb_rgbs[2])
                beeb_image.putpixel(x+dx+1,y+dy+1,beeb_rgbs[3])

    pc_image.save(os.path.join(options.output_folder,'tia_palette_pc.png'))
    beeb_image.get_widened().save(os.path.join(options.output_folder,'tia_palette_beeb.png'))

##########################################################################
##########################################################################

def main(argv):
    p=argparse.ArgumentParser()

    p.add_argument('output_folder',metavar='FOLDER',help='''write output files to %(metavar)s''')

    main2(p.parse_args(argv))

if __name__=='__main__': main(sys.argv[1:])
