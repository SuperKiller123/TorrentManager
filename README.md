# Torrent Manager v0.7

Windowsos qBittorrent- és BitHuMen-kezelő. A forrás alapja a SuperKiller123/TorrentManager repó v0.6 címkéje, `d259423f96e6dc42d8cee4a0a5691b120cf27914` commit.

A csomag tesztelési állapotát és a még szükséges kézi próbákat a **TESZTELES-v0.7.md** részletezi. A sikeres fordítás nem helyettesíti a telepítés és eltávolítás ellenőrzését egy külön Windows-tesztgépen.

## Telepítés és első indítás

1. Indítsd a `TorrentManager-Setup-v0.7.exe` fájlt. A telepítő rendszergazdai jogosultságot kér, az alapkönyvtár a Program Files/Torrent Manager.
2. Egyetlen nyelvválasztás van, mind a 12 nyelvvel. Ez határozza meg a program induló nyelvét. A telepítő szövege minden választásnál egységesen angol: ez a korábban jóváhagyott tartalékmegoldás.
3. Az asztali parancsikon, a Windowszal indulás és a háttérben futás beállítható. A telepítés végén választható az alkalmazás indítása.
4. Az első indítási varázslóban add meg a qBittorrent WebUI címét, felhasználónevét, jelszavát, a letöltési mappát és a korlátokat. A kapcsolatnak sikeresen létre kell jönnie a mentéshez. A jelszó a WebUI-é, nem a trackeré.
5. A BitHuMen-bejelentkezés gomb külön böngészőt nyit, amelyben kézzel jelentkezhetsz be. Zárd be a böngészőt a folytatás előtt. A trackerbejelentkezést a varázsló nem igazolja automatikusan; a motor ezt az első ellenőrzéskor vizsgálja.
6. Először próbaüzemet használj. A teljes mód saját nyilvántartott torrenteket és fájljaikat is törölheti; ezt a program külön megerősítteti.

## Működés

- A WebUI-próba háttérszálon ismétlődik. Az automatizálás sikeres kapcsolat előtt nem indítható.
- A helyi WebUI-kérések nem használják a környezeti proxyt. A próba és a motor ugyanazokat a munkamenet- és HTTP-fejléc-beállításokat használja.
- A Kezdőlap nem görgethető. Az élő torrentdarabszám, a beállított korlátok, az átviteli grafikon, a tárhelymutató és a mini napló külön szerepel.
- A támogatott legkisebb ablak 1000×700 logikai képpont. A Windows DPI-méretezése befolyásolja a rendelkezésre álló logikai területet.
- F11 az aktuális monitor teljes képernyőjére vált, majd visszaállítja a korábbi ablakállapotot. Az Esc nem kapcsolja ki.
- A Beállításokban a nyelv csak kiválasztással változik; a görgő nem lépteti. A beállítások oldalra visszatérés a lap tetejére visz.
- A háttérben futás esetén a tálcaikon menüjéből nyitható meg vagy állítható le a program.
- A GitHub-kiadáslista induláskor automatikusan betöltődik. A kiválasztott kiadás újra is telepíthető, és korábbi kiadás is választható, amennyiben telepítője és ellenőrzőösszege elérhető.
- A frissítő menti a beállításokat, ellenőrzi a SHA-256 értéket, megvárja a program leállását, és UAC-val csak a telepítőt emeli. A telepítési könyvtárat kifejezetten átadja. UAC-megszakítás vagy telepítési hiba után újranyitja a meglévő alkalmazást és hibát jelez.
- A fő felület és a varázsló 12 nyelvet tartalmaz. Egyes technikai hibaüzenetek és a motor naplója magyar maradt; a teljes diagnosztikai lokalizáció nem készült el.

## Adatok és eltávolítás

A felhasználói adatok a `%LOCALAPPDATA%/TorrentManager` mappában vannak. A programkönyvtárba nem mentődnek jelszavak vagy futási állapotok. A WebUI-jelszó a jelenlegi örökölt JSON-beállításban olvasható szövegként tárolódik; ezt a forráscsomag nem tartalmazza.

Az eltávolító a csomag saját fájljait, böngészőjét, ismert régi saját fájljait, a ProfileListben felsorolt felhasználók TorrentManager-adatmappáit és a nyilvántartott saját parancsikonokat célozza. A qBittorrent-profilok és a torrenttartalmak nem szerepelnek a törlési listán. Új automatikus indítási bejegyzés saját Startup-parancsikonként készül. A betöltött felhasználói registry-hive-ok régi TorrentManager-bejegyzéseit is takarítja.

**Nem bizonyított a maradéktalan eltávolítás minden Windows-fióknál:** a kijelentkezett felhasználók régi registry-hive-jait nem tölti be, és az egyedi helyre átirányított LocalAppData vagy zárolt fájlok külön próbát igényelnek. Az ismeretlen, más által a telepítési mappába másolt fájlokat szándékosan nem törli, ezért ilyen esetben a könyvtár megmaradhat.

## Fejlesztői futtatás és teszt

Python 3.13, Windows x64:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe TorrentManager.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

A Windows-felületi tesztekhez előbb állítsd be a `TM_GUI_TESTS=1` környezeti változót. A helyi HTTP-tesztekhez engedélyezett loopback kapcsolat kell. A tesztek alapból nem lépnek be a trackerre és nem dolgoznak a felhasználó torrentjeivel.

`tests/live_qb_smoke.py`: külön indítható próba a `C:/Program Files/qBittorrent/qbittorrent.exe` fájllal, új munkamappabeli profillal és üres torrentlistával. Az eredeti profil ellenőrzőösszegeit összehasonlítja, a saját példányt leállítja.

`tests/frozen_smoke.py`: a kész EXE elkülönített adatkönyvtárú, legfeljebb kétperces indítási próbája. A felhasználó által a tesztablakba beírt adatok a tesztkönyvtárban maradnak; ezeket ne csomagold kiadásba.

## Windows-build

Inno Setup 6 szükséges; a build a szokásos telepítési helyeken és a `.tools/Inno/ISCC.exe` útvonalon keresi. Futtasd:

```powershell
.\build-windows.ps1
```

A build lefuttatja a regressziós teszteket, elkészíti a GUI-, motor-, bejelentkezési és frissítő EXE-ket, csomagolja a Chromiumot, majd a hordozható ZIP-et, telepítőt és SHA256SUMS.txt fájlt. A mellékelt `requirements-tested.txt` a teszteléskor használt pontos függőségeket rögzíti. A szokásos követelményfájl verziótartományokat használ.

A GitHub-munkafolyamat frissítve lett a v0.7 fájlnevekre. Ebben a munkamenetben nem történt GitHub-push vagy kiadásközzététel.
