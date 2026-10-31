import os, subprocess, time, uuid
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=root/'.test-tmp'/('frozen-v08-'+uuid.uuid4().hex)
data.mkdir(parents=True,exist_ok=True)
env=dict(os.environ, LOCALAPPDATA=str(data/'local'), APPDATA=str(data/'roaming'), QBT_PROFILE=str(data/'qb-profile'))
for path in (data/'local',data/'roaming'):
 path.mkdir(exist_ok=True)
p=subprocess.Popen([str(root/'dist'/'TorrentManager'/'TorrentManager.exe')],env=env)
(root/'frozen-smoke.pid').write_text(str(p.pid))
time.sleep(5)
assert p.poll() is None, f'Frozen GUI exited early: {p.returncode}'
print('Frozen GUI alive; PID='+str(p.pid),flush=True)
try:
 p.wait(timeout=15)
except subprocess.TimeoutExpired:
 subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True)
print('Frozen smoke finished',flush=True)
