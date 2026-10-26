# Torrent Manager v0.5.0

A Torrent Manager a BitHuMen **legtöbbet seedelt** torrentjeit figyeli, a qBittorrent Web UI segítségével kezeli a torrenteket. A program magyar nyelvű, Windowsra csomagolható; a Playwright/Chromium böngészőben kezeli a BitHuMen-bejelentkezést.

**Fix toplista:** https://bithumen.be/browse.php?sort=seeders&d=DESC

## Új funkciók a v0.5-ben

- **Kezdőlap:** kompakt „Legtöbbet seedelt torrentek kezelése” panel **Indítás** és **Leállítás** gombbal, a tárhely, üzemmód, korlátok és legutóbbi műveletek megjelenítésével. Nincsenek összes/kezelt torrentszámlálók és más fülekre mutató gyorsgombok.
- **Beállítások:** jelszó gombja **Mutatás / Elrejtés**; „Torrentek száma (darab)”; alapból üres torrentméretmezők, valódi **GB** (SI, 1 GB = 1 000 000 000 bájt); nincs Windows-automatikus indítási kapcsoló vagy qBittorrent-indítási kapcsoló.
- **qBittorrent:** Torrent Manager indulásakor automatikusan megpróbálja elindítani, ha még nem fut. Minimalizált állapotot kér Windowstól. Az értesítési területre helyezéshez a qBittorrent saját „Start minimized” és „Minimize to notification area” beállításait is kapcsold be. **A torrentautomatizálás ettől még nem indul automatikusan**.
- **Napló:** mindenhol Segoe UI betűkészletre váltottunk, UTF-8 naplózás megőrizve; a naplóban és az oldalak fejlécében sincs állapotjelző.
- **Frissítések:** szerkeszthetetlen, beépített `SuperKiller123/TorrentManager` kiadási tároló, egyszerű kétgombos oldal, verzió- és programismertető. Az ellenőrzött frissítő külön segédalkalmazással a főprogram bezárása után csendesen futtatja az Inno Setup telepítőt, majd siker esetén újraindítja a programot. Az Inno Setup megőrzi a régi telepítési mappát, csoportot és a választott feladatokat (pl. asztali parancsikon).

**Korlát:** a Windows jogosultságkérései/UAC és bizonyos kritikus telepítési hibák továbbra is megjelenhetnek. A csendes frissítés az **új v0.5 és későbbi kiadásokból** induló frissítéseket érinti. A **v0.4 → v0.5** frissítést még a v0.4 régi frissítője indítja, ezért ez az átmenet kérhet megerősítést, és megjelenhet a telepítő varázslója.

## Fontos tudnivalók

- A méretkorlát **továbbra is a .torrent metainfóból** származó teljes méretre vonatkozik. Az üres mező = nincs megadott korlát. Tizedes GB is használható, pl. `1,5`.
- **Migráció:** a v0.4 `min_size_gib` és `max_size_gib` értékei pontos SI GB-ra konvertálódnak (10 GiB → 10.73741824 GB), így a régi tényleges határ nem változik. A következő mentéskor a régi mezők kikerülnek a felhasználói konfigurációból.
- A v0.4-ben bekapcsolt, Torrent Managerhez tartozó Windows-felhasználói automatikus indítási bejegyzést a v0.5 indításkor megpróbálja eltávolítani.
- A qBittorrent **önálló** Windows-indítási beállítását nem módosítja, és a qBittorrentet a Torrent Manager leállítása nem zárja be.
- A beépített módok változatlanok: **Próbaüzem**, **Csak új torrentek hozzáadása**, **Hozzáadás és törlés (fájlokkal)**.
- Fájltörlés csak a saját, korábban azonosított torrentekre engedélyezett, a hash, név, mappa és a teljes, két egymást követő sikeres toplista-ellenőrzés után. Hibás/hiányos lista esetén nincs törlés. Használj először Próbaüzemet és készíts biztonsági másolatot, mielőtt a törléses módot engedélyeznéd.
- A lemezlimitet a program az új torrentek hozzáadása előtt ellenőrzi. **A már aktív letöltéseket nem állítja meg**, ezért a korlát nem garantálja a teljes lemezhasználat plafonját.

## Windows-build a saját GitHub-repóban

1. A ZIP-ben található **TorrentManager_v0.5 mappa tartalmát** (ne a teljes mappát) másold a GitHub Desktop helyi `TorrentManager` tárolójának **gyökerébe**. A `.github/workflows/build-windows.yml` is a gyökérbe kerüljön; a régi fájlokat felül kell írni.
2. A felhasználói adatokat **ne** töltsd fel: `beallitasok.json`, `kezelt_torrentek.json`, `automatizalas.log`, `bithumen_bongeszo_profil`, illetve qBittorrent- vagy BitHuMen-jelszó nem kerülhet a repóba.
3. GitHub Desktop → **Commit to main** (például `Torrent Manager v0.5.0`) → **Push origin**.
4. Nyisd meg: https://github.com/SuperKiller123/TorrentManager/actions . A sikeres `main` build artifactja: `TorrentManager-v0.5-Windows`. Tartalmazza a telepítőt, a hordozható ZIP-et és a SHA256SUMS.txt ellenőrzőösszeget.
5. **Előbb teszteld a telepítőt Próbaüzemben.** Csak ezután hozd létre a GitHub Release `v0.5.0` címkéjét a `main` ágról; a címke-build feltölti a kiadási fájlokat a Release-hez.
6. Miután a Release-ben megjelent a `TorrentManager-Setup-v0.5.0.exe` és a `SHA256SUMS.txt`, a már telepített v0.4 alkalmazás **Frissítések** fülén kereshető az új kiadás. A v0.4 frissítője még kérhet jóváhagyást. A v0.5-re való átállás után a következő frissítés már csendes lehet.

A Windows-buildekhez GitHub Actions szükséges. A `build-windows.ps1` Windows alatt Python 3.13-mal elkészíti a GUI-t, a háttérmotort, a `TorrentUpdater.exe` segédet, a Chromiumot, a hordozható ZIP-et és (Inno Setup 6 használatával) a telepítőt.

## Adatok és fejlesztői indítás

A felhasználói állományok telepítéskor megmaradnak:

- `%LOCALAPPDATA%\TorrentManager\beallitasok.json`
- `%LOCALAPPDATA%\TorrentManager\kezelt_torrentek.json`
- `%LOCALAPPDATA%\TorrentManager\automatizalas.log`
- `%LOCALAPPDATA%\TorrentManager\bithumen_bongeszo_profil\`

Pythonból: `python -m pip install -r requirements.txt`, `python -m playwright install chromium`, majd `python TorrentManager.py`.

Offline regressziós tesztek: `python -m unittest discover -s tests -v`.

**Tesztelési állapot:** a Python-tesztek és a Linux/Tkinter grafikus próbák lefutottak. Ebben a környezetben **nem készült Windows `.exe`**, és nem történt élő BitHuMen/qBittorrent- vagy Windows Inno Setup telepítési teszt. Ezeket az Actions után, a saját Windows gépeden ellenőrizd.
