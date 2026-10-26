# -*- coding: utf-8 -*-
"""v0.5: SI GB, v0.4-ből biztonságos migráció és felületi invariánsok."""
import sys
import unittest
from pathlib import Path
from decimal import Decimal
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import policy
import updater

class V05SettingsTests(unittest.TestCase):
    def test_empty_limits_default(self):
        cfg = policy.validate_settings({})
        self.assertEqual(cfg['min_size_gb'], '')
        self.assertEqual(cfg['max_size_gb'], '')
        self.assertNotIn('startup_windows', cfg)
        self.assertNotIn('launch_qbittorrent', cfg)
        self.assertNotIn('github_repository', cfg)

    def test_old_gib_limit_migration_is_byte_exact(self):
        cfg = policy.validate_settings({'min_size_gib':10, 'max_size_gib':20})
        self.assertEqual(Decimal(cfg['min_size_gb']) * 10**9, 10*1024**3)
        self.assertEqual(Decimal(cfg['max_size_gb']) * 10**9, 20*1024**3)
        self.assertTrue(policy.allowed_size(10*1024**3, cfg))
        self.assertFalse(policy.allowed_size(10*1024**3-1, cfg))
        self.assertFalse(policy.allowed_size(20*1024**3+1, cfg))
        self.assertEqual(policy.normalize_settings(cfg)['min_size_gb'], cfg['min_size_gb'])

    def test_decimal_gb_boundary_and_comma(self):
        cfg=policy.validate_settings({'min_size_gb':'1,5', 'max_size_gb':'2.5'})
        self.assertEqual(cfg['min_size_gb'],'1.5')
        self.assertTrue(policy.allowed_size(1500000000,cfg))
        self.assertFalse(policy.allowed_size(1499999999,cfg))
        self.assertFalse(policy.allowed_size(2500000001,cfg))

    def test_invalid_sizes_are_rejected(self):
        for bad in ['0','-1','NaN','inf','1e99999999','szöveg']:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                policy.validate_settings({'min_size_gb':bad})

    def test_mode_migration_keeps_delete_protection(self):
        a=policy.normalize_settings({'dry_run':False,'enable_additions':True,'enable_deletions':True,'delete_files':False})
        self.assertEqual(a['mode'],'add')

    def test_version(self):
        self.assertEqual(updater.VERSION,'0.5.0')

    def test_new_gui_does_not_expose_removed_controls(self):
        src=(Path(__file__).resolve().parents[1]/'TorrentManager.py').read_text(encoding='utf8')
        self.assertNotIn('repo_var',src)
        self.assertNotIn('self.stat_owned',src)
        self.assertNotIn('self.stat_total',src)
        self.assertNotIn('"startup_windows"',src)
        self.assertNotIn('"launch_qbittorrent"',src)
        self.assertIn('"Mutatás"',src)
        self.assertIn('"Elrejtés"',src)
        self.assertIn('"Frissítés letöltése és telepítése"',src)

if __name__=='__main__': unittest.main()
