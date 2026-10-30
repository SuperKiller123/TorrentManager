# -*- coding: utf-8 -*-
"""Torrent Manager v0.6 – modern, DPI-aware Windows UI for the safe torrent engine."""
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from paths import BASE, SETTINGS, DATA_DIR, LOG, migrate_old_data, find_playwright_browsers
from policy import GITHUB_REPO, normalize_settings, validate_settings
from updater import VERSION, list_releases, download_installer, UpdateError, parse_version
from localization import tr, LANGUAGES
from webui import check_webui, webui_session, read_telemetry
from windows_integration import (launch_qbittorrent, apply_windows_titlebar,
                                 set_windows_startup, set_desktop_shortcut, FullscreenController)

DARK = dict(bg='#0C1220', sidebar='#111B2B', panel='#151F31', panel_hi='#1D2B42',
            input='#0F1A2B', text='#EEF5FF', muted='#99ADC4', line='#29374C',
            blue='#528CF4', bluehover='#4078DF', green='#3CD6AE', amber='#FFBF69',
            red='#FF7588', white='#FFFFFF')
LIGHT = dict(bg='#F1F5FB', sidebar='#E4EAF4', panel='#FFFFFF', panel_hi='#DAE5F5',
             input='#F3F7FC', text='#162339', muted='#546A83', line='#CBD6E6',
             blue='#316EE5', bluehover='#245CC9', green='#0C9B79', amber='#B27107',
             red='#D24056', white='#FFFFFF')
P = dict(DARK)
FONT = 'Segoe UI' if os.name == 'nt' else 'Noto Sans'


def read_settings():
    try:
        saved = json.loads(SETTINGS.read_text(encoding='utf-8')) if SETTINGS.exists() else {}
    except (ValueError, OSError):
        saved = {}
    # The installer saves first-install language without overwriting an existing settings.json.
    if 'language' not in saved and os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\TorrentManager') as key:
                saved['language'] = winreg.QueryValueEx(key, 'Language')[0]
        except (OSError, ImportError):
            pass
    defaults_file = BASE / 'install-defaults.ini'
    if defaults_file.is_file():
        import configparser
        defaults = configparser.ConfigParser()
        defaults.read(defaults_file, encoding='utf-8-sig')
        if defaults.has_section('Settings'):
            for key in ('language', 'startup', 'close_to_tray', 'desktopicon'):
                if key not in saved and defaults.has_option('Settings', key):
                    saved[key] = (defaults.get('Settings', key) if key == 'language'
                                  else defaults.getboolean('Settings', key))
    return normalize_settings(saved)


def theme_is_dark(theme):
    if theme != 'system':
        return theme != 'light'
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                    r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as key:
                return not bool(winreg.QueryValueEx(key, 'AppsUseLightTheme')[0])
        except OSError:
            return True
    return True


class App:
    def __init__(self, root):
        self.root = root
        self.cfg = read_settings()
        self.events = queue.Queue()
        self.proc = None
        self.running = False
        self.closed = False
        self.tray = None
        self.connected = False
        self.bithumen_ready = False
        self.connection_message = 'check_qb'
        self.last_webui_cfg = None
        self.current_page = None
        self.vars = {}
        self.nav_buttons = {}
        self.sections = {}
        self.log_lines = []
        self.releases = []
        self.speed_history = []
        self.live_torrents = tk.StringVar(value='–')
        self.release_by_version = {}
        self.downloading = False
        self.update_message = tk.StringVar(value='')
        self.stat_disk = tk.StringVar(value='–')
        self.stat_used = tk.StringVar(value='–')
        self.home_mode = tk.StringVar(value='')
        self.home_details = tk.StringVar(value='')
        self.status = tk.StringVar(value='')
        self.webui_status = tk.StringVar(value='')
        self.next_check = tk.StringVar(value='–')
        self.disk_fraction = 0.0
        self.disk_target = 0.0
        self._animating_bar = False
        self._last_bar_update = 0.0
        self.last_action_time = time.monotonic()
        self._load_log_tail()
        root.title(' ')  # no app version or name in caption: branded sidebar is the title
        root.geometry('1200x820')
        root.minsize(1000, 700)
        try:
            root.iconbitmap(str(Path(getattr(sys, '_MEIPASS', BASE)) / 'assets' / 'app_icon.ico'))
        except tk.TclError:
            pass
        try:
            root.state('zoomed')  # maximize into usable work area, not F11 fullscreen
        except tk.TclError:
            root.geometry('1200x820')
        root.bind('<F11>', self.toggle_fullscreen)
        self.fullscreen = FullscreenController(root, lambda: apply_windows_titlebar(
            root, theme_is_dark(self.cfg['theme']), P['bg']))
        root.bind_all('<MouseWheel>', self._wheel_active)
        root.bind_all('<Button-4>', lambda _event: self._wheel_active(None, -3))
        root.bind_all('<Button-5>', lambda _event: self._wheel_active(None, 3))
        root.protocol('WM_DELETE_WINDOW', self.close)
        self._render('dashboard')
        threading.Thread(target=self._try_start_qb, daemon=True).start()
        threading.Thread(target=self._webui_loop, daemon=True).start()
        root.after(120, self.poll)
        root.after(15000, self._periodic_stats)
        root.after(500, self.check_updates)

    def T(self, key):
        return tr(self.cfg.get('language', 'hu'), key)

    def toggle_fullscreen(self, _event=None):
        self.fullscreen.toggle()
        return 'break'  # Escape is intentionally NOT bound to fullscreen

    def _render(self, page):
        global P
        dark = theme_is_dark(self.cfg.get('theme', 'dark'))
        P = dict(DARK if dark else LIGHT)
        self.root.configure(bg=P['bg'])
        apply_windows_titlebar(self.root, dark, P['bg'])
        if hasattr(self, 'sidebar'):
            self.sidebar.destroy()
            self.main.destroy()
        self.vars, self.nav_buttons, self.sections = {}, {}, {}
        self.current_page = None
        self._styles()
        self._structure()
        self._create_pages()
        self.show_page(page)
        self.refresh_stats()
        self._connection_update(self.connected, self.connection_message)
        self._status(self.running)
        self._bit_status()
        self._reload_visible_logs()
        self._releases_to_combobox()
        if self.releases:
            self.latest_value.set(self.releases[0]['version'])

    def _styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('TM.TCombobox', fieldbackground=P['input'], background=P['panel_hi'],
                        foreground=P['text'], arrowcolor=P['text'], bordercolor=P['line'],
                        lightcolor=P['input'], darkcolor=P['input'], padding=8)
        style.map('TM.TCombobox', fieldbackground=[('readonly', P['input'])],
                  foreground=[('readonly', P['text'])])
        style.configure('TM.Vertical.TScrollbar', background=P['panel_hi'], troughcolor=P['bg'],
                        arrowcolor=P['muted'], borderwidth=0)

    def _label(self, parent, text='', size=10, color='text', bold=False, **kw):
        return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=P.get(color, color),
                        font=(FONT, size, 'bold' if bold else 'normal'), anchor='w', **kw)

    def _button(self, parent, text, command, kind='primary', small=False, state='normal'):
        bg = P['blue'] if kind == 'primary' else P['panel_hi'] if kind == 'secondary' else P['panel']
        fg = P['white'] if kind == 'primary' else P['text']
        active = P['bluehover'] if kind == 'primary' else P['line']
        button = tk.Button(parent, text=text, command=command, state=state, bg=bg, fg=fg,
                           activebackground=active, activeforeground=fg,
                           disabledforeground=P['muted'], relief='flat', bd=0, highlightthickness=0,
                           font=(FONT, 9, 'bold'), padx=13 if small else 19,
                           pady=7 if small else 10, cursor='hand2')
        button.bind('<Enter>', lambda _e: self._animate_bg(button, active) if button['state'] == 'normal' else None)
        button.bind('<Leave>', lambda _e: self._animate_bg(button, bg if button['state'] == 'normal' else P['line']))
        return button

    def _animate_bg(self, widget, target):
        """Smooth 120 ms button hover transitions, no permanent high-FPS redraw."""
        try:
            current = widget.cget('bg')
            if not (current.startswith('#') and target.startswith('#')):
                widget.configure(bg=target)
                return
            start = tuple(int(current[i:i+2], 16) for i in (1, 3, 5))
            end = tuple(int(target[i:i+2], 16) for i in (1, 3, 5))
            widget._tm_token = getattr(widget, '_tm_token', 0) + 1
            token = widget._tm_token
            def step(index):
                if not widget.winfo_exists() or widget._tm_token != token:
                    return
                amount = 1 - (1 - index/8)**2
                rgb = [round(a+(b-a)*amount) for a, b in zip(start, end)]
                widget.configure(bg='#' + ''.join(f'{v:02x}' for v in rgb))
                if index < 8:
                    self.root.after(15, lambda: step(index+1))
            step(1)
        except (tk.TclError, AttributeError, ValueError):
            pass

    def _card(self, parent, pad=15):
        return tk.Frame(parent, bg=P['panel'], padx=pad, pady=pad,
                        highlightthickness=1, highlightbackground=P['line'])

    def _structure(self):
        self.sidebar = tk.Frame(self.root, bg=P['sidebar'], width=225)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        brand = tk.Frame(self.sidebar, bg=P['sidebar'])
        brand.pack(fill='x', padx=17, pady=(25, 29))
        icon = Path(getattr(sys, '_MEIPASS', BASE)) / 'assets' / 'app_icon.png'
        try:
            self.brand_icon = tk.PhotoImage(file=str(icon))
            tk.Label(brand, image=self.brand_icon, bg=P['sidebar']).pack(side='left', padx=(0, 10))
        except tk.TclError:
            tk.Label(brand, text='◈', bg=P['sidebar'], fg=P['green'],
                     font=(FONT, 25)).pack(side='left', padx=(0, 8))
        self._label(brand, 'Torrent Manager', 11, bold=True).pack(side='left')
        for key, icon_txt in [('dashboard', '▦'), ('settings', '⚙'), ('activity', '≡'), ('updates', '↻')]:
            title_key = 'logs' if key == 'activity' else 'home' if key == 'dashboard' else key
            b = tk.Button(self.sidebar, text=f'{icon_txt}   {self.T(title_key)}',
                          command=lambda p=key: self.show_page(p),
                          bg=P['sidebar'], fg=P['muted'], activeforeground=P['text'],
                          activebackground=P['panel_hi'], font=(FONT, 10),
                          relief='flat', bd=0, padx=17, pady=15, anchor='w',
                          highlightthickness=0, cursor='hand2')
            b.pack(fill='x', padx=8, pady=2)
            self.nav_buttons[key] = b
        self.main = tk.Frame(self.root, bg=P['bg'])
        self.main.pack(side='left', fill='both', expand=True)
        self.body = tk.Frame(self.main, bg=P['bg'])
        self.body.pack(fill='both', expand=True, padx=24, pady=22)

    def _create_pages(self):
        for page in ('dashboard', 'settings', 'activity', 'updates'):
            self.sections[page] = tk.Frame(self.body, bg=P['bg'])
        self._dashboard(self.sections['dashboard'])
        self._settings(self.sections['settings'])
        self._activity(self.sections['activity'])
        self._updates(self.sections['updates'])

    def show_page(self, page):
        if self.current_page == page:
            return
        if self.current_page:
            self.sections[self.current_page].pack_forget()
        self.current_page = page
        self.sections[page].pack(fill='both', expand=True)
        for name, button in self.nav_buttons.items():
            selected = name == page
            button.configure(bg=P['panel_hi'] if selected else P['sidebar'],
                             fg=P['text'] if selected else P['muted'],
                             font=(FONT, 10, 'bold' if selected else 'normal'))
        if page == 'settings':
            self.root.after_idle(lambda: self.settings_canvas.yview_moveto(0)
                                 if self.current_page == 'settings' else None)
        if page == 'dashboard':
            self.refresh_stats()

    def _scroll_page(self, parent):
        frame = tk.Frame(parent, bg=P['bg'])
        frame.pack(fill='both', expand=True)
        canvas = tk.Canvas(frame, bg=P['bg'], highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview,
                           style='TM.Vertical.TScrollbar')
        sb.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=sb.set)
        interior = tk.Frame(canvas, bg=P['bg'])
        win = canvas.create_window((0, 0), window=interior, anchor='nw')
        interior.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(win, width=event.width))
        return interior, canvas

    def _wheel_active(self, event=None, amount=None):
        canvas = {'dashboard': getattr(self, 'dashboard_canvas', None),
                  'settings': getattr(self, 'settings_canvas', None),
                  'updates': getattr(self, 'updates_canvas', None)}.get(self.current_page)
        if canvas is not None and canvas.winfo_exists():
            steps = amount if amount is not None else (-int(event.delta / 120) if event.delta else 0)
            if steps:
                canvas.yview_scroll(steps, 'units')

    def _metric(self, parent, heading, variable, subtitle=''):
        card = self._card(parent, 13)
        self._label(card, heading, 9, 'muted').pack(anchor='w')
        tk.Label(card, textvariable=variable, bg=P['panel'], fg=P['text'],
                 font=(FONT, 18, 'bold'), anchor='w').pack(anchor='w', pady=(5, 2))
        if subtitle:
            self._label(card, subtitle, 9, 'muted').pack(anchor='w')
        return card

    def _dashboard(self, page):
        # Dense monitoring surface, with controls deliberately subordinate to metrics.
        title = tk.Frame(page, bg=P['bg'])
        title.pack(fill='x', pady=(0, 10))
        self._label(title, self.T('home'), 22, bold=True).pack(side='left')
        actions = tk.Frame(title, bg=P['bg'])
        actions.pack(side='right')
        self.start_btn = self._button(actions, self.T('start'), self.start, small=True)
        self.start_btn.pack(side='left', padx=4)
        self.stop_btn = self._button(actions, self.T('stop'), self.stop, 'secondary', True, 'disabled')
        self.stop_btn.pack(side='left', padx=4)
        interior = tk.Frame(page, bg=P['bg'])
        interior.pack(fill='both', expand=True)
        self.dashboard_canvas = None
        metrics = tk.Frame(interior, bg=P['bg'])
        metrics.pack(fill='x', pady=(0, 9))
        for i in range(4):
            metrics.columnconfigure(i, weight=1, uniform='metric')
        self.metric_auto = tk.StringVar()
        cards = [(self.T('automation'), self.metric_auto), (self.T('total'), self.live_torrents),
                 (self.T('mode'), self.home_mode), (self.T('next'), self.next_check)]
        for i, (head, var) in enumerate(cards):
            metric = self._metric(metrics, head, var)
            if i == 3:
                for label in metric.winfo_children():
                    if isinstance(label, tk.Label) and str(label.cget('textvariable')):
                        label.configure(font=(FONT, 12, 'bold'))
            metric.grid(row=0, column=i, sticky='nsew', padx=(0, 5) if i < 3 else 0)
        extra = tk.Frame(interior, bg=P['bg'])
        extra.pack(fill='x', pady=(0, 9))
        for i in range(4):
            extra.columnconfigure(i, weight=1, uniform='extra')
        self.mini_total = tk.StringVar(value='–')
        self.mini_interval = tk.StringVar(value='–')
        self.mini_min = tk.StringVar(value='–')
        self.mini_max = tk.StringVar(value='–')
        for i, (title, variable) in enumerate([
            (self.T('total_n'), self.mini_total), (self.T('interval'), self.mini_interval),
            (self.T('minsize'), self.mini_min), (self.T('maxsize'), self.mini_max)]):
            card = self._card(extra, 11)
            card.grid(row=0, column=i, sticky='nsew', padx=(0, 5) if i < 3 else 0)
            self._label(card, title, 9, 'muted').pack(anchor='w')
            tk.Label(card, textvariable=variable, bg=P['panel'], fg=P['text'],
                     font=(FONT, 13, 'bold')).pack(anchor='w', pady=(5, 0))
        disk = self._card(interior)
        disk.pack(fill='x', pady=(0, 9))
        dline = tk.Frame(disk, bg=P['panel'])
        dline.pack(fill='x')
        self._label(dline, self.T('disk_info'), 11, bold=True).pack(side='left')
        tk.Label(dline, textvariable=self.stat_used, bg=P['panel'], fg=P['muted'],
                 font=(FONT, 10)).pack(side='right')
        self.disk_track = tk.Canvas(disk, height=13, bg=P['panel'], bd=0, highlightthickness=0)
        self.disk_track.pack(fill='x', pady=(12, 5))
        self.disk_track.bind('<Configure>', lambda _: self._paint_disk_bar())
        more = tk.Frame(interior, bg=P['bg'])
        more.pack(fill='both', expand=True, pady=(0, 9))
        more.rowconfigure(0, weight=1)
        for i in range(2):
            more.columnconfigure(i, weight=1, uniform='more')
        limits = self._card(more)
        limits.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        self._label(limits, self.T('transfer'), 12, bold=True).pack(anchor='w')
        self.speed_chart = tk.Canvas(limits, height=70, bg=P['panel'], highlightthickness=0)
        self.speed_chart.pack(fill='both', expand=True)
        self.speed_chart.bind('<Configure>', lambda _: self._paint_speed())
        system = self._card(more)
        system.grid(row=0, column=1, sticky='nsew')
        self._label(system, self.T('connection'), 12, bold=True).pack(anchor='w', pady=(0, 7))
        self.qb_indicator = self._label(system, '○  qBittorrent', 10, 'muted')
        self.qb_indicator.pack(anchor='w', pady=2)
        self.webui_indicator = self._label(system, '', 10, 'amber')
        self.webui_indicator.pack(anchor='w', pady=2)
        self.bit_indicator = self._label(system, '○  BitHuMen', 10, 'muted')
        self.bit_indicator.pack(anchor='w', pady=2)
        logcard = self._card(interior)
        logcard.pack(fill='both', expand=True, pady=(0, 9))
        self._label(logcard, self.T('recent'), 12, bold=True).pack(anchor='w', pady=(0, 8))
        self.preview = tk.Text(logcard, height=3, bg=P['input'], fg=P['text'], relief='flat',
                               bd=0, padx=12, pady=11, wrap='word',
                               font=(FONT, 10), state='disabled')
        self.preview.pack(fill='both', expand=True)

    def _group(self, parent, title):
        box = self._card(parent, 18)
        box.pack(fill='x', pady=(0, 12))
        self._label(box, title, 12, bold=True).pack(anchor='w', pady=(0, 12))
        inner = tk.Frame(box, bg=P['panel'])
        inner.pack(fill='x')
        inner.columnconfigure(0, weight=1)
        return inner

    def _input(self, parent, key, title, row, secret=False, browse=False):
        wrap = tk.Frame(parent, bg=P['panel'])
        wrap.grid(row=row, column=0, sticky='ew', pady=(0, 11))
        self._label(wrap, title, 9, bold=True).pack(anchor='w', pady=(0, 5))
        entryrow = tk.Frame(wrap, bg=P['panel'])
        entryrow.pack(fill='x')
        variable = tk.StringVar(value=str(self.cfg.get(key, '')))
        self.vars[key] = variable
        entry = tk.Entry(entryrow, textvariable=variable, bg=P['input'], fg=P['text'],
                         insertbackground=P['text'], relief='flat', bd=0,
                         font=(FONT, 10), highlightthickness=1,
                         highlightbackground=P['line'], highlightcolor=P['blue'],
                         show='•' if secret else '')
        entry.pack(side='left', fill='x', expand=True, ipady=9, ipadx=8)
        if secret:
            btn = self._button(entryrow, self.T('show'), None, 'secondary', True)
            def toggle():
                visible = bool(entry.cget('show'))
                entry.configure(show='' if visible else '•')
                btn.configure(text=self.T('hide') if visible else self.T('show'))
            btn.configure(command=toggle)
            btn.pack(side='left', padx=(7, 0))
        if browse:
            self._button(entryrow, self.T('browse'), self.choose_folder, 'secondary', True).pack(side='left', padx=(7, 0))

    def _settings(self, page):
        heading = tk.Frame(page, bg=P['bg'])
        heading.pack(fill='x', pady=(0, 15))
        self._label(heading, self.T('settings'), 22, bold=True).pack(side='left')
        self.save_btn = self._button(heading, self.T('save'), self.save, state='disabled')
        self.save_btn.pack(side='right')
        interior, self.settings_canvas = self._scroll_page(page)
        group = self._group(interior, self.T('connection_settings'))
        for i, (key, title) in enumerate([('qb_url', 'url'), ('qb_username', 'user'),
                                         ('qb_password', 'password'), ('qb_save_path', 'path')]):
            self._input(group, key, self.T(title), i, secret=key == 'qb_password',
                        browse=key == 'qb_save_path')
        group = self._group(interior, self.T('automation_limits'))
        for i, (key, title) in enumerate([('check_minutes', 'interval_m'),
                                         ('max_managed_torrents', 'total_n'),
                                         ('max_disk_usage_percent', 'limit_percent'),
                                         ('min_size_gb', 'min_gb'), ('max_size_gb', 'max_gb')]):
            self._input(group, key, self.T(title), i)
        operation = self._card(interior, 18)
        operation.pack(fill='x', pady=(0, 12))
        self._label(operation, self.T('safety'), 12, bold=True).pack(anchor='w', pady=(0, 8))
        self.vars['mode'] = tk.StringVar(value=self.cfg.get('mode', 'dry'))
        for mode, label in (('dry', 'dry_full'), ('add', 'add_full'), ('full', 'delete_full')):
            tk.Radiobutton(operation, text=self.T(label), value=mode, variable=self.vars['mode'],
                           font=(FONT, 10), bg=P['panel'], fg=P['text'], selectcolor=P['input'],
                           activebackground=P['panel'], activeforeground=P['text']).pack(anchor='w', pady=4)
        login_row = self._card(interior, 14)
        login_row.pack(fill='x', pady=(0, 12))
        self._label(login_row, self.T('login_title'), 11, bold=True).pack(side='left')
        self._button(login_row, self.T('login_open'), self.open_bithumen_login,
                     'secondary', True).pack(side='right')
        appearance = self._card(interior, 18)
        appearance.pack(fill='x', pady=(0, 12))
        self._label(appearance, self.T('appearance'), 12, bold=True).pack(anchor='w', pady=(0, 11))
        r1 = tk.Frame(appearance, bg=P['panel'])
        r1.pack(fill='x', pady=(0, 8))
        self._label(r1, self.T('theme'), 10, bold=True).pack(side='left', padx=(0, 18))
        self.vars['theme'] = tk.StringVar(value=self.cfg.get('theme', 'dark'))
        for key in ('dark', 'light', 'system'):
            tk.Radiobutton(r1, text=self.T(key), value=key, variable=self.vars['theme'],
                           bg=P['panel'], fg=P['text'], font=(FONT, 9),
                           selectcolor=P['input'], activebackground=P['panel'],
                           activeforeground=P['text']).pack(side='left', padx=(0, 9))
        r2 = tk.Frame(appearance, bg=P['panel'])
        r2.pack(fill='x', pady=(5, 7))
        self._label(r2, self.T('language'), 10, bold=True).pack(side='left', padx=(0, 18))
        self.vars['language'] = tk.StringVar(value=self.cfg.get('language', 'hu'))
        choices = list(LANGUAGES.items())
        codes = [code for code, _ in choices]
        self.language_box = ttk.Combobox(r2, state='readonly', style='TM.TCombobox',
                                          values=[label for _, label in choices], width=24, height=12)
        self.language_box.bind('<MouseWheel>', lambda _: 'break')
        self.language_box.bind('<Button-4>', lambda _: 'break')
        self.language_box.bind('<Button-5>', lambda _: 'break')
        self.language_box.current(codes.index(self.cfg.get('language', 'hu')))
        self.language_box.pack(side='left', fill='x', expand=True)
        self.language_box.bind('<<ComboboxSelected>>', lambda _: self.vars['language'].set(codes[self.language_box.current()]))
        self._label(appearance, self.T('language_note'), 9, 'muted').pack(anchor='w')
        for key in ('startup', 'close_to_tray', 'desktopicon'):
            self.vars[key] = tk.BooleanVar(value=self.cfg.get(key, False))
            tk.Checkbutton(appearance, text=self.T(key), variable=self.vars[key],
                           bg=P['panel'], fg=P['text'], selectcolor=P['input']).pack(anchor='w')
        self._saved_signature = self._form_signature()
        for variable in self.vars.values():
            variable.trace_add('write', lambda *_: self._sync_dirty())
        self._sync_dirty()

    def _form_signature(self):
        return tuple((key, variable.get()) for key, variable in sorted(self.vars.items()))

    def _sync_dirty(self):
        if hasattr(self, 'save_btn') and self.save_btn.winfo_exists():
            dirty = self._form_signature() != self._saved_signature
            self.save_btn.configure(state='normal' if dirty else 'disabled',
                                    bg=P['blue'] if dirty else P['line'])

    def _activity(self, page):
        header = tk.Frame(page, bg=P['bg'])
        header.pack(fill='x', pady=(0, 13))
        self._label(header, self.T('logs'), 22, bold=True).pack(side='left')
        self._button(header, self.T('open_logs'), self.open_data_folder, 'secondary', True).pack(side='right')
        box = self._card(page)
        box.pack(fill='both', expand=True)
        self._label(box, self.T('live_log'), 12, bold=True).pack(anchor='w', pady=(0, 10))
        self.logbox = tk.Text(box, wrap='word', bg=P['input'], fg=P['text'],
                              insertbackground=P['text'], selectbackground=P['panel_hi'],
                              font=(FONT, 11), bd=0, padx=14, pady=12, state='disabled')
        scrollbar = ttk.Scrollbar(box, orient='vertical', command=self.logbox.yview,
                                  style='TM.Vertical.TScrollbar')
        self.logbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.logbox.pack(fill='both', expand=True)
        for name, color in (('error', P['red']), ('success', P['green']), ('muted', P['muted'])):
            self.logbox.tag_configure(name, foreground=color)

    def _updates(self, page):
        self._label(page, self.T('updates'), 22, bold=True).pack(anchor='w', pady=(0, 13))
        interior, self.updates_canvas = self._scroll_page(page)
        metrics = tk.Frame(interior, bg=P['bg'])
        metrics.pack(fill='x', pady=(0, 10))
        metrics.columnconfigure(0, weight=1)
        metrics.columnconfigure(1, weight=1)
        installed = self._card(metrics, 17)
        installed.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        self._label(installed, self.T('installed'), 9, 'muted').pack(anchor='w')
        self._label(installed, 'v' + VERSION, 21, bold=True).pack(anchor='w', pady=(6, 0))
        newest = self._card(metrics, 17)
        newest.grid(row=0, column=1, sticky='nsew')
        self._label(newest, self.T('latest'), 9, 'muted').pack(anchor='w')
        self.latest_value = tk.StringVar(value='–')
        tk.Label(newest, textvariable=self.latest_value, bg=P['panel'], fg=P['text'],
                 font=(FONT, 21, 'bold'), anchor='w').pack(anchor='w', pady=(6, 0))
        actions = self._card(interior, 18)
        actions.pack(fill='x', pady=(0, 10))
        self._label(actions, self.T('versions'), 12, bold=True).pack(anchor='w', pady=(0, 8))
        tk.Label(actions, textvariable=self.update_message, bg=P['panel'], fg=P['muted'],
                 font=(FONT, 10), justify='left', anchor='w', wraplength=720).pack(fill='x', pady=(0, 9))
        buttons = tk.Frame(actions, bg=P['panel'])
        buttons.pack(fill='x', pady=(0, 9))
        self.check_button = self._button(buttons, self.T('check'), self.check_updates, 'secondary')
        self.check_button.pack(side='left')
        self.version_choice = tk.StringVar()
        self.versions_box = ttk.Combobox(actions, textvariable=self.version_choice,
                                          state='readonly', style='TM.TCombobox', width=38)
        self.versions_box.pack(fill='x', pady=(0, 9))
        self.versions_box.bind('<<ComboboxSelected>>', lambda _e: self._update_install_enabled())
        self.install_button = self._button(actions, self.T('install'), self.install_update, state='disabled')
        self.install_button.pack(fill='x', pady=(0, 9))
        self._label(actions, self.T('download_note'), 9, 'muted', wraplength=720, justify='left').pack(anchor='w')
        about = self._card(interior, 18)
        about.pack(fill='both', expand=True)
        self._label(about, self.T('about'), 12, bold=True).pack(anchor='w', pady=(0, 8))
        description = self.T('about_description')
        self._label(about, description, 10, 'text', wraplength=920, justify='left').pack(anchor='w', fill='x', pady=(0, 15))
        self._button(about, self.T('github'), lambda: webbrowser.open('https://github.com/' + GITHUB_REPO),
                     'secondary').pack(anchor='w')

    def _load_log_tail(self):
        if not LOG.exists():
            return
        try:
            with LOG.open('rb') as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                handle.seek(max(0, size - 28000))
                lines = handle.read().decode('utf-8', errors='replace').splitlines()
            self.log_lines = (lines[1:] if size > 28000 else lines)[-130:]
        except OSError:
            self.log_lines = []

    def _reload_visible_logs(self):
        self.logbox.configure(state='normal')
        self.logbox.delete('1.0', 'end')
        for line in self.log_lines[-600:]:
            self._write_log_widget(self.logbox, line)
        self.logbox.configure(state='disabled')
        self.logbox.see('end')
        self.preview.configure(state='normal')
        self.preview.delete('1.0', 'end')
        for line in self.log_lines[-14:]:
            self.preview.insert('end', line[:250] + '\n')
        self.preview.configure(state='disabled')
        self.preview.see('end')

    def _write_log_widget(self, widget, line):
        lower = line.lower()
        tag = 'error' if ('hiba' in lower or 'sikertelen' in lower or 'error' in lower) else \
              'success' if ('hozzáadva' in lower or 'sikeres' in lower) else 'muted'
        widget.insert('end', line + '\n', tag)

    def append(self, line):
        line = str(line)
        self.log_lines.append(line)
        self.log_lines = self.log_lines[-1400:]
        self._write_text(self.logbox, line, styled=True)
        self._write_text(self.preview, line[:250], maxlines=55)

    def _write_text(self, widget, line, styled=False, maxlines=1400):
        widget.configure(state='normal')
        if styled:
            self._write_log_widget(widget, line)
        else:
            widget.insert('end', line + '\n')
        if int(widget.index('end-1c').split('.')[0]) > maxlines:
            widget.delete('1.0', f'{max(1, maxlines // 4)}.0')
        widget.see('end')
        widget.configure(state='disabled')

    def open_bithumen_login(self):
        # Opening a visible browser requires an explicit click; never show it at app start.
        if self.proc and self.proc.poll() is None:
            messagebox.showinfo('BitHuMen',
                'Előbb állítsd le az automatizálást, hogy a böngészőprofil felszabaduljon.',
                parent=self.root)
            return
        if getattr(sys, 'frozen', False):
            executable = BASE / 'TorrentLogin.exe'
            cmd = [str(executable)]
        else:
            executable = BASE / 'auth_browser.py'
            cmd = [sys.executable, str(executable)]
        if not executable.exists():
            messagebox.showerror('BitHuMen', 'Hiányzik a bejelentkezési segédprogram.', parent=self.root)
            return
        env = os.environ.copy()
        browser = find_playwright_browsers()
        if browser:
            env['PLAYWRIGHT_BROWSERS_PATH'] = str(browser)
        try:
            subprocess.Popen(cmd, cwd=str(DATA_DIR), stdin=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), env=env)
            self.append('Kézi BitHuMen-bejelentkezés megnyitva.')
        except OSError as exc:
            messagebox.showerror('BitHuMen', str(exc), parent=self.root)

    def choose_folder(self):
        folder = filedialog.askdirectory(parent=self.root)
        if folder:
            self.vars['qb_save_path'].set(folder)

    def _validated_settings(self):
        config = dict(self.cfg)
        for key, var in self.vars.items():
            config[key] = var.get().strip() if isinstance(var, tk.StringVar) and key != 'qb_password' else var.get()
        config = validate_settings(config)
        if not str(config['qb_url']).strip():
            raise ValueError('Hiányzik a WebUI címe.')
        # Connection credentials and folder can be filled in later; start remains disabled until ready.
        if config['qb_save_path'] and not Path(config['qb_save_path']).is_dir():
            raise ValueError('A letöltési mappa nem létezik.')
        return config

    def save(self):
        try:
            new = self._validated_settings()
            if new['mode'] == 'full' and self.cfg.get('mode') != 'full':
                if not messagebox.askyesno('Végleges fájltörlés',
                    'A kezelt torrentek és letöltött fájljaik törlődhetnek. Engedélyezed?', parent=self.root):
                    return False
            changed_view = (new['theme'], new['language']) != (self.cfg.get('theme'), self.cfg.get('language'))
            changed_webui = any(new[k] != self.cfg.get(k) for k in ('qb_url','qb_username','qb_password'))
            if new['startup'] != self.cfg['startup']:
                set_windows_startup(new['startup'])
            if new['desktopicon'] != self.cfg['desktopicon']:
                set_desktop_shortcut(new['desktopicon'])
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            tmp = SETTINGS.with_suffix('.json.tmp')
            tmp.write_text(json.dumps(new, indent=2, ensure_ascii=False), encoding='utf-8')
            tmp.replace(SETTINGS)
            self.cfg = new
            if changed_webui:
                self.connected = False
                self.connection_message = 'check_qb'
                self.events.put(('trigger_webui', None))
            if changed_view:
                self._render('settings')
            else:
                self._saved_signature = self._form_signature()
                self._sync_dirty()
            self.append(self.T('saved'))
            self.refresh_stats()
            return True
        except (ValueError, OSError) as exc:
            messagebox.showerror('Beállítási hiba', str(exc), parent=self.root)
            return False

    def _status(self, running):
        self.running = running
        label = self.T('running' if running else 'stopped')
        self.status.set(label)
        self.metric_auto.set(label)
        self.start_btn.configure(state='disabled' if running or not self.connected else 'normal',
                                 bg=P['line'] if running or not self.connected else P['blue'])
        self.stop_btn.configure(state='normal' if running else 'disabled')

    def _bit_status(self):
        if hasattr(self, 'bit_indicator'):
            self.bit_indicator.configure(text=('●  ' if self.bithumen_ready else '○  ') + 'BitHuMen',
                                         fg=P['green'] if self.bithumen_ready else P['muted'])

    def _connection_update(self, ready, message):
        self.connected = ready
        self.connection_message = message
        if ready:
            text = self.T('connected')
        elif message in ('missing_credentials', 'bad_credentials', 'invalid_url'):
            text = self.T(message)
        else:
            text = self.T('waiting')
        self.webui_status.set(text)
        if hasattr(self, 'qb_indicator'):
            self.qb_indicator.configure(text=('●  ' if ready else '○  ') + 'qBittorrent',
                                        fg=P['green'] if ready else P['muted'])
        if hasattr(self, 'webui_indicator'):
            self.webui_indicator.configure(text=('●  ' if ready else '○  ') + text,
                                           fg=P['green'] if ready else P['amber'])
        self._status(self.running)

    def _webui_loop(self):
        last_signature = None
        while not self.closed:
            cfg = self.cfg.copy()
            signature = (cfg.get('qb_url'), cfg.get('qb_username'), cfg.get('qb_password'))
            if signature != last_signature:
                last_signature = signature
            try:
                with webui_session(signature[0]) as http:
                    ready, message = check_webui(*signature, session=http)
                    if ready:
                        try:
                            self.events.put(('telemetry', (signature, read_telemetry(http, signature[0]))))
                        except Exception:
                            pass
                self.events.put(('webui', (signature, ready, message)))
            except Exception as exc:
                self.events.put(('webui', (signature, False, 'not_ready')))
            for _ in range(30):
                if self.closed:
                    break
                time.sleep(.1)

    def start(self):
        if self.proc and self.proc.poll() is None:
            return
        if not self.connected:
            self.append('A WebUI még nem elérhető. Várakozás a kapcsolatra.')
            return
        if self._form_signature() != self._saved_signature or not SETTINGS.exists():
            if not self.save():
                self.show_page('settings')
                return
            # If connection credentials were changed, await fresh WebUI probe.
            if not self.connected:
                return
        if not self.cfg.get('qb_save_path') or not Path(self.cfg['qb_save_path']).is_dir():
            messagebox.showerror('Beállítási hiba', 'Előbb állíts be egy érvényes letöltési mappát.', parent=self.root)
            self.show_page('settings')
            return
        if getattr(sys, 'frozen', False):
            engine, cmd = BASE / 'TorrentMotor.exe', [str(BASE / 'TorrentMotor.exe')]
        else:
            engine, cmd = BASE / 'motor.py', [sys.executable, '-X', 'utf8', '-u', str(BASE / 'motor.py')]
        if not engine.is_file():
            messagebox.showerror('Hiányzó motor', str(engine), parent=self.root)
            return
        env = os.environ.copy()
        env.update(PYTHONIOENCODING='utf-8', PYTHONUTF8='1', PYTHONUNBUFFERED='1')
        if getattr(sys, 'frozen', False):
            browser = find_playwright_browsers()
            if not browser:
                messagebox.showerror('Hiányzó Chromium', 'Nem található a Playwright Chromium böngésző.', parent=self.root)
                return
            env['PLAYWRIGHT_BROWSERS_PATH'] = str(browser)
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            # Child logs are decoded UTF-8; the subprocess is headless (motor.py).
            self.bithumen_ready = False
            self._bit_status()
            self.proc = subprocess.Popen(cmd, cwd=str(DATA_DIR), stdin=subprocess.DEVNULL,
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         text=True, encoding='utf-8', errors='replace', bufsize=1,
                                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), env=env)
            self.last_action_time = time.monotonic()
            self._status(True)
            self.append('Automatizálás elindítva; Chromium háttérmódban működik.')
            threading.Thread(target=self.reader, args=(self.proc,), daemon=True).start()
        except (OSError, ValueError) as exc:
            self._status(False)
            messagebox.showerror('Indítási hiba', str(exc), parent=self.root)

    def reader(self, proc):
        try:
            for line in proc.stdout:
                self.events.put(('line', line.rstrip('\r\n')))
        except Exception as exc:
            self.events.put(('line', 'Naplóolvasási hiba: ' + str(exc)))
        self.events.put(('done', (proc, proc.wait())))

    def stop(self):
        proc = self.proc
        if not proc or proc.poll() is not None:
            return
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=15, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            else:
                proc.terminate()
            self.append('Leállítás kérve.')
        except (OSError, subprocess.TimeoutExpired) as exc:
            messagebox.showerror('Leállítási hiba', str(exc), parent=self.root)

    def _paint_speed(self):
        canvas = self.speed_chart
        canvas.delete('all')
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if not self.speed_history:
            canvas.create_text(width/2,height/2, text=self.T('unavailable'), fill=P['muted'])
            return
        maximum = max(1, max(max(pair) for pair in self.speed_history))
        for index, color in [(0,P['blue']), (1,P['green'])]:
            points = []
            for i, pair in enumerate(self.speed_history):
                points.extend((10 + i * max(1,width-20)/max(1,len(self.speed_history)-1),
                               height-8 - pair[index]/maximum*max(1,height-34)))
            if len(points) >= 4:
                canvas.create_line(*points, fill=color, width=2, smooth=True)
        down, up = self.speed_history[-1]
        canvas.create_text(8,8, anchor='nw', text=f'↓ {down/1e6:.2f} MB/s   ↑ {up/1e6:.2f} MB/s', fill=P['text'])

    def _paint_disk_bar(self):
        if not hasattr(self, 'disk_track') or not self.disk_track.winfo_exists():
            return
        w = max(1, self.disk_track.winfo_width())
        self.disk_track.delete('all')
        self.disk_track.create_rectangle(0, 0, w, 13, fill=P['input'], outline='')
        color = P['amber'] if self.disk_target > int(self.cfg.get('max_disk_usage_percent', 70)) / 100 else P['green']
        self.disk_track.create_rectangle(0, 0, int(w*self.disk_fraction), 13,
                                         fill=color, outline='')

    def _animate_disk(self):
        if self.closed:
            self._animating_bar = False
            return
        delta = self.disk_target - self.disk_fraction
        if abs(delta) < .003:
            self.disk_fraction = self.disk_target
            self._paint_disk_bar()
            self._animating_bar = False
            return
        # ~60 FPS for short easing animations, idle UI has no continuous render loop.
        self.disk_fraction += delta * .18
        self._paint_disk_bar()
        self.root.after(16, self._animate_disk)

    def refresh_stats(self):
        cfg = self.cfg
        try:
            path = str(cfg.get('qb_save_path','')).strip()
            if not path or not Path(path).is_dir():
                raise OSError('Hiányzó mappa')
            usage = shutil.disk_usage(path)
            percent = 100 * usage.used / usage.total
            limit = int(cfg['max_disk_usage_percent'])
            self.stat_disk.set(f'{percent:.1f}%')
            self.stat_used.set(f'{percent:.1f}% / {limit}%')
            self.disk_target = max(0., min(1., percent / 100))
        except (OSError, ValueError, ZeroDivisionError):
            self.stat_disk.set('–')
            self.stat_used.set(self.T('unavailable'))
            self.disk_target = 0.
        if not self._animating_bar:
            self._animating_bar = True
            self._animate_disk()
        mode = self.T(cfg.get('mode','dry'))
        self.home_mode.set(mode)
        lo, hi = cfg.get('min_size_gb',''), cfg.get('max_size_gb','')
        sizes = (f'{lo or "–"} – {hi or "–"} GB') if lo or hi else self.T('no_limit')
        if hasattr(self, 'mini_total'):
            self.mini_total.set(str(cfg['max_managed_torrents']))
            self.mini_interval.set(str(cfg['check_minutes']) + ' min')
            self.mini_min.set(str(lo) + ' GB' if lo else '–')
            self.mini_max.set(str(hi) + ' GB' if hi else '–')
        self.home_details.set(f"{self.T('total')}: {cfg['max_managed_torrents']}\n"
                              f"{self.T('interval')}: {cfg['check_minutes']} min\n"
                              f"{self.T('minsize')} / {self.T('maxsize')}: {sizes}\n"
                              f"{self.T('limit')}: {cfg['max_disk_usage_percent']}%")
        if self.running:
            remainder = max(0, int(cfg['check_minutes']) * 60 - int((time.monotonic() - self.last_action_time) % (int(cfg['check_minutes']) * 60)))
            self.next_check.set(f'{remainder // 60:02d}:{remainder % 60:02d} (becslés)')
        else:
            self.next_check.set('–')

    def _periodic_stats(self):
        if not self.closed:
            self.refresh_stats()
            self.root.after(1000, self._periodic_stats)

    def _try_start_qb(self):
        try:
            started = launch_qbittorrent()
            self.events.put(('line', 'qBittorrent háttérben elindítva.' if started
                             else 'A qBittorrent már fut; meglévő ablak változatlan.'))
        except Exception as exc:
            self.events.put(('line', 'qBittorrent indítási hiba: ' + str(exc)))

    def _releases_to_combobox(self):
        if not hasattr(self, 'versions_box'):
            return
        self.release_by_version = {item['version']: item for item in self.releases}
        options = [i['version'] for i in self.releases]
        self.versions_box.configure(values=options)
        if self.version_choice.get() not in options:
            self.version_choice.set(next((v for v in options if v == 'v' + VERSION), options[0] if options else ''))
        self._update_install_enabled()

    def _update_install_enabled(self):
        release = self.release_by_version.get(self.version_choice.get())
        enabled = (not self.downloading and release is not None and release['installer'] is not None
                   and release['checksums'] is not None
                   )
        self.install_button.configure(state='normal' if enabled else 'disabled',
                                      bg=P['blue'] if enabled else P['line'])

    def check_updates(self):
        self.check_button.configure(state='disabled')
        self.update_message.set('GitHub Releases…')
        def work():
            try:
                self.events.put(('releases_ok', list_releases(GITHUB_REPO)))
            except Exception as exc:
                self.events.put(('releases_error', str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def install_update(self):
        if os.name != 'nt':
            messagebox.showinfo('Windows', 'A telepítő kizárólag Windows alatt indítható.', parent=self.root)
            return
        release = self.release_by_version.get(self.version_choice.get())
        if self.downloading or not release or not release.get('installer') or not release.get('checksums'):
            return
        version = release['version']
        older = parse_version(version) < parse_version(VERSION)
        if older:
            if not messagebox.askyesno('Korábbi verzió telepítése',
                    f'A(z) {version} régebbi a telepített v{VERSION} verziónál. '
                    'A régi verzió nem feltétlenül érti a jelenlegi beállításokat. '
                    'Automatikus mentés készül. Folytatod?', parent=self.root):
                return
        if not messagebox.askyesno('Verzió telepítése', f'Telepítendő: {version}. Folytatod?', parent=self.root):
            return
        if SETTINGS.exists():
            backup = DATA_DIR / 'backups'
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SETTINGS, backup / ('settings-before-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.json'))
        self.downloading = True
        self._update_install_enabled()
        self.update_message.set('Telepítő letöltése és SHA-256 ellenőrzése…')
        def work():
            try:
                dest = download_installer(release, DATA_DIR / 'updates')
                self.events.put(('download_ok', dest))
            except Exception as exc:
                self.events.put(('download_error', str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def _run_installer(self, installer):
        try:
            if getattr(sys, 'frozen', False):
                helper = BASE / 'TorrentUpdater.exe'
                if not helper.is_file():
                    raise FileNotFoundError('Hiányzik a TorrentUpdater.exe.')
                copy = DATA_DIR / 'updates' / 'TorrentUpdater.exe'
                shutil.copy2(helper, copy)
                cmd = [str(copy)]
            else:
                cmd = [sys.executable, str(BASE / 'update_helper.py')]
            exe = BASE / ('TorrentManager.exe' if getattr(sys, 'frozen', False) else 'TorrentManager.py')
            if self.proc and self.proc.poll() is None:
                self.stop()
                if self.proc.poll() is None:
                    raise RuntimeError('Nem állt le az automatizálási folyamat.')
            subprocess.Popen(cmd + [str(installer), str(exe), str(os.getpid())],
                             cwd=str(DATA_DIR / 'updates'), stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), close_fds=True)
            self.closed = True
            if self.tray:
                self.tray.stop()
            self.root.destroy()
        except (OSError, RuntimeError) as exc:
            self.update_message.set('Telepítő indítási hiba: ' + str(exc))
            messagebox.showerror('Frissítési hiba', str(exc), parent=self.root)

    def poll(self):
        if self.closed:
            return
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == 'restore':
                    self.root.deiconify()
                    self.root.lift()
                elif kind == 'exit':
                    self.exit()
                    if self.closed:
                        return
                elif kind == 'line':
                    if 'BitHuMen bejelentkezés ellenőrizve' in data:
                        self.bithumen_ready = True
                        self._bit_status()
                    if 'BitHuMen bejelentkezés szükséges' in data:
                        self.bithumen_ready = False
                        self._bit_status()
                    self.append(data)
                elif kind == 'done':
                    proc, code = data
                    if proc is self.proc:
                        self.bithumen_ready = False
                        self._bit_status()
                        self._status(False)
                        self.append(f'A háttérprogram leállt. Kilépési kód: {code}.')
                        self.proc = None
                elif kind == 'webui':
                    signature, connected, message = data
                    current = tuple(self.cfg.get(key) for key in ('qb_url','qb_username','qb_password'))
                    if signature == current:
                        previous = self.connected
                        self._connection_update(connected, message)
                        if previous != connected:
                            self.append('WebUI kapcsolat létrejött.' if connected else 'WebUI kapcsolat megszakadt.')
                elif kind == 'telemetry':
                    signature, snapshot = data
                    if signature == tuple(self.cfg.get(k) for k in ('qb_url','qb_username','qb_password')):
                        self.live_torrents.set(str(snapshot['total']))
                        self.speed_history = (self.speed_history + [(snapshot['download'],snapshot['upload'])])[-60:]
                        self._paint_speed()
                elif kind == 'releases_ok':
                    self.releases = data
                    self._releases_to_combobox()
                    self.latest_value.set(data[0]['version'] if data else '–')
                    self.update_message.set(self.T('update_ready'))
                    self.check_button.configure(state='normal')
                elif kind == 'releases_error':
                    self.update_message.set('GitHub hiba: ' + data)
                    self.check_button.configure(state='normal')
                elif kind == 'download_ok':
                    self.downloading = False
                    self._run_installer(data)
                elif kind == 'download_error':
                    self.downloading = False
                    self._update_install_enabled()
                    self.update_message.set('Letöltési hiba: ' + data)
                    messagebox.showerror('Frissítési hiba', data, parent=self.root)
        except queue.Empty:
            pass
        if not self.closed:
            self.root.after(120, self.poll)

    def open_data_folder(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            os.startfile(str(DATA_DIR))
        else:
            messagebox.showinfo('Naplók', str(DATA_DIR), parent=self.root)

    def close(self):
        if self.cfg.get('close_to_tray'):
            try:
                if self.tray is None:
                    import pystray
                    from PIL import Image
                    self.tray = pystray.Icon('TorrentManager', Image.open(Path(getattr(sys, '_MEIPASS', BASE)) / 'assets' / 'app_icon.ico'),
                        'Torrent Manager', menu=pystray.Menu(
                            pystray.MenuItem(self.T('show'), lambda *_: self.events.put(('restore', None)), default=True),
                            pystray.MenuItem(self.T('exit'), lambda *_: self.events.put(('exit', None)))))
                    self.tray.run_detached()
                self.root.withdraw()
                return
            except Exception as exc:
                self.append(str(exc))
        self.exit()

    def exit(self):
        if self.proc and self.proc.poll() is None:
            if not messagebox.askyesno('Kilépés', 'Leállítsuk az automatizálást is?', parent=self.root):
                return
            self.stop()
        self.closed = True
        if self.tray:
            self.tray.stop()
        self.root.destroy()


if __name__ == '__main__':
    migrate_old_data()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    cfg = read_settings()
    if not cfg.get('setup_complete'):
        from setup_wizard import run_setup
        threading.Thread(target=lambda: launch_qbittorrent(), daemon=True).start()
        cfg = run_setup(root, cfg)
    if cfg:
        App(root)
        root.mainloop()
    else:
        root.destroy()
