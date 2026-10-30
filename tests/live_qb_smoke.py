"""Opt-in qBittorrent smoke test; exclusively uses a new workspace profile."""
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from webui import check_webui, webui_session, read_telemetry

def main():
    root = Path(__file__).resolve().parents[1]
    profile = root / '.test-tmp' / ('qb-profile-' + str(time.time_ns()))
    config = profile / 'qBittorrent' / 'config' / 'qBittorrent.ini'
    config.parent.mkdir(parents=True)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port = sock.getsockname()[1]
    password = 'Tm-v07-test-' + str(time.time_ns())
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha512',password.encode(),salt,100000,64)
    secret = base64.b64encode(salt).decode()+':'+base64.b64encode(key).decode()
    config.write_text('[LegalNotice]\nAccepted=true\n[Preferences]\n'
        f'WebUI\\Enabled=true\nWebUI\\Address=127.0.0.1\nWebUI\\Port={port}\n'
        f'WebUI\\Username=admin\nWebUI\\Password_PBKDF2="@ByteArray({secret})"\n'
        'WebUI\\LocalHostAuth=true\nWebUI\\CSRFProtection=true\n'
        '[BitTorrent]\nSession\\DHTEnabled=false\nSession\\LSDEnabled=false\nSession\\PeXEnabled=false\n'
        '[Network]\nPortForwardingEnabled=false\n',encoding='utf-8')
    original = [Path(os.environ['APPDATA'])/'qBittorrent'/'qBittorrent.ini',
                Path(os.environ['LOCALAPPDATA'])/'qBittorrent'/'BT_backup']
    def snapshot():
        files = []
        for path in original:
            files.extend(path.rglob('*') if path.is_dir() else [path])
        return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
    before = snapshot()
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    proc = subprocess.Popen([r'C:\Program Files\qBittorrent\qbittorrent.exe',
        '--profile='+str(profile),'--webui-port='+str(port), '--confirm-legal-notice','--no-splash'],
        startupinfo=startup, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    url = f'http://127.0.0.1:{port}'
    try:
        ready = False
        for _ in range(40):
            ready, status = check_webui(url,'admin',password,timeout=1)
            if ready:
                break
            if proc.poll() is not None:
                raise RuntimeError('Isolated qBittorrent exited: '+str(proc.returncode))
            time.sleep(.5)
        if not ready:
            raise RuntimeError('Isolated WebUI: '+status)
        assert check_webui(url,'admin','wrong')[1] == 'bad_credentials'
        with webui_session(url) as http:
            assert check_webui(url,'admin',password,session=http)[0]
            version = http.get(url+'/api/v2/app/version',timeout=3).text
            telemetry = read_telemetry(http,url)
            assert telemetry['total'] == 0, telemetry
            print(json.dumps({'version':version,'connection':True,'wrong_password_rejected':True,
                              'telemetry':telemetry,'user_profile_unchanged':before==snapshot()}))
            http.post(url+'/api/v2/app/shutdown',timeout=3)
        proc.wait(timeout=15)
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)
    assert before == snapshot(), 'Existing profile changed during isolated test'
    return 0

if __name__ == '__main__':
    sys.exit(main())
