# -*- coding: utf-8 -*-
"""GitHub Releases-alapú, ellenőrzött, kifejezett kérésre induló frissítés."""
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

VERSION = "0.6.0"
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
INSTALLER_PATTERN = re.compile(r"^TorrentManager-Setup-v[0-9]+(?:\.[0-9]+){1,3}\.exe$", re.I)
CHECKSUM_NAME = "SHA256SUMS.txt"


class UpdateError(RuntimeError):
    pass


def parse_version(value):
    value = value.strip().lstrip("vV")
    if not re.fullmatch(r"\d+(?:\.\d+){1,3}", value):
        raise UpdateError("Nem értelmezhető verziószám: " + value)
    return tuple(int(part) for part in value.split("."))


def normalize_repo(value):
    repo = value.strip()
    if not REPO_PATTERN.fullmatch(repo) or ".." in repo:
        raise UpdateError("A GitHub-tároló alakja: felhasználó/projekt")
    return repo


def check_latest(repository, current=VERSION, session=None):
    repository = normalize_repo(repository)
    http = session or requests
    url = f"https://api.github.com/repos/{repository}/releases/latest"
    try:
        response = http.get(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "TorrentManager-Updater"}, timeout=20)
        if response.status_code == 404:
            raise UpdateError("Ehhez a GitHub-tárolóhoz még nincs közzétett kiadás, vagy a tároló nem nyilvános.")
        response.raise_for_status()
        release = response.json()
    except requests.RequestException as exc:
        raise UpdateError(f"A frissítések ellenőrzése nem sikerült: {exc}") from exc
    if not isinstance(release, dict):
        raise UpdateError("Érvénytelen GitHub-válasz.")
    newer = parse_version(str(release.get("tag_name", ""))) > parse_version(current)
    assets = release.get("assets") or []
    installer = next((a for a in assets if isinstance(a, dict) and INSTALLER_PATTERN.fullmatch(a.get("name", ""))), None)
    sums = next((a for a in assets if isinstance(a, dict) and a.get("name") == CHECKSUM_NAME), None)
    return {
        "version": str(release.get("tag_name")),
        "newer": newer,
        "url": str(release.get("html_url", "")),
        "notes": str(release.get("body", ""))[:1600],
        "installer": installer,
        "checksums": sums,
    }



def list_releases(repository, session=None):
    """List verified-installable current and historical GitHub releases.

    Reject prereleases and malformed/mismatched installer versions; only use
    GitHub release download URLs and the signed-in-release SHA256 manifest.
    """
    repository = normalize_repo(repository)
    http = session or requests
    url = f"https://api.github.com/repos/{repository}/releases?per_page=100"
    try:
        response = http.get(url, headers={"Accept":"application/vnd.github+json",
                                           "User-Agent":"TorrentManager-Updater"}, timeout=25)
        if response.status_code == 404:
            raise UpdateError("Nem találhatók nyilvános GitHub-kiadások.")
        response.raise_for_status()
        entries = response.json()
    except requests.RequestException as exc:
        raise UpdateError(f"A kiadások lekérdezése sikertelen: {exc}") from exc
    if not isinstance(entries, list):
        raise UpdateError("Érvénytelen kiadáslista a GitHubtól.")
    releases = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('draft') or entry.get('prerelease'):
            continue
        tag = str(entry.get('tag_name') or '')
        try:
            version = parse_version(tag)
        except UpdateError:
            continue
        if version in seen:
            continue
        seen.add(version)
        assets = entry.get('assets') or []
        installer = next((a for a in assets if isinstance(a, dict)
                 and a.get('name','').casefold() == f"torrentmanager-setup-v{tag.lstrip('vV')}.exe".casefold()), None)
        sums = next((a for a in assets if isinstance(a, dict)
                     and a.get('name') == CHECKSUM_NAME), None)
        releases.append({'version': 'v' + tag.lstrip('vV'), 'newer': version > parse_version(VERSION),
                         'url': entry.get('html_url',''), 'notes': str(entry.get('body',''))[:1600],
                         'installer': installer, 'checksums': sums})
    releases.sort(key=lambda r: parse_version(r['version']), reverse=True)
    return releases


def valid_asset_url(asset):
    url = str(asset.get("browser_download_url", "")) if isinstance(asset, dict) else ""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise UpdateError("Nem biztonságos vagy hiányzó GitHub-letöltési hivatkozás.")
    return url


def sha256_for_file(checksum_text, filename):
    for row in checksum_text.splitlines():
        match = re.match(r"^([a-fA-F0-9]{64})\s+\*?(.+)$", row.strip())
        if match and match.group(2) == filename:
            return match.group(1).lower()
    raise UpdateError("A telepítő SHA-256 ellenőrzőösszege nem található a kiadásban.")


def download_installer(release, folder, session=None):
    """Csak érvényes SHA256SUMS.txt mellett ad vissza futtatható telepítőt."""
    installer = release.get("installer")
    sums = release.get("checksums")
    if not installer or not sums:
        raise UpdateError("A kiadásból hiányzik a telepítő vagy a SHA256SUMS.txt.")
    name = installer.get("name", "")
    if not INSTALLER_PATTERN.fullmatch(name):
        raise UpdateError("Váratlan telepítőfájlnév.")
    http = session or requests
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    tmp = folder / (name + ".download")
    try:
        hashes_response = http.get(valid_asset_url(sums), timeout=30)
        hashes_response.raise_for_status()
        expected = sha256_for_file(hashes_response.text, name)
        digest = hashlib.sha256()
        written = 0
        with http.get(valid_asset_url(installer), stream=True, timeout=(20, 90)) as response:
            response.raise_for_status()
            with tmp.open("wb") as out:
                for chunk in response.iter_content(chunk_size=128 * 1024):
                    if not chunk:
                        continue
                    written += len(chunk)
                    if written > 700 * 1024 * 1024:
                        raise UpdateError("A letöltött telepítő túllépte a méretkorlátot.")
                    digest.update(chunk)
                    out.write(chunk)
        if written == 0 or digest.hexdigest().lower() != expected:
            raise UpdateError("A frissítés ellenőrzőösszege nem egyezik. A telepítő nem indítható.")
        tmp.replace(target)
        return target
    except (requests.RequestException, OSError) as exc:
        raise UpdateError(f"A frissítés letöltése sikertelen: {exc}") from exc
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
