"""Exercise the real PowerShell remover exclusively against isolated fixture roots."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import json

REPO = Path(__file__).resolve().parents[1]
OWNED_ID = '4D0F0B02-0C6E-4C4C-9DFA-DBDAE8A15F5F'


@unittest.skipUnless(os.name == 'nt', 'Windows cleanup helper')
class CleanupTests(unittest.TestCase):
    def setUp(self):
        temp = REPO / '.test-tmp'
        temp.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='uninstall-v08-', dir=temp)
        self.root = Path(self.temp.name)
        (self.root / '.torrentmanager-test').write_text(OWNED_ID)
        self.app = self.root / 'Torrent Manager'
        self.app.mkdir()
        (self.app / '.torrentmanager-install').write_text(OWNED_ID)
        (self.app / 'TorrentManager.exe').write_bytes(b'app-owned')
        self.report = self.root / 'report.txt'
        self.addCleanup(self.temp.cleanup)

    def run_cleanup(self):
        return subprocess.run([
            str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'),
            '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
            '-File', str(REPO / 'uninstall_cleanup.ps1'), '-Mode', 'Remove',
            '-AppDirectory', str(self.app), '-TestRoot', str(self.root),
            '-ReportPath', str(self.report),
        ], capture_output=True, text=True, timeout=40,
            creationflags=subprocess.CREATE_NO_WINDOW)

    def test_removes_own_files_all_fixture_profiles_preserves_other_data(self):
        downloads = self.root / 'downloads'
        downloads.mkdir()
        (downloads / 'film.mkv').write_bytes(b'keep downloaded content')
        for user in ('Alice', 'Bob'):
            local = self.root / 'profiles' / user / 'AppData' / 'Local'
            owned = local / 'TorrentManager'
            owned.mkdir(parents=True)
            (owned / 'beallitasok.json').write_text(json.dumps({'qb_save_path': str(downloads)}))
            (owned / 'generated-cache').mkdir()
            (owned / 'generated-cache' / 'extra.bin').write_bytes(b'cache')
            qb = local / 'qBittorrent'
            qb.mkdir()
            (qb / 'settings.ini').write_bytes(b'keep qBittorrent settings')
        result = self.run_cleanup()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr + (self.report.read_text(encoding='utf-8-sig') if self.report.exists() else ''))
        self.assertFalse(self.app.exists())
        for user in ('Alice', 'Bob'):
            local = self.root / 'profiles' / user / 'AppData' / 'Local'
            self.assertFalse((local / 'TorrentManager').exists())
            self.assertEqual((local / 'qBittorrent/settings.ini').read_bytes(), b'keep qBittorrent settings')
        self.assertEqual((downloads / 'film.mkv').read_bytes(), b'keep downloaded content')

    def test_missing_ownership_marker_refuses_delete(self):
        (self.app / '.torrentmanager-install').unlink()
        result = self.run_cleanup()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.app / 'TorrentManager.exe').exists())

    def test_legacy_downloads_inside_owned_data_are_preserved(self):
        owned = self.root / 'profiles/Alice/AppData/Local/TorrentManager'
        downloads = owned / 'downloads'
        downloads.mkdir(parents=True)
        (downloads / 'film.mkv').write_bytes(b'keep')
        (owned / 'beallitasok.json').write_text(json.dumps({'qb_save_path': str(downloads)}))
        result = self.run_cleanup()
        self.assertNotEqual(result.returncode, 0)  # Reports an intentionally retained directory.
        self.assertEqual((downloads / 'film.mkv').read_bytes(), b'keep')
        self.assertFalse((owned / 'beallitasok.json').exists())
        self.assertIn('Preserved download directory', self.report.read_text(encoding='utf-8-sig'))

    def test_missing_test_marker_refuses_delete(self):
        (self.root / '.torrentmanager-test').unlink()
        self.assertNotEqual(self.run_cleanup().returncode, 0)
        self.assertTrue(self.app.exists())

    def test_junction_target_is_not_traversed(self):
        target = self.root / 'downloads'
        target.mkdir()
        (target / 'film.mkv').write_bytes(b'keep')
        junction = self.app / 'linked-cache'
        # Native PowerShell creates a directory junction without developer mode/admin.
        result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
            'New-Item -ItemType Junction -Path $env:TM_TEST_LINK -Target $env:TM_TEST_TARGET | Out-Null'],
            env=dict(os.environ, TM_TEST_LINK=str(junction), TM_TEST_TARGET=str(target)),
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_cleanup().returncode, 0)
        self.assertFalse(self.app.exists())
        self.assertEqual((target / 'film.mkv').read_bytes(), b'keep')

    def test_torrent_metainfo_inside_app_is_not_deleted(self):
        (self.app / 'personal.torrent').write_bytes(b'torrent metadata')
        self.assertNotEqual(self.run_cleanup().returncode, 0)
        self.assertEqual((self.app / 'personal.torrent').read_bytes(), b'torrent metadata')


if __name__ == '__main__':
    unittest.main()
