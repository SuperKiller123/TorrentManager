# -*- coding: utf-8 -*-
"""Windows UI controls: qBittorrent tray start and DWM frame colors."""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

RUN_NAME = 'TorrentManager'

def set_windows_startup(enabled):
    if os.name != 'nt':
        if enabled:
            raise OSError('Automatikus indítás csak Windows alatt.')
        return
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Run', 0,
            winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            winreg.DeleteValue(key, RUN_NAME)
        except FileNotFoundError:
            pass
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
        startup = Path(os.path.expandvars(winreg.QueryValueEx(key, 'Startup')[0]))
    _set_shortcut(startup / 'Torrent Manager.lnk', enabled, 'StartupShortcut')

def remove_legacy_windows_startup():
    set_windows_startup(False)

def find_qbittorrent():
    choices = [shutil.which('qbittorrent.exe')]
    for variable in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
        base = os.environ.get(variable)
        if base:
            choices.extend((str(Path(base) / 'qBittorrent' / 'qbittorrent.exe'),
                            str(Path(base) / 'Programs' / 'qBittorrent' / 'qbittorrent.exe')))
    return next((str(Path(p)) for p in choices if p and Path(p).is_file()), None)

def qb_tray_enabled(config_path=None):
    """Read only the tray setting; never alter the user's qBittorrent profile."""
    import configparser
    if config_path is None:
        base = os.environ.get('APPDATA')
        if not base:
            return False
        config_path = Path(base) / 'qBittorrent' / 'qBittorrent.ini'
    try:
        config = configparser.ConfigParser(interpolation=None, strict=False)
        with Path(config_path).open(encoding='utf-8-sig') as stream:
            config.read_file(stream)
        # qBittorrent's upstream default is true; a missing/unreadable profile is
        # deliberately not assumed to have created its notification icon yet.
        return config.getboolean('Preferences', r'General\SystrayEnabled', fallback=True)
    except (OSError, ValueError, configparser.Error):
        return False


def minimize_pid_windows(pid, to_tray=False):
    """Hide only our newly started qB main window; never close/terminate qB.

Hiding gives the requested notification-area behavior even when CloseToTray is
disabled. With no tray enabled, keep the accessible minimized taskbar window.
"""
    if os.name != 'nt':
        return 0
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetWindow.restype = wintypes.HWND
    count = 0
    def visit(hwnd, _):
        nonlocal count
        owner = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        title = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title, len(title))
        if (owner.value == pid and user32.IsWindowVisible(hwnd)
                and 'qbittorrent' in title.value.lower() and not user32.GetWindow(hwnd, 4)):
            # SW_HIDE cannot quit the process (WM_CLOSE can). Leave owned modal
            # dialogs, legal notices and unrelated windows available to the user.
            user32.ShowWindow(hwnd, 0 if to_tray else 6)
            count += 1
        return True
    user32.EnumWindows(callback_type(visit), 0)
    return count

def launch_qbittorrent():
    if os.name != 'nt':
        raise OSError('A qBittorrent háttérindítása Windowsra készült.')
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq qbittorrent.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=7)
    if '"qbittorrent.exe"' in result.stdout.lower():
        return False
    exe = find_qbittorrent()
    if not exe:
        raise FileNotFoundError('A qBittorrent.exe nem található.')
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = 7  # SW_SHOWMINNOACTIVE
    proc = subprocess.Popen([exe], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, close_fds=True, startupinfo=info,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    # qBittorrent/Qt may ignore the startup hint and restore a maximized window later.
    # Re-minimize only this newly launched process for its first few seconds.
    for _ in range(14):
        if proc.poll() is not None:
            break
        time.sleep(0.45)
        minimize_pid_windows(proc.pid, to_tray=qb_tray_enabled())
    return True

def apply_windows_titlebar(root, dark, background, show_icon=False):
    """Match Windows 10/11 native titlebar/buttons to the application theme."""
    if os.name != 'nt':
        return
    try:
        import ctypes
        from ctypes import wintypes
        root.update_idletasks()
        ctypes.windll.user32.GetParent.argtypes = [wintypes.HWND]
        ctypes.windll.user32.GetParent.restype = wintypes.HWND
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
        user = ctypes.windll.user32
        getter = user.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user.GetWindowLongW
        setter = user.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user.SetWindowLongW
        getter.argtypes = [wintypes.HWND, ctypes.c_int]
        getter.restype = ctypes.c_ssize_t
        setter.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
        setter.restype = ctypes.c_ssize_t
        style = getter(hwnd, -20)
        # A dialog-style native caption keeps Windows resize/snap/system buttons
        # while suppressing the small caption icon. Unlike theme hints this works
        # on modern DWM captions, too. The executable keeps its taskbar branding.
        setter(hwnd, -20, style & ~1 if show_icon else style | 1)
        user.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user.SendMessageW.restype = ctypes.c_ssize_t
        if show_icon:
            for size, icon in getattr(root, '_caption_icons', {}).items():
                if icon:
                    user.SendMessageW(hwnd, 0x80, size, icon)  # WM_SETICON
            root._caption_icons = {}
        else:
            saved = getattr(root, '_caption_icons', {})
            if not getattr(root, '_blank_caption_icon', None):
                user.CreateIcon.argtypes = [wintypes.HINSTANCE, ctypes.c_int, ctypes.c_int,
                                           ctypes.c_byte, ctypes.c_byte, ctypes.c_void_p, ctypes.c_void_p]
                user.CreateIcon.restype = wintypes.HICON
                and_mask = (ctypes.c_ubyte * 32)(*([255] * 32))
                xor_mask = (ctypes.c_ubyte * 32)()
                root._blank_caption_icon = user.CreateIcon(None, 16, 16, 1, 1, and_mask, xor_mask)
            for size in (0,):
                previous = user.SendMessageW(hwnd, 0x80, size, root._blank_caption_icon)
                if previous and previous != root._blank_caption_icon:
                    saved[size] = previous
            root._caption_icons = saved
        user.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                      ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        user.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x37)  # FRAMECHANGED|NOACTIVATE|NOMOVE|NOSIZE|NOZORDER
        dwm = ctypes.windll.dwmapi
        # Suppress the native small Tk feather without removing taskbar branding.
        class WTA_OPTIONS(ctypes.Structure):
            _fields_ = [('dwFlags', wintypes.DWORD), ('dwMask', wintypes.DWORD)]
        options = WTA_OPTIONS(0 if show_icon else 2, 2)  # WTNCA_NODRAWICON
        ctypes.windll.uxtheme.SetWindowThemeAttribute(wintypes.HWND(hwnd), 1,
            ctypes.byref(options), ctypes.sizeof(options))
        flag = ctypes.c_int(1 if dark else 0)
        for attr in (20, 19):
            if dwm.DwmSetWindowAttribute(wintypes.HWND(hwnd), attr, ctypes.byref(flag), ctypes.sizeof(flag)) == 0:
                break
        col = background.lstrip('#')
        red, green, blue = (int(col[i:i+2], 16) for i in (0, 2, 4))
        color = ctypes.c_uint(red | (green << 8) | (blue << 16))
        dwm.DwmSetWindowAttribute(wintypes.HWND(hwnd), 35, ctypes.byref(color), ctypes.sizeof(color))
        text = ctypes.c_uint(0xFFFFFF if dark else 0x202020)
        dwm.DwmSetWindowAttribute(wintypes.HWND(hwnd), 36, ctypes.byref(text), ctypes.sizeof(text))
    except (OSError, ValueError, AttributeError):
        pass  # older Windows versions may not support colored caption


def set_desktop_shortcut(enabled):
    if os.name != 'nt':
        if enabled:
            raise OSError('Windows required')
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
        desktop = Path(os.path.expandvars(winreg.QueryValueEx(key, 'Desktop')[0]))
    _set_shortcut(desktop / 'Torrent Manager.lnk', enabled, 'DesktopShortcut')


def _set_shortcut(shortcut, enabled, setting):
    import configparser
    from paths import DATA_DIR
    record = DATA_DIR / 'windows.ini'
    ini = configparser.ConfigParser(interpolation=None)
    ini.optionxform = str
    ini.read(record, encoding='utf-8')
    if not ini.has_section('Windows'):
        ini.add_section('Windows')
    previous = ini.get('Windows', setting, fallback='')
    if previous and previous != str(shortcut) and Path(previous).name == 'Torrent Manager.lnk':
        Path(previous).unlink(missing_ok=True)
    if not enabled:
        shortcut.unlink(missing_ok=True)
    else:
        if not getattr(sys, 'frozen', False):
            raise OSError('Shortcut requires an installed application')
        shortcut.parent.mkdir(parents=True, exist_ok=True)
        script = "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:TM_SHORTCUT);$s.TargetPath=$env:TM_TARGET;$s.Save()"
        env = dict(os.environ, TM_SHORTCUT=str(shortcut), TM_TARGET=sys.executable)
        subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script], check=True, env=env,
                        creationflags=subprocess.CREATE_NO_WINDOW)
    ini.set('Windows',setting,str(shortcut) if enabled else '')
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with record.open('w', encoding='utf-8') as stream:
        ini.write(stream)


class FullscreenController:
    def __init__(self, root, repaint):
        self.root, self.repaint = root, repaint
        self.active = False
        self.previous = None

    def toggle(self):
        root = self.root
        if not self.active:
            self.previous = root.state(), root.geometry()
            root.update_idletasks()
            if os.name == 'nt':
                import ctypes
                from ctypes import wintypes
                class MONITORINFO(ctypes.Structure):
                    _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT),
                                ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]
                user = ctypes.WinDLL('user32', use_last_error=True)
                user.GetParent.argtypes = [wintypes.HWND]
                user.GetParent.restype = wintypes.HWND
                user.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
                user.MonitorFromWindow.restype = wintypes.HANDLE
                user.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]
                hwnd = user.GetParent(root.winfo_id()) or root.winfo_id()
                monitor = user.MonitorFromWindow(hwnd, 2)
                info = MONITORINFO()
                info.cbSize = ctypes.sizeof(info)
                if not user.GetMonitorInfoW(monitor, ctypes.byref(info)):
                    raise ctypes.WinError()
                rect = info.rcMonitor
                root.state('normal')
                root.overrideredirect(True)
                root.geometry(f'{rect.right-rect.left}x{rect.bottom-rect.top}+0+0')
                root.update_idletasks()
                # Tk interprets -x/-y as distance from the screen's far edge,
                # whereas secondary monitors may have negative absolute origins.
                # SetWindowPos accepts the monitor's signed desktop coordinates.
                hwnd = user.GetParent(root.winfo_id()) or root.winfo_id()
                user.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                    ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
                user.SetWindowPos.restype = wintypes.BOOL
                if not user.SetWindowPos(hwnd, None, rect.left, rect.top,
                        rect.right-rect.left, rect.bottom-rect.top, 0x24):
                    root.overrideredirect(False)
                    root.geometry(self.previous[1])
                    root.state(self.previous[0])
                    raise ctypes.WinError()
                root.lift()
            else:
                root.attributes('-fullscreen', True)
            self.active = True
        else:
            if os.name == 'nt':
                root.overrideredirect(False)
                root.geometry(self.previous[1])
                root.state(self.previous[0])
            else:
                root.attributes('-fullscreen', False)
            self.active = False
            root.after(80, self.repaint)
