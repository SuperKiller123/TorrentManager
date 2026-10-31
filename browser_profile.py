"""Cross-process lock protecting the persistent Chromium profile.

OS locks release after crashes. Retain the lock file to avoid unlink/recreate races.
"""
import os
from pathlib import Path


class ProfileBusyError(RuntimeError):
    pass


class ProfileLock:
    def __init__(self, profile):
        self.path = Path(profile).parent / 'browser-profile.lock'
        self.stream = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stream = self.path.open('a+b')
        try:
            stream.seek(0, 2)
            if stream.tell() == 0:
                stream.write(b'0')
                stream.flush()
            stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            stream.close()
            raise ProfileBusyError('The BitHuMen browser profile is in use.') from exc
        self.stream = stream
        return self

    def __exit__(self, *_):
        if self.stream:
            try:
                self.stream.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.stream, fcntl.LOCK_UN)
            finally:
                self.stream.close()
                self.stream = None
