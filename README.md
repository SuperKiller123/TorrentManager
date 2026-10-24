# Torrent Manager v0.3 – Windows 10/11

**Modern, magyar nyelvű kezelőfelület** a BitHuMen toplistájának qBittorrenttel történő kezeléséhez. A v0.3 **a felhasználó által működőnek tesztelt v0.2 motorra épül**; a toplista feldolgozását, a torrentek hozzáadását, a tárhelykorlátozást és a törlési biztonsági feltételeket megtartja.

> **Fontos:** Ez a ZIP **forráskódot** tartalmaz. A kész, Windows alatt futtatható `.exe` változatot a GitHub Actions ingyenes Windows-fordítása vagy a helyi `build-windows.ps1` hozza létre. A kiadás Windowsos működését ezen a fejlesztői gépen nem volt lehetőség teljesen ellenőrizni.

## Mi új a v0.3-ban?

- **Újratervezett, sötét kezelőfelület**: bal oldali menü, áttekintés, biztonsági beállítások, napló és frissítési központ.
- **Áttekintő oldal**: állapot, indítás/leállítás, nyilvántartott torrentek száma, qBittorrent összes torrentszáma (sikeres API-kapcsolat esetén), tárhelyhasználat, beállított időköz, legutóbbi események.
- **Kényelmesebb beállítások**: görgethető felület, fájlkezelő, jelszó megjelenítése, mentés, korábban megadott értékek megőrzése.
- **Indítási hibajavítás**: a program `TorrentMotor.exe` indítása esetén a mellékelt `browsers` mappában keresi a Playwright Chromiumot; ha az nincs meg, a felhasználó `%LOCALAPPDATA%\ms-playwright` mappáját is ellenőrzi. A motor közvetlen indításakor is működik a keresés. A nem nulla kilépési kód a GUI naplójában látható.
- **Frissítések**: GitHub Releases-ről új kiadás ellenőrzése; Windows-telepítő letöltése és kézi jóváhagyással történő indítása **csak egyező SHA-256 ellenőrzőösszeg esetén**. A program nem telepít frissítést magától.
- **Automatikus Windows-fordítás**: GitHub Actions munkafolyamat, amely v0.3-as telepítőt, hordozható ZIP-et és SHA256SUMS.txt-t hoz létre. A `v...` címkék automatikusan GitHub Release-t is létrehoznak.

## A korábbi beállításaid megmaradnak

A v0.2-höz hasonlóan a felhasználói fájlok helye:

```text
%LOCALAPPDATA%\TorrentManager\beallitasok.json
%LOCALAPPDATA%\TorrentManager\kezelt_torrentek.json
%LOCALAPPDATA%\TorrentManager\bithumen_bongeszo_profil\
%LOCALAPPDATA%\TorrentManager\automatizalas.log
```

**Ne töröld ezeket a fájlokat.** Az új verzió ugyanazokat a beállításokat és BitHuMen böngészőprofilt használja. A meglévő v0.2-es programot érdemes biztonsági másolatként megtartani, amíg az új verziót nem tesztelted.

## Ajánlott: automatikus .exe fordítás GitHubon

A v0.3 forrásmappájában már benne van `.github/workflows/build-windows.yml`.

1. Hozz létre egy **privát** GitHub-repozitóriumot; csak a forrásfájlokat töltsd fel, **ne** a beállításfájlokat, a böngészőprofilt, a torrentfájlokat vagy jelszavakat. A GitHub Actions build a privát tárolóban is működhet a fiókod erőforrás-korlátai szerint.
2. Töltsd fel a **v0.3 mappa tartalmát** a repó gyökerébe (így a `.github` rejtett mappa is megmarad).
3. Nyisd meg a **GitHub → Actions → Torrent Manager – Windows build és kiadás → Run workflow** részt.
4. A sikeres futás után **Artifacts → TorrentManager-v0.3-Windows** alatt töltheted le a telepítőt, a hordozható ZIP-et és a SHA256SUMS.txt-t.
5. Futtasd a telepítőt, vagy csomagold ki a hordozható ZIP-et egy új mappába. A hordozható verzióban az **összes** fájlt és a `browsers` almappát együtt kell tartani; a `TorrentManager.exe` indítja a GUI-t.

**Frissítési központ aktiválása:** amikor rendelkezel saját **nyilvános** GitHub-repozitóriummal és közzétett GitHub Release-zel, a Frissítések oldalon írd be a `felhasználónév/tárolónév` értéket, és mentsd el. A frissítő csak a nyilvános Releases API-t használja, **privát repó esetén nem működik token nélkül**. A kód nem kér GitHub-jelszót. Ha az alap repód privát, használhatsz külön nyilvános, kizárólag kiadásokat tartalmazó repót is; a GitHub Actions munkafolyamatot ebben az esetben ehhez kell igazítani.

**Jövőbeli automatikus kiadások:** ha a forrásodhoz megfelelő `v0.3.0` Git-címkét hozol létre és feltöltöd, a workflow automatikusan elkészíti a GitHub Release-t a telepítővel. Az új verziókhoz módosítani kell a `updater.py` verziószámát, a telepítő és buildfájl verziószámait, a csomagneveket és a munkafolyamat nevét.

## Alternatíva: saját gépen való fordítás

Szükséges: Windows 10/11 x64 és Python 3.13; Inno Setup 6 opcionális. A projektmappában nyiss PowerShellt, majd:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\build-windows.ps1"
```

Kimenet:

```text
dist\TorrentManager\TorrentManager.exe
dist\TorrentManager\TorrentMotor.exe
dist\TorrentManager\browsers\...
dist\TorrentManager-v0.3-Windows-portable.zip
dist\installer\TorrentManager-Setup-v0.3.0.exe  (Inno Setup 6 mellett)
dist\SHA256SUMS.txt
```

A Chromiumot a script a `.browser-cache` könyvtárban tárolja, újabb fordításnál újrahasználhatja. Ha csak a Python-kód változott, a beállításokat, a böngészőt és a fejlesztői környezetet nem kell elölről létrehozni.

## Fejlesztői futtatás

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe TorrentManager.py
```

A GUI a motor elindítása nélkül is megnyílik. **A program induláskor nem kezdi el az automatizálást, és nem indul automatikusan a Windows indításával sem.**

## Biztonság

- Az automatikus torrent- és fájltörlés alapértelmezés szerint **kikapcsolt**. A régebben mentett felhasználói kapcsolók megmaradnak; **frissítés után ellenőrizd a beállításokat**.
- A törlési logika továbbra is csak a program által igazolt torrentazonosítókkal dolgozik és csak teljes, legalább 50 elemű toplista mellett tud eltávolítani. A `delete_files` opció tényleges adatvesztést okozhat.
- A tárhelykorlát csak az **új torrentek hozzáadását** tiltja a beállított százaléknál. Már elindult letöltéseket nem szakít meg.
- A qBittorrent-jelszó továbbra is a helyi `beallitasok.json` fájlban **egyszerű szövegként** szerepel. Ezt ne töltsd fel GitHubra. A repó `.gitignore` fájlja tiltja a leggyakoribb helyi adatfájlokat, de a feltöltés előtt magad is ellenőrizd a fájlokat.
- A frissítő HTTPS-en használja a GitHubot, és az ugyanahhoz a kiadáshoz tartozó `SHA256SUMS.txt` értékével hasonlítja össze a letöltött `.exe`-t. Ez letöltési sérülés ellen véd, de **nem helyettesíti a kódaláírást vagy a kiadó megbízhatóságát**. A telepítőt a Windows figyelmeztetéssel fogadhatja, ha nincs aláírva.
- Kizárólag jogszerűen hozzáférhető és megosztható tartalmakhoz használd.

## Tesztelés

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

A 10 offline teszt a beállításmigrációra, a torrent-hozzáadás paramétereire, a böngészőútvonalra és a kiadás/ellenőrzőösszeg kezelésére terjed ki. A GitHubos Windows-fordítást, a BitHuMen bejelentkezést és a teljes élő qBittorrent-működést új Windows-környezetben még tesztelni kell.
