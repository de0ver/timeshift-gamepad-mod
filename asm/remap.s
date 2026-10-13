.intel_syntax noprefix
.set G_MOVE,  0x10e0f00
.set G_LOOKX, 0x10e0f04
.set G_LOOKY, 0x10e0f08
.set G_BTN,   0x10e0f34
.set G_THM,   0x10e0f38
.globl _start
_start:                          # VA 0xd10d00 : wrapper for joystick poll (vtable +0x80)
    push ecx
    mov  eax, 0x7bcce0
    call eax
    pop  ecx
    pushad
    mov  ebx, ecx
    # ---- buttons: virtual slot (code 0x112+i) = physical slot (code 0x108+perm[i])
    mov  eax, [G_BTN]
    cmp  eax, 3
    jbe  1f
    xor  eax, eax
1:  imul esi, eax, 12
    add  esi, offset perm
    xor  ecx, ecx
2:  movzx edx, byte ptr [esi+ecx]
    mov  edx, [ebx+0x430+edx*4]
    mov  [ebx+0x458+ecx*4], edx
    inc  ecx
    cmp  ecx, 10
    jb   2b
    cmp  byte ptr [esi+10], 0       # trigger swap
    je   3f
    xor  dword ptr [ebx+0x4e8], 0x80000000
3:  # ---- sticks: normalized physical n[0..3] = LX/m, LY/m, RX/lx, RY/ly
    sub  esp, 16
    movss xmm0, [ebx+0x4d8]
    movss xmm1, [G_MOVE]
    call sdiv
    movss [esp], xmm0
    movss xmm0, [ebx+0x4e0]
    movss xmm1, [G_MOVE]
    call sdiv
    movss [esp+4], xmm0
    movss xmm0, [ebx+0x4f0]
    movss xmm1, [G_LOOKX]
    call sdiv
    movss [esp+8], xmm0
    movss xmm0, [ebx+0x4f8]
    movss xmm1, [G_LOOKY]
    call sdiv
    movss [esp+12], xmm0
    mov  eax, [G_THM]
    cmp  eax, 3
    jbe  4f
    xor  eax, eax
4:  lea  esi, [thm+eax*4]
    movzx edx, byte ptr [esi]        # virtual LX (codes 0x13c/0x13d) -> slot 0x500
    movss xmm0, [esp+edx*4]
    mulss xmm0, [G_MOVE]
    movss [ebx+0x500], xmm0
    movzx edx, byte ptr [esi+1]      # virtual LY (0x13e/0x13f) -> 0x508
    movss xmm0, [esp+edx*4]
    mulss xmm0, [G_MOVE]
    movss [ebx+0x508], xmm0
    movzx edx, byte ptr [esi+2]      # virtual RX (0x140/0x141) -> 0x510
    movss xmm0, [esp+edx*4]
    mulss xmm0, [G_LOOKX]
    movss [ebx+0x510], xmm0
    movzx edx, byte ptr [esi+3]      # virtual RY (0x146/0x147) -> 0x528
    movss xmm0, [esp+edx*4]
    mulss xmm0, [G_LOOKY]
    movss [ebx+0x528], xmm0
    add  esp, 16
    popad
    ret

# xmm0 = xmm0 / xmm1 (0 if xmm1 == 0)
sdiv:
    xorps xmm2, xmm2
    comiss xmm1, xmm2
    je   1f
    divss xmm0, xmm1
    ret
1:  xorps xmm0, xmm0
    ret

# GetName translation: eax = code in/out (called from GetName hook)
.globl translate
translate:
    cmp  eax, 0x112
    jb   9f
    cmp  eax, 0x11b
    ja   5f
    push ecx
    mov  ecx, [G_BTN]
    cmp  ecx, 3
    jbe  1f
    xor  ecx, ecx
1:  imul ecx, ecx, 12
    movzx eax, byte ptr [perm+ecx+eax-0x112]
    add  eax, 0x108
    pop  ecx
    ret
5:  cmp  eax, 0x136
    je   6f
    cmp  eax, 0x137
    jne  7f
6:  push ecx
    mov  ecx, [G_BTN]
    cmp  ecx, 3
    jbe  1f
    xor  ecx, ecx
1:  imul ecx, ecx, 12
    cmp  byte ptr [perm+ecx+10], 0
    pop  ecx
    je   9f
    xor  eax, 1
    ret
7:  # virtual axes -> physical stick code
    push ecx
    mov  ecx, -1
    cmp  eax, 0x13c
    je   10f
    cmp  eax, 0x13d
    je   10f
    cmp  eax, 0x13e
    je   11f
    cmp  eax, 0x13f
    je   11f
    cmp  eax, 0x140
    je   12f
    cmp  eax, 0x141
    je   12f
    cmp  eax, 0x146
    je   13f
    cmp  eax, 0x147
    je   13f
    pop  ecx
    ret
10: mov  ecx, 0
    jmp  14f
11: mov  ecx, 1
    jmp  14f
12: mov  ecx, 2
    jmp  14f
13: mov  ecx, 3
14: push edx
    mov  edx, [G_THM]
    cmp  edx, 3
    jbe  15f
    xor  edx, edx
15: movzx ecx, byte ptr [thm+edx*4+ecx]
    movzx eax, byte ptr [physax+ecx]
    add  eax, 0x100
    pop  edx
    pop  ecx
9:  ret

# button perms: virtual i <- physical perm[i]  (A B X Y LB RB Back Start LS RS), byte10 = trigger swap
perm:
    .byte 0,1,2,3,4,5,6,7,8,9, 0,0
    .byte 9,1,2,3,5,4,6,7,0,8, 1,0
    .byte 0,9,2,3,4,5,6,7,8,1, 0,0
    .byte 9,8,2,3,5,4,6,7,0,1, 1,0
# stick maps: sources for (VLX, VLY, VRX, VRY) among (LX, LY, RX, RY)
thm:
    .byte 0,1,2,3
    .byte 2,3,0,1
    .byte 2,1,0,3
    .byte 0,3,2,1
physax: .byte 0x32,0x34,0x38,0x3a
