"""Upgrade vs reinstall, failure recovery, and current release equivalence."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import updater
import update_helper


class ReleaseStateTests(unittest.TestCase):
    def test_current_and_zero_patch_are_not_upgrades(self):
        for tag in ('v0.8', '0.8.0', 'v0.8.0.0', 'v0.7'):
            self.assertEqual(updater.release_state([{'version': tag}]), 'up_to_date')
        self.assertEqual(updater.release_state([{'version': 'v0.8.1'}]), 'update_available')
        self.assertEqual(updater.release_state([]), 'no_releases')

    def run_helper(self, effect):
        with tempfile.TemporaryDirectory() as td:
            setup, app = Path(td)/'setup.exe', Path(td)/'TorrentManager.exe'
            setup.touch()
            app.touch()
            with patch.object(sys, 'argv', ['helper', str(setup), str(app), '123']), \
                 patch.object(update_helper, 'wait_for_exit'), \
                 patch.object(update_helper, 'run_elevated', side_effect=effect), \
                 patch.object(update_helper.subprocess, 'Popen') as launch, \
                 patch('ctypes.windll.user32.MessageBoxW'):
                code = update_helper.main()
                return code, launch.call_count

    def test_cancelled_uac_reopens_old_app(self):
        self.assertEqual(self.run_helper(OSError('cancelled')), (1, 1))

    def test_timed_out_setup_does_not_race_restarted_app(self):
        self.assertEqual(self.run_helper(TimeoutError('setup running')), (1, 0))

    def test_restart_required_is_success_without_early_restart(self):
        self.assertEqual(self.run_helper(lambda *a, **k: 3010), (0, 0))
