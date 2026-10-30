"""First-run setup, completed only after a successful real WebUI probe."""
import json
import queue
import threading
import tkinter as tk
import os
import sys
import subprocess
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from localization import tr
from policy import validate_settings
from webui import check_webui
from paths import SETTINGS, DATA_DIR, BASE, find_playwright_browsers


def run_setup(root, cfg):
    root.title('Torrent Manager')
    root.geometry('850x700')
    root.minsize(700, 600)
    code = cfg['language']
    T = lambda key: tr(code, key)
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text=T('setup_title'), font=('Segoe UI', 19, 'bold')).pack(anchor='w')
    ttk.Label(frame, text=T('setup_intro'), wraplength=780).pack(anchor='w', pady=10)
    tabs = ttk.Notebook(frame)
    tabs.pack(fill='both', expand=True)
    variables = {}
    connection = ttk.Frame(tabs, padding=14)
    limits = ttk.Frame(tabs, padding=14)
    options = ttk.Frame(tabs, padding=14)
    tabs.add(connection, text=T('connection_settings'))
    tabs.add(limits, text=T('automation_limits'))
    tabs.add(options, text=T('settings'))
    fields = [('qb_url','url'), ('qb_username','user'), ('qb_password','password'), ('qb_save_path','path'),
              ('check_minutes','interval_m'), ('max_managed_torrents','total_n'),
              ('max_disk_usage_percent','limit_percent'), ('min_size_gb','min_gb'), ('max_size_gb','max_gb')]
    for i, (key, label) in enumerate(fields):
        parent = connection if i < 4 else limits
        ttk.Label(parent, text=T(label)).pack(anchor='w', pady=(7, 0))
        variables[key] = tk.StringVar(value=str(cfg[key]))
        ttk.Entry(parent, textvariable=variables[key], show='•' if key == 'qb_password' else '').pack(fill='x')
        ttk.Label(parent, text=T('help_' + key), wraplength=720).pack(anchor='w')
    ttk.Button(connection, text=T('browse'), command=lambda: variables['qb_save_path'].set(
        filedialog.askdirectory(parent=root) or variables['qb_save_path'].get())).pack(anchor='e', pady=6)
    for key in ('startup','close_to_tray','desktopicon'):
        variables[key] = tk.BooleanVar(value=cfg[key])
        ttk.Checkbutton(options, text=T(key), variable=variables[key]).pack(anchor='w', pady=8)
        ttk.Label(options, text=T('help_' + key), wraplength=720).pack(anchor='w')
    for key, values in [('theme',('dark','light','system')), ('mode',('dry','add','full'))]:
        variables[key] = tk.StringVar(value=cfg[key])
        ttk.Label(options, text=T(key)).pack(anchor='w', pady=(12,0))
        for value in values:
            ttk.Radiobutton(options, text=T(value), variable=variables[key], value=value).pack(anchor='w')
    ttk.Label(options, text=T('setup_login'), wraplength=720).pack(anchor='w', pady=10)
    login_proc = None
    def login():
        nonlocal login_proc
        if login_proc is not None and login_proc.poll() is None:
            return
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        cmd = ([str(BASE / 'TorrentLogin.exe')] if getattr(sys, 'frozen', False)
               else [sys.executable, str(BASE / 'auth_browser.py')])
        env = os.environ.copy()
        browsers = find_playwright_browsers()
        if browsers:
            env['PLAYWRIGHT_BROWSERS_PATH'] = str(browsers)
        try:
            login_proc = subprocess.Popen(cmd, cwd=str(DATA_DIR), env=env,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except OSError as exc:
            status.set(str(exc))
    ttk.Button(options, text=T('login_open'), command=login).pack(anchor='w')
    status = tk.StringVar()
    ttk.Label(frame, textvariable=status, wraplength=780).pack(fill='x', pady=8)
    events = queue.Queue()
    result = None
    pending = None
    poll_id = None

    def submit():
        nonlocal pending
        if login_proc is not None and login_proc.poll() is None:
            status.set(T('setup_close_browser'))
            return
        try:
            pending = validate_settings(dict(cfg, **{k:v.get() for k,v in variables.items()}))
            if not Path(pending['qb_save_path']).is_dir() or not pending['qb_save_path']:
                raise ValueError(T('help_qb_save_path'))
            if pending['mode'] == 'full' and not messagebox.askyesno('Torrent Manager', T('delete_full'), parent=root):
                return
        except ValueError as exc:
            status.set(str(exc))
            return
        button.configure(state='disabled')
        status.set(T('check_qb'))
        snapshot = pending.copy()
        def check():
            events.put(check_webui(snapshot['qb_url'], snapshot['qb_username'], snapshot['qb_password']))
        threading.Thread(target=check, daemon=True).start()

    def poll():
        nonlocal result, poll_id
        try:
            ready, message = events.get_nowait()
            if ready:
                try:
                    from windows_integration import set_windows_startup, set_desktop_shortcut
                    set_windows_startup(pending['startup'])
                    set_desktop_shortcut(pending['desktopicon'])
                    pending['setup_complete'] = True
                    DATA_DIR.mkdir(parents=True, exist_ok=True)
                    tmp = SETTINGS.with_suffix('.json.tmp')
                    tmp.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding='utf-8')
                    tmp.replace(SETTINGS)
                    result = pending
                    root.quit()
                    return
                except OSError as exc:
                    status.set(str(exc))
            else:
                status.set(T(message) if message != 'not_ready' else T('waiting'))
            button.configure(state='normal')
        except queue.Empty:
            pass
        poll_id = root.after(100, poll)

    button = ttk.Button(frame, text=T('setup_finish'), command=submit)
    button.pack(anchor='e')
    root.protocol('WM_DELETE_WINDOW', root.quit)
    poll()
    root.mainloop()
    if poll_id:
        root.after_cancel(poll_id)
    frame.destroy()
    return result
