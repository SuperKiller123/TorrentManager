# Torrent Manager v0.6.0

A Torrent Manager a BitHuMen legtöbbet **seedelt** torrentjeit figyeli, a qBittorrent WebUI segítségével automatizálja a hozzáadást és – külön engedélyezett üzemmódban – a biztonságosan azonosított, már nem toplistás saját torrentek törlését. A Windowsra készülő felületet és a telepítőt továbbfejlesztettük.

**Fix toplista:** https://bithumen.be/browse.php?sort=seeders&d=DESC  
**GitHub:** https://github.com/SuperKiller123/TorrentManager

## A v0.6 újdonságai

- **Indítás:** a Torrent Manager maximalizált ablakkal indul. A qBittorrentet, ha nincs elindítva, Windows alatt külön folyamat indítja; az induló qBittorrent ablakát a program ismételten minimalizálja. Már futó példány ablakát nem piszkálja.
- **WebUI:** külön, háttérben futó, 3 másodpercenként megismételt bejelentkezési/kapcsolatellenőrzés. Az automatizálás Indítás gombja addig nem engedélyezett, amíg a valódi WebUI-hívás nem sikerült.
- **Chromium:** az automata motor mindig **headless** módot használ. Ha a BitHuMen ismét bejelentkezést kér, az alkalmazás Beállítások fülén **kézzel** megnyitható külön bejelentkezési ablak; a belépési profil megmarad a következő háttérindításhoz. A Chrome nem ugrik fel önmagától.
- **Ablak:** Windows 10/11 alatt a támogatott DWM-beállításokkal a címsor és az ablakvezérlők témához illesztése. A címsor nem mutatja a program nevét vagy verzióját. **F11**: valódi teljes képernyő; az **Esc nincs hozzárendelve** a kilépéshez. Az F11 ismételt lenyomása kapcsol vissza. Windows-rendszeren való ellenőrzés szükséges.
- **Ikon:** a bal felső sarokban megjelenő zöld gyémántlogó egységes PNG/ICO fájlban, az alkalmazás és telepítő ikonjaként is.
- **Oldalsáv:** csak a Torrent Manager felirat jelenik meg az ikon mellett, verzió és alsó magyarázó feliratok nélkül.
- **Kezdőlap:** új, sűrű műszerfal nyolc élő beállítás-/állapotkártyával, animált tárhelyjelzővel, kapcsolatjelzőkkel, korlátokkal, közelítő következő ellenőrzéssel és mini eseménynaplóval. Az Indítás/Leállítás gombok nem foglalják el az oldal központját.
- **Animációk:** rövid, kb. 60 FPS időzítésű interpolált mutatók és gombhover; az alkalmazás nem próbál folyamatosan felesleges FPS-t előállítani.
- **Témák:** sötét, világos és Windows rendszerbeállítást követő mód. A Beállítások mentése után azonnal vált. A mentés gomb felül, a Beállítások címmel egy sorban jelenik meg. Visszatérve a Beállításokba az oldal a tetejére görget.
- **Nyelvválasztás:** tíz széles körben beszélt nyelv (angol, mandarin kínai, hindi, spanyol, francia, arab, bengáli, portugál, orosz, urdu) + magyar, továbbá német. **Egyetlen telepítő és program tartalmazza mind a 12 választható nyelvet**, a fordítások offline működnek. A fő vezérlőelemek, állapotok és ismertető szövegek fordítottak. A motor technikai naplóüzenetei és néhány diagnosztikai üzenet továbbra is magyar nyelvű, amit következő kiadásban egységesíteni lehet.
- **Frissítések:** a fül teljes elérhető tartományra terül ki. Külön verzióválasztóval a GitHubon hozzáférhető korábbi kiadások is letölthetők, ha van hozzájuk telepítő és SHA256SUMS.txt. Visszalépéskor a felhasználó figyelmeztetést kap, a beállítások biztonsági másolata elkészül. GitHub-megnyitó gomb és részletes programismertető is van.
- **Telepítő:** első telepítésnél a felhasználó kiválaszthatja a nyelvet és az asztali parancsikon létrehozását; ugyanazon AppId meglévő telepítésénél a könyvtár és korábbi feladatválasztások megmaradnak, a telepítő kihagyja a már megadott választásokat. Frissítésből a segédprogram Inno Setupot csendes kapcsolókkal indítja; a Windows rendszerengedélykéréseit nem kerüli meg.
- **Napló:** a motor konzolkimenete és az alkalmazás kapcsolata UTF-8-ra van konfigurálva, a felület Windows alatt Segoe UI betűkészletet használ. Az olyan, már korábban kérdőjellé alakult karakterek utólag nem rekonstruálhatók; az új bejegyzések javulásához Windows alatti ellenőrzés szükséges.

## Biztonság és korlátok

- Az alapmód továbbra is a **Próbaüzem**. Valós hozzáadáshoz vagy törléshez a felhasználó külön üzemmódot választ.
- Fájltörlés csak a motor által korábban nyilvántartott, hash, név és mappa szerint egyező torrenteknél engedélyezett, két hiánytalan toplista-ellenőrzés után. Hiányos lista vagy bizonytalan állapot esetén nincs törlés.
- A méretkorlát tizedes **GB**-ban értendő: 1 GB = 1 000 000 000 bájt. Üres mező = nincs méretkorlát.
- A tárhelykorlát új torrentek hozzáadását akadályozza, **nem állítja le a már meglévő letöltéseket**, ezért a tényleges telítettség túllépheti a határt.
- A böngészőprofilt és belépési adatokat a felhasználó helyi könyvtára tárolja, **ne töltsd fel a GitHubra**.
- Régebbi verziók telepítésekor fennállhat beállítás- és adatkompatibilitási kockázat; a beállításokról automatikus mentés készül, de ez nem jelenti minden visszalépés garantált kompatibilitását.

## Telepítés és kiadás GitHub Desktopból

1. Bontsd ki a v0.6 forrás-ZIP-et. A **TorrentManager_v0.6 könyvtár tartalmát** másold a helyi `SuperKiller123/TorrentManager` GitHub-repó gyökerébe, a rejtett `.github` mappával és az `assets` könyvtárral együtt; a régi forrásfájlokat írd felül.
2. GitHub Desktop: **Commit to main**, üzenet például `Torrent Manager v0.6.0`; majd **Push origin**.
3. Ellenőrizd a Windows-build sikerét a [GitHub Actions](https://github.com/SuperKiller123/TorrentManager/actions) felületen. A kész **Actions Artifact** neve `TorrentManager-v0.6-Windows`; ebben lesz a Windows-telepítő, a hordozható ZIP és az ellenőrzőösszeg.
4. **Először próbáld ki Windows alatt, Próbaüzemben**, ellenőrizd az F11-et, a qBittorrent háttérindítását, a magyar karaktereket, a telepítéskor megőrzött parancsikont és a telepítő visszaállítási funkcióit.
5. Ha minden megfelelő, hozz létre `v0.6.0` címkéjű GitHub Release-t a `main` ágról. A címkére induló Actions feltölti a `TorrentManager-Setup-v0.6.0.exe` és `SHA256SUMS.txt` fájlokat a Release Assets alá. Ezután a telepített v0.5 alkalmazásból frissíthetsz.

Az alkalmazás építéséhez GitHub Actions `windows-latest`, Python 3.13, PyInstaller, Playwright Chromium és Inno Setup 6 szükséges. A `build-windows.ps1` együttesen készíti a főprogramot, a motort, a bejelentkezési és frissítési segédalkalmazást, a hordozható kiadást és a telepítőt.

## Fejlesztői indítás és tesztek

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
python TorrentManager.py
python -m unittest discover -s tests -v
```

A felhasználó adatai: `%LOCALAPPDATA%\TorrentManager\`. Fontos fájlok: `beallitasok.json`, `kezelt_torrentek.json`, `automatizalas.log`, `bithumen_bongeszo_profil`, illetve régebbi verzió telepítésekor `backups\`.

**Validáció:** 38 offline regressziós teszt sikeres, virtuális kijelzőn Tkinter-GUI és témaváltási próba készült. **A jelenlegi Linux-környezetben Windows `.exe` nem állítható elő; éles qBittorrent/BitHuMen, Windows DWM és Inno Setup telepítési ellenőrzés nem történt.** Ezeket a GitHub Actions build és a saját Windows gépeden végzett teszt igazolhatja.
