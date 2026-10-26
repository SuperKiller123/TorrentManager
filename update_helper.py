# -*- coding: utf-8 -*-
"""Külön folyamatból végrehajtott csendes Inno Setup-frissítés.

A külső segéd a már ellenőrzött telepítőt indítja, majd csak siker esetén
indítja újra az alkalmazást. A Windows UAC felugró ablakát NEM kerüli meg.
"""
import os
import subprocess
import sys
from pathlib import Path


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
                 '/CLOSEAPPLICATIONS',
                 f'/LOG={installer.parent / "inno_frissites.log"}']
        result = subprocess.run([str(installer)] + flags, timeout=900)
        if result.returncode != 0:
            raise RuntimeError(f'Telepítő kilépési kód: {result.returncode}')
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
        return 1

if __name__ == '__main__':
    sys.exit(main())
