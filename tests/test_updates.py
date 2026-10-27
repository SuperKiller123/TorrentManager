# -*- coding: utf-8 -*-
"""Offline tesztek: kiadásfigyelés, letöltés ellenőrzése és böngészőútvonal."""
import hashlib
import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import updater


class FakeResponse:
    def __init__(self, body=b"", json_data=None, status=200):
        self.content = body
        self.text = body.decode("utf-8")
        self.status_code = status
        self.json_data = json_data
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")
    def json(self):
        return self.json_data
    def iter_content(self, chunk_size):
        yield self.content
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        pass


class FakeSession:
    def __init__(self, responses):
        self.responses = iter(responses)
    def get(self, url, **_kwargs):
        assert url.startswith("https://")
        return next(self.responses)


class UpdateTests(unittest.TestCase):
    def test_version_comparison(self):
        self.assertTrue(updater.parse_version("v0.3.10") > updater.parse_version("0.3.2"))
        self.assertTrue(updater.parse_version("0.5.0") > updater.parse_version("v0.4.0"))
        with self.assertRaises(updater.UpdateError):
            updater.parse_version("v0.4.0-preview")

    def test_repository_validation(self):
        self.assertEqual(updater.normalize_repo(" user/repo "), "user/repo")
        for bad in ("", "https://github.com/me/repo", "../../evil", "user/repo/extra"):
            with self.assertRaises(updater.UpdateError):
                updater.normalize_repo(bad)

    def test_check_latest(self):
        response = FakeResponse(json_data={
            "tag_name": "v0.7.0", "html_url": "https://github.com/user/repo/releases/tag/v0.7.0",
            "body": "Javítások", "assets": [
                {"name": "TorrentManager-Setup-v0.7.0.exe", "browser_download_url": "https://github.com/user/repo/a"},
                {"name": "SHA256SUMS.txt", "browser_download_url": "https://github.com/user/repo/b"},
            ]})
        rel = updater.check_latest("user/repo", session=FakeSession([response]))
        self.assertTrue(rel["newer"])
        self.assertIsNotNone(rel["installer"])
        self.assertIsNotNone(rel["checksums"])

    def test_download_integrity(self):
        content = b"Safe test executable bytes"
        expected = hashlib.sha256(content).hexdigest()
        rel = {"installer": {"name": "TorrentManager-Setup-v0.5.0.exe",
                             "browser_download_url": "https://github.com/user/repo/installer"},
               "checksums": {"name": "SHA256SUMS.txt",
                             "browser_download_url": "https://github.com/user/repo/sha"}}
        sums = f"{expected}  TorrentManager-Setup-v0.5.0.exe\n".encode()
        with tempfile.TemporaryDirectory() as td:
            result = updater.download_installer(rel, td,
                session=FakeSession([FakeResponse(sums), FakeResponse(content)]))
            self.assertEqual(result.read_bytes(), content)
            with self.assertRaises(updater.UpdateError):
                updater.download_installer(rel, td,
                    session=FakeSession([FakeResponse(sums), FakeResponse(b"tampered")]))
            self.assertFalse((Path(td) / "TorrentManager-Setup-v0.5.0.exe.download").exists())

    def test_reject_bad_download_url(self):
        with self.assertRaises(updater.UpdateError):
            updater.valid_asset_url({"browser_download_url": "http://example.com/a.exe"})

    def test_find_browser_frozen(self):
        import paths
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            browser = home / "browsers" / "chromium-1248" / "chrome-win64"
            browser.mkdir(parents=True)
            (browser / "chrome.exe").touch()
            with patch.object(paths.sys, "frozen", True, create=True), patch.object(paths, "BASE", home):
                self.assertEqual(paths.find_playwright_browsers(), home / "browsers")


if __name__ == "__main__":
    unittest.main()
