"""v0.9 regressions for fixed operating mode and expired tracker sessions."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import policy


class V09Tests(unittest.TestCase):
    def test_all_legacy_modes_become_full(self):
        for mode in ('dry', 'add', 'full', 'unknown'):
            with self.subTest(mode=mode):
                self.assertEqual(policy.validate_settings({'mode': mode})['mode'], 'full')

    def test_login_page_is_not_considered_usable(self):
        import auth_browser
        page = Mock(url='https://bithumen.be/login.php')
        page.locator.return_value.count.return_value = 1
        self.assertEqual(auth_browser.page_status(page), auth_browser.LOGIN_REQUIRED)

    def test_motor_exits_for_expired_session(self):
        import motor
        page = Mock(url='https://bithumen.be/login.php')
        page.locator.return_value.count.return_value = 1
        with patch.object(motor, 'log'), self.assertRaises(motor.TrackerLoginRequired):
            motor.wait_for_bithumen_login(page, {})
        page.goto.assert_not_called()


if __name__ == '__main__':
    unittest.main()
