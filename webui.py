# -*- coding: utf-8 -*-
"""Safe, non-blocking qBittorrent WebUI readiness probe."""
from urllib.parse import urlparse
import requests


def check_webui(url, username, password, timeout=3, session=None):
    """Returns (ready: bool, message: str); distinguishes startup from bad credentials."""
    parsed = urlparse(str(url).strip())
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        return False, 'invalid_url'
    if not username or not password:
        return False, 'missing_credentials'
    http = session or requests.Session()
    try:
        base = str(url).rstrip('/')
        login = http.post(base + '/api/v2/auth/login', data={'username': username, 'password': password},
                          timeout=timeout, headers={'Referer': base + '/'})
        if login.status_code in (401, 403) or login.text.strip() != 'Ok.':
            return False, 'bad_credentials'
        response = http.get(base + '/api/v2/app/version', timeout=timeout)
        if response.ok and response.text.strip():
            return True, 'connected'
        return False, 'not_ready'
    except requests.RequestException:
        return False, 'not_ready'
    finally:
        if session is None:
            http.close()
