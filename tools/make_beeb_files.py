#!/usr/bin/python3
# Write the BeebLink metadata for the BBC build: the .inf for the
# main binary, and $.!BOOT plus *OPT4,3 so SHIFT+BREAK runs it.

import os,argparse

def main(options):
    with open(options.binary+'.inf','wt') as f:
        f.write('$.%s ffff%04x ffff%04x\n'%(options.name,options.load,options.load))

    folder=os.path.dirname(options.binary)
    with open(os.path.join(folder,'$.!BOOT'),'wb') as f:
        for line in options.boot: f.write(line.encode('ascii')+b'\r')
    with open(os.path.join(folder,'$.!BOOT.inf'),'wt') as f:
        f.write('$.!BOOT ffffffff ffffffff\n')
    with open(os.path.join(folder,'.opt4'),'wb') as f: f.write(b'3')

def auto_int(x): return int(x,0)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='write BeebLink metadata for the BBC build')
    parser.add_argument('--load',type=auto_int,required=True,help='load and execution address')
    parser.add_argument('--name',required=True,help='BBC name of the binary (in $)')
    parser.add_argument('--boot',action='append',default=[],help='add line to $.!BOOT')
    parser.add_argument('binary',help='path of binary in the BeebLink folder')
    main(parser.parse_args())
