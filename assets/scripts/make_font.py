import numpy as np, io, struct, sys
from PIL import Image, ImageDraw
I='/tmp/claude-0/-home-claude/5a395db8-292c-5075-84b1-06a93cc5a564/scratchpad/out/icons/'
O='/tmp/claude-0/-home-claude/5a395db8-292c-5075-84b1-06a93cc5a564/scratchpad/glyph/'
def comps(img,thr=40,gap=2):
    a=np.array(img)[:,:,3]>thr
    rows=np.where(a.any(1))[0]; bands=[];s=p=rows[0]
    for r in rows[1:]:
        if r>p+gap: bands.append((s,p)); s=r
        p=r
    bands.append((s,p)); out=[]
    for y0,y1 in bands:
        cols=np.where(a[y0:y1+1].any(0))[0]; s=p=cols[0]; row=[]
        for c in cols[1:]:
            if c>p+gap: row.append((s,p)); s=c
            p=c
        row.append((s,p))
        cells=[]
        for x0,x1 in row:
            ys=np.where(a[y0:y1+1,x0:x1+1].any(1))[0]
            cells.append((x0,y0+ys[0],x1,y0+ys[-1]))
        out.append(cells)
    return out
def bgra(im):
    r,g,b,a=im.convert('RGBA').split(); return Image.merge('RGBA',(b,g,r,a))
def circle(im,inset=0.04):
    im=im.convert('RGBA'); m=Image.new('L',im.size,0); w,h=im.size
    ImageDraw.Draw(m).ellipse((w*inset,h*inset,w*(1-inset),h*(1-inset)),fill=255)
    a=Image.composite(im.getchannel('A'),m,m); im.putalpha(Image.eval(Image.merge('L',[a]) if False else a,lambda v:v)); 
    im.putalpha(Image.composite(Image.new('L',im.size,255),Image.new('L',im.size,0),m)); return im
def trim(im):
    bb=im.getchannel('A').point(lambda v:255 if v>20 else 0).getbbox(); return im.crop(bb)
# --- icon sources
ab={k:trim(bgra(Image.open(I+f'xbox_{c}_button.png'))) for k,c in [('A','green'),('B','red'),('X','blue'),('Y','yellow')]}
rb=Image.open(I+'xbox_r_button.png')
sh=[trim(rb.crop(b)) for b in [(0,0,64,128),(64,0,122,128),(122,0,256,64),(122,64,256,128)]]
ab.update(LT=sh[0],RT=sh[1],RB=sh[2],LB=sh[3])
joy=Image.open(I+'xbox360joystick_joy.png')
def badge(base,shape):
    im=trim(bgra(Image.open(I+f'xbox_{base}_button.png'))).resize((128,128)); d=ImageDraw.Draw(im)
    if shape=='back': d.polygon([(40,64),(84,36),(84,92)],fill=(30,30,30,255))
    else: d.polygon([(88,64),(44,36),(44,92)],fill=(30,30,30,255))
    return im
ab['BACK']=badge('white','back'); ab['START']=badge('white','start')
def stick(box,letter):
    im=circle(joy.crop(box).resize((128,128))); d=ImageDraw.Draw(im)
    from PIL import ImageFont
    f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',70)
    w=d.textlength(letter,font=f); d.text(((128-w)/2,20),letter,font=f,fill=(255,255,255,255),stroke_width=4,stroke_fill=(0,0,0,255))
    return im
ab['LS']=stick((272,195,368,291),'L'); ab['RS']=stick((556,292,652,388),'R')
ab['DPAD']=circle(joy.crop((352,282,472,402)),0.02)
# glyph slots (row,col) in *_additional textures: row0 = À Á Ä È É Æ Œ Ì Í Ñ Ò ; row1 = Ó Ö Ù Ú Ü
SLOTS={'A':(0,0,'À'),'B':(0,1,'Á'),'X':(0,2,'Ä'),'Y':(0,3,'È'),'LT':(0,4,'É'),'LB':(0,5,'Æ'),'RB':(0,6,'Œ'),
       'RT':(0,9,'Ñ'),'BACK':(0,10,'Ò'),'START':(1,0,'Ó'),'LS':(1,1,'Ö'),'RS':(1,2,'Ù'),'DPAD':(1,3,'Ú')}
LAYOUT={'font_main_additional':['ÀÁÄÈÉÆŒÌÍÑÒ','ÓÖÙÚÜß'],'font_regular_additional':['ÀÁÄÈÉÆŒÌÍÑ','ÒÓÖÙÚÜß']}
def build(name):
    tex=Image.open(I+name+'.png').convert('RGBA'); cells=comps(tex)
    pos={}
    for r,chars in enumerate(LAYOUT[name]):
        assert len(cells[r])>=len(chars),(name,r,len(cells[r]))
        for c,ch in enumerate(chars): pos[ch]=cells[r][c]
    for key,(r,c,ch) in SLOTS.items():
        x0,y0,x1,y1=pos[ch]
        # clear whole glyph cell (incl. outline) then draw icon on baseline
        tex.paste((0,0,0,0),(x0-2,y0-2,x1+3,y1+3))
        w=x1-x0+1; h=y1-y0+1
        icon=ab[key]; ih=min(h,int(w*icon.height/icon.width*1.0)) if key in('LB','RB') else None
        iw=w; ih=int(round(iw*icon.height/icon.width))
        if ih>h: ih=h; iw=int(round(ih*icon.width/icon.height))
        ic=icon.resize((iw,ih),Image.LANCZOS)
        tex.alpha_composite(ic,(x0+(w-iw)//2, y1+1-ih - max(0,(h-ih)//6)))
    return tex
def to_pc_texture(img):
    b=io.BytesIO(); img.save(b,'DDS',pixel_format='DXT5'); dds=b.getvalue(); data=dds[128:]
    assert len(data)==img.width*img.height
    hdr=bytearray(51)
    hdr[0:3]=b'\x00\xf0\x00'; hdr[3:7]=b'\xff'*4; hdr[7:11]=b'TCIP'; hdr[11:13]=b'\xf1\x00'; hdr[13:17]=b'\xff'*4
    struct.pack_into('<II',hdr,17,img.width,img.height); hdr[25:27]=b'\xf2\x00'; hdr[27:31]=b'\xff'*4
    struct.pack_into('<I',hdr,31,0x11); hdr[35:37]=b'\xf9\x00'; hdr[37:41]=b'\xff'*4; struct.pack_into('<I',hdr,41,1)
    hdr[45:47]=b'\xff\x00'; hdr[47:51]=b'\xff'*4
    return bytes(hdr)+data+b'\x01\x00'+b'\xff'*4
out={}
for n in ('font_main_additional','font_regular_additional'):
    t=build(n); t.save(O+n+'_mod.png'); out[n]=to_pc_texture(t); open(O+n+'.tex','wb').write(out[n]); print(n,len(out[n]))
labels={k:v[2] for k,v in SLOTS.items()}; print(labels)
