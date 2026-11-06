# Torrent Manager v1.0 (fejlesztői forrás)

Windowsos qBittorrent- és BitHuMen-kezelő. A v1.0 új kezdőlapot, átrendezett Alkalmazás fület, értesítési területi vezérlést és egyszerűbb telepítőt tartalmaz.

## Használat

A TorrentManager-Setup-v1.0.exe alapértelmezetten a Program Files/Torrent Manager mappába telepít, rendszergazdai jogosultsággal. A nyelvválasztás a telepítő és a program nyelvét is meghatározza. Az első indítás témázott, egyoldalas beállításánál add meg a WebUI-adatokat, letöltési mappát és korlátokat. A Mentés sikeres kapcsolatellenőrzést igényel.

Induláskor a program ellenőrzi a BitHuMen-munkamenetet; ha belépés szükséges, megnyitja a böngészőt. A jelszót a felhasználó írja be. Ha az automatizálás alatt jár le a munkamenet, a program új belépést kér és siker esetén folytatja. Az automatizálás teljes módban működik: csak a saját nyilvántartott torrentjeit és fájljaikat törölheti, két hiánytalan ellenőrzés után.

A Windowszal indulás, bezáráskor és minimalizáláskor háttérben futás, téma és nyelv a Beállításokban módosítható. Az értesítési terület menüjéből az automatizálás is indítható és leállítható. A háttérben futó automatizálás az ablak elrejtésekor nem áll le. F11 kapcsolja a teljes képernyőt az első beállításban és az alkalmazásban.

Az Alkalmazás fül automatikusan keresi az újabb kiadást. A letöltés és telepítés gomb csak ellenőrzött újabb kiadásnál aktív; a jelenlegi verzió újratelepítése külön művelet. A frissítő SHA-256 ellenőrzést végez és menti a beállításokat. Az Eltávolítás a telepített Inno eltávolítót indítja.

A Windows Gépházból indított eltávolítás után az Inno eltávolító nem kér újabb indítási megerősítést. A GitHubról letöltött, aláíratlan telepítőre a böngésző továbbra is figyelmeztethet; ennek feloldásához hiteles kódaláírás szükséges.

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

A v1.0 forrásának valós BitHuMen- és qBittorrent-kapcsolaton, valamint fordított Windows-telepítővel végzett ellenőrzése szükséges a kiadás előtt.
