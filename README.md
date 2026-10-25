# Torrent Manager v0.4.0

Magyar nyelvű, Windowsra csomagolható Torrent Manager, amely a BitHuMen **legtöbbet seedelt** torrentjeit figyeli, és a qBittorrent Web UI-t használja. A GUI külön háttérmotorral működik, Playwright/Chromium bejelentkezési profillal.

**Rögzített toplista:** `https://bithumen.be/browse.php?sort=seeders&d=DESC`. Nincs felhasználó által szerkeszthető toplista-URL.

## Újdonságok

- **Kezdőlap**: összes torrent, valóban meglévő, alkalmazás által kezelt torrentek, tárhely, ellenőrzési időköz, beállítás-összegzés, csak tényleges műveleteket mutató mini eseménynapló.
- **Letisztult beállítások**: a Mentés gomb csak módosításkor aktív; egyetlen torrentszám határozza meg a figyelt **top N** tartományt és az összes qBittorrent-torrent maximális számát; egész százalékos tárhelyhatár.
- **Módok**: Próbaüzem; Csak új torrentek hozzáadása; Új torrentek hozzáadása és törlése **letöltött fájlokkal együtt**.
- **Méretkorlát**: minimum és maximum GiB; a **0 kikapcsolt korlátot** jelent. A motor a hozzáadás előtt a `.torrent` metainfóból ellenőrzi a méretet. Ismeretlen metainfót nem ad hozzá.
- **Windows-indítás**: a jelenlegi Windows-felhasználó bejelentkezésekor a GUI indítása; opcionálisan a qBittorrent indítása. Az automatizálás az Indítás gombbal indul, nem automatikusan.
- **GitHub**: a forrás feltöltésekor automatikus Windows build, `v0.4.0` címke alapján GitHub Release; az alkalmazás alapértelmezett frissítési tárolója: `SuperKiller123/TorrentManager`.
- **Nincs CPU-hőmérséklet-figyelés vagy automatikus hibernálás/kikapcsolás.**

## Biztonsági szabályok

A törlés **végleges**, a `qBittorrent /api/v2/torrents/delete` API-t `deleteFiles=true` paraméterrel hívja. Csak a Torrent Manager saját `kezelt_torrentek.json` állományában tárolt **hash és név** egyezése esetén töröl; azonosítatlan torrenteket nem töröl. A mentési útvonalnak meg kell egyeznie a kiválasztott mappával, megosztott tartalomútvonal esetén nem töröl.

A törléshez a beállított **teljes top N** lista **két külön sikeres ellenőrzése** és a „Hozzáadás és törlés” üzemmód kell. Sikertelen/hiányos lekérdezéskor nincs törlés. A várható teljes méret alapján is ellenőrzi a tárhelyhatárt, de a qBittorrent már aktív letöltéseit **nem állítja meg**; a beállított lemezlimitet hardveres garanciaként nem szabad értelmezni.

**Első indításnál használj Próbaüzemet.** A törléses módra csak azután válts, hogy ellenőrizted a saját torrentlistát, a rangsort és a naplót. Letöltött fájlok törlése előtt készíts biztonsági mentést.

## Windows-frissítés, telepítés nélkül fordítás a számítógépeden

A GitHub-projekted: <https://github.com/SuperKiller123/TorrentManager>

1. **GitHub Desktop** → klónozott `TorrentManager` projekt megnyitása.
2. A `TorrentManager_v0.4` mappából másold át a **tartalmat** a GitHub Desktop által kezelt `TorrentManager` mappába, a régieket felülírva. Ne másolj egy új alkönyvtárat; a `.github/workflows/build-windows.yml` pontosan a repó gyökerében legyen. A korábbi, felesleges forrásfájlokat a GitHub Desktopban látható módon távolítsd el.
3. Ellenőrizd, hogy a felülírás előtt **nem** tartalmaz személyes `beallitasok.json`, böngészőprofil vagy torrent-fájlokat a feltöltés.
4. GitHub Desktop → **Summary:** `Torrent Manager v0.4.0` → **Commit to main** → **Push origin**.
5. A `main` ágba érkező push **automatikusan** elindítja az Actions buildet: <https://github.com/SuperKiller123/TorrentManager/actions>. A `TorrentManager-v0.4-Windows` artifact tartalmazza az Inno Setup telepítőt, a hordozható ZIP-et és a SHA256SUMS.txt állományt.
6. Először az Actions-artifactból telepítsd a v0.4-et, majd **Próbaüzemben teszteld**. A v0.3-at egyelőre tartsd meg.
7. Ha a teszt sikerült, a GitHub **Releases → Draft a new release** oldalon hozd létre a `v0.4.0` címkét a `main` ágból. A címke push-ja külön buildet indít, amely a kész telepítőt és ellenőrzőösszeget feltölti a megfelelő GitHub Release-hez. A frissítés ellenőrzése az alkalmazásban már erre a nyilvános kiadásra támaszkodik. A létrehozott kiadás még üres lehet, amíg a build fut.

**Fontos:** a GitHub nyilvános projektje a forráskódot is megosztja. A felhasználói beállítások, jelszavak és BitHuMen bejelentkezési profil a telepített program mellett **nem**, hanem a `%LOCALAPPDATA%\TorrentManager` mappában maradnak; ne töltsd fel ezeket a GitHubra.

A build Windows alatt a `build-windows.ps1` fájlt futtatja és a Playwright Chromiumot is csomagolja. A `requirements-build.txt` csak a buildhez szükséges függőségeket tartalmazza. Python-forrásból futtatáshoz `python -m pip install -r requirements.txt`, `python -m playwright install chromium`, majd `python TorrentManager.py` használható.

### Hogyan frissül a telepített v0.3?

A v0.3 **Frissítések** oldalán a tároló legyen `SuperKiller123/TorrentManager`, és legyen **mentve**. Miután a `v0.4.0` GitHub Release már rendelkezik a `TorrentManager-Setup-v0.4.0.exe` és `SHA256SUMS.txt` fájlokkal, a „Frissítés keresése” megkeresheti, letöltheti, ellenőrizheti és jóváhagyás után elindíthatja a telepítőt. Alternatíva az Actions artifactból származó telepítő kézi indítása.

A frissítő SHA-256 ellenőrzése védi az átviteli sérülésektől, **nem egyenértékű a Windows kódaláírással**. Egy magát kiadónak feltüntető, idegen feltöltés veszélyes lehet; mindig csak a saját GitHub-repóból származó telepítőt használj.

## Beállítások helye, átállás v0.3-ról

- `%LOCALAPPDATA%\TorrentManager\beallitasok.json`
- `%LOCALAPPDATA%\TorrentManager\kezelt_torrentek.json`
- `%LOCALAPPDATA%\TorrentManager\automatizalas.log`
- `%LOCALAPPDATA%\TorrentManager\bithumen_bongeszo_profil\`

A v0.4 a meglévő adatokat **nem írja felül** a telepítéssel, a régi mezőket az új sémára alakítja át a következő mentéskor. Régi fájltörlés nélküli üzemmódból nem kapcsol automatikusan fájltörlésre. A régi `70.0` tárhelyhatárt `70` százalékként kezeli.

**Még nem történt élő BitHuMen- és qBittorrent-integrációs teszt ebben a környezetben.** A Python-szintű tesztek offline futnak; a Windowsra csomagolt .exe-t a GitHub-fordítás után a saját gépeden kell ellenőrizned.
