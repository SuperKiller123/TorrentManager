# -*- coding: utf-8 -*-
"""Felhasználónkénti Windows-indítás és opcionális qBittorrent indítás."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

RUN_NAME = "TorrentManager"

def set_windows_startup(enabled):
    if os.name != "nt":
        if enabled:
            raise OSError("Automatikus Windows-indítás csak Windows alatt állítható.")
        return
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
        if enabled:
            if not getattr(sys, "frozen", False):
                raise OSError("Automatikus indítást a telepített TorrentManager.exe esetén lehet bekapcsolni.")
            winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, f'"{Path(sys.executable).resolve()}"')
        else:
            try: winreg.DeleteValue(key, RUN_NAME)
            except FileNotFoundError: pass

def find_qbittorrent():
    choices = [shutil.which("qbittorrent.exe")]
    for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(variable)
        if base:
            choices.append(str(Path(base) / "qBittorrent" / "qbittorrent.exe"))
            choices.append(str(Path(base) / "Programs" / "qBittorrent" / "qbittorrent.exe"))
    return next((str(Path(p)) for p in choices if p and Path(p).is_file()), None)

def launch_qbittorrent():
    if os.name != "nt":
        raise OSError("A qBittorrent automatikus indítása jelenleg csak Windowsra készült.")
    result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq qbittorrent.exe", "/FO", "CSV", "/NH"],
                            capture_output=True, text=True,
                            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0), timeout=7)
    if '"qbittorrent.exe"' in result.stdout.lower():
        return False
    exe = find_qbittorrent()
    if not exe:
        raise FileNotFoundError("A qBittorrent.exe nem található a szokásos telepítési helyeken.")
    subprocess.Popen([exe], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True,
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return True
