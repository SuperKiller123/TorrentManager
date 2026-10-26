# -*- coding: utf-8 -*-
"""Torrent Manager v0.5 – GB (SI), biztonságos v0.4 migráció."""
from decimal import Decimal, InvalidOperation

TOP_URL = "https://bithumen.be/browse.php?sort=seeders&d=DESC"
GITHUB_REPO = "SuperKiller123/TorrentManager"
DEFAULT = {
    "qb_url": "http://127.0.0.1:8080", "qb_username": "admin",
    "qb_password": "", "qb_save_path": "", "check_minutes": 5,
    "max_disk_usage_percent": 70, "max_managed_torrents": 50,
    "min_size_gb": "", "max_size_gb": "", "mode": "dry",
    "headless": False,
}
MODES = ("dry", "add", "full")
INT_KEYS = ("check_minutes", "max_disk_usage_percent", "max_managed_torrents")

def _legacy_gib_to_gb(raw):
    """A régi GiB-határ SI GB-ként is pontosan ugyanazt a bájtértéket jelölje."""
    try:
        amount = Decimal(str(raw or 0)) * (Decimal(1024) ** 3) / Decimal(1000000000)
        return format(amount.normalize(), 'f') if amount else ""
    except (InvalidOperation, ValueError):
        return raw

def normalize_settings(saved):
    if not isinstance(saved, dict):
        saved = {}
    result = dict(DEFAULT)
    for key in DEFAULT:
        if key in saved:
            result[key] = saved[key]
    if "min_size_gb" not in saved and "min_size_gib" in saved:
        result["min_size_gb"] = _legacy_gib_to_gb(saved["min_size_gib"])
    if "max_size_gb" not in saved and "max_size_gib" in saved:
        result["max_size_gb"] = _legacy_gib_to_gb(saved["max_size_gib"])
    if "mode" not in saved:
        if saved.get("dry_run", True):
            result["mode"] = "dry"
        elif saved.get("enable_additions", False):
            result["mode"] = "full" if saved.get("enable_deletions") and saved.get("delete_files") else "add"
    if result["mode"] not in MODES:
        result["mode"] = "dry"
    disk = result.get("max_disk_usage_percent")
    if isinstance(disk, float) and disk.is_integer():
        result["max_disk_usage_percent"] = int(disk)
    return result

def validate_settings(raw):
    result = normalize_settings(raw)
    for key in INT_KEYS:
        value = str(result[key]).strip()
        if not value.isdecimal():
            raise ValueError(f"{key}: csak nemnegatív egész szám adható meg.")
        result[key] = int(value)
    if not 1 <= result["check_minutes"] <= 1440:
        raise ValueError("Az ellenőrzési időköz 1–1440 perc lehet.")
    if not 1 <= result["max_managed_torrents"] <= 500:
        raise ValueError("A torrentek száma 1–500 lehet.")
    if not 1 <= result["max_disk_usage_percent"] <= 99:
        raise ValueError("A tárhelykorlát 1–99% lehet.")
    for key in ("min_size_gb", "max_size_gb"):
        value = str(result.get(key) or "").strip().replace(",", ".")
        if not value:
            result[key] = ""
            continue
        try:
            decimal = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("A torrentméret pozitív GB-érték vagy üres mező lehet.") from exc
        if not decimal.is_finite() or decimal <= 0 or decimal > 1000000:
            raise ValueError("A torrentméret 0-nál nagyobb, legfeljebb 1 000 000 GB lehet.")
        result[key] = format(decimal.normalize(), 'f')
    if result["min_size_gb"] and result["max_size_gb"] and Decimal(result["min_size_gb"]) > Decimal(result["max_size_gb"]):
        raise ValueError("A minimális méret nem lehet nagyobb a maximálisnál.")
    if result["mode"] not in MODES:
        raise ValueError("Ismeretlen működési üzemmód.")
    return result

def allowed_size(size_bytes, settings):
    # bytes are integers; the limits are decimal GB, not binary GiB.
    minimum = Decimal(str(settings.get("min_size_gb") or "0")) * 1000000000
    maximum = Decimal(str(settings.get("max_size_gb") or "0")) * 1000000000
    return size_bytes >= minimum and (not maximum or size_bytes <= maximum)
