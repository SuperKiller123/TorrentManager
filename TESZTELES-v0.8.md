# Torrent Manager v0.8 – ellenőrzési jegyzőkönyv

Dátum: 2026. október 31. Windows x64, Python 3.13. Alap: a helyben elkészített v0.7, összevetve a GitHub v0.7 címkével (185a1bd3294f845fb0e08f6c52e8101bd4306e7a).

## Elkészült változások

- Egységes Torrent Manager név; az Inno automatikus „All Users” jelölése kikapcsolva. Ez nem a Program Files szükségszerű velejárója.
- Egyetlen, az alkalmazás nyelvét kérő nyelvválasztó, 12 nyelv; az engedélyezett egységes angol telepítőszöveggel.
- Egyetlen Options csoport, azonos behúzás és térköz. Tálca-/Start-kitűzési opciók felhasználói útmutatóval: nem állítják, hogy automatikusan kitűztek bármit.
- Az eltávolító bezárja a saját programkönyvtárból futó saját folyamatokat, külön segéddel törli a generált saját fájlokat, és ellenőrzi a könyvtár tulajdonjelölését. Nem járja be a junction célját. A megadott torrentletöltési helyet és .torrent fájlokat megőrzi, akadály esetén hibajelentést készít.
- Betöltött és offline felhasználói registry-profilok kezelése, átirányított AppData/asztal/Startup útvonalak feloldása.
- Maximált, témázott első beállítás, saját ikon és név, egyetlen oldal, két címzett oszlop, hangsúlyos Mentés. Általános megjelenési/Windows/működési opciók csak a főalkalmazás beállításaiban. Kis munkaterületen a tartalom görgethető; a Mentés látható marad.
- Induláskor valódi BitHuMen-munkamenet-ellenőrzés; lejárt/hiányzó belépésnél bejelentkezési böngésző. Profilzár akadályozza a motor és a bejelentkezés egyidejű profilhasználatát.
- Az újonnan indított qBittorrent ablaka elrejthető a működő értesítési terület mellett; a folyamat nem kap kilépést okozó WM_CLOSE üzenetet. Kikapcsolt vagy nem olvasható tray-beállításnál elérhető minimalizált ablak marad.
- Magasabb felső három dashboard-sor, rövidebb alsó két sor, továbbra sincs dashboard-görgetés.
- A főablak címsorában vizuálisan nincs ikon; az eredeti Windows-ablakgombok megmaradnak. A beállítóablak ikonja megmarad.
- Azonos verzió nem frissítés; külön újratelepítés/régi verzió telepítése felirat. Hosszabb bemutató mind a 12 nyelven.
- Hibás WebUI-jelszóval nem ismétlődik folyamatosan a belépés (IP-kitiltás elkerülése); módosított kapcsolati adatok új próbát engednek. Hálózati indulási hiba továbbra is újrapróbálódik.
- Frissítéskor 3010 újraindítási kód kezelése; időtúllépett telepítő mellett nincs versengő app-újraindítás.

## Bizonyított ellenőrzések

- 70 automatikus teszt sikeres, nulla kihagyott teszt: `evidence/test-v08.log`. Valódi Windows/Tk ablakok, 12 nyelv, három ablakméret, F11/Esc, mentés, kapcsolat újrapróbálása, letöltési épség és törlési védelem.
- Valódi Chromium elkülönített profillal, hálózati válaszok helyi helyettesítésével: belépés hiánya, tartós munkamenetsüti két böngészőindítás között, lejárat, 503 és váratlan oldal. Nem használ valódi trackerfiókot.
- Valódi Inno telepítő telepítése/eltávolítása külön teszt-AppId-val és ártalmatlan tesztpayload-dal. A „Torrent Manager” DisplayName pontos; a nyelv átadása sikeres; a teljes programkönyvtár és két szimulált profil saját adatai eltűntek; torrent- és qBittorrent-sentinel fájlok változatlanok. Napló: `evidence/lifecycle-v08.log`.
- Valódi PowerShell-takarítás teszteli a hiányzó tulajdonjelölés elutasítását, a junction cél védelmét, a saját könyvtárba régebben beállított torrentletöltések megőrzését.
- A főablak ikonmentes fejlécét és az új dashboard-arányokat Windows-képernyőképen is ellenőriztük.
- Valódi qBittorrent v5.3.0 külön üres profillal: sikeres kapcsolat/adatlekérés, hibás jelszó elutasítása, a felhasználó eredeti profiljának előtte/utána hash-egyezése. Napló: `evidence/live-qb-v08.log`.
- A PyInstallerrel lefordított v0.8 GUI rövid indítási próbája új, elkülönített AppData-könyvtárral sikeres; napló: `evidence/frozen-v08.log`. Ez indítási próba, nem teljes éles munkafolyamat.

## Megmaradó korlátok és nem igazolt esetek

Nem állítható teljes hibamentesség. Az izolált telepítőteszt nem emelt Program Files-telepítés: a valódi UAC, offline felhasználói hive-ok jogosultságai, zárolt profilok és régi per-user v0.6 telepítésből machine-wide migráció külön tesztgépes ellenőrzést igényelnek. Régi per-user telepítés maradványainak automatikus migrációja nincs teljesen megoldva. A régi telepítők downgrade-viselkedése sem garantált.

Több fizikai monitor és vegyes DPI nincs igazolva. A valódi BitHuMen-fiókos teljes letöltés/törlés munkafolyamat nincs végigpróbálva; a felhasználói belépést nem automatizáltuk. A fordítások nem anyanyelvi lektoráltak, néhány technikai hiba/napló továbbra is magyar. Ezek a korábbi nyitott tételek nem tekinthetők lezártnak.

Védett torrenttartalom vagy hozzáférési hiba esetén az eltávolító szándékosan meghagyhat fájlokat és jelentést ad. A Windows automatikus kitűzése helyett felhasználói lépéseket kínálunk. A csomag nincs kódaláírva. Nincs GitHub-push vagy release-közzététel.

## Dokumentáció

- Inno telepítőparaméterek: https://jrsoftware.org/ishelp/topic_setupcmdline.htm
- Windows kitűzés: https://learn.microsoft.com/windows/apps/develop/windows-integration/pin-to-taskbar
