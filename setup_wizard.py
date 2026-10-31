"""Themed single-page first setup, saved only after a successful WebUI probe."""
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
    # Import at invocation to share the actual application's palette without
    # constructing its dashboard or starting any worker processes.
    from TorrentManager import DARK, LIGHT, FONT, theme_is_dark
    from windows_integration import apply_windows_titlebar
    dark = theme_is_dark(cfg.get('theme', 'dark'))
    colors = DARK if dark else LIGHT
    T = lambda key: tr(cfg['language'], key)
    root.title('Torrent Manager')
    root.configure(bg=colors['bg'])
    root.geometry('1200x820')
    root.minsize(1000, 700)
    assets = Path(getattr(sys, '_MEIPASS', BASE)) / 'assets'
    try:
        root.iconbitmap(str(assets / 'app_icon.ico'))
    except tk.TclError:
        pass
    try:
        root.state('zoomed')
    except tk.TclError:
        pass
    apply_windows_titlebar(root, dark, colors['bg'], show_icon=True)
    frame = tk.Frame(root, bg=colors['bg'], padx=24, pady=18)
    frame.pack(fill='both', expand=True)

    def label(parent, text, size=10, bold=False, muted=False, **kw):
        return tk.Label(parent, text=text, bg=parent.cget('bg'),
                        fg=colors['muted' if muted else 'text'],
                        font=(FONT, size, 'bold' if bold else 'normal'), anchor='w', **kw)

    def action(parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command,
                         bg=colors['blue' if primary else 'panel_hi'],
                         fg=colors['white' if primary else 'text'],
                         activebackground=colors['bluehover' if primary else 'line'],
                         activeforeground=colors['white' if primary else 'text'],
                         disabledforeground=colors['muted'], relief='flat', bd=0,
                         font=(FONT, 12 if primary else 10, 'bold'),
                         padx=32 if primary else 14, pady=13 if primary else 8,
                         cursor='hand2')

    heading = tk.Frame(frame, bg=colors['bg'])
    heading.pack(fill='x')
    try:
        brand = tk.PhotoImage(file=str(assets / 'app_icon.png'))
        factor = max(1, brand.width() // 42)
        brand = brand.subsample(factor, factor)
        icon = tk.Label(heading, image=brand, bg=colors['bg'])
        icon.image = brand
        icon.pack(side='left', padx=(0, 14))
    except tk.TclError:
        pass
    title = tk.Frame(heading, bg=colors['bg'])
    title.pack(side='left', fill='x', expand=True)
    label(title, 'Torrent Manager', 23, True).pack(anchor='w')
    label(title, T('setup_title'), 13, muted=True).pack(anchor='w', pady=(2, 0))
    intro = label(frame, T('setup_intro'), muted=True, justify='left')
    intro.pack(fill='x', pady=(12, 14))
    intro.bind('<Configure>', lambda e: intro.configure(wraplength=max(200, e.width)))

    # Save remains visible at every size. The body scrolls only if DPI or a small
    # work area needs it; it is one continuous page with no hidden settings tabs.
    footer = tk.Frame(frame, bg=colors['bg'])
    footer.pack(side='bottom', fill='x', pady=(14, 0))
    status = tk.StringVar()
    status_label = label(footer, '', muted=True, justify='left', textvariable=status)
    status_label.pack(side='left', fill='x', expand=True, padx=(0, 20))
    status_label.bind('<Configure>', lambda e: status_label.configure(wraplength=max(100, e.width)))
    viewport = tk.Frame(frame, bg=colors['bg'])
    viewport.pack(fill='both', expand=True)
    canvas = tk.Canvas(viewport, bg=colors['bg'], bd=0, highlightthickness=0)
    scrollbar = ttk.Scrollbar(viewport, orient='vertical', command=canvas.yview)
    scrollbar.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)
    canvas.configure(yscrollcommand=scrollbar.set)
    body = tk.Frame(canvas, bg=colors['bg'])
    window = canvas.create_window(0, 0, window=body, anchor='nw')
    canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window, width=e.width))
    body.bind('<Configure>', lambda _e: canvas.configure(scrollregion=canvas.bbox('all')))
    body.columnconfigure(0, weight=1, uniform='setup')
    body.columnconfigure(1, weight=1, uniform='setup')

    def section(column, text):
        card = tk.Frame(body, bg=colors['panel'], padx=18, pady=16,
                        highlightbackground=colors['line'], highlightthickness=1)
        card.grid(row=0, column=column, sticky='nsew', padx=(0, 8) if column == 0 else (8, 0))
        label(card, text, 15, True).pack(fill='x', pady=(0, 8))
        return card

    connection = section(0, T('connection_settings'))
    limits = section(1, T('automation_limits'))
    variables = {}
    fields = [('qb_url','url'), ('qb_username','user'), ('qb_password','password'), ('qb_save_path','path'),
              ('check_minutes','interval_m'), ('max_managed_torrents','total_n'),
              ('max_disk_usage_percent','limit_percent'), ('min_size_gb','min_gb'), ('max_size_gb','max_gb')]
    for i, (key, caption) in enumerate(fields):
        parent = connection if i < 4 else limits
        field = tk.Frame(parent, bg=colors['panel'])
        field.pack(fill='x', pady=(5, 7))
        label(field, T(caption), 10, True).pack(fill='x')
        line = tk.Frame(field, bg=colors['panel'])
        line.pack(fill='x', pady=(4, 3))
        variables[key] = tk.StringVar(value=str(cfg[key]))
        entry = tk.Entry(line, textvariable=variables[key], show='•' if key == 'qb_password' else '',
                         bg=colors['input'], fg=colors['text'], insertbackground=colors['text'],
                         font=(FONT, 11), relief='flat', bd=0, highlightthickness=1,
                         highlightbackground=colors['line'], highlightcolor=colors['blue'])
        entry.pack(side='left', fill='x', expand=True, ipady=5)
        if key == 'qb_save_path':
            action(line, T('browse'), lambda: variables['qb_save_path'].set(
                filedialog.askdirectory(parent=root) or variables['qb_save_path'].get())).pack(side='right', padx=(8, 0))
        help_label = label(field, T('help_' + key), 9, muted=True, justify='left')
        help_label.pack(fill='x')
        help_label.bind('<Configure>', lambda e, w=help_label: w.configure(wraplength=max(150, e.width)))

    label(connection, 'BitHuMen', 13, True).pack(anchor='w', pady=(10, 4))
    hint = label(connection, T('setup_login'), 9, muted=True, justify='left')
    hint.pack(fill='x')
    hint.bind('<Configure>', lambda e: hint.configure(wraplength=max(150, e.width)))
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
            status.set(f"{T('setup_error')}: {exc}")
    action(connection, T('login_open'), login).pack(anchor='w', pady=(8, 0))
    events = queue.Queue()
    result = None
    pending = None
    poll_id = None
    closed = False

    def submit():
        nonlocal pending
        if pending is not None:
            return
        if login_proc is not None and login_proc.poll() is None:
            status.set(T('setup_close_browser'))
            return
        try:
            candidate = validate_settings(dict(cfg, **{k:v.get() for k,v in variables.items()}))
            if not candidate['qb_save_path'] or not Path(candidate['qb_save_path']).is_dir():
                status.set(T('help_qb_save_path'))
                return
            if candidate['mode'] == 'full' and not messagebox.askyesno('Torrent Manager', T('delete_full'), parent=root):
                return
        except (ValueError, OSError) as exc:
            status.set(f"{T('setup_error')}: {exc}")
            return
        pending = candidate
        button.configure(state='disabled')
        status.set(T('check_qb'))
        snapshot = pending.copy()
        def check():
            try:
                events.put(check_webui(snapshot['qb_url'], snapshot['qb_username'], snapshot['qb_password']))
            except Exception:
                events.put((False, 'unavailable'))
        threading.Thread(target=check, daemon=True).start()

    def poll():
        nonlocal result, poll_id, pending
        if closed:
            return
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
                except (OSError, subprocess.SubprocessError) as exc:
                    status.set(f"{T('setup_error')}: {exc}")
            else:
                status.set(T(message) if message != 'not_ready' else T('waiting'))
            pending = None
            button.configure(state='normal')
        except queue.Empty:
            pass
        poll_id = root.after(100, poll)

    def wheel(event):
        # Binding belongs to this window only and is removed before the dashboard.
        if canvas.bbox('all') and canvas.bbox('all')[3] > canvas.winfo_height():
            canvas.yview_scroll(-int(event.delta / 120), 'units')
        return 'break'

    wheel_id = root.bind('<MouseWheel>', wheel, add='+')
    button = action(footer, T('setup_finish'), submit, primary=True)
    button.pack(side='right')
    root.protocol('WM_DELETE_WINDOW', root.quit)
    poll()
    root.mainloop()
    closed = True
    if poll_id:
        root.after_cancel(poll_id)
    root.unbind('<MouseWheel>', wheel_id)
    frame.destroy()
    return result
