.intel_syntax noprefix
.set G_MOVE,  0x10e0f00
.set G_LOOKX, 0x10e0f04
.set G_LOOKY, 0x10e0f08
.set G_DZ,    0x10e0f10
.set G_VIB,   0x10e0f14
.set G_PADLAST, 0x10e0f18
.set G_GPPI,  0x10e0f1c
.set G_GPPS,  0x10e0f20
.set G_CNT,   0x10e0f24
.set G_CFA,   0x10e0f28
.set G_RF,    0x10e0f2c
.set G_CH,    0x10e0f30
.set G_BTN,   0x10e0f34
.set G_THM,   0x10e0f38
.set IAT_GetModuleFileNameA, 0xd11178
.set IAT_GetModuleHandleA,   0xd11130
.set IAT_GetProcAddress,     0xd11304
.globl _start
_start:                              # VA 0xd10600 ; hook of input frame update 0x785fe0
    push ebx
    mov  ebx, [esp+8]
    push ebp
    pushad
    mov  dword ptr [0x10e0f3c], ebx
    cmp  dword ptr [ebx+0x3144], -1
    jne  after_init
    cmp  dword ptr [ebx+0x1804], 0
    je   after_init
    mov  dword ptr [ebx+0x3144], -2
    mov  dword ptr [G_VIB], -1
    mov  dword ptr [G_DZ], 0x3e6147ae
    call read_cfg
    push 1
    push ebx
    push 0x7bcee0
    push 4
    mov  eax, [ebx+0x1804]
    push eax
    mov  ecx, [eax]
    call dword ptr [ecx+0x10]            # EnumDevices(GAMECTRL)
    cmp  dword ptr [ebx+0x3140], 0
    jle  after_init
    mov  eax, [G_DZ]
    mov  [ebx+0x3148], eax
    mov  edi, ebx
    xor  eax, eax
    mov  ecx, 0x7bca50
    call ecx                             # create joystick #0
    test eax, eax
    jz   after_init
    mov  eax, [ebx+0x1bbc]
    test eax, eax
    jz   after_init
    push eax
    mov  ecx, [eax]
    call dword ptr [ecx+0x1c]            # Acquire
    or   dword ptr [ebx+4], 0xC
    mov  ecx, ebx
    mov  eax, [ebx]
    call dword ptr [eax+0x84]            # XInput init
    mov  dword ptr [G_VIB], -1           # force vibration state apply
    call read_cfg
after_init:
    cmp  dword ptr [ebx+0x1bbc], 0
    je   done
    inc  dword ptr [G_CNT]
    mov  eax, [G_CNT]
    xor  edx, edx
    mov  ecx, 30
    div  ecx
    test edx, edx
    jnz  park
    call read_cfg
park:
    mov  eax, [ebx+0x1b80]
    or   eax, [ebx+0x1b84]
    and  eax, 0x7fffffff
    jz   7f
    mov  dword ptr [G_PADLAST], 0
7:  xor  ecx, ecx
    movss xmm1, [c_half]
8:  movss xmm0, [ebx+0x430+ecx*4]
    comiss xmm0, xmm1
    ja   9f
    inc  ecx
    cmp  ecx, 10
    jb   8b
    xor  ecx, ecx
10: movss xmm0, [ebx+0x518+ecx*4]
    andps xmm0, [c_abs]
    comiss xmm0, xmm1
    ja   9f
    inc  ecx
    cmp  ecx, 4
    jb   10b
    movss xmm0, [ebx+0x4d8]
    andps xmm0, [c_abs]
    comiss xmm0, xmm1
    ja   9f
    movss xmm0, [ebx+0x4e0]
    andps xmm0, [c_abs]
    comiss xmm0, xmm1
    ja   9f
    jmp  11f
9:  mov  dword ptr [G_PADLAST], 1
11: cmp  dword ptr [G_PADLAST], 0
    je   done
    mov  eax, [c_p1]
    mov  [ebx+0x1b74], eax
    mov  [ebx+0x1b78], eax
done:
    popad
    push 0x785fe6
    ret

# ---------- helpers
append:
    mov  al, [esi]
    mov  [edi], al
    test al, al
    jz   1f
    inc  esi
    inc  edi
    jmp  append
1:  ret

# find_val: esi = key (asciz), returns eax = ptr to value text in file buffer [ebp-0x4400], or 0
find_val:
    push ebx
    push edi
    lea  edi, [ebp-0x4400]
    mov  ebx, edi                    # line start candidate
1:  cmp  byte ptr [ebx], 0
    je   9f
    # compare key at ebx
    push esi
    mov  edx, ebx
2:  mov  al, [esi]
    test al, al
    jz   3f
    cmp  al, [edx]
    jne  4f
    inc  esi
    inc  edx
    jmp  2b
3:  mov  al, [edx]                   # key matched; next must be ' ' '=' or '\t'
    cmp  al, 0x20
    je   5f
    cmp  al, 0x3d
    je   5f
    cmp  al, 0x09
    je   5f
4:  pop  esi
    # advance ebx to next line
6:  mov  al, [ebx]
    test al, al
    jz   9f
    inc  ebx
    cmp  al, 0x0a
    jne  6b
    jmp  1b
5:  pop  esi
7:  mov  al, [edx]                   # skip spaces, '=', tabs, quotes
    cmp  al, 0x20
    je   8f
    cmp  al, 0x3d
    je   8f
    cmp  al, 0x09
    je   8f
    cmp  al, 0x22
    je   8f
    mov  eax, edx
    pop  edi
    pop  ebx
    ret
8:  inc  edx
    jmp  7b
9:  xor  eax, eax
    pop  edi
    pop  ebx
    ret

# get_int: esi = key, ecx = default -> eax  (yes/true->1, no/false->0, digits->int)
get_int:
    push ecx
    call find_val
    pop  ecx
    test eax, eax
    jz   1f
    movzx edx, byte ptr [eax]
    or   dl, 0x20
    cmp  dl, 0x79                    # 'y'
    je   2f
    cmp  dl, 0x74                    # 't'
    je   2f
    cmp  dl, 0x6e                    # 'n'
    je   3f
    cmp  dl, 0x66                    # 'f'
    je   3f
    mov  edx, eax
    xor  eax, eax
    movzx ecx, byte ptr [edx]
    sub  ecx, 0x30
    cmp  ecx, 9
    ja   1f
4:  movzx ecx, byte ptr [edx]
    sub  ecx, 0x30
    cmp  ecx, 9
    ja   5f
    imul eax, eax, 10
    add  eax, ecx
    inc  edx
    jmp  4b
5:  ret
1:  mov  eax, ecx
    ret
2:  mov  eax, 1
    ret
3:  xor  eax, eax
    ret

# ---------- read settings from <exe dir>\<Folder><Name>\user.ini  (ebx = input object)
read_cfg:
    push ebp
    mov  ebp, esp
    mov  ecx, 0x12                   # probe stack page by page (0x12 * 0x400 = 0x4800)
30: sub  esp, 0x400
    mov  dword ptr [esp], 0
    dec  ecx
    jnz  30b
    cmp  dword ptr [G_GPPS], 0
    jne  1f
    push offset s_k32
    call dword ptr [IAT_GetModuleHandleA]
    mov  esi, eax
    push offset s_gpps
    push esi
    call dword ptr [IAT_GetProcAddress]
    mov  [G_GPPS], eax
    push offset s_cfa
    push esi
    call dword ptr [IAT_GetProcAddress]
    mov  [G_CFA], eax
    push offset s_rf
    push esi
    call dword ptr [IAT_GetProcAddress]
    mov  [G_RF], eax
    push offset s_ch
    push esi
    call dword ptr [IAT_GetProcAddress]
    mov  [G_CH], eax
1:  push 0x104
    lea  eax, [ebp-0x400]
    push eax
    push 0
    call dword ptr [IAT_GetModuleFileNameA]
    lea  edi, [ebp-0x400]
    lea  esi, [ebp-0x400]
2:  mov  al, [esi]
    test al, al
    jz   3f
    inc  esi
    cmp  al, 0x5c
    jne  2b
    mov  edi, esi
    jmp  2b
3:  mov  byte ptr [edi], 0
    lea  edi, [ebp-0x300]
    lea  esi, [ebp-0x400]
    call append
    mov  esi, offset s_sw
    call append
    lea  eax, [ebp-0x300]
    push eax
    push 0x80
    lea  eax, [ebp-0x100]
    push eax
    push offset s_folder_def
    push offset k_folder
    push offset s_profile
    call dword ptr [G_GPPS]
    lea  eax, [ebp-0x300]
    push eax
    push 0x7c
    lea  eax, [ebp-0x80]
    push eax
    push offset s_name_def
    push offset k_name
    push offset s_profile
    call dword ptr [G_GPPS]
    lea  edi, [ebp-0x200]
    lea  esi, [ebp-0x400]
    call append
    lea  esi, [ebp-0x100]
    call append
    lea  esi, [ebp-0x80]
    call append
    mov  esi, offset s_userini
    call append
    # read whole file into [ebp-0x4400] (max 0x3ff0)
    mov  byte ptr [ebp-0x4400], 0
    push 0
    push 0
    push 3
    push 0
    push 3
    push 0x80000000
    lea  eax, [ebp-0x200]
    push eax
    call dword ptr [G_CFA]
    cmp  eax, -1
    je   20f
    mov  edi, eax
    mov  dword ptr [ebp-0x4404], 0
    push 0
    lea  eax, [ebp-0x4404]
    push eax
    push 0x3ff0
    lea  eax, [ebp-0x4400]
    push eax
    push edi
    call dword ptr [G_RF]
    push edi
    call dword ptr [G_CH]
    mov  eax, [ebp-0x4404]
    mov  byte ptr [ebp-0x4400+eax], 0
20: # --- LookSensitivity
    mov  esi, offset k_look
    mov  ecx, 100
    call get_int
    cmp  eax, 5
    jge  4f
    mov  eax, 100
4:  cvtsi2ss xmm0, eax
    mulss xmm0, [c_look]
    movss [G_LOOKX], xmm0
    movss [G_LOOKY], xmm0
    mov  esi, offset k_inv
    xor  ecx, ecx
    call get_int
    test eax, eax
    jz   5f
    movss xmm0, [G_LOOKY]
    xorps xmm1, xmm1
    subss xmm1, xmm0
    movss [G_LOOKY], xmm1
5:  mov  esi, offset k_mv
    mov  ecx, 100
    call get_int
    cmp  eax, 5
    jge  6f
    mov  eax, 100
6:  cvtsi2ss xmm0, eax
    mulss xmm0, [c_move]
    movss [G_MOVE], xmm0
    mov  esi, offset k_dz
    mov  ecx, 22
    call get_int
    cmp  eax, 60
    jle  13f
    mov  eax, 60
13: cvtsi2ss xmm0, eax
    mulss xmm0, [c_pct]
    movss xmm1, [G_DZ]
    movss [G_DZ], xmm0
    comiss xmm0, xmm1
    je   14f
    cmp  dword ptr [ebx+0x1bbc], 0
    je   14f
    sub  esp, 4
    movss [esp], xmm0
    mov  ecx, ebx
    mov  eax, [ebx]
    call dword ptr [eax+0x20]
14: mov  esi, offset k_btn
    mov  ecx, 1
    call get_int
    dec  eax
    cmp  eax, 3
    jbe  16f
    xor  eax, eax
16: mov  [G_BTN], eax
    mov  esi, offset k_thm
    mov  ecx, 1
    call get_int
    dec  eax
    cmp  eax, 3
    jbe  17f
    xor  eax, eax
17: mov  [G_THM], eax
    mov  esi, offset k_vib
    mov  ecx, 1
    call get_int
    test eax, eax
    setnz al
    movzx eax, al
    cmp  eax, [G_VIB]
    je   15f
    mov  [G_VIB], eax
    cmp  dword ptr [ebx+0x1bbc], 0
    je   15f
    cmp  dword ptr [ebx+0x314c], 0
    je   15f
    push eax
    mov  ecx, ebx
    mov  eax, [ebx]
    call dword ptr [eax+0x3c]
15: mov  esp, ebp
    pop  ebp
    ret

.align 4
c_m1:   .float -1.0
c_p1:   .float 1.0
c_look: .float 0.12
c_move: .float 0.04
c_pct:  .float 0.01
c_half: .float 0.5
.align 16
c_abs:  .long 0x7fffffff,0x7fffffff,0x7fffffff,0x7fffffff
s_k32:  .asciz "kernel32.dll"
s_cfa:  .asciz "CreateFileA"
s_rf:   .asciz "ReadFile"
s_ch:   .asciz "CloseHandle"
s_gpps: .asciz "GetPrivateProfileStringA"
s_sw:   .asciz "steamwars.ini"
s_profile: .asciz "Profile"
k_folder:  .asciz "Folder"
k_name:    .asciz "Name"
s_folder_def: .asciz "..\\UserConfigs\\"
s_name_def:   .asciz "Default"
s_userini: .asciz "\\user.ini"
k_look: .asciz "LookSensitivity"
k_inv:  .asciz "InvertLookY"
k_mv:   .asciz "MoveSensitivity"
k_dz:   .asciz "DeadZone"
k_vib:  .asciz "Vibration"
k_btn:  .asciz "GamepadButtons"
k_thm:  .asciz "GamepadSticks"
