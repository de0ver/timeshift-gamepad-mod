import struct
def tiled_offset(x,y,w,bpb):
    aw=(w+31)&~31
    lb=(bpb>>2)+((bpb>>1)>>(bpb>>2))
    macro=((x>>5)+(y>>5)*(aw>>5))<<(lb+7)
    micro=((x&7)+((y&0xE)<<2))<<lb
    off=macro+((micro&~0xF)<<1)+(micro&0xF)+((y&1)<<4)
    return (((off&~0x1FF)<<3)+((y&16)<<7)+((off&0x1C0)<<2)+(((((y&8)>>2)+(x>>3))&3)<<6)+(off&0x3F))>>lb
def untile(data,wb,hb,bpb):
    # wb,hb in blocks; returns linear
    out=bytearray(len(data))
    for y in range(hb):
        for x in range(wb):
            s=tiled_offset(x,y,wb,bpb)*bpb
            dd=(y*wb+x)*bpb
            out[dd:dd+bpb]=data[s:s+bpb]
    return bytes(out)
def swap16(b):
    a=bytearray(b); a[0::2],a[1::2]=b[1::2],b[0::2]; return bytes(a)
