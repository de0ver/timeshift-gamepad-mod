#!/bin/sh
# Builds dinput8.dll (32-bit) with zig's bundled MinGW toolchain: pip install ziglang
set -e
cd "$(dirname "$0")"
mkdir -p dist/bin
python3 -m ziglang cc -target x86-windows-gnu -O2 -shared -s \
    -o dist/bin/dinput8.dll src/dinput8_proxy.c src/dinput8.def -lkernel32 -luser32
