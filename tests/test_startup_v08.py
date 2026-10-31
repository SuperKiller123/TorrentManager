"""Startup guards: persisted-session authentication and safe background handling."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auth_browser import (page_status, ensure_session, probe_context,
                          READY, LOGIN_REQUIRED, UNAVAILABLE)
from browser_profile import ProfileLock, ProfileBusyError
from windows_integration import qb_tray_enabled
from webui import webui_session


class Page:
    def __init__(self, url, password=False, details=False, logout=False):
        self.url = url
        self.selectors = {'input[type="password"]': password,
                          'a[href*="details.php?id="]': details,
                          'a[href*="logout.php"]': logout}
    def locator(self, selector):
        return SimpleNamespace(count=lambda: int(self.selectors.get(selector, False)))
    def is_closed(self):
        return False
    def goto(self, *args, **kwargs):
        return SimpleNamespace(status=200)


class StartupTests(unittest.TestCase):
    def test_auth_requires_expected_origin_and_torrent_access(self):
        self.assertEqual(page_status(Page('https://bithumen.be/browse.php', details=True)), READY)
        self.assertEqual(page_status(Page('https://bithumen.be/login.php', password=True)), LOGIN_REQUIRED)
        self.assertEqual(page_status(Page('https://bithumen.be/browse.php', password=True, details=True)), LOGIN_REQUIRED)
        self.assertEqual(page_status(Page('https://other.example/browse.php', details=True)), UNAVAILABLE)
        self.assertEqual(page_status(Page('https://bithumen.be/browse.php')), UNAVAILABLE)

    def test_valid_saved_session_does_not_open_visible_browser(self):
        context = Mock(pages=[Page('https://bithumen.be/browse.php', details=True)])
        browser = Mock()
        browser.chromium.launch_persistent_context.return_value = context
        self.assertEqual(ensure_session(browser, Path('test-profile')), READY)
        browser.chromium.launch_persistent_context.assert_called_once_with('test-profile', headless=True)
        context.close.assert_called_once()

    def test_login_context_starts_only_after_check_is_closed(self):
        order = []
        check = Mock(pages=[Page('https://bithumen.be/login.php', password=True)])
        check.close.side_effect = lambda: order.append('closed check')
        login = Mock(pages=[Page('https://bithumen.be/browse.php', details=True)])
        def launch(*args, **kwargs):
            if kwargs['headless']:
                return check
            order.append('opened login')
            return login
        browser = Mock()
        browser.chromium.launch_persistent_context.side_effect = launch
        self.assertEqual(ensure_session(browser, Path('profile')), READY)
        self.assertEqual(order, ['closed check', 'opened login'])
        login.close.assert_called_once()

    def test_check_only_does_not_prompt(self):
        context = Mock(pages=[Page('https://bithumen.be/login.php', password=True)])
        browser = Mock()
        browser.chromium.launch_persistent_context.return_value = context
        self.assertEqual(ensure_session(browser, Path('profile'), check_only=True), LOGIN_REQUIRED)
        self.assertEqual(browser.chromium.launch_persistent_context.call_count, 1)

    def test_profile_lock_excludes_another_owner_and_releases_after_error(self):
        with tempfile.TemporaryDirectory() as folder:
            profile = Path(folder) / 'profile'
            with self.assertRaisesRegex(ValueError, 'test'):
                with ProfileLock(profile):
                    with self.assertRaises(ProfileBusyError):
                        with ProfileLock(profile):
                            self.fail('Concurrent profile opened')
                    raise ValueError('test')
            with ProfileLock(profile):
                pass

    def test_tray_settings_are_read_only_and_disabled_is_respected(self):
        with tempfile.TemporaryDirectory() as folder:
            ini = Path(folder) / 'qBittorrent.ini'
            self.assertFalse(qb_tray_enabled(ini))
            for value, expected in [('true', True), ('false', False), ('nonsense', False)]:
                content = '[Preferences]\nGeneral\\SystrayEnabled=' + value + '\n'
                ini.write_text(content, encoding='utf-8')
                before = ini.read_bytes()
                self.assertEqual(qb_tray_enabled(ini), expected)
                self.assertEqual(ini.read_bytes(), before)

    def test_reverse_proxy_origin_has_no_path(self):
        with webui_session('https://host.example/qb') as session:
            self.assertEqual(session.headers['Origin'], 'https://host.example')
            self.assertEqual(session.headers['Referer'], 'https://host.example/qb/')


@unittest.skipUnless(os.environ.get('TM_BROWSER_TESTS') == '1', 'Opt-in isolated Chromium integration')
class ChromiumStartupTests(unittest.TestCase):
    def test_real_browser_check_login_redirect_and_saved_cookie(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as folder, sync_playwright() as p:
            context = p.chromium.launch_persistent_context(folder, headless=True)
            def respond(route):
                if 'tm_test_session=verified' in route.request.headers.get('cookie', ''):
                    route.fulfill(status=200, content_type='text/html', body='<a href="details.php?id=42">Test torrent</a>')
                else:
                    route.fulfill(status=200, content_type='text/html', body='<input type="password">')
            context.route('https://bithumen.be/**', respond)
            self.assertEqual(probe_context(context), LOGIN_REQUIRED)
            context.add_cookies([{'name': 'tm_test_session', 'value': 'verified',
                                 'domain': 'bithumen.be', 'path': '/', 'expires': 4102444800}])
            self.assertEqual(probe_context(context), READY)
            context.close()
            context = p.chromium.launch_persistent_context(folder, headless=True)
            try:
                context.route('https://bithumen.be/**', respond)
                self.assertEqual(probe_context(context), READY)
                context.clear_cookies()
                self.assertEqual(probe_context(context), LOGIN_REQUIRED)
                context.unroute('https://bithumen.be/**')
                context.route('https://bithumen.be/**', lambda route: route.fulfill(
                    status=503, content_type='text/html', body='<h1>Unavailable</h1>'))
                self.assertEqual(probe_context(context), UNAVAILABLE)
                context.unroute('https://bithumen.be/**')
                context.route('https://bithumen.be/**', lambda route: route.fulfill(
                    status=200, content_type='text/html', body='<h1>Unexpected page</h1>'))
                self.assertEqual(probe_context(context), UNAVAILABLE)
            finally:
                context.close()


if __name__ == '__main__':
    unittest.main()
