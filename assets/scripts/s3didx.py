import zlib,struct,sys
def read_index(path):
    d=open(path,'rb').read(); p=0
    us,cs=struct.unpack_from('<II',d,p); narc=struct.unpack('<I',zlib.decompress(d[p+8:p+8+cs]))[0]; p+=8+cs
    arcs=[]
    for i in range(narc):
        us,cs=struct.unpack_from('<II',d,p); b=zlib.decompress(d[p+8:p+8+cs]); p+=8+cs
        n=struct.unpack_from('<I',b,0)[0]; arcs.append(b[4:4+n].decode())
    io=struct.unpack_from('<I',d,p)[0]
    us,cs=struct.unpack_from('<II',d,io); b=zlib.decompress(d[io+8:io+8+cs])
    n=struct.unpack_from('<I',b,0)[0]; q=4; out=[]
    for i in range(n):
        nl=struct.unpack_from('<I',b,q)[0]; q+=4; name=b[q:q+nl].decode('latin1'); q+=nl
        t,m1,idx,off,size=struct.unpack_from('<IiIII',b,q); q+=20
        out.append(dict(name=name,type=t,m1=m1,arc=idx,off=off,size=size))
    return d,arcs,out,p+4,io
if __name__=='__main__':
    d,arcs,es,dstart,io=read_index(sys.argv[1]); print(arcs,'entries',len(es),'data start',hex(dstart),'index',hex(io))
    import collections; print(collections.Counter(e['arc'] for e in es))
    for e in es:
        if len(sys.argv)<3 or any(k in e['name'].lower() for k in sys.argv[2].split(',')): print(e)
