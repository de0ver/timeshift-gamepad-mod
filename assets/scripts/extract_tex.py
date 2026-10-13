import struct,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from x360tex import swap16
from PIL import Image
raw,listf,outdir=sys.argv[1:4]; pref=tuple(sys.argv[4].split(',')) if len(sys.argv)>4 else ('',)
d=open(raw,'rb').read(); os.makedirs(outdir,exist_ok=True)
for line in open(listf):
    p=line.split()
    if len(p)==6 and p[2]=='6' and p[5].startswith(pref):
        off=int(p[0],16); sz=int(p[1]); h=d[off:off+57]; px=d[off+51:off+sz]
        w,hh=struct.unpack_from('<II',h,17); fmt=h[31]
        try:
            if fmt==0: im=Image.frombytes('RGBA',(w,hh),px[:w*hh*4])
            elif fmt==0x11: im=Image.frombytes('RGBA',(w,hh),px[:w*hh],'bcn',3)
            elif fmt in (0x10,0x0f): im=Image.frombytes('RGBA',(w,hh),px[:w*hh//2],'bcn',1)
            else: print('skip',p[5],hex(fmt)); continue
            im.save(f'{outdir}/{p[5]}.png')
        except Exception as e: print('err',p[5],hex(fmt),w,hh,e)
