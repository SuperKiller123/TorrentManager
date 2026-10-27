# Torrent Manager v0.6.0 – változásnapló

A kiadás a 18 felmerült fejlesztési kérés alapján készült, a következő pontosításokkal:

1. A qBittorrent induló ablakának Windows-alapú minimalizálása; már futó példányt nem módosít.
2. WebUI hitelesítés, készenlét ellenőrzése, Indítás gomb reteszelése, háttérben ismételt próbák.
3. Maximalizált kezdőablak.
4. A Chrome/Chromium automatikusan kizárólag headless módban működik; a belépési ablak kézzel nyitható.
5. Natív Windows címsor témához igazítása; F11 mód, kilépés csak F11-gyel, Esc-hez nincs hozzárendelve kilépés.
6. Egységes ikon: oldalsáv, EXE, Inno Setup.
7. Megőrzött telepítési feladatok és könyvtár, új verziónál a visszakérdezés kihagyása.
8. Csak „Torrent Manager” az oldalsáv tetején, verzió nélkül, azonos betűvastagsággal.
9. Elérhető GitHub-kiadások közötti verzióválasztás; telepítő/SHA256 ellenőrzés; GitHub-gomb; hosszabb ismertető.
10. Sűrű kezdőlap nyolc mutatóval, állapotjelzőkkel, tárhelyanimációval, rövid naplóval.
11. Sötét, világos, Windows témája szerint.
12. Mentés gomb a Beállítások címével egy sorban.
13. Reszponzív Tkinter méretezés és rövid ~60 FPS animációk; nem cél korlátlan FPS.
14. Konzolkimenet UTF-8, alapból Segoe UI; valós Windows alatt még ellenőrizendő.
15. Alsó oldalsávfeliratok eltávolítása.
16. A Beállítások lapra visszalépve a görgetés felülről indul.
17. 10 sokak által beszélt nyelv + magyar és német (12 nyelv) egy telepítőben és programban; a motor naplója jelenleg magyar.
18. A Frissítések fül a kijelölt tartalomterületet kitölti.

## Tesztelés

38 offline Python-teszt és Tkinter GUI-smoke-teszt sikeres. Windows build, Windows-tálcás viselkedés, Inno Setup és élő BitHuMen/qBittorrent teszt még szükséges a kiadás jóváhagyásához.
