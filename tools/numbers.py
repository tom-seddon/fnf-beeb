#!/usr/bin/python3
# print Frogs & Flies score digits

def main():
    with open('Frogs and Flies (USA).a26','rb') as f: data=f.read()
    def read(addr): return data[addr&0xfff]

    digits_data=0xfb00

    print()
    for digit_set in range(2):
        for digit_row in range(4,-1,-1):
            row=u''
            for digit in range(10):
                value=read(digits_data+digit_set*50+digit*5+digit_row)
                for i in range(7,-1,-1):
                    row+=u'\u2588\u2588' if value&1<<i else u'  '
            print(row)
    print()
    
if __name__=='__main__': main()
    
