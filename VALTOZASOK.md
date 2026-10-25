# v0.4.0 – Változások

- Áttérés a fix BitHuMen `sort=seeders&d=DESC` toplistára.
- Toplista elemszám = összes qBittorrent torrentszámkorlát; nem szerkeszthető URL és külön elemszám.
- Mentés gomb csak eltérésnél aktív; egyszerűbb beállítások.
- Három egymást kizáró üzemmód; törlés esetén qBittorrent torrent + fájlok együtt.
- Törlési védelem: saját rekord hash/név, azonos mentési mappa, két teljes ellenőrzés, hiányos lista esetén blokkolás.
- Opcionális indítás Windows bejelentkezéskor és qBittorrent indítása.
- Min/max torrentméret GiB metainfo alapján; várható tárhely-telítettség ellenőrzése.
- Kezdőlap részletesebb, valós qBittorrent-állapot alapú számlálással; rövid műveleti naplóval.
- Nyilvános `SuperKiller123/TorrentManager` GitHub Releases tároló előbeállítása.
- GitHub Actions modern Node.js-kompatibilis actions verziókkal; build automatikusan main push-ra.
- CPU-hőmérséklet-figyelés **nincs**, a korábbi ötletet teljesen elvetettük.
