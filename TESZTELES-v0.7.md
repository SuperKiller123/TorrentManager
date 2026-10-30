# Torrent Manager v0.7 – ellenőrzési jegyzőkönyv

Dátum: 2026. október 29. Környezet: Windows x64, Python 3.13. Alapforrás: GitHub SuperKiller123/TorrentManager v0.6, d259423f96e6dc42d8cee4a0a5691b120cf27914.

## Bizonyított eredmények

- **49/49 teszt sikeres**, kihagyott teszt nélkül a `TM_GUI_TESTS=1` futtatásban. A teljes napló: `evidence/test-v07.log`.
- Valódi helyi HTTP-szerver ellenőrizte a munkamenetsüti továbbítását, a Referer fejlécet, az ékezetes/speciális karakteres jelszó továbbítását, a helyi proxy megkerülését, a hibás jelszó megkülönböztetését és az indulás utáni automatikus kapcsolódási újrapróbálást.
- Valódi **qBittorrent v5.3.0** külön munkamappabeli, üres profillal: sikeres hitelesítés, hibás jelszó elutasítása, verzió- és torrent-/sebességadatok lekérése. A felhasználó eredeti qBittorrent-beállításai és BT_backup fájljai a teszt előtti és utáni hash-összehasonlításban egyeztek. Napló: `evidence/live-qb-v07.log`.
- Valódi Tk/Windows ablakon ellenőrzött dashboard-elrendezés: **1000×700, 1366×768, 1920×1080**. A mini napló látható tartománya a főablakon belül maradt. A dashboard nem kapott görgetővásznat.
- Mind a **12 nyelv** szerepel a választóban; az egérgörgő egyik vizsgált nyelven sem változtatta meg a kijelölést. A fordításkulcsok száma a nyelvek között azonos.
- A Windowsos F11-kapcsoló bekapcsolt, az Esc után is bekapcsolva maradt, és újabb F11-re visszaállt.
- A varázsló sikeres, valódi HTTP-kapcsolatteszt után atomikusan mentette a beállításokat és az első beállítás befejezését. Megszakításkor nem készült beállításfájl.
- A jelenlegi verzió újratelepítésének gombja engedélyezett ellenőrzőösszeggel rendelkező telepítő kijelölésekor. A `v0.7` és `v0.7.0` verzió összehasonlításkor azonosnak számít, de a megjelenítés `v0.7`.
- A frissítő segéd a telepítési könyvtárat átadja a telepítőnek. Ennek argumentumát és a siker utáni újraindítást külön teszt ellenőrizte.
- Az örökölt torrentmetaadat-, méretkorlát-, migrációs-, próbaüzem- és saját torrentet védő tesztek is sikeresek.
- PyInstallerrel elkészült a GUI, a motor, a bejelentkezési segéd és a frissítő segéd Windows EXE-je. A Chromium a csomag része.
- A csomagolt GUI elindult elkülönített alkalmazásadatokkal. A varázsló és a később megnyitott fő dashboard Windowsos képernyőképen szemrevételezhető volt. Ez indítási és vizuális próba, nem teljes telepítési teszt.
- Inno Setup **6.7.4** fordítóval elkészült a Windows-telepítő. A fordító telepítőjének Authenticode-aláírása letöltéskor érvényes volt, kiadója Pyrsys B.V. A Torrent Manager saját EXE-jei/telepítője **nincsenek kódaláíró tanúsítvánnyal aláírva**.

## Követelmények és állapotuk

| Terület | Megvalósítás / ellenőrzés |
|---|---|
| Egyetlen nyelvválasztás | A telepítő kezdeti 12 elemű választója; nincs második alkalmazásnyelv-oldal. A választás install-defaults.ini útján kerül az alkalmazásba. A tényleges interaktív telepítőválasztás még kézi próba. |
| Telepítő szövege | Egységesen angol, a beszélgetésben engedélyezett tartalékmegoldás szerint. |
| Program Files és UAC | `{autopf}/Torrent Manager`, `PrivilegesRequired=admin`, x64 telepítés. A valódi UAC-os telepítést nem futtattuk a használatban lévő rendszeren. |
| Telepítési opciók | Személyes desktop- és Startup-parancsikon, tálcára zárás; később is beállítható. Az opciók a varázsló mentésekor válnak aktívvá. |
| Telepítés végi indítás | Inno postinstall és runasoriginaluser opció. Kézi telepítési próba szükséges. |
| Eltávolítás | Saját csomagfájlok, böngésző, ismert legacy saját fájlok, profilok saját TorrentManager-adatkönyvtárai, saját parancsikonok és betöltött régi registry-bejegyzések takarítása. Teljes eltávolítási próba még nem történt. |
| Név és verzió | AppName és AppVerName: Torrent Manager. Megjelenített kiadás: v0.7; telepítő: TorrentManager-Setup-v0.7.exe. |
| WebUI | Ismételt háttérpróba; sütis munkamenet; közös motor/probe HTTP-beállítások; helyi proxy megkerülése. Valódi qBittorrenttel sikeres. |
| Első indítás | Külön varázsló, mezőnkénti súgó, kötelező sikeres WebUI-teszt. A BitHuMen-belépés kézi; nem feltétele a beállításmentésnek. |
| Dashboard | Görgetősáv nélküli elrendezés, élő torrentdarabszám és átviteli grafikon; automatizált méretpróbák sikeresek. |
| F11 és címsor | Aktuális monitor lekérése, keret nélküli mód, előző állapot visszaállítása és DWM-színezés. Esc/F11 próba sikeres; valódi többmonitoros és Windows 10/11 összehasonlító próba még szükséges. |
| Nyelvek | 12 fő felületi és varázslónyelv, offline fordítások. Egyes technikai naplók és hibaablakok továbbra is magyarok. |
| Frissítő | Automatikus lekérés, jelenlegi/régi verzió választása, SHA-256, mentés, UAC-s telepítőindítás, hiba utáni app-újranyitás. A teljes telepítési lánc még nem próbált. |

## Pontosan mi nincs még bizonyítva / ismert korlátok

1. **Nem igazolt a nyomtalan eltávolítás minden Windows-felhasználónál.** A kijelentkezett fiókok régi NTUSER.DAT hive-jait a kód nem tölti be. Esetleges régi Run/Software bejegyzéseik megmaradhatnak. Új Startup-bejegyzést fájlként kezelünk, így az a profilból törölhető. Egyedi LocalAppData-átirányítás, megváltozott jogosultság vagy zárolt fájl külön eset.
2. Az ismeretlen, idegen fájlok a telepítési mappában megmaradnak; ilyenkor a mappa nem lesz üres, tehát az eltávolító nem törli. Ez védi az odakerült idegen tartalmat, de ilyen körülmények között nem teljesül a főkönyvtár feltétlen eltűnése.
3. A v0.6 per-user telepítésről v0.7 machine-wide telepítésre váltás és a régi per-user telepítők használatával végzett downgrade még nincs végigtesztelve. A régi telepítők eltérő registry-hatókört használhatnak. Ezt nem tekintjük bizonyítottan kész migrációs útvonalnak.
4. UAC-jóváhagyás, UAC-megszakítás, admin fiók jelszavas emelése, telepítési zárolások és rendszer-újraindítást kérő Setup-visszatérési kódok tényleges próbája külön Windows-tesztgépen szükséges.
5. Többmonitoros elrendezés, eltérő DPI, negatív monitorkoordináták és 1000×700 logikai képpontnál kisebb munkaterület nem volt fizikai kijelzőn végigpróbálva. A Windows 10 címsorszínezése rendszerverziótól függhet. A varázsló a rendszer szokásos világos megjelenését használja.
6. A fordításokat nem ellenőrizte anyanyelvi lektor. Az arab/urdu jobbról balra tördelés és az indiai írásrendszerek megjelenése külön vizuális ellenőrzést igényel. A technikai magyar üzenetek teljes lokalizációja nyitott tétel.
7. A BitHuMen teljes éles munkafolyamatát nem igazoltuk automatikus bejelentkezéssel vagy torrentek hozzáadásával/törlésével. A motor meglévő biztonsági regressziós tesztjei és a qBittorrent API-kapcsolat sikeresek, de a tracker oldalszerkezetének változása befolyásolhatja az éles működést.
8. A frissítő éles v0.7 kiadást csak közzététel után találhat a GitHubon. Ebben a munkamenetben nincs push, tag vagy release. Régi kiadás csak akkor telepíthető, ha megfelelő telepítő és SHA256SUMS.txt is szerepel az Assets között. A hash épségellenőrzés; nem kódaláírás.

## Kiadási megítélés

Ez egy **tesztelt v0.7 fejlesztői/elfogadási csomag**, valóban elkészült Windows-telepítővel. Nem állítható róla, hogy mind a 16 pont minden Windows-környezetben maradéktalanul és kiadásra készen bizonyított. Különösen a többfiókos eltávolítás és a régi per-user kiadásokról történő váltás még nyitott. Stabil kiadás előtt az előbbi kézi elfogadási próbák szükségesek.

## Használt elsődleges dokumentáció

- qBittorrent WebUI API 5.0+: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-5.0)
- qBittorrent külön profilos/portable használat: https://github.com/qbittorrent/qBittorrent/wiki/How-to-use-portable-mode
- Inno Setup kiadások: https://jrsoftware.org/isdl.php
