#!/usr/bin/python3
import tia_palette,argparse,sys

def main2(options):
    data=bytearray(128*3)
    j=0
    for i in range(0,256,2):
        rgb=tia_palette.get_rgb(i)
        data[j+0]=rgb[0]
        data[j+1]=rgb[1]
        data[j+2]=rgb[2]
        j+=3

    with open(options.output_path,'wb') as f: f.write(data)
    
def main(argv):
    p=argparse.ArgumentParser()

    p.add_argument('output_path',metavar='FILE',help='''write output to %(metavar)s''')

    main2(p.parse_args(argv))

if __name__=='__main__': main(sys.argv[1:])
