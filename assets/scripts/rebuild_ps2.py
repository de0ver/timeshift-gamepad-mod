import struct,zlib,sys
S='/tmp/claude-0/-home-claude/5a395db8-292c-5075-84b1-06a93cc5a564/scratchpad'
d=open(S+'/out/pc_ps.bin','rb').read()
s=open(S+'/out/ps_stream.bin','rb').read()
nb,nf,tot=struct.unpack_from('<III',d,0); p=12; blocks=[]; off=0
for i in range(nb):
    cs,n=struct.unpack_from('<II',d,p); files=[]
    for k in range(n):
        h1,h2,sz=struct.unpack_from('<III',d,p+8+12*k); files.append([h1,h2,s[off:off+sz]]); off+=sz
    blocks.append(files); p+=8+12*n
hdr_end=p
# replacements: stream offset of file start -> new content
REPL={0x14d96e: open(S+'/ui/OptionsMouse_v2.ui').read().replace('\r\n','\n').replace('\n','\r\n').encode('latin1')}
# locate and replace
off=0; done=0
for files in blocks:
    for f in files:
        ol=len(f[2])
        if off in REPL:
            assert f[2].startswith(b'name           = OptionsMouse'), f[2][:40]
            f[2]=REPL[off]; done+=1
        off+=ol
# HUDFIX: uncomment xbox button textures in every Hud variant
hud=0
for files in blocks:
    for f in files:
        if b'//texture = xbox_' in f[2] and b'TimeShortcut' in f[2]:
            f[2]=f[2].replace(b'//texture = xbox_',b'texture = xbox_'); hud+=1
print('hud files',hud)

# GPFIX: buttons with XBoxShortCut get text key suffixed _GP<letter> (exe hook strips it when no pad)
import re,json
pairs=set(); gpn=0
blk=re.compile(rb'\{[^{}]*\}')
def fixblk(m):
    global gpn
    b=m.group(0)
    k=re.search(rb'XBoxShortCut\s*=\s*"?([ABXY])\b',b)
    t=re.search(rb'(\btext\s*=\s*"?)(UI_[A-Za-z0-9_]+)',b)
    if not k or not t or t.group(2).endswith(b'_GP'+k.group(1)): return b
    pairs.add((t.group(2).decode(),k.group(1).decode())); gpn+=1
    return b[:t.start(2)]+t.group(2)+b'_GP'+k.group(1)+b[t.end(2):]
for files in blocks:
    for f in files:
        if b'XBoxShortCut' in f[2]:
            f[2]=blk.sub(fixblk,f[2])
json.dump(sorted(pairs),open(S+'/ui/gp_pairs.json','w')); print('gp buttons',gpn,'pairs',len(pairs))
# recompute offsets properly (second pass not needed for replacement since keyed by original offsets)
assert done==len(REPL), done
# original compressed blocks for reuse
q=hdr_end; orig_c=[]; p=12
for i in range(nb):
    cs,n=struct.unpack_from('<II',d,p); orig_c.append(d[q:q+cs]); q+=cs; p+=8+12*n
hdr=bytearray(struct.pack('<III',nb,nf,0)); body=bytearray(); total=0
for i,files in enumerate(blocks):
    raw=b''.join(f[2] for f in files)
    oc=orig_c[i]
    c=oc if zlib.decompress(oc)==raw else zlib.compress(raw,9)
    hdr+=struct.pack('<II',len(c),len(files))
    for h1,h2,data in files: hdr+=struct.pack('<III',h1,h2,len(data))
    body+=c; total+=len(c)
struct.pack_into('<I',hdr,8,total)
out=bytes(hdr)+bytes(body)
open(S+'/ui/ps_new.bin','wb').write(out); print('size',len(out),'hdr',len(hdr),hdr_end)
