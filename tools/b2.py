#!/usr/bin/python3
# Drive the BBC build in b2 for testing, through b2's HTTP API.
#
# Usable as a module (import b2 from tools/) or from the command line.
# Addresses come from the last build (build/fnf-beeb.labels and
# build/fnf-beeb.lst), so build before use.
#
# b2 must be set to draw every frame (not throttled in the
# background), or screenshots can be stale. Even then a screenshot
# shows the game 1-2 frames behind a peek taken at the same time.
#
# Common recipes:
#
# - Drive the inputs yourself: patch_call('scan_keyboard') NOPs out the
#   main loop's keyboard scan, then poke SWCHA/SWCHB/INPT4/INPT5
#   (0 = pressed, as on the 2600).
# - Freeze the flies: patch_call('sub_F5FD') (fly AI), then poke
#   mi_xs/mi_ys and zero mi_dxs/mi_dys.
# - Park a frog: set its state to 0 and position it; to stop the CPU
#   taking it over, clear pl_flags bit 6 and set unk_BD to $ff.
# - Skip ahead in time of day: poke byte_B8 to 1; the next step happens
#   within 64 frames. Do that with byte_B7=1 to start the end sequence.
#
# Patches are in memory only; run() (or make run) loads a clean copy.

import os,sys,re,time,argparse,urllib.request

ROOT=os.path.join(os.path.dirname(os.path.realpath(__file__)),'..')
BUILD=os.path.join(ROOT,'build')

sys.path.append(os.path.join(ROOT,'submodules/beeb/bin'))
import png

# BBC picture position and pixel size in a b2 screenshot (736x576).
SHOT_X0=48
SHOT_Y0=90
SHOT_XS=4
SHOT_YS=2
WIDTH=160
HEIGHT=192

BBC_COLOURS={(0,0,0):'black',(255,0,0):'red',(0,255,0):'green',
             (255,255,0):'yellow',(0,0,255):'blue',(255,0,255):'magenta',
             (0,255,255):'cyan',(255,255,255):'white'}

NOP=0xea

class B2:
    def __init__(self,port=48075,window='b2'):
        self.base='http://localhost:%d'%port
        self.window=window
        self._labels=None
        self._lst=None

    # --- HTTP

    def _url(self,endpoint,*args):
        return '/'.join([self.base,endpoint,self.window]+[str(a) for a in args])

    def peek(self,addr,n=1):
        addr=self.addr(addr)
        with urllib.request.urlopen(self._url('peek','%x'%addr,'+%d'%n)) as f:
            return f.read()

    def peek_byte(self,addr): return self.peek(addr,1)[0]

    def peek_word(self,addr):
        d=self.peek(addr,2)
        return d[0]|d[1]<<8

    def poke(self,addr,data):
        if isinstance(data,int): data=[data]
        req=urllib.request.Request(self._url('poke','%x'%self.addr(addr)),
                                   data=bytes(data),method='POST',
                                   headers={'Content-Type':'application/octet-stream'})
        urllib.request.urlopen(req).read()

    def screenshot(self,path):
        urllib.request.urlretrieve(self._url('screenshot'),path)
        return path

    def run(self,ssd=os.path.join(BUILD,'fnf-beeb.ssd'),wait=4.0):
        with open(ssd,'rb') as f: data=f.read()
        req=urllib.request.Request(self._url('run')+'?name=fnf-beeb.ssd',data=data,
                                   method='POST',headers={'Content-Type':'application/binary'})
        urllib.request.urlopen(req).read()
        self._labels=None
        self._lst=None
        time.sleep(wait)        # boot, load, draw the background

    # --- addresses

    def labels(self):
        if self._labels is None:
            self._labels={}
            with open(os.path.join(BUILD,'fnf-beeb.labels'),'rt') as f:
                for line in f:
                    m=re.match(r'^(\S+)\s*=\s*\$([0-9a-fA-F]+)',line)
                    if m: self._labels[m.group(1)]=int(m.group(2),16)
        return self._labels

    def addr(self,x):
        """Address from a label name, or an int."""
        if isinstance(x,int): return x
        m=re.match(r'^(\w+)([+-]\d+)?$',x)
        if not m or m.group(1) not in self.labels(): raise KeyError('unknown label: %s'%x)
        return self.labels()[m.group(1)]+int(m.group(2) or 0)

    def call_sites(self,name):
        """Addresses of every 'jsr name', in assembly order."""
        if self._lst is None:
            with open(os.path.join(BUILD,'fnf-beeb.lst'),'rt') as f: self._lst=f.read()
        return [int(a,16) for a in
                re.findall(r'\.([0-9a-f]{4})\s+20 [0-9a-f]{2} [0-9a-f]{2}\s+jsr \$[0-9a-f]{4}\s+jsr %s\b'%re.escape(name),self._lst)]

    def patch_call(self,name,which=-1):
        """NOP out a 'jsr name'. The default is the last one assembled,
        which for the per-frame routines is the call in main_loop."""
        site=self.call_sites(name)[which]
        self.poke(site,[NOP]*3)
        return site

    # --- game state

    def state(self):
        z=self.peek(0,0x90)
        def a(name,i=0): return z[self.addr(name)+i]
        return {
            'frogs':[{'state':a('pl_states',i),'x':a('pl_xs',i),'y':a('pl_ys',i),
                      'frame':a('byte_DB',i),'flags':a('pl_flags',i),
                      'tongue':a('pl_tongue_counters',i)} for i in (0,1)],
            'flies':[{'x':a('mi_xs',i),'y':a('mi_ys',i),'dx':a('mi_dxs',i),
                      'dy':a('mi_dys',i)} for i in (0,1)],
            'scores':[a('pl_scores',0),a('pl_scores',1)],
            'frame':a('byte_B3'),'time_of_day':a('byte_B7'),'game_over':a('byte_B4'),
            'colup':[a('COLUP0'),a('COLUP1')],'pf_eor':a('pf_eor_value'),
            'render_us':self.peek_word('render_time'),
        }

    def step_time_of_day(self):
        """Make the next time-of-day step happen (within 64 frames), and
        wait for it."""
        old=self.peek_byte('byte_B7')
        self.poke('byte_B8',1)
        for i in range(100):
            if self.peek_byte('byte_B7')!=old or self.peek_byte('byte_B4')!=0: return
            time.sleep(0.05)
        raise RuntimeError('time of day didn\'t change')

# --- screenshots

def load_screen(path):
    """b2 screenshot -> 192 rows of 160 BBC colour names."""
    w,h,rows,_=png.Reader(path).asRGB8()
    rows=[bytes(r) for r in rows]
    screen=[]
    for y in range(HEIGHT):
        row=rows[SHOT_Y0+y*SHOT_YS]
        screen.append([BBC_COLOURS.get(tuple(row[x*3:x*3+3]),'?')
                       for x in (SHOT_X0+i*SHOT_XS for i in range(WIDTH))])
    return screen

def find_colour(screen,colour,lines=range(HEIGHT)):
    """Bounding box (x0,x1,y0,y1) of a colour in some lines, or None."""
    pts=[(x,y) for y in lines for x in range(WIDTH) if screen[y][x]==colour]
    if not pts: return None
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return min(xs),max(xs),min(ys),max(ys)

def print_screen(screen,lines,xs=range(WIDTH)):
    chars={'black':'#','red':'r','green':'g','yellow':'y','blue':'~',
           'magenta':'m','cyan':'.','white':'W','?':'?'}
    for y in lines: print('%3d %s'%(y,''.join(chars[screen[y][x]] for x in xs)))

# --- command line

def auto_int(x): return int(x,0)

def main():
    parser=argparse.ArgumentParser(description='drive the BBC build in b2')
    sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('run',help='load build/fnf-beeb.ssd and run it')
    p=sub.add_parser('state',help='print the game state')
    p=sub.add_parser('peek',help='print memory')
    p.add_argument('addr',help='label (e.g. pl_xs+1) or address (e.g. 0x3300)')
    p.add_argument('n',type=auto_int,nargs='?',default=1)
    p=sub.add_parser('poke',help='write memory')
    p.add_argument('addr',help='label or address')
    p.add_argument('values',type=auto_int,nargs='+')
    p=sub.add_parser('patch-call',help='NOP out a jsr (default: the last one, i.e. main_loop\'s)')
    p.add_argument('name')
    p=sub.add_parser('step-time',help='advance the time of day one step')
    p=sub.add_parser('screenshot',help='save a screenshot')
    p.add_argument('path')
    p=sub.add_parser('show',help='screenshot and print some lines as characters')
    p.add_argument('y0',type=int)
    p.add_argument('y1',type=int)
    options=parser.parse_args()

    b2=B2()
    def addr(x):
        try: return int(x,0)
        except ValueError: return x
    if options.cmd=='run': b2.run()
    elif options.cmd=='state':
        for k,v in b2.state().items(): print('%-12s %s'%(k,v))
    elif options.cmd=='peek': print(' '.join('%02x'%v for v in b2.peek(addr(options.addr),options.n)))
    elif options.cmd=='poke': b2.poke(addr(options.addr),options.values)
    elif options.cmd=='patch-call': print('patched jsr at &%04x'%b2.patch_call(options.name))
    elif options.cmd=='step-time':
        b2.step_time_of_day(); print('time of day now',b2.peek_byte('byte_B7'))
    elif options.cmd=='screenshot': b2.screenshot(options.path)
    elif options.cmd=='show':
        path=os.path.join(BUILD,'b2-show.png')
        print_screen(load_screen(b2.screenshot(path)),range(options.y0,options.y1))

if __name__=='__main__': main()
