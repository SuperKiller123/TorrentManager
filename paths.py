# -*- coding: utf-8 -*-
"""Az alkalmazás program- és felhasználói adatmappáinak kezelése."""
import os
import sys
import shutil
from pathlib import Path

# Az exe vagy a Python-forrás telepítési mappája (csak olvasható állományok).
BASE=(Path(sys.executable) if getattr(sys,"frozen",False) else Path(__file__)).resolve().parent
# Helyi, felhasználónként elkülönített írható adattár, nem a Program Files.
local=os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME")
DATA_DIR=Path(local).expanduser()/"TorrentManager" if local else Path.home()/".torrentmanager"
SETTINGS=DATA_DIR/"beallitasok.json"
STATE=DATA_DIR/"kezelt_torrentek.json"
PROFILE=DATA_DIR/"bithumen_bongeszo_profil"
LOG=DATA_DIR/"automatizalas.log"

def migrate_old_data():
 """v0.1.x mappából egyszer, meglévő felhasználói adatok felülírása nélkül."""
 DATA_DIR.mkdir(parents=True,exist_ok=True)
 if BASE==DATA_DIR:
  return
 for name in ("beallitasok.json","kezelt_torrentek.json"):
  original=BASE/name
  target=DATA_DIR/name
  if original.is_file() and not target.exists():
   shutil.copy2(original,target)
 original=BASE/"bithumen_bongeszo_profil"
 if original.is_dir() and not PROFILE.exists():
  shutil.copytree(original,PROFILE)


def find_playwright_browsers():
    """Windows exe: csomagolt Chromium; szükség esetén felhasználói Playwright cache."""
    if not getattr(sys, "frozen", False):
        return None  # Fejlesztői futtatás: Playwright szokásos útvonalai.
    options = [BASE / "browsers"]
    localapp = os.environ.get("LOCALAPPDATA")
    if localapp:
        options.append(Path(localapp) / "ms-playwright")
    for path in options:
        if path.is_dir() and any(path.glob("chromium-*/chrome-win64/chrome.exe")):
            return path
    return None
