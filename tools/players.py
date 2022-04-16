#!/usr/bin/python3
# print Frogs & Flies score digits

def main():
    with open('Frogs and Flies (USA).a26','rb') as f: data=f.read()
    def read(addr): return data[addr&0xfff]

    players_data=0xfc00

    print()
    for y in range(255,-1,-1):
        row=u'%03u: '%y
        value=read(players_data+y)
        for x in range(8): row+=u'\u2588\u2588' if value&1<<x else u'  '
        print(row)
    print()
    
if __name__=='__main__': main()
