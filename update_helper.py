# -*- coding: utf-8 -*-
"""Külön folyamatból végrehajtott csendes Inno Setup-frissítés.

A külső segéd a már ellenőrzött telepítőt indítja, majd csak siker esetén
indítja újra az alkalmazást. A Windows UAC felugró ablakát NEM kerüli meg.
"""
import os
import subprocess
import sys
from pathlib import Path


def run_elevated(installer, flags, timeout=900):
    """Elevate only Setup, wait for its real exit status; keep helper unelevated."""
    if os.name != 'nt':
        return subprocess.run([str(installer)] + flags, timeout=timeout).returncode
    import ctypes
    from ctypes import wintypes
    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [('cbSize',wintypes.DWORD),('fMask',wintypes.ULONG),('hwnd',wintypes.HWND),
            ('lpVerb',wintypes.LPCWSTR),('lpFile',wintypes.LPCWSTR),('lpParameters',wintypes.LPCWSTR),
            ('lpDirectory',wintypes.LPCWSTR),('nShow',ctypes.c_int),('hInstApp',wintypes.HINSTANCE),
            ('lpIDList',ctypes.c_void_p),('lpClass',wintypes.LPCWSTR),('hkeyClass',wintypes.HKEY),
            ('dwHotKey',wintypes.DWORD),('hIcon',wintypes.HANDLE),('hProcess',wintypes.HANDLE)]
    info = SHELLEXECUTEINFO()
    info.cbSize, info.fMask = ctypes.sizeof(info), 0x40
    info.lpVerb, info.lpFile = 'runas', str(installer)
    info.lpParameters, info.nShow = subprocess.list2cmdline(flags), 1
    shell, kernel = ctypes.WinDLL('shell32', use_last_error=True), ctypes.WinDLL('kernel32', use_last_error=True)
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(SHELLEXECUTEINFO)]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE,wintypes.DWORD]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    if not shell.ShellExecuteExW(ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if kernel.WaitForSingleObject(info.hProcess, timeout*1000) != 0:
            raise TimeoutError('Setup did not finish')
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(info.hProcess,ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value
    finally:
        kernel.CloseHandle(info.hProcess)


def wait_for_exit(pid, timeout=90):
    if os.name != 'nt':
        return
    import ctypes
    from ctypes import wintypes
    SYNCHRONIZE = 0x00100000
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(SYNCHRONIZE, False, pid)
    if handle:
        try:
            result = kernel.WaitForSingleObject(handle, timeout * 1000)
            if result != 0:
                raise TimeoutError('A korábbi Torrent Manager nem állt le.')
        finally:
            kernel.CloseHandle(handle)
    else:
        # Lehetséges, hogy a GUI már bezárult; a telepítő ennek ellenére
        # csak a saját konfigurációjával, kritikus hiba esetén megszakítva futhat.
        error = ctypes.get_last_error()
        if error not in (87,):  # ERROR_INVALID_PARAMETER = nincs ilyen PID
            raise OSError(error, 'Nem sikerült ellenőrizni a korábbi folyamatot.')


def main():
    if len(sys.argv) != 4:
        return 2
    installer, app, pid = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    logfile = installer.parent / 'utolso_frissites.log'
    try:
        wait_for_exit(pid)
        if not installer.is_file():
            raise FileNotFoundError(str(installer))
        flags = ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-',
                 '/CLOSEAPPLICATIONS', '/NORESTARTAPPLICATIONS', '/RESTARTEXITCODE=3010', f'/DIR={app.parent}',
                 f'/LOG={installer.parent / "inno_frissites.log"}']
        code = run_elevated(installer, flags)
        if code not in (0, 3010):
            raise RuntimeError(f'Telepítő kilépési kód: {code}')
        if code == 3010:
            logfile.write_text('Installation succeeded. Restart Windows before opening Torrent Manager.\n', encoding='utf-8')
            if os.name == 'nt':
                import ctypes
                ctypes.windll.user32.MessageBoxW(None, 'Installation succeeded. Please restart Windows.', 'Torrent Manager', 0x40)
            return 0
        if not app.exists():
            raise RuntimeError('A telepített alkalmazás nem található.')
        if app.suffix.lower() == '.py':
            subprocess.Popen([sys.executable, str(app)], cwd=str(app.parent))
        else:
            subprocess.Popen([str(app)], cwd=str(app.parent), close_fds=True)
        logfile.write_text('A frissítés sikeres.\n', encoding='utf-8')
        return 0
    except Exception as exc:
        try:
            logfile.write_text(f'Frissítési hiba: {exc}\n', encoding='utf-8')
        except OSError:
            pass
        # A cancelled UAC request or failed Setup must leave the existing app usable.
        try:
            if app.is_file() and not isinstance(exc, TimeoutError):
                command = [sys.executable, str(app)] if app.suffix.lower() == '.py' else [str(app)]
                subprocess.Popen(command, cwd=str(app.parent), close_fds=True)
            if os.name == 'nt':
                import ctypes
                ctypes.windll.user32.MessageBoxW(None, str(exc), 'Torrent Manager', 0x10)
        except OSError:
            pass
        return 1

if __name__ == '__main__':
    sys.exit(main())
