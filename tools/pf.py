#!/usr/bin/python3
# print Frogs & Flies playfield data

def main():
    with open('Frogs and Flies (USA).a26','rb') as f: data=f.read()
    def read(addr): return data[addr&0xfff]

    pf0_data=0xfd00
    pf1_data=0xfd55
    pf2_data=0xfdaa

    # F&F has REF=1
    for y in range(84,-1,-1):
        pf0=read(pf0_data+y)
        pf1=read(pf1_data+y)
        pf2=read(pf2_data+y)

        def px(x,i): return u'\u2588\u2588' if x&1<<i else u'  '

        row=u''
        for i in range(4,8): row+=px(pf0,i)
        for i in range(7,-1,-1): row+=px(pf1,i)
        for i in range(8): row+=px(pf2,i)
        row+=row[::-1]

        print(u'%03d: '%y+row)

if __name__=='__main__': main()
