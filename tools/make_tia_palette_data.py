#!/usr/bin/python3
import tia_palette,argparse,sys

def main2(options):
    data=[]
    j=0
    for i in range(0,256,2):
        rgb=tia_palette.get_rgb(i)
        if options.nula:
            data.append((rgb[0]&0xf0)>>4)
            data.append(rgb[1]&0xf0|(rgb[2]&0xf0)>>4)
        else:
            data.append(rgb[0])
            data.append(rgb[1])
            data.append(rgb[2])

    with open(options.output_path,'wb') as f: f.write(bytearray(data))
    
def main(argv):
    p=argparse.ArgumentParser()

    p.add_argument('-n','--nula',action='store_true',help='''write NuLA-friendly data''')
    p.add_argument('output_path',metavar='FILE',help='''write output to %(metavar)s''')

    main2(p.parse_args(argv))

if __name__=='__main__': main(sys.argv[1:])
