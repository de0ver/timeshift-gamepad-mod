.intel_syntax noprefix
.set G_INP, 0x10e0f3c
.set G_KP,  0x10e0f40
.set G_KB,  0x10e0f44
.globl _start
_start:                         # VA 0xd10c50 ; hook of sorted-table lookup 0x691210(tbl, &key, ctx)
    mov  eax, [esp]               # skip string-table loader callers (add/replace/find while parsing)
    cmp  eax, 0x68f2a7
    je   orig
    cmp  eax, 0x68f370
    je   orig
    cmp  eax, 0x690077
    je   orig
    cmp  eax, 0x6902a6
    je   orig
    mov  eax, [esp+8]
    mov  eax, [eax]
    test eax, eax
    jz   orig
    cmp  word ptr [eax], 0x4955   # "UI"
    jne  orig
    push ecx
    push edx
    mov  edx, eax
1:  cmp  byte ptr [edx], 0
    je   2f
    inc  edx
    jmp  1b
2:  mov  ecx, edx
    sub  ecx, eax                 # len
    cmp  ecx, 8
    jb   done
    cmp  ecx, 0x60
    ja   done
    mov  edx, [edx-4]
    and  edx, 0x00ffffff
    cmp  edx, 0x50475f            # "_GP"
    jne  done
    mov  edx, [G_INP]             # pad present? keep _GPx key (has icon)
    test edx, edx
    jz   done                     # input not created yet (string tables loading): leave keys alone
    cmp  dword ptr [edx+0x1bbc], 0
    jne  done
strip:
    sub  ecx, 4
    push esi
    push edi
    mov  esi, eax
    mov  edi, G_KB
    rep  movsb
    mov  byte ptr [edi], 0
    pop  edi
    pop  esi
    mov  dword ptr [G_KP], G_KB
    mov  dword ptr [esp+0x10], G_KP   # replace &key arg (2 pushes + ret)
done:
    pop  edx
    pop  ecx
orig:
    push ebx
    push ebp
    mov  ebp, [esp+0xc]
    push 0x691216
    ret
