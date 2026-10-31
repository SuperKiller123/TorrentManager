# Torrent Manager v0.8

Windowsos qBittorrent- és BitHuMen-kezelő. Részletes változások, bizonyított eredmények és nyitott korlátok: [TESZTELES-v0.8.md](TESZTELES-v0.8.md).

## Használat

A TorrentManager-Setup-v0.8.exe alapértelmezetten a Program Files/Torrent Manager mappába telepít, rendszergazdai jogosultsággal. Egyetlen nyelvválasztás határozza meg a program nyelvét; a telepítő egységesen angol. Az első indítás témázott, egyoldalas beállításánál add meg a WebUI-adatokat, letöltési mappát és korlátokat. A Mentés sikeres kapcsolatellenőrzést igényel.

Induláskor a program ellenőrzi a BitHuMen-munkamenetet; ha belépés szükséges, megnyitja a böngészőt. A jelszót a felhasználó írja be. Az automatizálás az Indítás gombbal indul. Az alapmód próbaüzem; módváltás a Beállításokban. A teljes mód saját nyilvántartott torrenteket és fájljaikat törölheti.

A Windowszal indulás, asztali parancsikon, háttérben futás, téma és nyelv a Beállításokban módosítható. A tálca-/Start-kitűzéshez a telepítő útmutatót kínál, a kitűzés felhasználói művelet. F11 kapcsolja a teljes képernyőt, Esc nem lép ki belőle.

A kiadáslista automatikusan betöltődik; a telepítés külön kérésre indul. Azonos verzió újratelepítésként jelenik meg. A frissítő SHA-256 ellenőrzést végez és menti a beállításokat.

## Adatok és eltávolítás

A saját adatok a %LOCALAPPDATA%/TorrentManager mappába kerülnek. Az örökölt WebUI-jelszó JSON-ban tárolódik, a forráscsomag nem tartalmaz felhasználói adatot. A torrentletöltéseknek külön, az alkalmazás saját könyvtárain kívüli mappát válassz.

Az eltávolító saját folyamatokra és saját program-/adatkönyvtárakra korlátozott takarítást végez. A torrentletöltési helyet, .torrent fájlokat és junction célokat megőrzi. Hozzáférési hiba vagy védett tartalom esetén jelentést ad. A régi per-user telepítések migrációja és a valódi offline Windows-profilok emelt jogosultságú takarítása még külön ellenőrzést igényel.

## Fejlesztés és fordítás

Python 3.13 és Inno Setup 6 szükséges. A build a requirements-tested.txt pontos verzióit használja:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-tested.txt
.\build-windows.ps1
```

A dist mappában készül a hordozható ZIP, az installer almappában a telepítő; mellettük SHA256SUMS.txt. A hordozható csomag is felhasználói AppData-mappát használ.

Teljes tesztfutás:

```powershell
$env:TM_GUI_TESTS='1'
$env:TM_BROWSER_TESTS='1'
$env:PLAYWRIGHT_BROWSERS_PATH=Join-Path $PWD '.browser-cache'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Külön próbák: tests/live_qb_smoke.py (üres külön qB-profil), tests/installer_lifecycle_v08.py (külön Inno AppId és próbaadatok), tests/frozen_smoke.py (EXE első indítás). A tesztkönyvtárakat ne tedd kiadásba. A forráscsomag engedélyezett fájltípusokból a package-source.ps1 segítségével készül.

A v0.8 helyi csomag; a GitHubra közzétételt ez a munkamenet nem végzi el. A teljes hibamentesség és minden Windows-környezet kompatibilitása nem igazolt.
