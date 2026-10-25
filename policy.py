# -*- coding: utf-8 -*-
"""v0.4: egyetlen, biztonságosan migrálható beállítási séma."""
TOP_URL = "https://bithumen.be/browse.php?sort=seeders&d=DESC"
GITHUB_REPO = "SuperKiller123/TorrentManager"
DEFAULT = {
    "qb_url": "http://127.0.0.1:8080", "qb_username": "admin",
    "qb_password": "", "qb_save_path": "", "check_minutes": 5,
    "max_disk_usage_percent": 70, "max_managed_torrents": 50,
    "min_size_gib": 0, "max_size_gib": 0, "mode": "dry",
    "startup_windows": False, "launch_qbittorrent": False,
    "github_repository": GITHUB_REPO, "headless": False,
}
MODES = ("dry", "add", "full")
INT_KEYS = ("check_minutes", "max_disk_usage_percent", "max_managed_torrents", "min_size_gib", "max_size_gib")

def normalize_settings(saved):
    """A v0.3 saját adatokat megőrizzük; önmagában egy korábbi törléskapcsoló nem engedélyez törlést."""
    if not isinstance(saved, dict):
        saved = {}
    result = dict(DEFAULT)
    for key in DEFAULT:
        if key in saved:
            result[key] = saved[key]
    if "mode" not in saved:
        if saved.get("dry_run", True):
            result["mode"] = "dry"
        elif saved.get("enable_additions", False):
            # Régi fájltörlés nélküli beállításból sosem lesz automatikus fájltörlés.
            result["mode"] = "full" if saved.get("enable_deletions") and saved.get("delete_files") else "add"
    if result["mode"] not in MODES:
        result["mode"] = "dry"
    # v0.3 a százalékot lebegőpontos értékként mentette, pl. 70.0.
    old_disk = result.get("max_disk_usage_percent")
    if isinstance(old_disk, float) and old_disk.is_integer():
        result["max_disk_usage_percent"] = int(old_disk)
    if not result.get("github_repository"):
        result["github_repository"] = GITHUB_REPO
    # A régi browse_url/top_count/enable_deletions mezőket szándékosan elhagyjuk.
    return result

def validate_settings(raw):
    result = normalize_settings(raw)
    for key in INT_KEYS:
        val = str(result[key]).strip()
        if not val.isdecimal():
            raise ValueError(f"{key}: csak nemnegatív egész szám adható meg.")
        result[key] = int(val)
    if not 1 <= result["check_minutes"] <= 1440:
        raise ValueError("Az ellenőrzési időköz 1–1440 perc lehet.")
    if not 1 <= result["max_managed_torrents"] <= 500:
        raise ValueError("A maximális torrentszám 1–500 lehet.")
    if not 1 <= result["max_disk_usage_percent"] <= 99:
        raise ValueError("A tárhelykorlát 1–99% lehet.")
    if result["max_size_gib"] and result["min_size_gib"] > result["max_size_gib"]:
        raise ValueError("A minimális méret nem lehet nagyobb a maximálisnál.")
    if result["mode"] not in MODES:
        raise ValueError("Ismeretlen működési üzemmód.")
    return result

def allowed_size(size_bytes, settings):
    unit = 1024 ** 3
    minimum = int(settings.get("min_size_gib", 0))
    maximum = int(settings.get("max_size_gib", 0))
    return size_bytes >= minimum * unit and (maximum == 0 or size_bytes <= maximum * unit)
