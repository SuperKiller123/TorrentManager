# Torrent Manager v0.5.0 – változások

- Áttervezett, kompakt Kezdőlap: Indítás/Leállítás, tárhely, üzemmód, korlátok, legutóbbi események; felesleges számlálók és gyorslinkek nélkül.
- Beállítások: Mutatás/Elrejtés jelszógomb, „Torrentek száma (darab)”, üres méretmezők, valódi decimális GB.
- Régi GiB-korlátok pontos migrációja SI GB-ba.
- qBittorrent automatikus, lehetőség szerint minimalizált indítása; Windows-autostart kapcsolók eltávolítása és korábbi Run-bejegyzés takarítása.
- Napló: magyar karaktereknek megfelelő Segoe UI, UTF-8 kezelés, felesleges státuszjelzők nélkül.
- Frissítések: rögzített GitHub tároló, kétgombos frissítési oldal, programismertető.
- Új külön frissítési segéd, csendes Inno Setup, korábbi telepítési beállítások megőrzése, automatikus újraindítás (csak sikeres telepítés után).
- Törlésvédelmi ellenőrzések, motor és qBittorrent-kezelési működés megőrizve.

A Windows UAC-megerősítés nem kerülhető meg. A v0.4-ről v0.5-re váltásnál még a v0.4 frissítési rendszer működik; az új csendes frissítő a v0.5-ből induló következő kiadásnál használható.
