#!/usr/bin/python3
# Compare a Stella snapshot with a b2 screenshot of the BBC version.
#
# Both are reduced to one pixel per TIA colour clock and one row per
# scanline (160x192), each pixel classified by what it is (sky, water,
# green, ...) rather than its exact colour, since the BBC only has 8
# colours. Then the rows that differ are listed, and a PNG is written
# with Stella, BBC and the differences side by side.
#
# Stella snapshots taken at window/fullscreen size are resampled to a
# non-integer number of rows per scanline, so the scanline pitch is
# found by fitting it to where the picture changes from row to row.

import sys,os,argparse
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../submodules/beeb/bin'))
import png

WIDTH=160
HEIGHT=192

# b2 screenshot geometry: BBC picture position and pixel size.
B2_X0=48
B2_Y0=90
B2_XS=4
B2_YS=2

# Classes. Frogs/flies/tongue are 'sprite' and never count as a
# difference, as the BBC doesn't draw them yet.
CLASSES={
    'S':((0x5a,0x97,0xdd),(0x00,0xff,0xff)), # sky
    'W':((0x43,0x28,0xad),(0x00,0x00,0xff)), # water
    'G':((0x28,0x79,0x27),(0x3d,0x97,0x3c),(0x00,0xff,0x00)), # tree/lily green
    'K':((0x62,0x6b,0x21),(0xff,0xff,0x00)), # khaki
    '0':((0x84,0x84,0x83),(0xff,0xff,0xff)), # P0 score
    '1':((0xc0,0x61,0x2f),),                 # P1 score (Stella)
    'X':((0,0,0),),                          # black
}
SPRITE='*'
DISPLAY={'S':(0x5a,0x97,0xdd),'W':(0x43,0x28,0xad),'G':(0x3d,0x97,0x3c),
         'K':(0x62,0x6b,0x21),'0':(0x84,0x84,0x83),'1':(0xc0,0x61,0x2f),
         'X':(0,0,0),SPRITE:(0x80,0x80,0x80)}

def classify(rgb,beeb):
    if beeb and rgb==(0xff,0,0): return '1' # P1 score is red on the BBC
    best=None
    for name,refs in CLASSES.items():
        for ref in refs:
            d=sum((a-b)**2 for a,b in zip(rgb,ref))
            if best is None or d<best[0]: best=(d,name)
    if best[0]>40*40: return SPRITE
    return best[1]

def load(path):
    w,h,rows,_=png.Reader(path).asRGB8()
    return w,h,[bytes(r) for r in rows]

def sample(rows,x0,xs,y0,ys,beeb):
    img=[]
    for ly in range(HEIGHT):
        row=rows[int(y0+(ly+0.5)*ys)]
        line=''
        for lx in range(WIDTH):
            x=int(x0+(lx+0.5)*xs)
            line+=classify(tuple(row[x*3:x*3+3]),beeb)
        img.append(line)
    return img

def fit_stella(w,h,rows):
    xs=w/WIDTH
    nonblack=[y for y in range(h) if any(rows[y])]
    top,bottom=nonblack[0],nonblack[-1]+1
    changes=[y for y in range(top+1,bottom) if rows[y]!=rows[y-1]]
    best=None
    guess=(bottom-top)/HEIGHT
    for i in range(-300,301):
        p=guess+i/1000
        for j in range(100):
            o=top-0.5+j/100*p
            err=0
            for y in changes:
                f=((y-o)/p)%1
                err+=min(f,1-f)**2
            if best is None or err<best[0]: best=(err,p,o)
    _,ys,y0=best
    return 0,xs,y0,ys

def main(options):
    sw,sh,srows=load(options.stella)
    x0,xs,y0,ys=fit_stella(sw,sh,srows)
    print('Stella: %.3f px/clock, %.3f px/scanline, first scanline at y=%.2f'%(xs,ys,y0))
    stella=sample(srows,x0,xs,y0,ys,False)
    _,_,brows=load(options.beeb)
    beeb=sample(brows,B2_X0,B2_XS,B2_Y0,B2_YS,True)

    def row_diffs(sy,by):
        if not (0<=by<HEIGHT): return None
        return [x for x in range(WIDTH)
                if stella[sy][x]!=SPRITE and stella[sy][x]!=beeb[by][x]]

    # Find the vertical offset with the fewest differences.
    best=None
    for offset in range(-8,9):
        n=0
        for sy in range(HEIGHT):
            d=row_diffs(sy,sy+offset)
            n+=WIDTH if d is None else len(d)
        if best is None or n<best[0]: best=(n,offset)
    offset=best[1]
    print('BBC line = Stella scanline %+d'%offset)

    out=[]
    for sy in range(HEIGHT):
        by=sy+offset
        d=row_diffs(sy,by)
        if d is None:
            print('scanline %3d: no BBC line'%sy)
        elif len(d)>0:
            print('scanline %3d (BBC line %3d): %3d px differ, first at x=%d'%(sy,by,len(d),d[0]))
            if options.verbose:
                print('   stella: %s'%stella[sy])
                print('   beeb:   %s'%beeb[by])
        out.append((sy,by,d))

    if options.output is not None:
        img=[]
        for sy,by,d in out:
            row=[]
            for x in range(WIDTH): row+=DISPLAY[stella[sy][x]]
            row+=(0,0,0)*4
            for x in range(WIDTH):
                row+=DISPLAY[beeb[by][x]] if d is not None else (0,0,0)
            row+=(0,0,0)*4
            for x in range(WIDTH):
                if d is None or x in d: row+=(255,0,255)
                else: row+=tuple(c//3 for c in DISPLAY[stella[sy][x]])
            scaled=[]
            for i in range(0,len(row),3): scaled+=row[i:i+3]*2
            img.append(scaled)
            img.append(scaled)
        with open(options.output,'wb') as f:
            png.Writer(len(img[0])//3,len(img),greyscale=False).write(f,img)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='compare Stella snapshot with b2 screenshot')
    parser.add_argument('-v','--verbose',action='store_true',help='print differing rows')
    parser.add_argument('-o',dest='output',metavar='FILE',help='write comparison PNG to %(metavar)s')
    parser.add_argument('stella',metavar='STELLA-PNG',help='Stella snapshot')
    parser.add_argument('beeb',metavar='B2-PNG',help='b2 screenshot')
    main(parser.parse_args())
