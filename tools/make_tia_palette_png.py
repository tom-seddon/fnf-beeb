#!/usr/bin/python3
import tia_palette,argparse,sys,os.path,os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../submodules/beeb/bin'))
import png

def get_flattened_image(tuple_image):
    result=[]
    for row in tuple_image:
        result.append([])
        for pixel in row: result[-1]+=pixel
    return result

def main2(options):
    image=[]
    for y in range(256): image.append(320*[(0,0,0)])
        
    for index in range(128):
        rgb=tia_palette.get_rgb(index<<1)
        x=index%8*40
        y=index//8*16
        for dy in range(16):
            for dx in range(40): image[y+dy][x+dx]=rgb

    with open(options.output_path,'wb') as f:
        png.Writer(320,256,greyscale=False).write(f,get_flattened_image(image))
            
def main(argv):
    p=argparse.ArgumentParser()

    p.add_argument('output_path',metavar='FILE',help='''write output to %(metavar)s''')

    main2(p.parse_args(argv))

if __name__=='__main__': main(sys.argv[1:])
