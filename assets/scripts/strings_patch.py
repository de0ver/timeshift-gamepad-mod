import sys,zlib
sys.path.insert(0,'/tmp/claude-0/-home-claude/5a395db8-292c-5075-84b1-06a93cc5a564/scratchpad/tools')
from s3didx import read_index
S='/tmp/claude-0/-home-claude/5a395db8-292c-5075-84b1-06a93cc5a564/scratchpad'
d,a,es,ds,io=read_index('/mnt/user-data/outputs/pc_mod/patch_original.s3darc')
EN={'UI_GP_MODVER':'Xbox 360 Gamepad Mod v1.2','UI_GP_SENS':'Gamepad sensitivity','UI_GP_SENS_HINT':'Camera speed for the right stick',
    'UI_GP_INVERT':'Gamepad invert Y','UI_GP_INVERT_HINT':'Invert vertical look on the right stick',
    'UI_GP_VIBR':'Gamepad vibration','UI_GP_VIBR_HINT':'Controller rumble',
    'UI_GP_DZ':'Gamepad dead zone','UI_GP_DZ_HINT':'Ignore small stick movements',
    'UI_GP_PAGE':'Settings','UI_GP_USE':'Use/Reload','UI_GP_TIME':'Time Control','UI_GP_PAGE_CAMERA':'Camera','UI_GP_PAGE_BUTTONS':'Gamepad buttons','UI_GP_PAGE_STICKS':'Gamepad sticks',
    'UI_GP_FWDBACK':'Forward/Back','UI_GP_STRAFE':'Strafe','UI_GP_TURN':'Turn','UI_GP_LOOKUD':'Look Up/Down',
    'UI_CTRL_buttons_1':'Common','UI_CTRL_buttons_2':'Left-Handed','UI_CTRL_buttons_3':'Swapped','UI_CTRL_buttons_4':'Swapped Left-Handed',
    'UI_CTRL_thumb_1':'Common','UI_CTRL_thumb_2':'Left-Handed','UI_CTRL_thumb_3':'Mixed','UI_CTRL_thumb_4':'Mixed Left-Handed'}
RU={'UI_GP_MODVER':'Xbox 360 Gamepad Mod v1.2','UI_GP_SENS':'Чувствительность геймпада','UI_GP_SENS_HINT':'Скорость поворота камеры правым стиком',
    'UI_GP_INVERT':'Инверсия геймпада по Y','UI_GP_INVERT_HINT':'Инверсия вертикального обзора правым стиком',
    'UI_GP_VIBR':'Вибрация геймпада','UI_GP_VIBR_HINT':'Вибрация контроллера',
    'UI_GP_DZ':'Мертвая зона стиков','UI_GP_DZ_HINT':'Игнорировать малые отклонения стиков',
    'UI_GP_PAGE':'Раздел','UI_GP_USE':'Использовать/перезарядка','UI_GP_TIME':'Хроноконтроль','UI_GP_PAGE_CAMERA':'Камера','UI_GP_PAGE_BUTTONS':'Кнопки геймпада','UI_GP_PAGE_STICKS':'Стики геймпада',
    'UI_GP_FWDBACK':'Вперед/назад','UI_GP_STRAFE':'Вбок','UI_GP_TURN':'Поворот','UI_GP_LOOKUD':'Взгляд вверх/вниз',
    'UI_CTRL_buttons_1':'Обычная','UI_CTRL_buttons_2':'Для левши','UI_CTRL_buttons_3':'Обратная','UI_CTRL_buttons_4':'Обратная для левши',
    'UI_CTRL_thumb_1':'Обычная','UI_CTRL_thumb_2':'Для левши','UI_CTRL_thumb_3':'Смешанная','UI_CTRL_thumb_4':'Смешанная для левши'}
REN_EN={'UI_BTN_MOUSE_CONTROLS':'MOUSE AND GAMEPAD','UI_FRAME_OPTIONS_MOUSE':'Mouse and Gamepad'}
REN_RU={'UI_BTN_MOUSE_CONTROLS':'МЫШЬ И ГЕЙМПАД','UI_FRAME_OPTIONS_MOUSE':'Мышь и геймпад'}
import re,json
GL={'A':'\u00c0','B':'\u00c1','X':'\u00c4','Y':'\u00c8'}
PAIRS=json.load(open(S+'/ui/gp_pairs.json'))
def kv(t):
    return {m.group(1):m.group(2) for m in re.finditer(r'(?m)^(\w+)\t+"([^"\r\n]*)"',t)}
EN_ALL=None
for e in es:
    if e['type']==14 and e['name']=='strings_english': EN_ALL=kv(zlib.decompress(d[e['m1']:e['m1']+e['size']]).decode('utf-16'))
for e in es:
    if e['type']!=14: continue
    t=zlib.decompress(d[e['m1']:e['m1']+e['size']]).decode('utf-16')
    ru=e['name']=='strings_russian'
    ren=REN_RU if ru else (REN_EN if e['name']=='strings_english' else {})
    for k,v in ren.items():
        t,n=re.subn(r'(?m)^('+k+r'\t+)"[^"\r\n]*"',lambda m:m.group(1)+'"'+v+'"',t); assert n>=1,(e['name'],k)
    add=RU if ru else EN
    if not t.endswith('\r\n'): t+='\r\n'
    for k,v in add.items():
        if not re.search(r'(?m)^'+k+r'\t',t): t+=f'{k}\t\t\t\t"{v}"\r\n'
    cur=kv(t); n=0
    for k,l in PAIRS:
        v=cur.get(k, EN_ALL.get(k, k))
        if not re.search(r'(?m)^'+k+'_GP'+l+r'\t',t): t+=f'{k}_GP{l}\t\t\t\t"{GL[l]} {v}"\r\n'; n+=1
    print(' gp keys',n)
    out=('﻿'+t if not t.startswith('﻿') else t).encode('utf-16-le')
    open(f"{S}/ui/{e['name']}.bin",'wb').write(out); print(e['name'],len(out))
