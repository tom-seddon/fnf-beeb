#!/usr/bin/python3
import argparse,sys

# TODO: gamma

def get_rgb(index): return (index%5/6,index//5%5/6,index//5//5%5/6)

def get_lum(index):
    rgb=get_rgb(index)
    return 0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2]

def main(_):
    
    colours=[x for x in range(125)]

    colours=sorted(colours,key=get_lum)

    print(colours)
    print([get_rgb(i) for i in colours])

# def main(argv):
#     parser=argparse.ArgumentParser()

#     parser.add_argument('-o',metavar='FILE',dest='output_path',help='''write output to %(metavar)s''')

#     dither_order(parser.parse_args(argv))
    
if __name__=='__main__': main(sys.argv[1:])
