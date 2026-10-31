"""Isolated visual preview. Never starts qB, tracker, updater, or automation."""
import sys
import tkinter as tk
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import TorrentManager as gui
from policy import normalize_settings

root = tk.Tk()
cfg = normalize_settings({'setup_complete': True, 'language': 'hu'})
root.after(180000, root.quit)
if '--wizard' in sys.argv:
    from setup_wizard import run_setup
    run_setup(root, cfg)
else:
    with patch.object(gui, 'read_settings', return_value=cfg), \
         patch.object(gui.App, '_try_start_qb'), patch.object(gui.App, '_webui_loop'), \
         patch.object(gui.App, 'check_updates'), patch.object(gui.App, 'open_bithumen_login'):
        app = gui.App(root)
        app.live_torrents.set('12')
        app.releases = [{'version': 'v0.8', 'installer': {}, 'checksums': {}}]
        app._releases_to_combobox()
        app.latest_value.set('v0.8')
        app.update_message.set(app.T('up_to_date'))
        app.append('Elkülönített megjelenítési próba — nincs aktív kapcsolat.')
        if '--updates' in sys.argv:
            app.show_page('updates')
        root.mainloop()
        app.closed = True
root.destroy()
