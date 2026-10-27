# -*- coding: utf-8 -*-
"""User-triggered visible Chromium login to save a persistent BitHuMen profile.
Never launched automatically. Avoid concurrent access to the same profile.
"""
import os
from playwright.sync_api import sync_playwright
from paths import PROFILE, DATA_DIR, find_playwright_browsers

def main():
    found = find_playwright_browsers()
    if found:
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(found)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            str(PROFILE), headless=False, no_viewport=True)
        try:
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto('https://bithumen.be/', wait_until='domcontentloaded')
            # User manually signs in, then closes the window. Keeping the profile
            # persistent makes the next HEADLESS motor startup reuse its cookies.
            while browser.pages:
                try:
                    page.wait_for_timeout(1200)
                except Exception:
                    break
        finally:
            browser.close()

if __name__ == '__main__':
    main()
