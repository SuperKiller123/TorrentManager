# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from localization import LANGUAGES, TEXT, tr
from webui import check_webui
from policy import normalize_settings
from updater import list_releases, VERSION

class FakeResponse:
    def __init__(self, status=200, text='Ok.', data=None):
        self.status_code=status; self.text=text; self.data=data
        self.ok = status == 200
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('http error')
    def json(self): return self.data

class Session:
    def __init__(self, login=None, version=None, releases=None):
        self.login = login or FakeResponse()
        self.version = version or FakeResponse(text='5.1.0')
        self.releases = releases or FakeResponse(data=[])
        self.calls=[]
    def post(self, url, **kw):
        self.calls.append(('post',url,kw))
        return self.login
    def get(self, url, **kw):
        self.calls.append(('get',url,kw))
        if url.endswith('/releases?per_page=100'):
            return self.releases
        return self.version

class V06Tests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(VERSION, '0.8')
    def test_12_languages_with_hungarian_and_german(self):
        self.assertEqual(len(LANGUAGES), 12)
        for code in LANGUAGES:
            with self.subTest(code=code):
                self.assertIn(code, TEXT)
                self.assertTrue(tr(code,'settings'))
                self.assertTrue(tr(code,'save'))
                self.assertTrue(tr(code,'updates'))
                self.assertTrue(tr(code,'min_gb'))
                self.assertEqual(len(TEXT[code]), len(TEXT['hu']))
    def test_settings_defaults_and_migration(self):
        self.assertEqual(normalize_settings({})['language'], 'hu')
        self.assertEqual(normalize_settings({})['theme'], 'dark')
        self.assertEqual(normalize_settings({})['headless'], True)
        self.assertEqual(normalize_settings({'language':'xx'})['language'],'hu')
        self.assertEqual(normalize_settings({'language':'ur'})['language'],'ur')
        self.assertEqual(normalize_settings({'theme':'light'})['theme'],'light')
    def test_webui_ready(self):
        session=Session()
        self.assertEqual(check_webui('http://127.0.0.1:8080', 'admin', 'secret',session=session),
                         (True,'connected'))
        self.assertEqual(len(session.calls),2)
        self.assertEqual(session.calls[0][0],'post')
    def test_webui_not_ready_until_login(self):
        session=Session(login=FakeResponse(403,'Forbidden'))
        self.assertEqual(check_webui('http://localhost:8080', 'admin','bad',session=session),
                         (False,'bad_credentials'))
        self.assertEqual(len(session.calls),1)
    def test_webui_missing_credentials(self):
        self.assertEqual(check_webui('http://127.0.0.1:8080','admin',''),
                         (False,'missing_credentials'))
        self.assertEqual(check_webui('invalid','admin','secret'),
                         (False,'invalid_url'))
    def test_list_releases_and_older(self):
        def release(version, draft=False, prerelease=False, files=True):
            tag='v'+version
            assets=([{'name':f'TorrentManager-Setup-v{version}.exe','browser_download_url': 'https://github.com/a/b'},
                    {'name':'SHA256SUMS.txt','browser_download_url': 'https://github.com/a/b'}] if files else [])
            return {'tag_name':tag,'draft':draft,'prerelease':prerelease,'assets':assets}
        session=Session(releases=FakeResponse(data=[release('0.3.0'),release('0.6.0'),
                       release('0.4.0'),release('0.8.0',draft=True),
                       release('0.7.0',prerelease=True),release('0.5.0',files=False)]))
        items=list_releases('author/repo',session=session)
        self.assertEqual([item['version'] for item in items],['v0.6','v0.5','v0.4','v0.3'])
        self.assertIsNone(items[1]['installer'])
        self.assertIsNotNone(items[2]['installer'])
        self.assertTrue(all(not item['newer'] for item in items))
    def test_installer_previous_shortcut_and_custom_language(self):
        ins=(Path(__file__).resolve().parents[1]/'installer.iss').read_text(encoding='utf-8')
        self.assertIn('UsePreviousTasks=yes',ins)
        self.assertIn('ShouldSkipPage(PageID: Integer)',ins)
        self.assertNotIn('CreateInputOptionPage',ins)
        self.assertIn('Key: "language"; String: "{language}"',ins)
    def test_start_requires_webui(self):
        src=(Path(__file__).resolve().parents[1]/'TorrentManager.py').read_text(encoding='utf-8')
        self.assertIn('if not self.connected:',src)
        self.assertIn('headless=True',(Path(__file__).resolve().parents[1]/'motor.py').read_text(encoding='utf-8'))
        self.assertIn("root.bind('<F11>'",src)
        self.assertNotIn("root.bind('<Escape>'",src)

if __name__=='__main__':unittest.main()
