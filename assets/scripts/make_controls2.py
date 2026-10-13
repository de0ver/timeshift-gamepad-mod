import re,sys
src,dst=sys.argv[1],sys.argv[2]
V=lambda i:0x112+i            # virtual buttons (remapped by preset): A0 B1 X2 Y3 LB4 RB5 Back6 Start7 LS8 RS9
A,B,X,Y,LB,RB,LS,RS=V(0),V(1),V(2),V(3),V(4),V(5),V(8),V(9)
BACK,START,PA=0x10E,0x10F,0x108  # physical (never remapped)
LT,RT=0x136,0x137
VLXp,VLXn,VLYp,VLYn,VRXp,VRXn,VRYp,VRYn=0x13C,0x13D,0x13E,0x13F,0x140,0x141,0x146,0x147
DU,DD,DR,DL=0x142,0x143,0x144,0x145
PAD={'MOVE_FORWARD':([VLYn],None),'MOVE_BACKWARD':([VLYp],None),'MOVE_LEFT':([VLXn],None),'MOVE_RIGHT':([VLXp],None),
 'ROTATE_LEFT':([VRXn],None),'ROTATE_RIGHT':([VRXp],None),'LOOK_UP':([VRYn],None),'LOOK_DOWN':([VRYp],None),
 'JUMP':([A],None),'CROUCH':([LS],None),'USE':([X],None),'FORCE_RECHARGE':([X],None),
 'UI':([START],None),'STOP_CINEMATIC':([START],[PA]),'SHOWFRAGS':([BACK],None),
 'UI_UP':([DU],None),'UI_DOWN':([DD],None),'UI_ACTION':([PA],None),
 'WPN_NEXT':([Y],[DR]),'WPN_PREV':([DL],None),'NEXT_GRENADE':([DD],None),
 'ATTACK_1':([RT],None),'ATTACK_2':([LT],None),'ATTACK_3':([B],None),'MINIZOOM':([RS],None),
 'ACTIVATE_TIME_AUTO':([LB],None),'ACTIVATE_SLOW_MOTION':([LB,X],None),'ACTIVATE_TIME_FREEZE':([LB,Y],None),
 'ACTIVATE_TIME_REVERSAL':([LB,B],None),'ACTIVATE_TIME_CANCEL':([LB,A],None),
 'ACTIVATE_GREN_AUTO':([RB],None),'ACTIVATE_GREN_STICKY':([RB,X],None),'ACTIVATE_GREN_WASP':([RB,Y],None),
 'ACTIVATE_GREN_MINE':([RB,A],None),'ACTIVATE_GREN_LASER_MINE':([RB,B],None),
 'BIKE_FORW':([RT],None),'BIKE_BACK':([LT],None),'BIKE_BOOST':([A],None)}
def fmt(c): return '{ }' if not c else '{ '+' '.join('0x%X'%x for x in c)+' }'
def isjoy(tok):
    codes=[int(x,16) for x in re.findall(r'0x[0-9A-Fa-f]+',tok)]
    return codes and all((0x108<=c<=0x123) or (0x132<=c<=0x153) for c in codes)
raw=open(src,newline='').read(); nl='\r\n' if '\r\n' in raw else '\n'
out=[];n=0
for line in raw.replace('\r\n','\n').split('\n'):
    m=re.match(r'^(\s*)(\w+)(\s*=\s*)"(.*)"\s*$',line.rstrip())
    if m and m.group(2) in PAD:
        slots=re.findall(r'\{[^}]*\}',m.group(4))
        keep=[s for s in slots if not isjoy(s) and s.strip('{} ')]      # drop any old pad codes / empties
        keep=(keep+['{ }']*3)[:3]
        s4,s5=PAD[m.group(2)]
        slots=[fmt(s4)]+keep+[fmt(s5) if s5 else '{ }']
        line=f'{m.group(1)}{m.group(2)}{m.group(3)}" '+' '.join(slots)+'"'; n+=1
    out.append(line)
open(dst,'w',newline='').write(nl.join(out)); print('patched',n)
