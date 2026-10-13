.intel_syntax noprefix
.globl _start
_start:                          # VA 0xd10400, hook of GetName(code, outbuf) @0x786700
    mov  eax, [esp+4]
    push ecx
    mov  ecx, 0xd10e45
    call ecx
    pop  ecx
    mov  edx, offset table
1:  cmp  dword ptr [edx], 0
    je   orig
    cmp  [edx], eax
    je   found
    add  edx, 8
    jmp  1b
found:
    push esi
    push edi
    mov  esi, [edx+4]
    mov  edi, [esp+0x10]
2:  mov  cx, [esi]
    mov  [edi], cx
    add  esi, 2
    add  edi, 2
    test cx, cx
    jnz  2b
    pop  edi
    pop  esi
    mov  eax, 1
    ret  8
orig:
    push ebp
    mov  ebp, esp
    and  esp, -8
    push 0x786706
    ret
.align 4
table:
    .long 0x108, str0
    .long 0x109, str1
    .long 0x10a, str2
    .long 0x10b, str3
    .long 0x10c, str4
    .long 0x10d, str5
    .long 0x10e, str6
    .long 0x10f, str7
    .long 0x110, str8
    .long 0x111, str9
    .long 0x136, str10
    .long 0x137, str11
    .long 0x132, str12
    .long 0x133, str13
    .long 0x134, str14
    .long 0x135, str15
    .long 0x138, str16
    .long 0x139, str17
    .long 0x13a, str18
    .long 0x13b, str19
    .long 0x142, str20
    .long 0x143, str21
    .long 0x144, str22
    .long 0x145, str23
    .long 0, 0
str0: .short 192,0
str1: .short 193,0
str2: .short 196,0
str3: .short 200,0
str4: .short 198,0
str5: .short 338,0
str6: .short 210,0
str7: .short 211,0
str8: .short 214,0
str9: .short 217,0
str10: .short 201,0
str11: .short 209,0
str12: .short 214,0
str13: .short 214,0
str14: .short 214,0
str15: .short 214,0
str16: .short 217,0
str17: .short 217,0
str18: .short 217,0
str19: .short 217,0
str20: .short 218,0
str21: .short 218,0
str22: .short 218,0
str23: .short 218,0
