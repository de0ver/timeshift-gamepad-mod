import sys,struct,zlib,re
S='/tmp/claude-0/-home-claude/5a395db8-292c-5075-84b1-06a93cc5a564/scratchpad'
sys.path.insert(0,S+'/tools')
from s3didx import read_index
src='/mnt/user-data/outputs/pc_mod/patch_original.s3darc'; dst='/mnt/user-data/outputs/pc_mod/patch.s3darc'
d,arcs,es,ds,io=read_index(src)
G=S+'/glyph'; U=S+'/ui'; P=S+'/padui'
repl={'font_main_additional@6':G+'/font_main_additional.tex','font_regular_additional@6':G+'/font_regular_additional.tex','ps@2':U+'/ps_new.bin'}
for l in 'czech english french german hungarian italian polish russian spanish'.split(): repl[f'strings_{l}@14']=f'{U}/strings_{l}.bin'
NEWTEX=['gp_pad','gp_pad_spider','gp_pad_sticks1','gp_pad_sticks2','gp_pad_sticks3','gp_pad_sticks4','xbox_blue_button','xbox_yellow_button','xbox_red_button','xbox_green_button']
body=bytearray(d[:io]); nlist=0
def put(e,u):
    global body
    c=zlib.compress(u,9); e.update(m1=len(body),arc=zlib.crc32(u),off=len(u),size=len(c)); body+=c
for e in es:
    key=f"{e['name']}@{e['type']}"
    if key in repl: put(e,open(repl[key],'rb').read())
    elif e['type']==0 and e['m1']>=0:
        u=zlib.decompress(d[e['m1']:e['m1']+e['size']]); t=u[4:]
        if b'Textures    =    [\n' in t:
            add=b''.join(b'\t"'+n.encode()+b'",\n' for n in NEWTEX)
            t=t.replace(b'Textures    =    [\n',b'Textures    =    [\n'+add,1)
            put(e,struct.pack('<I',len(t))+t); nlist+=1
for n in NEWTEX:
    e=dict(name=n,type=6,m1=0,arc=0,off=0,size=0); put(e,open(f'{P}/{n}.tex','rb').read()); es.append(e)
idx=bytearray(struct.pack('<I',len(es)))
for e in es:
    nm=e['name'].encode('latin1'); idx+=struct.pack('<I',len(nm))+nm+struct.pack('<IiIII',e['type'],e['m1'],e['arc'],e['off'],e['size'])
c=zlib.compress(bytes(idx),9)
struct.pack_into('<I',body,ds-4,len(body))
body+=struct.pack('<II',len(idx),len(c))+c
open(dst,'wb').write(body); print('lists updated',nlist,'entries',len(es),'size',len(body))
d2,a2,es2,ds2,io2=read_index(dst)
bad=[e['name'] for e in es2 if e['m1']>=0 and zlib.crc32(zlib.decompress(d2[e['m1']:e['m1']+e['size']]))!=e['arc']]
print('bad',bad,[e['name'] for e in es2[-6:]])
