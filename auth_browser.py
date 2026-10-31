# -*- coding: utf-8 -*-
"""Validate saved BitHuMen session and request user login when needed.

Exit status: 0 verified, 2 cancelled/login needed, 3 unavailable, 4 profile busy.
Credentials are entered only by the user; never logged or passed through the GUI.
"""
import argparse
import os
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Error as BrowserError
from paths import PROFILE, DATA_DIR, find_playwright_browsers
from policy import TOP_URL
from browser_profile import ProfileLock, ProfileBusyError

READY, LOGIN_REQUIRED, UNAVAILABLE, BUSY = 0, 2, 3, 4


def page_status(page):
    location = urlparse(page.url)
    if location.hostname != urlparse(TOP_URL).hostname:
        return UNAVAILABLE
    if 'login' in location.path.lower() or page.locator('input[type="password"]').count():
        return LOGIN_REQUIRED
    if location.path.endswith('/browse.php') and (
            page.locator('a[href*="details.php?id="]').count() or
            page.locator('a[href*="logout.php"]').count()):
        return READY
    return UNAVAILABLE


def probe_context(context):
    page = context.pages[0] if context.pages else context.new_page()
    response = page.goto(TOP_URL, wait_until='domcontentloaded', timeout=30000)
    if response is not None and response.status >= 400:
        return UNAVAILABLE
    return page_status(page)


def ensure_session(playwright, profile, interactive=False, check_only=False):
    if not interactive:
        context = playwright.chromium.launch_persistent_context(str(profile), headless=True)
        try:
            result = probe_context(context)
        finally:
            context.close()
        if result != LOGIN_REQUIRED or check_only:
            return result
    # Release the check browser before opening a visible browser on the same profile.
    context = playwright.chromium.launch_persistent_context(
        str(profile), headless=False, no_viewport=True)
    verified = False
    try:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(TOP_URL, wait_until='domcontentloaded', timeout=30000)
        while context.pages:
            live = next((item for item in context.pages if not item.is_closed()), None)
            if live is None:
                break
            status = page_status(live)
            if status == READY:
                verified = True
                break
            location = urlparse(live.url)
            # Never navigate away from an unfinished password/CAPTCHA form.
            if (location.hostname == urlparse(TOP_URL).hostname and
                    status != LOGIN_REQUIRED and
                    live.locator('a[href*="logout.php"]').count()):
                verified = probe_context(context) == READY
                if verified:
                    break
            live.wait_for_timeout(750)
    except BrowserError:
        if context.pages:
            raise
    finally:
        try:
            context.close()
        except BrowserError:
            pass
    return READY if verified else LOGIN_REQUIRED


def main(argv=None):
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--ensure', action='store_true')
    mode.add_argument('--login', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    found = find_playwright_browsers()
    if found:
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(found)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with ProfileLock(PROFILE), sync_playwright() as playwright:
            return ensure_session(playwright, PROFILE,
                                  interactive=args.login or not (args.ensure or args.check),
                                  check_only=args.check)
    except ProfileBusyError:
        return BUSY
    except (BrowserError, OSError):
        return UNAVAILABLE


if __name__ == '__main__':
    raise SystemExit(main())
