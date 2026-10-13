/*
 * TimeShift Xbox 360 Gamepad Mod: dinput8.dll proxy.
 *
 * The game imports dinput8.dll, so this DLL is loaded before TimeShift.Exe starts running.
 * On load it:
 *   1. checks that the exe in memory is the supported build (every patched byte must match);
 *   2. writes the gamepad patches into the exe image in memory (the exe on disk is untouched);
 *   3. adds the mod's keys to the profile user.ini and gamepad bindings to controls.ini;
 * and then forwards every DirectInput call to the real system dinput8.dll.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string.h>
#include <stdio.h>
#include "patches.h"

typedef HRESULT (WINAPI *DI8Create_t)(HINSTANCE, DWORD, REFIID, LPVOID *, void *);
typedef HRESULT (WINAPI *Simple_t)(void);
typedef HRESULT (WINAPI *GetClassObject_t)(REFCLSID, REFIID, LPVOID *);
typedef LPCVOID (WINAPI *GetdfDIJoystick_t)(void);

static HMODULE g_real;
static int g_status;              /* 0 = not tried, 1 = patched, -1 = exe not supported */
static int g_warned;

static void load_real(void)
{
    char path[MAX_PATH];
    if (g_real) return;
    GetSystemDirectoryA(path, MAX_PATH);
    strcat(path, "\\dinput8.dll");
    g_real = LoadLibraryA(path);
}

static FARPROC real_proc(const char *name)
{
    load_real();
    return g_real ? GetProcAddress(g_real, name) : NULL;
}

/* ---------------------------------------------------------------- exe patches */

/* 1 = every patch already in place (an exe that was patched on disk), 0 otherwise */
static int already_patched(void)
{
    unsigned i;
    for (i = 0; i < NPATCHES; i++) {
        MEMORY_BASIC_INFORMATION mbi;
        const void *p = (const void *)(ULONG_PTR)PATCHES[i].va;
        if (!VirtualQuery(p, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT) return 0;
        if (memcmp(p, PATCHES[i].new_, PATCHES[i].len) != 0) return 0;
    }
    return 1;
}

static int apply_patches(void)
{
    unsigned i;
    DWORD old;
    if (already_patched()) return 1;
    for (i = 0; i < NPATCHES; i++) {
        MEMORY_BASIC_INFORMATION mbi;
        const void *p = (const void *)(ULONG_PTR)PATCHES[i].va;
        if (!VirtualQuery(p, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT) return 0;
        if (memcmp(p, PATCHES[i].old_, PATCHES[i].len) != 0) return 0;
    }
    for (i = 0; i < NPATCHES; i++) {
        void *p = (void *)(ULONG_PTR)PATCHES[i].va;
        VirtualProtect(p, PATCHES[i].len, PAGE_EXECUTE_READWRITE, &old);
        memcpy(p, PATCHES[i].new_, PATCHES[i].len);
        VirtualProtect(p, PATCHES[i].len, old, &old);
    }
    FlushInstructionCache(GetCurrentProcess(), NULL, 0);
    return 1;
}

/* ---------------------------------------------------------------- config files */

static char *read_file(const char *path, DWORD *size)
{
    HANDLE h = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    char *buf;
    DWORD n = 0;
    if (h == INVALID_HANDLE_VALUE) return NULL;
    *size = GetFileSize(h, NULL);
    buf = (char *)HeapAlloc(GetProcessHeap(), 0, *size + 1);
    if (buf && !ReadFile(h, buf, *size, &n, NULL)) n = 0;
    CloseHandle(h);
    if (!buf) return NULL;
    buf[n] = 0;
    *size = n;
    return buf;
}

static int write_file(const char *path, const char *data, DWORD size)
{
    HANDLE h = CreateFileA(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, 0, NULL);
    DWORD n = 0;
    if (h == INVALID_HANDLE_VALUE) return 0;
    WriteFile(h, data, size, &n, NULL);
    CloseHandle(h);
    return n == size;
}

static void backup_once(const char *path)
{
    char bak[MAX_PATH + 16];
    snprintf(bak, sizeof bak, "%s.before_gamepad_mod", path);
    CopyFileA(path, bak, TRUE);   /* TRUE: never overwrite an existing backup */
}

/* user.ini: flat "key = value" lines.
 * The mod's keys are added when missing. On the mod's first run in a profile (LookSensitivity missing,
 * or 0 because the game saved an empty slider) the stick settings are reset to defaults and the
 * time-control radial menu (TimeShortcuts, LB) is switched on, since the PC default is No. */
static const char *USER_KEYS[][2] = {
    {"LookSensitivity", "100"}, {"InvertLookY", "no"}, {"MoveSensitivity", "100"},
    {"DeadZone", "22"}, {"Vibration", "yes"},
    {"GamepadButtons", "\"1\""}, {"GamepadSticks", "\"1\""}, {"TimeShortcuts", "yes"},
};
#define NUSER_KEYS (sizeof USER_KEYS / sizeof USER_KEYS[0])

/* returns pointer to the value of `key` on its own line, or NULL */
static const char *ini_find(const char *txt, const char *key)
{
    size_t kl = strlen(key);
    const char *s = txt;
    while ((s = strstr(s, key)) != NULL) {
        if ((s == txt || s[-1] == '\n') && (s[kl] == ' ' || s[kl] == '=' || s[kl] == '\t')) {
            s += kl;
            while (*s == ' ' || *s == '\t' || *s == '=') s++;
            return s;
        }
        s += kl;
    }
    return NULL;
}

static void ensure_user_ini(const char *path)
{
    DWORD size, i;
    char *txt = read_file(path, &size), *out, *line;
    size_t len = 0;
    const char *v;
    int first, changed = 0;
    if (!txt) return;     /* first start: the game creates the file, the mod uses defaults */
    v = ini_find(txt, "LookSensitivity");
    first = !v || atof(v) < 10.0;
    out = (char *)HeapAlloc(GetProcessHeap(), 0, size + 1024);
    for (line = txt; *line; ) {
        char *eol = strchr(line, '\n');
        size_t ll = eol ? (size_t)(eol - line + 1) : strlen(line);
        int replaced = 0;
        if (first) {
            for (i = 0; i < NUSER_KEYS; i++) {
                const char *k = USER_KEYS[i][0];
                size_t kl = strlen(k);
                if (!strncmp(line, k, kl) && (line[kl] == ' ' || line[kl] == '=' || line[kl] == '\t')) {
                    len += sprintf(out + len, "%s = %s\r\n", k, USER_KEYS[i][1]);
                    replaced = changed = 1;
                    break;
                }
            }
        }
        if (!replaced) { memcpy(out + len, line, ll); len += ll; }
        line += ll;
    }
    for (i = 0; i < NUSER_KEYS; i++) {
        if (!ini_find(txt, USER_KEYS[i][0])) {
            if (len && out[len - 1] != '\n') { out[len++] = '\r'; out[len++] = '\n'; }
            len += sprintf(out + len, "%s = %s\r\n", USER_KEYS[i][0], USER_KEYS[i][1]);
            changed = 1;
        }
    }
    if (changed) { backup_once(path); write_file(path, out, (DWORD)len); }
    HeapFree(GetProcessHeap(), 0, out);
    HeapFree(GetProcessHeap(), 0, txt);
}

/*
 * controls.ini: every command has 5 slots "{ codes }". The mod puts the gamepad codes in slot 1,
 * keeps the keyboard and mouse slots, and drops the old joystick ones.
 * Virtual buttons 0x112+i and virtual axes are remapped by the button and stick presets in the exe.
 */
#define VB(i) (0x112 + (i))
enum { A_ = VB(0), B_ = VB(1), X_ = VB(2), Y_ = VB(3), LB_ = VB(4), RB_ = VB(5), LS_ = VB(8), RS_ = VB(9),
       BACK_ = 0x10E, START_ = 0x10F, PA_ = 0x108, LT_ = 0x136, RT_ = 0x137,
       VLXp = 0x13C, VLXn = 0x13D, VLYp = 0x13E, VLYn = 0x13F, VRXp = 0x140, VRXn = 0x141, VRYp = 0x146, VRYn = 0x147,
       DU = 0x142, DD = 0x143, DR = 0x144, DL = 0x145 };
static const struct bind { const char *name; int s1[2]; int s5; } BINDS[] = {
    {"MOVE_FORWARD", {VLYn}}, {"MOVE_BACKWARD", {VLYp}}, {"MOVE_LEFT", {VLXn}}, {"MOVE_RIGHT", {VLXp}},
    {"ROTATE_LEFT", {VRXn}}, {"ROTATE_RIGHT", {VRXp}}, {"LOOK_UP", {VRYn}}, {"LOOK_DOWN", {VRYp}},
    {"JUMP", {A_}}, {"CROUCH", {LS_}}, {"USE", {X_}}, {"FORCE_RECHARGE", {X_}},
    {"UI", {START_}}, {"STOP_CINEMATIC", {START_}, PA_}, {"SHOWFRAGS", {BACK_}},
    {"UI_UP", {DU}}, {"UI_DOWN", {DD}}, {"UI_ACTION", {PA_}},
    {"WPN_NEXT", {Y_}, DR}, {"WPN_PREV", {DL}}, {"NEXT_GRENADE", {DD}},
    {"ATTACK_1", {RT_}}, {"ATTACK_2", {LT_}}, {"ATTACK_3", {B_}}, {"MINIZOOM", {RS_}},
    {"ACTIVATE_TIME_AUTO", {LB_}}, {"ACTIVATE_SLOW_MOTION", {LB_, X_}}, {"ACTIVATE_TIME_FREEZE", {LB_, Y_}},
    {"ACTIVATE_TIME_REVERSAL", {LB_, B_}}, {"ACTIVATE_TIME_CANCEL", {LB_, A_}},
    {"ACTIVATE_GREN_AUTO", {RB_}}, {"ACTIVATE_GREN_STICKY", {RB_, X_}}, {"ACTIVATE_GREN_WASP", {RB_, Y_}},
    {"ACTIVATE_GREN_MINE", {RB_, A_}}, {"ACTIVATE_GREN_LASER_MINE", {RB_, B_}},
    {"BIKE_FORW", {RT_}}, {"BIKE_BACK", {LT_}}, {"BIKE_BOOST", {A_}},
};

static int is_joy(int c) { return (c >= 0x108 && c <= 0x123) || (c >= 0x132 && c <= 0x153); }

/* slot text "{ 0x1 0x2 }" -> 1 if it holds only joystick codes (or nothing) */
static int slot_is_joy_or_empty(const char *s, const char *e)
{
    int any = 0;
    while (s < e) {
        if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) {
            char *end;
            long c = strtol(s, &end, 16);
            if (!is_joy((int)c)) return 0;
            any = 1;
            s = end;
        } else s++;
    }
    (void)any;
    return 1;
}

static int fmt_slot(char *o, const int *codes, int n)
{
    int k, len = sprintf(o, "{ ");
    for (k = 0; k < n; k++) if (codes[k]) len += sprintf(o + len, "0x%X ", codes[k]);
    return len + sprintf(o + len, "}");
}

static void patch_controls(const char *path)
{
    DWORD size;
    char *txt = read_file(path, &size), *out, *line;
    size_t len = 0;
    if (!txt) return;
    if (strstr(txt, "0x112 }") || strstr(txt, "0x112 0x")) {   /* already has the mod's bindings */
        HeapFree(GetProcessHeap(), 0, txt);
        return;
    }
    out = (char *)HeapAlloc(GetProcessHeap(), 0, size * 2 + 4096);
    line = txt;
    while (*line) {
        char *eol = strchr(line, '\n'), *p = line, *q;
        size_t ll = eol ? (size_t)(eol - line + 1) : strlen(line);
        const struct bind *b = NULL;
        unsigned i;
        while (*p == ' ' || *p == '\t') p++;
        for (i = 0; i < sizeof BINDS / sizeof BINDS[0]; i++) {
            size_t nl = strlen(BINDS[i].name);
            if (!strncmp(p, BINDS[i].name, nl) && (p[nl] == ' ' || p[nl] == '\t' || p[nl] == '=')) { b = &BINDS[i]; break; }
        }
        q = b ? memchr(p, '"', ll - (p - line)) : NULL;
        if (b && q) {
            /* collect the keyboard/mouse slots to keep */
            const char *keep[3][2];
            int nk = 0, k;
            char *s = q + 1, *lend = line + ll;
            while (s < lend) {
                char *o = memchr(s, '{', lend - s), *c;
                if (!o) break;
                c = memchr(o, '}', lend - o);
                if (!c) break;
                if (!slot_is_joy_or_empty(o + 1, c) && nk < 3) { keep[nk][0] = o; keep[nk][1] = c + 1; nk++; }
                s = c + 1;
            }
            memcpy(out + len, line, q - line + 1);
            len += q - line + 1;
            out[len++] = ' ';
            len += fmt_slot(out + len, b->s1, 2);
            for (k = 0; k < 3; k++) {
                out[len++] = ' ';
                if (k < nk) { memcpy(out + len, keep[k][0], keep[k][1] - keep[k][0]); len += keep[k][1] - keep[k][0]; }
                else len += sprintf(out + len, "{ }");
            }
            out[len++] = ' ';
            len += fmt_slot(out + len, &b->s5, 1);
            len += sprintf(out + len, "\"%s", (eol && eol > line && eol[-1] == '\r') ? "\r\n" : (eol ? "\n" : ""));
        } else {
            memcpy(out + len, line, ll);
            len += ll;
        }
        line += ll;
    }
    backup_once(path);
    write_file(path, out, (DWORD)len);
    HeapFree(GetProcessHeap(), 0, out);
    HeapFree(GetProcessHeap(), 0, txt);
}

static void setup_configs(void)
{
    char exe[MAX_PATH], dir[MAX_PATH], ini[MAX_PATH], folder[MAX_PATH], name[MAX_PATH], prof[MAX_PATH * 2], f[MAX_PATH * 2];
    char *s;
    GetModuleFileNameA(NULL, exe, MAX_PATH);
    strcpy(dir, exe);
    s = strrchr(dir, '\\');
    if (s) s[1] = 0;
    snprintf(ini, sizeof ini, "%ssteamwars.ini", dir);
    GetPrivateProfileStringA("Profile", "Folder", "..\\UserConfigs\\", folder, MAX_PATH, ini);
    GetPrivateProfileStringA("Profile", "Name", "Default", name, MAX_PATH, ini);
    snprintf(prof, sizeof prof, "%s%s%s%s\\", dir, folder,
             (folder[0] && folder[strlen(folder) - 1] != '\\') ? "\\" : "", name);
    snprintf(f, sizeof f, "%scontrols.ini", dir);   patch_controls(f);   /* defaults for new profiles */
    snprintf(f, sizeof f, "%scontrols.ini", prof);  patch_controls(f);
    snprintf(f, sizeof f, "%suser.ini", dir);       ensure_user_ini(f);   /* defaults for new profiles */
    snprintf(f, sizeof f, "%suser.ini", prof);      ensure_user_ini(f);
}

/* ---------------------------------------------------------------- entry points */

static void init_mod(void)
{
    if (g_status) return;
    g_status = apply_patches() ? 1 : -1;
    if (g_status == 1) setup_configs();
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, LPVOID reserved)
{
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(inst);
        if (apply_patches()) { g_status = 1; setup_configs(); }
        /* otherwise retry on the first DirectInput8Create (e.g. the exe was still packed) */
    }
    return TRUE;
}

HRESULT WINAPI DirectInput8Create(HINSTANCE h, DWORD ver, REFIID riid, LPVOID *out, void * outer)
{
    DI8Create_t fn = (DI8Create_t)real_proc("DirectInput8Create");
    init_mod();
    if (g_status < 0 && !g_warned) {
        g_warned = 1;
        MessageBoxA(NULL,
            "TimeShift Gamepad Mod: this TimeShift.Exe is not supported, the gamepad patches were not applied.\n\n"
            "Use the multi-core fix exe v1.2 (see README). The game will start without the mod.",
            "TimeShift Gamepad Mod", MB_OK | MB_ICONWARNING);
    }
    return fn ? fn(h, ver, riid, out, outer) : E_FAIL;
}

HRESULT WINAPI DllCanUnloadNow(void)       { Simple_t f = (Simple_t)real_proc("DllCanUnloadNow"); return f ? f() : S_FALSE; }
HRESULT WINAPI DllRegisterServer(void)     { Simple_t f = (Simple_t)real_proc("DllRegisterServer"); return f ? f() : E_FAIL; }
HRESULT WINAPI DllUnregisterServer(void)   { Simple_t f = (Simple_t)real_proc("DllUnregisterServer"); return f ? f() : E_FAIL; }
HRESULT WINAPI DllGetClassObject(REFCLSID c, REFIID r, LPVOID *o)
{
    GetClassObject_t f = (GetClassObject_t)real_proc("DllGetClassObject");
    return f ? f(c, r, o) : CLASS_E_CLASSNOTAVAILABLE;
}
LPCVOID WINAPI GetdfDIJoystick(void)       { GetdfDIJoystick_t f = (GetdfDIJoystick_t)real_proc("GetdfDIJoystick"); return f ? f() : NULL; }
