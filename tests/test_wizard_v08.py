"""First setup remains a single themed page and saves only validated settings."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from localization import LANGUAGES, TEXT
from localization_v08 import KEYS, ABOUT_EXTRA
from policy import normalize_settings


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class TranslationTests(unittest.TestCase):
    def test_expanded_descriptions_and_all_new_strings(self):
        self.assertEqual(set(ABOUT_EXTRA), set(LANGUAGES))
        for code in LANGUAGES:
            with self.subTest(code=code):
                self.assertTrue(all(TEXT[code].get(key) for key in KEYS))
                self.assertIn(ABOUT_EXTRA[code], TEXT[code]['about_description'])
                self.assertGreaterEqual(TEXT[code]['about_description'].count('\n\n'), 3)
        self.assertEqual(TEXT['hu']['setup_finish'], 'Mentés')
        self.assertEqual(TEXT['en']['setup_finish'], 'Save')


@unittest.skipUnless(os.environ.get('TM_GUI_TESTS') == '1', 'Opt-in: creates temporary Tk windows')
class WizardTests(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, 'root'):
            for job in self.root.tk.call('after', 'info'):
                self.root.after_cancel(job)
            self.root.destroy()

    def test_single_page_all_languages_and_visible_save(self):
        import tkinter as tk
        from tkinter import ttk
        import setup_wizard as wizard
        from TorrentManager import LIGHT, DARK
        self.root = tk.Tk()
        errors = []
        for code in LANGUAGES:
            theme = 'light' if code == 'en' else 'dark'
            cfg = normalize_settings({'language': code, 'theme': theme})
            def inspect():
                try:
                    self.root.state('normal')
                    self.root.geometry('1000x700')
                    self.root.update()
                    widgets = list(descendants(self.root))
                    self.assertFalse(any(isinstance(w, ttk.Notebook) for w in widgets))
                    self.assertFalse(any(isinstance(w, (tk.Checkbutton, tk.Radiobutton)) for w in widgets))
                    self.assertEqual(sum(isinstance(w, tk.Entry) for w in widgets), 9)
                    save = next(w for w in widgets if isinstance(w, tk.Button)
                                and w['text'] == TEXT[code]['setup_finish'])
                    self.assertGreater(save.winfo_height(), 40)
                    self.assertLessEqual(save.winfo_rooty() + save.winfo_height(),
                                         self.root.winfo_rooty() + self.root.winfo_height())
                    self.assertEqual(self.root.cget('bg'), (LIGHT if theme == 'light' else DARK)['bg'])
                    self.assertEqual(self.root.title(), 'Torrent Manager')
                except BaseException as exc:
                    errors.append((code, exc))
                finally:
                    self.root.quit()
            self.root.after(40, inspect)
            self.assertIsNone(wizard.run_setup(self.root, cfg))
        self.assertFalse(errors, errors)

    def test_failed_connection_does_not_save_and_retry_preserves_hidden_defaults(self):
        import tkinter as tk
        import setup_wizard as wizard
        import windows_integration as integration
        self.root = tk.Tk()
        errors = []
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            cfg = normalize_settings({'language': 'en', 'qb_save_path': temp,
                                      'qb_password': ' secret ', 'startup': True,
                                      'desktopicon': True, 'close_to_tray': True,
                                      'mode': 'add', 'theme': 'light'})
            def save_button():
                return next(w for w in descendants(self.root) if isinstance(w, tk.Button) and w['text'] == 'Save')
            def retry():
                try:
                    self.assertFalse((folder / 'settings.json').exists())
                    self.assertEqual(save_button()['state'], 'normal')
                    save_button().invoke()
                except BaseException as exc:
                    errors.append(exc)
                    self.root.quit()
            with patch.object(wizard, 'SETTINGS', folder / 'settings.json'), \
                 patch.object(wizard, 'DATA_DIR', folder), \
                 patch.object(wizard, 'check_webui', side_effect=[(False, 'bad_credentials'), (True, 'connected')]) as check, \
                 patch.object(integration, 'set_windows_startup') as startup, \
                 patch.object(integration, 'set_desktop_shortcut') as desktop:
                self.root.after(30, lambda: save_button().invoke())
                self.root.after(350, retry)
                self.root.after(3000, self.root.quit)
                result = wizard.run_setup(self.root, cfg)
                self.assertFalse(errors, errors)
                self.assertIsNotNone(result)
                saved = json.loads((folder / 'settings.json').read_text(encoding='utf-8'))
                for key in ('startup', 'desktopicon', 'close_to_tray', 'mode', 'theme'):
                    self.assertEqual(saved[key], cfg[key])
                self.assertTrue(saved['setup_complete'])
                self.assertEqual(check.call_count, 2)
                self.assertEqual(check.call_args.args[2], ' secret ')
                startup.assert_called_once_with(True)
                desktop.assert_called_once_with(True)


if __name__ == '__main__':
    unittest.main()
