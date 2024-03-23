#!/usr/bin/python3
# print Frogs & Flies playfield data

import sys,os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../submodules/beeb/bin'))
import png

def get_fg_colour(y):
    assert y>=0 and y<=84
    if y<=47: return 0xc6       # lighter green
    elif y<=54: return 0xe5     # dull khaki
    else: return 0xc4           # darker green

def get_bg_colour(y):
    assert y>=0 and y<=84
    if y<=32: return 0x74       # dark blue/purple
    else: return 0x98           # lighter blue

    # good (as posted to slack)
# def get_beeb_colours(c):
#     if c==0xc6: return (2,2)    # lighter green
#     elif c==0xc4: return (2,0)  # darker green
#     elif c==0xe5: return (1,5)  # dull khaki
#     elif c==0x74: return (4,0)  # dark blue/purple
#     elif c==0x98: return (6,4)  # lighter blue
#     else: assert False,hex(c)

    
def get_beeb_colours(c):
    if c==0xc6: return (2,2)    # lighter green
    elif c==0xc4: return (2,0)  # darker green
    elif c==0xe5: return (1,5)  # dull khaki
    elif c==0x74: return (4,0)  # dark blue/purple
    elif c==0x98: return (6,4)  # lighter blue
    else: assert False,hex(c)

def pf_add(pf,byte,bits):
    for bit in bits: pf.append((byte&1<<bit)!=0)
    
def main():
    with open('Frogs and Flies (USA).a26','rb') as f: data=f.read()
    def read(addr): return data[addr&0xfff]

    pf0_data=0xfd00
    pf1_data=0xfd55
    pf2_data=0xfdaa

    # F&F has REF=1
    image=[]
    for y in range(84,-1,-1):
        pf0=read(pf0_data+y)
        pf1=read(pf1_data+y)
        pf2=read(pf2_data+y)

        pf=[]
        pf_add(pf,pf0,range(4,8))
        pf_add(pf,pf1,range(7,-1,-1))
        pf_add(pf,pf2,range(8))
        pf+=pf[::-1]

        fg_colours=get_beeb_colours(get_fg_colour(y))
        bg_colours=get_beeb_colours(get_bg_colour(y))
        
        image.append([])
        image.append([])
        for x in pf:
            colours=fg_colours if x else bg_colours
            image[-1].append(colours[0])
            image[-1].append(colours[0])
            image[-1].append(colours[0])
            image[-1].append(colours[0])
            image[-1].append(colours[1])
            image[-1].append(colours[1])
            image[-1].append(colours[1])
            image[-1].append(colours[1])
            image[-2].append(colours[1])
            image[-2].append(colours[1])
            image[-2].append(colours[1])
            image[-2].append(colours[1])
            image[-2].append(colours[0])
            image[-2].append(colours[0])
            image[-2].append(colours[0])
            image[-2].append(colours[0])

    while len(image)%8!=0: image.append(len(image[0])*[0])

    with open('build/bg.png','wb') as f:
        png.Writer(len(image[0]),
                   len(image),
                   palette=[
                       (0,0,0),
                       (255,0,0),
                       (0,255,0),
                       (255,255,0),
                       (0,0,255),
                       (255,0,255),
                       (0,255,255),
                       (255,255,255),
                   ]).write(f,image)
        
if __name__=='__main__': main()
