# -*- coding: utf-8 -*-
"""Safe, non-blocking qBittorrent WebUI readiness probe."""
from urllib.parse import urlparse
import requests

def webui_session(url):
    http = requests.Session()
    # Local qBittorrent traffic must not go through corporate/environment proxies.
    if urlparse(url).hostname in ('localhost', '127.0.0.1', '::1'):
        http.trust_env = False
    base = url.strip().rstrip('/')
    parsed = urlparse(base)
    http.headers.update({'Referer': base + '/', 'Origin': f'{parsed.scheme}://{parsed.netloc}'})
    return http


def read_telemetry(http, url):
    base = url.strip().rstrip('/')
    transfer = http.get(base + '/api/v2/transfer/info', timeout=3)
    transfer.raise_for_status()
    torrents = http.get(base + '/api/v2/torrents/info', timeout=3)
    torrents.raise_for_status()
    info, items = transfer.json(), torrents.json()
    return {'download': max(0, int(info['dl_info_speed'])),
            'upload': max(0, int(info['up_info_speed'])), 'total': len(items)}


def check_webui(url, username, password, timeout=3, session=None):
    """Returns (ready: bool, message: str); distinguishes startup from bad credentials."""
    parsed = urlparse(str(url).strip())
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        return False, 'invalid_url'
    if not username or not password:
        return False, 'missing_credentials'
    http = session or webui_session(str(url).strip())
    try:
        base = str(url).strip().rstrip('/')
        login = http.post(base + '/api/v2/auth/login', data={'username': username, 'password': password},
                          timeout=timeout, headers={'Referer': base + '/'})
        if login.status_code in (401, 403) or (login.ok and login.text.strip().lower() not in ('ok.', '')):
            return False, 'bad_credentials'
        if not login.ok:
            return False, 'not_ready'
        response = http.get(base + '/api/v2/app/version', timeout=timeout)
        if response.ok and response.text.strip():
            return True, 'connected'
        return False, 'not_ready'
    except requests.RequestException:
        return False, 'not_ready'
    finally:
        if session is None:
            http.close()
