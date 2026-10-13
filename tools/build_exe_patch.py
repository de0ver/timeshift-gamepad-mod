"""
Assemble asm/*.s and write them into a clean TimeShift.Exe (multi-core fix v1.2, 11431936 bytes).

usage: python3 tools/build_exe_patch.py <clean TimeShift.Exe> [patched.exe]

Always regenerates src/patches.h (the table dinput8.dll writes into memory).
The optional patched.exe is only for debugging; the mod itself never ships an exe.
Needs GNU binutils with i386 support (as, ld, objcopy).
"""
import os, struct, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOBS = [('consts', 0xd10300), ('getname', 0xd10400), ('frame', 0xd10600), ('strkey', 0xd10c50), ('remap', 0xd10d00)]

def assemble(name, va):
    t = tempfile.mkdtemp()
    o, e, b = (os.path.join(t, name + x) for x in ('.o', '.elf', '.bin'))
    subprocess.check_call(['as', '--32', os.path.join(ROOT, 'asm', name + '.s'), '-o', o])
    subprocess.check_call(['ld', '-m', 'elf_i386', '-Ttext=0x%x' % va, '-e', '_start', o, '-o', e])
    subprocess.check_call(['objcopy', '-O', 'binary', '-j', '.text', e, b])
    return open(b, 'rb').read()

def jmp(src, dst, total):
    return b'\xE9' + struct.pack('<i', dst - (src + 5)) + b'\x90' * (total - 5)

def main():
    src = sys.argv[1]
    d = bytearray(open(src, 'rb').read())
    assert len(d) == 11431936, 'unexpected exe size, need the multi-core fix exe v1.2'
    o = lambda va: va - 0x400000
    def put(va, data, expect=None):
        if expect is not None:
            assert d[o(va):o(va) + len(expect)] == expect, 'signature mismatch at 0x%x' % va
        else:
            assert not any(d[o(va):o(va) + len(data)]), 'cave not empty at 0x%x' % va
        d[o(va):o(va) + len(data)] = data
    blobs = {n: assemble(n, va) for n, va in BLOBS}
    for (n, va), (n2, va2) in zip(BLOBS, BLOBS[1:] + [('end', 0xd11000)]):
        assert va + len(blobs[n]) <= va2, '%s overflows into %s' % (n, n2)
        put(va, blobs[n])
    # hooks
    put(0x785fe0, jmp(0x785fe0, 0xd10600, 6), bytes.fromhex('538b5c240855'))      # input frame update
    put(0x786700, jmp(0x786700, 0xd10400, 6), bytes.fromhex('558bec83e4f8'))      # key/button GetName
    put(0x691210, jmp(0x691210, 0xd10c50, 6), bytes.fromhex('53558b6c240c'))      # string-table lookup
    put(0xdb70b4, struct.pack('<I', 0xd10d00), struct.pack('<I', 0x7bcce0))       # joystick poll vtable slot
    # stick axis scale loads -> mod's sensitivity globals
    for va, const in [(0x7bcd4c, 0x10e0f00), (0x7bcd78, 0x10e0f00), (0x7bcd9c, 0xd103a0), (0x7bcdc0, 0x10e0f04), (0x7bcde4, 0x10e0f08)]:
        put(va, bytes.fromhex('f30f101d') + struct.pack('<I', const), bytes.fromhex('f30f109ec01b0000'))
    # menu commands: add gamepad alternatives (entries 0x84 bytes, alt count @+0x40, alts stride 0x10 @+0x44)
    A, B, START = 0x108, 0x109, 0x10F
    for e, name, codes in [(0xec1e14, b'LEFT', [0x145, 0x133]), (0xec1e98, b'RIGHT', [0x144, 0x132]),
                           (0xec1f1c, b'UP', [0x142, 0x135]), (0xec1fa0, b'DOWN', [0x143, 0x134]),
                           (0xec2234, b'ENTER', [A]), (0xec22b8, b'ESC', [B, START])]:
        assert d[o(e):o(e) + len(name) + 1] == name + b'\0'
        n = struct.unpack_from('<I', d, o(e) + 0x40)[0]
        for c in codes:
            assert n < 4
            struct.pack_into('<4I', d, o(e) + 0x44 + n * 0x10, 1, c, 0, 0)
            n += 1
        struct.pack_into('<I', d, o(e) + 0x40, n)
    if len(sys.argv) > 2:
        pe = struct.unpack_from('<I', d, 0x3c)[0]; opt = struct.unpack_from('<H', d, pe + 20)[0]
        struct.pack_into('<I', d, pe + 24 + opt + 8, 0x910000)      # .text VirtualSize covers the caves
        open(sys.argv[2], 'wb').write(d)
    tmp = os.path.join(tempfile.mkdtemp(), 'p.exe')
    open(tmp, 'wb').write(d)
    subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'make_patches.py'), src, tmp,
                           os.path.join(ROOT, 'src', 'patches.h')])

if __name__ == '__main__':
    main()
