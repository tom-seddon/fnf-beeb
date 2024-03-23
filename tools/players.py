#!/usr/bin/python3
# print Frogs & Flies score digits

def main():
    with open('Frogs and Flies (USA).a26','rb') as f: data=f.read()
    def read(addr): return data[addr&0xfff]

    players_data=0xfc00

    filled=u'X'#\u2588\u2588'
    clear=u' '

    print()
    for y in range(255,-1,-1):
        addr=players_data+y
        value=read(addr)
        row=u'%03u ($%04x) $%02x: '%(y,addr,value)
        for x in range(8): row+=filled if value&1<<7-x else clear
        print(row)
    print()
    
if __name__=='__main__': main()
