.intel_syntax noprefix
.globl _start
_start:                         # VA 0xd10300
    push ebx                    # original 785aa0..785aa5
    mov  ebx, [esp+8]
    push ebp
    pushad
    cmp  dword ptr [ebx+0x3144], -1   # -1 = not tried yet
    jne  done
    mov  eax, [ebx+0x1804]      # IDirectInput8*
    test eax, eax
    jz   done
    mov  dword ptr [ebx+0x3144], -2   # mark: tried
    push 1                      # DIEDFL_ATTACHEDONLY
    push ebx                    # pvRef = this
    push 0x7bcee0               # game's own enum callback
    push 4                      # DI8DEVCLASS_GAMECTRL
    push eax
    mov  ecx, [eax]
    call dword ptr [ecx+0x10]   # EnumDevices
    cmp  dword ptr [ebx+0x3140], 0
    jle  done
    mov  dword ptr [ebx+0x3148], 0x3e6147ae   # deadzone 0.22f
    mov  edi, ebx
    xor  eax, eax               # device index 0
    mov  ecx, 0x7bca50
    call ecx                    # game's CreateJoystick(index)
    test eax, eax
    jz   done
    mov  eax, [ebx+0x1bbc]      # IDirectInputDevice8*
    test eax, eax
    jz   done
    push eax
    mov  ecx, [eax]
    call dword ptr [ecx+0x1c]   # Acquire
    or   dword ptr [ebx+4], 0xC # poll joystick (4) + joystick features (8)
    mov  ecx, ebx
    mov  eax, [ebx]
    call dword ptr [eax+0x84]   # XInput init (detect 360 pad, load xinput9_1_0)
    mov  ecx, ebx
    push 1
    mov  eax, [ebx]
    call dword ptr [eax+0x3c]   # enable vibration
done:
    popad
    push 0x785fe6
    ret

.org 0xa0
move_scale: .float 4.0
look_scale: .float 12.0
