# Változások – v0.3.0

- Teljes GUI-újratervezés: sötét menü, áttekintő oldal, kártyás információmegjelenítés, görgethető beállítások.
- Élő és korábbi napló egy külön oldalon; hiba esetén a motor kilépési kódja megjelenik.
- Chromium-útvonal automatikus keresése csomagolt böngészőből vagy AppData Playwright-cache-ből.
- GitHub Releases frissítésellenőrzés, SHA-256 alapján ellenőrzött Windows-telepítő letöltése, kézi indítás.
- GitHub Actions build kézi futtatással vagy verziócímkével; portable ZIP és telepítő; ellenőrzőösszegek.
- Meglévő `%LOCALAPPDATA%\TorrentManager` beállítások, böngészőprofil és nyilvántartás változatlanul használható.
- A torrentmotor top50-, tárhely- és törlési logikája a kipróbált v0.2 verzióból származik, kivéve a böngészőútvonal inicializálását.
