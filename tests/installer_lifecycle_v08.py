"""Build/install/uninstall an isolated Inno fixture; never installs the production AppId.

Run explicitly on Windows. The installed payload is a harmless text stub, not the GUI.
Actual Windows UAC and offline-user hives still require a dedicated elevated VM test.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import winreg

REPO = Path(__file__).resolve().parents[1]
TEST_APPID = '{D186A29D-D24B-4A19-81C6-7EFD2330B872}_is1'
REG_PATH = 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\' + TEST_APPID
FLAGS = winreg.KEY_READ | winreg.KEY_WOW64_64KEY


def run():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, FLAGS):
            raise RuntimeError('An older lifecycle fixture is installed; refusing to overwrite it.')
    except FileNotFoundError:
        pass
    parent = REPO / '.test-tmp'
    parent.mkdir(exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='installer-v08-', dir=parent))
    payload = root / 'payload'
    payload.mkdir()
    (payload / 'TorrentManager.exe').write_bytes(b'isolated lifecycle test stub, never executed')
    (root / '.torrentmanager-test').write_text('4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F')
    downloads = root / 'downloads'
    downloads.mkdir()
    sentinel = downloads / 'film.mkv'
    sentinel.write_bytes(b'keep torrent content unchanged')
    qb_sentinels = []
    for user in ('Alice', 'Bob'):
        local = root / 'profiles' / user / 'AppData/Local'
        owned = local / 'TorrentManager'
        owned.mkdir(parents=True)
        (owned / 'beallitasok.json').write_text(json.dumps({'qb_save_path': str(downloads)}))
        (owned / 'cache.bin').write_bytes(b'own cache')
        qb = local / 'qBittorrent'
        qb.mkdir()
        qb_sentinel = qb / 'settings.ini'
        qb_sentinel.write_bytes(b'keep qBittorrent settings unchanged')
        qb_sentinels.append(qb_sentinel)
    compiler = REPO / '.tools/Inno/ISCC.exe'
    compiled = subprocess.run([str(compiler), '/Qp', f'/DTM_TEST_ROOT={root}',
        f'/DTM_TEST_SOURCE={payload}', f'/O{root}', '/FTorrentManager-test-v08',
        str(REPO / 'installer.iss')], capture_output=True, text=True, timeout=180)
    (root / 'compile.log').write_text(compiled.stdout + compiled.stderr, encoding='utf-8')
    if compiled.returncode:
        raise RuntimeError(f'Compiler failed; see {root / "compile.log"}: {compiled.stdout} {compiled.stderr}')
    setup = root / 'TorrentManager-test-v08.exe'
    app = root / 'Torrent Manager'
    installed = subprocess.run([str(setup), '/VERYSILENT', '/SUPPRESSMSGBOXES',
        '/NORESTART', '/LANG=hu', '/TASKS=desktopicon,startup,close_to_tray,pin_taskbar,pin_start',
        f'/LOG={root / "install.log"}'], timeout=120)
    if installed.returncode:
        raise RuntimeError(f'Install exit code {installed.returncode}; fixture at {root}')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, FLAGS) as key:
        display = winreg.QueryValueEx(key, 'DisplayName')[0]
    assert display == 'Torrent Manager', display
    assert 'language=hu' in (app / 'install-defaults.ini').read_text(encoding='utf-8-sig')
    # Runtime-generated files that Inno never registered must also disappear.
    generated = app / 'generated-cache/nested'
    generated.mkdir(parents=True)
    (generated / 'cache.bin').write_bytes(b'own generated file')
    uninstall = app / 'unins000.exe'
    removed = subprocess.run([str(uninstall), '/VERYSILENT', '/SUPPRESSMSGBOXES',
        '/NORESTART', f'/LOG={root / "uninstall.log"}'], timeout=120)
    assert removed.returncode == 0, removed.returncode
    deadline = time.monotonic() + 10
    while app.exists() and time.monotonic() < deadline:
        time.sleep(.1)  # Inno's final self-delete finishes after its launcher exits.
    assert not app.exists(), f'Install directory remains: {app}'
    for user in ('Alice', 'Bob'):
        assert not (root / 'profiles' / user / 'AppData/Local/TorrentManager').exists()
    assert sentinel.read_bytes() == b'keep torrent content unchanged'
    for sentinel in qb_sentinels:
        assert sentinel.read_bytes() == b'keep qBittorrent settings unchanged'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, FLAGS):
            raise AssertionError('Test uninstall registry entry remains')
    except FileNotFoundError:
        pass
    print(json.dumps({'installer_lifecycle': 'passed', 'display_name': display,
        'install_directory_removed': True, 'all_fixture_profile_data_removed': True,
        'torrent_and_qb_sentinels_unchanged': True, 'production_profiles_accessed': False,
        'evidence_directory': str(root)}))


if __name__ == '__main__':
    run()
