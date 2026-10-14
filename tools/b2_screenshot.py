#!/usr/bin/python3
# Grab the BBC version's screen from b2 as a PNG.
#
# b2 has no screenshot endpoint, so peek the screen memory and the
# OS's copy of the palette (VDU 19 keeps it up to date) and decode the
# 160x192 MODE 2 screen at &4400.

import sys,os,argparse,urllib.request
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../submodules/beeb/bin'))
import png

SCREEN=0x4400
WIDTH=160
HEIGHT=192
OS_PALETTE=0x36f                # OS 1.20 logical->physical palette

RGBS=[(0,0,0),(255,0,0),(0,255,0),(255,255,0),
      (0,0,255),(255,0,255),(0,255,255),(255,255,255)]

def peek(options,begin,end):
    url='http://localhost:%d/peek/b2/%x/%x'%(options.port,begin,end)
    with urllib.request.urlopen(url) as f: return f.read()

def main(options):
    screen=peek(options,SCREEN,0x8000)
    palette=peek(options,OS_PALETTE,OS_PALETTE+16)

    rows=[]
    for y in range(HEIGHT):
        row=[]
        for x in range(WIDTH):
            byte=screen[(y>>3)*640+(x>>1)*8+(y&7)]
            if x&1: byte<<=1
            logical=((byte>>4)&8)|((byte>>3)&4)|((byte>>2)&2)|((byte>>1)&1)
            rgb=RGBS[palette[logical]&7]
            row+=rgb*options.scale_x
        for i in range(options.scale_y): rows.append(row)

    with open(options.output,'wb') as f:
        png.Writer(WIDTH*options.scale_x,HEIGHT*options.scale_y,greyscale=False).write(f,rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='grab BBC screen from b2 as PNG')
    parser.add_argument('--port',type=int,default=48075,help='b2 HTTP port (default: %(default)s)')
    parser.add_argument('--scale-x',type=int,default=4,help='horizontal scale (default: %(default)s)')
    parser.add_argument('--scale-y',type=int,default=2,help='vertical scale (default: %(default)s)')
    parser.add_argument('output',metavar='FILE',help='write PNG to %(metavar)s')
    main(parser.parse_args())
