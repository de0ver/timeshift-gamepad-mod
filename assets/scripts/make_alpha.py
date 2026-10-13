from PIL import Image
import numpy as np, io, struct
from scipy import ndimage
S='/tmp/claude-0/-home-claude/5a395db8-292c-5075-84b1-06a93cc5a564/scratchpad'
body=np.load(S+'/out/body3.npy')
body=ndimage.gaussian_filter(ndimage.binary_erosion(body,iterations=1).astype(float),1.2)
def to_pc_texture(img):
    b=io.BytesIO(); img.save(b,'DDS',pixel_format='DXT5'); data=b.getvalue()[128:]
    assert len(data)==img.width*img.height
    hdr=bytearray(51)
    hdr[0:3]=b'\x00\xf0\x00'; hdr[3:7]=b'\xff'*4; hdr[7:11]=b'TCIP'; hdr[11:13]=b'\xf1\x00'; hdr[13:17]=b'\xff'*4
    struct.pack_into('<II',hdr,17,img.width,img.height); hdr[25:27]=b'\xf2\x00'; hdr[27:31]=b'\xff'*4
    struct.pack_into('<I',hdr,31,0x11); hdr[35:37]=b'\xf9\x00'; hdr[37:41]=b'\xff'*4; struct.pack_into('<I',hdr,41,1)
    hdr[45:47]=b'\xff\x00'; hdr[47:51]=b'\xff'*4
    return bytes(hdr)+data+b'\x01\x00'+b'\xff'*4
for n in ['gp_pad','gp_pad_spider']+[f'gp_pad_sticks{i}' for i in range(1,5)]:
    im=np.array(Image.open(f'{S}/padui/{n}.png')).astype(float)
    rgb=im[...,:3]; mx=rgb.max(2)
    lum=np.clip(mx*1.5,0,255)
    a=np.minimum(np.maximum(lum,body*255),im[...,3])
    scale=np.minimum(255/np.maximum(a,1),255/np.maximum(mx,1))
    unp=np.clip(rgb*scale[...,None],0,255)
    col=rgb*body[...,None]+unp*(1-body[...,None])
    img=Image.fromarray(np.dstack([col,a]).astype(np.uint8),'RGBA'); img.save(f'{S}/padui/{n}_t.png')
    open(f'{S}/padui/{n}.tex','wb').write(to_pc_texture(img))
for n in ['gp_pad_spider','gp_pad_sticks1']:
    bg=Image.new('RGBA',(1024,512),(90,70,60,255)); bg.alpha_composite(Image.open(f'{S}/padui/{n}_t.png')); bg.convert('RGB').save(f'{S}/out/prev_{n}.png')
