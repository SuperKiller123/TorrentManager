"""Real HTTP session tests plus isolated Tk layout and first-run checks."""
import json
import os
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from webui import check_webui, webui_session, read_telemetry
from updater import parse_version
from policy import normalize_settings


class Handler(BaseHTTPRequestHandler):
    ready = True
    def log_message(self, *args):
        pass
    def reply(self, status, body, cookie=False):
        self.send_response(status)
        if cookie:
            self.send_header('Set-Cookie', 'SID=test-session; Path=/; HttpOnly')
        self.end_headers()
        self.wfile.write(body.encode())
    def do_POST(self):
        if not type(self).ready:
            return self.reply(503,'Starting')
        form = parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode())
        if self.headers.get('Referer') != f'http://{self.headers["Host"]}/':
            return self.reply(403,'Bad referer')
        if form != {'username':['admin'],'password':['árvíztűrő & secret']}:
            return self.reply(200,'Fails.')
        self.reply(200,'Ok.',True)
    def do_GET(self):
        if self.headers.get('Cookie') != 'SID=test-session':
            return self.reply(403,'Forbidden')
        body = {'/api/v2/app/version':'5.1.4',
                '/api/v2/transfer/info':json.dumps({'dl_info_speed':1234567,'up_info_speed':765432}),
                '/api/v2/torrents/info':'[{"hash":"a"}]'}.get(self.path,'')
        self.reply(200 if body else 404,body)


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()
    def test_cookie_unicode_credentials_and_proxy_bypass(self):
        with patch.dict(os.environ, {'HTTP_PROXY':'http://127.0.0.1:1','NO_PROXY':''}):
            self.assertEqual(check_webui(self.url,'admin','árvíztűrő & secret'), (True,'connected'))
    def test_bad_credentials(self):
        self.assertEqual(check_webui(self.url,'admin','bad'), (False,'bad_credentials'))
    def test_starting_server_is_not_bad_password(self):
        Handler.ready = False
        try:
            self.assertEqual(check_webui(self.url,'admin','árvíztűrő & secret'), (False,'not_ready'))
        finally:
            Handler.ready = True
        self.assertEqual(check_webui(self.url,'admin','árvíztűrő & secret'), (True,'connected'))
    def test_actual_telemetry(self):
        with webui_session(self.url) as http:
            self.assertTrue(check_webui(self.url,'admin','árvíztűrő & secret',session=http)[0])
            self.assertEqual(read_telemetry(http,self.url), {'download':1234567,'upload':765432,'total':1})
    def test_gui_loop_recovers_from_startup(self):
        from TorrentManager import App
        app = App.__new__(App)
        import queue
        app.cfg = dict(qb_url=self.url, qb_username='admin', qb_password='árvíztűrő & secret')
        app.events, app.closed = queue.Queue(), False
        Handler.ready = False
        thread = threading.Thread(target=app._webui_loop, daemon=True)
        thread.start()
        messages = []
        deadline = time.monotonic()+9
        try:
            while time.monotonic() < deadline:
                kind, data = app.events.get(timeout=8)
                if kind != 'webui':
                    continue
                messages.append(data[1])
                if not data[1]:
                    Handler.ready = True
                else:
                    break
            self.assertEqual(messages, [False,True])
        finally:
            app.closed = True
            Handler.ready = True
            thread.join(4)


class SettingsTests(unittest.TestCase):
    def test_update_helper_preserves_install_directory(self):
        import update_helper as helper
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            installer, app = folder/'setup.exe',folder/'TorrentManager.exe'
            installer.touch()
            app.touch()
            with patch.object(sys,'argv',['helper',str(installer),str(app),'123']), \
                 patch.object(helper,'wait_for_exit'), patch.object(helper,'run_elevated',return_value=0) as elevate, \
                 patch.object(helper.subprocess,'Popen') as launch:
                self.assertEqual(helper.main(),0)
                self.assertIn('/DIR='+str(folder),elevate.call_args.args[1])
                launch.assert_called_once()

    def test_zero_patch_version_is_same_release(self):
        self.assertEqual(parse_version('v0.7'), parse_version('0.7.0'))
        self.assertLess(parse_version('0.7'), parse_version('0.7.1'))
    def test_first_run_marker_survives(self):
        self.assertFalse(normalize_settings({})['setup_complete'])
        cfg = normalize_settings({'setup_complete':True,'startup':True,'close_to_tray':True})
        self.assertTrue(cfg['setup_complete'])
        self.assertTrue(cfg['startup'])


@unittest.skipUnless(os.environ.get('TM_GUI_TESTS') == '1', 'Opt-in: creates temporary Tk windows')
class TkTests(unittest.TestCase):
    def test_first_setup_persists_only_after_real_connection(self):
        import tkinter as tk
        import setup_wizard as wizard
        import windows_integration as integration
        server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
        worker = threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        root = tk.Tk()
        def fill_and_submit():
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            entries = [w for w in descendants(root) if isinstance(w, tk.Entry)]
            values = [f'http://127.0.0.1:{server.server_port}', 'admin',
                      'árvíztűrő & secret', str(folder)]
            for entry,value in zip(entries,values):
                entry.delete(0,'end')
                entry.insert(0,value)
            [w for w in descendants(root) if isinstance(w,tk.Button)
                and w['text'] == 'Save'][0].invoke()
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            with patch.object(wizard,'SETTINGS',folder/'settings.json'), \
                 patch.object(wizard,'DATA_DIR',folder), \
                 patch.object(integration,'set_windows_startup') as startup, \
                 patch.object(integration,'set_desktop_shortcut') as desktop:
                root.after(50,fill_and_submit)
                root.after(6000,root.quit)
                try:
                    cfg = wizard.run_setup(root,normalize_settings({'language':'en'}))
                    self.assertIsNotNone(cfg)
                    self.assertTrue(json.loads((folder/'settings.json').read_text(encoding='utf-8'))['setup_complete'])
                    startup.assert_called_once_with(False)
                    desktop.assert_called_once_with(False)
                finally:
                    for job in root.tk.call('after','info'):
                        root.after_cancel(job)
                    root.destroy()
                    server.shutdown()
                    server.server_close()
                    worker.join()

    def test_cancel_setup_keeps_first_run_pending(self):
        import tkinter as tk
        import setup_wizard as wizard
        root = tk.Tk()
        with tempfile.TemporaryDirectory() as td, patch.object(wizard,'SETTINGS',Path(td)/'settings.json'):
            root.after(30,root.quit)
            try:
                self.assertIsNone(wizard.run_setup(root,normalize_settings({})))
                self.assertFalse((Path(td)/'settings.json').exists())
            finally:
                for job in root.tk.call('after','info'):
                    root.after_cancel(job)
                root.destroy()

    def test_dashboard_layout_languages_and_wheel(self):
        import tkinter as tk
        import TorrentManager as gui
        from localization import LANGUAGES
        root = tk.Tk()
        errors = []
        root.report_callback_exception = lambda *args: errors.append(args)
        cfg = normalize_settings({'setup_complete':True})
        with patch.object(gui,'read_settings',return_value=cfg), patch.object(threading.Thread,'start'), \
             patch.object(gui.App,'open_bithumen_login'), \
             patch.object(gui.App,'check_updates'):
            app = gui.App(root)
            try:
                root.state('normal')
                for size in ('1000x700','1366x768','1920x1080'):
                    root.geometry(size)
                    root.update()
                    self.assertIsNone(app.dashboard_canvas)
                    bottom = app.preview.winfo_rooty() + app.preview.winfo_height()
                    self.assertLessEqual(bottom, root.winfo_rooty()+root.winfo_height())
                    self.assertGreater(app.preview.winfo_height(), 20)
                for code in LANGUAGES:
                    app.cfg['language'] = code
                    app._render('settings')
                    root.update()
                    self.assertEqual(len(app.language_box['values']), 12)
                    previous = app.language_box.current()
                    app.language_box.event_generate('<MouseWheel>',delta=-120)
                    root.update()
                    self.assertEqual(app.language_box.current(),previous)
                app.cfg['language'] = 'hu'
                app._render('dashboard')
                app.toggle_fullscreen()
                root.update()
                self.assertTrue(app.fullscreen.active)
                root.event_generate('<Escape>')
                root.update()
                self.assertTrue(app.fullscreen.active)
                app.toggle_fullscreen()
                root.update()
                self.assertFalse(app.fullscreen.active)
                app.releases = [{'version':'v0.7','installer':{},'checksums':{}}]
                app._releases_to_combobox()
                self.assertEqual(str(app.install_button['state']),'normal')
                self.assertFalse(errors, errors)
            finally:
                app.closed = True
                for job in root.tk.call('after','info'):
                    root.after_cancel(job)
                root.destroy()

if __name__ == '__main__':
    unittest.main()
