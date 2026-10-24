# -*- coding: utf-8 -*-
"""Torrent Manager 0.3 – modern, magyar nyelvű Windows kezelőfelület (Tkinter)."""
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from paths import BASE, SETTINGS, STATE, DATA_DIR, LOG, migrate_old_data, find_playwright_browsers
from updater import VERSION, check_latest, download_installer, normalize_repo, UpdateError

INITIAL_FIELDS = {
    "qb_url": "http://127.0.0.1:8080",
    "browse_url": "https://bithumen.be/browse.php?sort=times_completed&d=DESC&type=legtobbet_letoltottek",
}
NONVISIBLE_DEFAULTS = {"minimum_valid_rows_for_deletion": 50, "headless": False}


def read_settings():
    if SETTINGS.exists():
        return {**NONVISIBLE_DEFAULTS, **json.loads(SETTINGS.read_text(encoding="utf-8"))}
    return {**NONVISIBLE_DEFAULTS, **INITIAL_FIELDS}


P = {
    "bg": "#0C1220", "sidebar": "#111B2B", "panel": "#151F31", "panel_hi": "#1B2940",
    "input": "#0F1A2B", "text": "#EEF5FF", "muted": "#93A4BA", "line": "#29374C",
    "blue": "#528CF4", "bluehover": "#4078DF", "green": "#3CD6AE", "amber": "#FFBF69",
    "red": "#FF7588", "white": "#FFFFFF",
}
FONT = "Segoe UI"


class App:
    def __init__(self, root):
        self.root = root
        self.proc = None
        self.events = queue.Queue()
        self.release = None
        self.downloading = False
        self.cfg = read_settings()
        self.vars = {}
        self.nav_buttons = {}
        self.sections = {}
        self.running = False
        self.current_page = None
        self.status = tk.StringVar(value="Leállítva")
        self.stat_total = tk.StringVar(value="–")
        self.stat_owned = tk.StringVar(value="–")
        self.stat_disk = tk.StringVar(value="–")
        self.stat_interval = tk.StringVar(value="–")
        self.update_message = tk.StringVar(value="Ellenőrizd, hogy elérhető-e új kiadás a GitHubon.")
        root.title(f"Torrent Manager • v{VERSION}")
        root.geometry("1120x790")
        root.minsize(900, 650)
        root.configure(bg=P["bg"])
        self._styles()
        self._structure()
        self._create_pages()
        self.show_page("dashboard")
        self._read_last_logs()
        self.refresh_stats()
        root.after(150, self.poll)
        root.after(20000, self._periodic_stats)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def _styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Vertical.TScrollbar", troughcolor=P["panel"], background=P["line"], borderwidth=0, arrowcolor=P["muted"])
        style.configure("TProgressbar", troughcolor=P["input"], background=P["blue"], borderwidth=0)

    def _label(self, parent, text="", size=11, color="text", bold=False, **kwargs):
        return tk.Label(parent, text=text, font=(FONT, size, "bold" if bold else "normal"),
                        fg=P.get(color, color), bg=parent.cget("bg"), anchor="w", **kwargs)

    def _button(self, parent, text, command, kind="primary", width=None, state="normal"):
        normal = P["blue"] if kind == "primary" else P["panel_hi"] if kind == "secondary" else P["panel"]
        active = P["bluehover"] if kind == "primary" else P["line"]
        b = tk.Button(parent, text=text, command=command, bg=normal, fg=P["white"],
                      activebackground=active, activeforeground=P["white"],
                      disabledforeground=P["muted"], relief="flat", bd=0,
                      cursor="hand2", font=(FONT, 10, "bold"), highlightthickness=0,
                      padx=19, pady=11, width=width, state=state)
        b.bind("<Enter>", lambda _e: b.configure(bg=active) if str(b.cget("state")) == "normal" else None)
        b.bind("<Leave>", lambda _e: b.configure(bg=normal))
        return b

    def _card(self, parent, pad=20):
        outer = tk.Frame(parent, bg=P["panel"], padx=pad, pady=pad, highlightthickness=1,
                         highlightbackground=P["line"])
        return outer

    def _structure(self):
        self.sidebar = tk.Frame(self.root, bg=P["sidebar"], width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        brand = tk.Frame(self.sidebar, bg=P["sidebar"])
        brand.pack(fill="x", padx=22, pady=(29, 36))
        tk.Label(brand, text="◈", bg=P["sidebar"], fg=P["green"], font=(FONT, 29, "bold")).pack(side="left", padx=(0, 12))
        titles = tk.Frame(brand, bg=P["sidebar"])
        titles.pack(side="left")
        self._label(titles, "TORRENT", 14, bold=True).pack(anchor="w")
        self._label(titles, "MANAGER  /  0.3", 9, color="muted", bold=True).pack(anchor="w")
        self._label(self.sidebar, "MENÜ", 9, color="muted", bold=True).pack(anchor="w", padx=26, pady=(0, 11))
        for key, text in (
            ("dashboard", "▦    Áttekintés"), ("settings", "⚙    Beállítások"),
            ("activity", "≡    Napló és események"), ("updates", "↻    Frissítések"),
        ):
            b = tk.Button(self.sidebar, text=text, command=lambda name=key: self.show_page(name),
                          anchor="w", bg=P["sidebar"], fg=P["muted"], bd=0, relief="flat",
                          font=(FONT, 11), padx=25, pady=16, activeforeground=P["white"],
                          activebackground=P["panel_hi"], cursor="hand2", highlightthickness=0)
            b.pack(fill="x", pady=2, padx=9)
            self.nav_buttons[key] = b
        tk.Frame(self.sidebar, bg=P["sidebar"]).pack(fill="both", expand=True)
        bottom = tk.Frame(self.sidebar, bg=P["sidebar"])
        bottom.pack(fill="x", padx=22, pady=(0, 26))
        self._label(bottom, "HELYI ÜZEMMÓD", 9, color="green", bold=True).pack(anchor="w", pady=(0, 7))
        self._label(bottom, "Nem indul el automatikusan.", 9, color="muted").pack(anchor="w")
        self._label(bottom, "Az ablak bezárása leállítja.", 9, color="muted").pack(anchor="w")

        main = tk.Frame(self.root, bg=P["bg"])
        main.pack(side="left", fill="both", expand=True)
        top = tk.Frame(main, bg=P["bg"], height=90)
        top.pack(fill="x", padx=29, pady=(24, 12))
        self.heading = self._label(top, "Áttekintés", 23, bold=True)
        self.heading.pack(side="left", anchor="center")
        right = tk.Frame(top, bg=P["bg"])
        right.pack(side="right")
        self.status_chip = tk.Label(right, text="●  Leállítva", fg=P["muted"],
                                    bg=P["panel"], padx=15, pady=9, font=(FONT, 10, "bold"))
        self.status_chip.pack(side="right")
        self.body = tk.Frame(main, bg=P["bg"])
        self.body.pack(fill="both", expand=True, padx=29, pady=(0, 23))

    def _create_pages(self):
        for name in ("dashboard", "settings", "activity", "updates"):
            self.sections[name] = tk.Frame(self.body, bg=P["bg"])
        self._dashboard(self.sections["dashboard"])
        self._settings(self.sections["settings"])
        self._activity(self.sections["activity"])
        self._updates(self.sections["updates"])

    def show_page(self, page):
        if page == self.current_page:
            return
        if self.current_page:
            self.sections[self.current_page].pack_forget()
        self.current_page = page
        self.sections[page].pack(fill="both", expand=True)
        self.heading.configure(text={"dashboard": "Áttekintés", "settings": "Beállítások",
                                     "activity": "Napló és események", "updates": "Frissítések"}[page])
        for name, button in self.nav_buttons.items():
            active = name == page
            button.configure(bg=P["panel_hi"] if active else P["sidebar"],
                             fg=P["white"] if active else P["muted"],
                             font=(FONT, 11, "bold" if active else "normal"))
        if page == "dashboard":
            self.refresh_stats()

    def _dashboard(self, page):
        hero = self._card(page, 26)
        hero.pack(fill="x", pady=(0, 18))
        self._label(hero, "AZ AUTOMATIZÁLÁS VEZÉRLŐKÖZPONTJA", 9, "green", True).pack(anchor="w", pady=(0, 9))
        self._label(hero, "Minden letöltés egy helyen.", 22, bold=True).pack(anchor="w")
        self._label(hero, "BitHuMen toplista figyelése és qBittorrent-kezelés, átláthatóan.",
                    10, "muted").pack(anchor="w", pady=(7, 19))
        row = tk.Frame(hero, bg=P["panel"])
        row.pack(fill="x")
        self.start_btn = self._button(row, "▶  Automatizálás indítása", self.start)
        self.start_btn.pack(side="left", padx=(0, 10))
        self.stop_btn = self._button(row, "■  Leállítás", self.stop, "secondary", state="disabled")
        self.stop_btn.pack(side="left")
        self._button(row, "Beállítások  →", lambda: self.show_page("settings"), "ghost").pack(side="right")

        metrics = tk.Frame(page, bg=P["bg"])
        metrics.pack(fill="x", pady=(0, 18))
        metrics.columnconfigure((0, 1, 2, 3), weight=1, uniform="metrics")
        for col, label, value, note in (
            (0, "ÖSSZES TORRENT", self.stat_total, "qBittorrentben"),
            (1, "KEZELT TORRENT", self.stat_owned, "helyi nyilvántartás"),
            (2, "TÁRHELYHASZNÁLAT", self.stat_disk, "letöltési meghajtó"),
            (3, "ELLENŐRZÉSI IDŐ", self.stat_interval, "beállított időköz"),
        ):
            card = self._card(metrics, 17)
            card.grid(row=0, column=col, sticky="nsew", padx=(0, 8) if col != 3 else (0, 0))
            self._label(card, label, 8, "muted", True).pack(anchor="w")
            tk.Label(card, textvariable=value, fg=P["white"], bg=P["panel"],
                     font=(FONT, 25, "bold"), anchor="w").pack(anchor="w", pady=(7, 1))
            self._label(card, note, 9, "muted").pack(anchor="w")

        middle = self._card(page, 22)
        middle.pack(fill="x", pady=(0, 18))
        self._label(middle, "Tárhelyvédelem", 13, bold=True).pack(anchor="w")
        self.disk_subtitle = self._label(middle, "A felhasznált tárhelyet a letöltési mappához tartozó lemezen mérjük.",
                                         10, "muted")
        self.disk_subtitle.pack(anchor="w", pady=(5, 14))
        barbg = tk.Frame(middle, bg=P["input"], height=10)
        barbg.pack(fill="x")
        barbg.pack_propagate(False)
        self.disk_bar = tk.Frame(barbg, bg=P["green"], width=1, height=10)
        self.disk_bar.place(x=0, y=0, relheight=1, relwidth=0)
        self.disk_bar_parent = barbg
        self._label(middle, "A korlát az új torrentek hozzáadását állítja meg, nem a folyamatban lévő letöltéseket.",
                    9, "muted").pack(anchor="w", pady=(11, 0))

        recent = self._card(page, 20)
        recent.pack(fill="both", expand=True)
        cap = tk.Frame(recent, bg=P["panel"])
        cap.pack(fill="x", pady=(0, 12))
        self._label(cap, "Legutóbbi események", 13, bold=True).pack(side="left")
        self._button(cap, "Teljes napló  →", lambda: self.show_page("activity"), "ghost").pack(side="right")
        self.preview = tk.Text(recent, bg=P["panel"], fg=P["muted"], bd=0,
                               selectbackground=P["panel_hi"], highlightthickness=0,
                               font=("Consolas", 10), height=7, wrap="word", state="disabled")
        self.preview.pack(fill="both", expand=True)

    def _scroll_page(self, parent):
        canvas = tk.Canvas(parent, bg=P["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview,
                                 bg=P["panel_hi"], troughcolor=P["input"],
                                 activebackground=P["blue"], relief="flat", bd=0,
                                 highlightthickness=0)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        interior = tk.Frame(canvas, bg=P["bg"])
        win = canvas.create_window((0, 0), window=interior, anchor="nw")
        interior.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(win, width=event.width))
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * int(event.delta / 120), "units")
                        if self.current_page == "settings" else None)
        canvas.bind_all("<Button-4>", lambda _event: canvas.yview_scroll(-3, "units")
                        if self.current_page == "settings" else None)
        canvas.bind_all("<Button-5>", lambda _event: canvas.yview_scroll(3, "units")
                        if self.current_page == "settings" else None)
        return interior

    def _input(self, parent, key, label, row, secret=False, folder=False, hint=None):
        wrap = tk.Frame(parent, bg=P["panel"])
        wrap.grid(row=row, column=0, sticky="ew", pady=(0, 14))
        self._label(wrap, label, 10, bold=True).pack(anchor="w", pady=(0, 6))
        entryrow = tk.Frame(wrap, bg=P["panel"])
        entryrow.pack(fill="x")
        var = tk.StringVar(value=str(self.cfg.get(key, "")))
        self.vars[key] = var
        entry = tk.Entry(entryrow, textvariable=var, bg=P["input"], fg=P["white"],
                         insertbackground=P["white"], relief="flat", bd=0,
                         font=(FONT, 11), highlightthickness=1,
                         highlightbackground=P["line"], highlightcolor=P["blue"],
                         show="•" if secret else "")
        entry.pack(side="left", fill="x", expand=True, ipady=10, ipadx=11)
        if secret:
            self._button(entryrow, "Mutat", lambda e=entry: e.configure(show="" if e.cget("show") else "•"), "secondary").pack(side="left", padx=(8, 0))
        if folder:
            self._button(entryrow, "Tallózás", self.choose_folder, "secondary").pack(side="left", padx=(8, 0))
        if hint:
            self._label(wrap, hint, 9, "muted", wraplength=680, justify="left").pack(anchor="w", pady=(6, 0))
        return entry

    def _group(self, parent, title, subtitle=None):
        card = self._card(parent, 22)
        card.pack(fill="x", pady=(0, 16))
        self._label(card, title, 14, bold=True).pack(anchor="w")
        if subtitle:
            self._label(card, subtitle, 9, "muted", wraplength=680, justify="left").pack(anchor="w", pady=(4, 14))
        else:
            tk.Frame(card, bg=P["panel"], height=14).pack()
        grid = tk.Frame(card, bg=P["panel"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        return grid

    def _switch(self, parent, label, key, note=None, warning=False):
        var = tk.BooleanVar(value=bool(self.cfg.get(key, False)))
        self.vars[key] = var
        wrapper = tk.Frame(parent, bg=P["panel"])
        wrapper.pack(fill="x", pady=6)
        check = tk.Checkbutton(wrapper, text=label, variable=var, bg=P["panel"],
                               fg=P["white"], activebackground=P["panel"],
                               activeforeground=P["white"], selectcolor=P["input"],
                               font=(FONT, 11, "bold" if warning else "normal"),
                               anchor="w", cursor="hand2")
        check.pack(anchor="w")
        if note:
            self._label(wrapper, note, 9, "amber" if warning else "muted",
                        wraplength=680, justify="left").pack(anchor="w", padx=25, pady=(0, 4))

    def _settings(self, page):
        toolbar = tk.Frame(page, bg=P["bg"])
        toolbar.pack(fill="x", pady=(0, 13))
        self._label(toolbar, "A módosítások a következő indításkor lépnek életbe.", 10, "muted").pack(side="left")
        self._button(toolbar, "✓  Beállítások mentése", self.save).pack(side="right")
        inner = self._scroll_page(page)
        group = self._group(inner, "qBittorrent kapcsolat", "A meglévő qBittorrent Web UI beállításokat megtartjuk.")
        self._input(group, "qb_url", "Web UI címe", 0)
        self._input(group, "qb_username", "Felhasználónév", 1)
        self._input(group, "qb_password", "Jelszó", 2, secret=True)
        self._input(group, "qb_save_path", "Letöltési mappa", 3, folder=True)

        group = self._group(inner, "Automatizálási korlátok", "A toplistából maximum a beállított számú torrentet vizsgáljuk.")
        for i, (key, label, hint) in enumerate((
            ("check_minutes", "Ellenőrzési időköz (perc)", None),
            ("max_managed_torrents", "Maximális torrentek száma összesen", "A kézzel hozzáadott torrentek is beleszámítanak."),
            ("max_disk_usage_percent", "Tárhelykorlát (%)", "Példa: 70 – ennél nagyobb telítettségnél nem adunk hozzá új torrentet."),
            ("top_count", "Toplista feldolgozandó elemei", "A top 50 alapján történő törléshez legalább 50 szükséges."),
            ("browse_url", "BitHuMen toplista URL", None),
        )):
            self._input(group, key, label, i, hint=hint)

        safety = self._card(inner, 22)
        safety.pack(fill="x", pady=(0, 16))
        self._label(safety, "Biztonság és működés", 14, bold=True).pack(anchor="w", pady=(0, 12))
        for label, key, note, warning in (
            ("Próbaüzem: nincs valódi hozzáadás vagy törlés", "dry_run", None, False),
            ("Új torrentek hozzáadása", "enable_additions", None, False),
            ("Top 50-ből kikerült, korábban kezelt torrentek eltávolítása", "enable_deletions",
             "Csak teljesen ellenőrzött toplista alapján; első tesztelésnél maradjon kikapcsolva.", True),
            ("Letöltött fájlok törlése is", "delete_files",
             "Végleges adatvesztést okozhat. Csak akkor használd, ha biztos vagy a beállításokban.", True),
        ):
            self._switch(safety, label, key, note, warning)
        self._label(safety, "A változtatások mentése nem indítja el az automatizálást.", 9, "muted").pack(anchor="w", pady=(10, 0))

    def _activity(self, page):
        box = self._card(page, 18)
        box.pack(fill="both", expand=True)
        top = tk.Frame(box, bg=P["panel"])
        top.pack(fill="x", pady=(0, 15))
        self._label(top, "Élő eseménynapló", 14, bold=True).pack(side="left")
        self._button(top, "Napló mappa megnyitása", self.open_data_folder, "secondary").pack(side="right")
        self.logbox = tk.Text(box, wrap="word", bg=P["input"], fg=P["text"],
                              insertbackground=P["text"], selectbackground=P["panel_hi"],
                              font=("Consolas", 10), bd=0, padx=14, pady=14, state="disabled")
        scroll = tk.Scrollbar(box, command=self.logbox.yview, bg=P["panel_hi"],
                              troughcolor=P["input"], activebackground=P["blue"],
                              highlightthickness=0, bd=0, relief="flat")
        self.logbox.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.logbox.pack(fill="both", expand=True)
        self.logbox.tag_configure("error", foreground=P["red"])
        self.logbox.tag_configure("success", foreground=P["green"])
        self.logbox.tag_configure("muted", foreground=P["muted"])

    def _updates(self, page):
        hero = self._card(page, 26)
        hero.pack(fill="x", pady=(0, 18))
        self._label(hero, "FRISSÍTÉSI KÖZPONT", 9, "green", True).pack(anchor="w", pady=(0, 12))
        self._label(hero, f"Torrent Manager  v{VERSION}", 22, bold=True).pack(anchor="w")
        self._label(hero, "Új kiadások keresése a GitHub Releases oldalon.", 10, "muted").pack(anchor="w", pady=(7, 18))
        self._label(hero, "GitHub-tároló (felhasználó/projekt)", 10, bold=True).pack(anchor="w", pady=(0, 7))
        row = tk.Frame(hero, bg=P["panel"])
        row.pack(fill="x")
        self.repo_var = tk.StringVar(value=str(self.cfg.get("github_repository", "")))
        repo = tk.Entry(row, textvariable=self.repo_var, bg=P["input"], fg=P["white"],
                        insertbackground=P["white"], relief="flat", bd=0, font=(FONT, 11),
                        highlightthickness=1, highlightbackground=P["line"], highlightcolor=P["blue"])
        repo.pack(side="left", fill="x", expand=True, ipady=10, ipadx=11)
        self.check_button = self._button(row, "Frissítés keresése", self.check_updates)
        self.check_button.pack(side="left", padx=(12, 0))
        self._label(hero, "A kiadásokat egy saját, nyilvános GitHub-projektből tudja ellenőrizni."
                    " A mező mentéskor tárolódik.", 9, "muted", wraplength=680,
                    justify="left").pack(anchor="w", pady=(11, 0))
        self._button(hero, "GitHub-beállítás mentése", self.save_repository, "secondary").pack(anchor="w", pady=(14, 0))

        result = self._card(page, 25)
        result.pack(fill="x")
        self._label(result, "Elérhető verzió", 14, bold=True).pack(anchor="w")
        tk.Label(result, textvariable=self.update_message, bg=P["panel"], fg=P["muted"],
                 font=(FONT, 11), anchor="w", justify="left", wraplength=650).pack(fill="x", pady=(9, 15))
        actions = tk.Frame(result, bg=P["panel"])
        actions.pack(fill="x")
        self.install_button = self._button(actions, "Telepítő letöltése és indítása", self.install_update, state="disabled")
        self.install_button.pack(side="left")
        self._button(actions, "Kiadási oldal megnyitása", self.open_release_page, "secondary").pack(side="left", padx=(12, 0))
        self._label(result, "A telepítő csak egyező SHA-256 ellenőrzőösszeggel indítható, és mindig megerősítést kér.",
                    9, "muted", wraplength=650, justify="left").pack(anchor="w", pady=(17, 0))

    def choose_folder(self):
        folder = filedialog.askdirectory(parent=self.root)
        if folder:
            self.vars["qb_save_path"].set(folder)

    def _validated_settings(self):
        cfg = read_settings()
        required = {
            "qb_url": "qBittorrent Web UI címe", "qb_username": "qBittorrent felhasználónév",
            "qb_password": "qBittorrent jelszó", "qb_save_path": "Letöltési mappa",
            "check_minutes": "Ellenőrzési időköz", "max_managed_torrents": "Maximális torrentszám",
            "max_disk_usage_percent": "Tárhelykorlát", "top_count": "Toplista elemszáma",
            "browse_url": "BitHuMen toplista URL",
        }
        for key, label in required.items():
            if not str(self.vars[key].get()).strip():
                raise ValueError("Hiányzó beállítás: " + label)
        if not Path(self.vars["qb_save_path"].get().strip()).is_dir():
            raise ValueError("A letöltési mappa nem létezik. Válassz létező mappát.")
        for key, var in self.vars.items():
            value = var.get().strip() if isinstance(var, tk.StringVar) else var.get()
            if key in ("check_minutes", "top_count", "max_managed_torrents"):
                value = int(value)
                if value < 1:
                    raise ValueError(key + ": legalább 1 szükséges.")
            if key == "max_disk_usage_percent":
                value = float(value)
                if not 1 <= value <= 100:
                    raise ValueError("A tárhelykorlát 1–100% lehet.")
            cfg[key] = value
        repo = self.repo_var.get().strip()
        cfg["github_repository"] = normalize_repo(repo) if repo else ""
        return cfg

    def _write_config(self, cfg):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = SETTINGS.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(SETTINGS)
        self.cfg = cfg

    def save(self):
        try:
            cfg = self._validated_settings()
            if cfg["enable_deletions"] and cfg["delete_files"]:
                if not messagebox.askyesno("Végleges fájltörlés",
                                           "Engedélyezed a torrentekhez tartozó fájlok végleges törlését?",
                                           parent=self.root):
                    return False
            self._write_config(cfg)
            self.append("Beállítások elmentve. A változások a következő indításkor érvényesek.")
            self.refresh_stats()
            return True
        except (ValueError, OSError, UpdateError) as exc:
            messagebox.showerror("Beállítási hiba", str(exc), parent=self.root)
            return False

    def save_repository(self):
        try:
            repo = self.repo_var.get().strip()
            repo = normalize_repo(repo) if repo else ""
            cfg = read_settings()
            cfg["github_repository"] = repo
            self._write_config(cfg)
            self.update_message.set("GitHub-tároló mentve." if repo else "GitHub-tároló beállítása törölve.")
        except (UpdateError, OSError, ValueError) as exc:
            messagebox.showerror("GitHub-beállítás", str(exc), parent=self.root)

    def append(self, line):
        line = str(line)
        lowered = line.lower()
        tag = "error" if "hiba" in lowered or "sikertelen" in lowered else "success" if "hozzáadva" in lowered else "muted"
        self.logbox.configure(state="normal")
        self.logbox.insert("end", line + "\n", tag)
        if int(self.logbox.index("end-1c").split(".")[0]) > 1600:
            self.logbox.delete("1.0", "300.0")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")
        self.preview.configure(state="normal")
        self.preview.insert("end", line + "\n")
        if int(self.preview.index("end-1c").split(".")[0]) > 22:
            self.preview.delete("1.0", "6.0")
        self.preview.see("end")
        self.preview.configure(state="disabled")

    def _read_last_logs(self):
        if not LOG.exists():
            self.append("A napló itt fog megjelenni az első indítás után.")
            return
        try:
            with LOG.open("rb") as file:
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(max(0, size - 24000))
                data = file.read().decode("utf-8", errors="replace")
            for line in data.splitlines()[-70:]:
                self.append(line)
        except OSError:
            self.append("A korábbi napló nem olvasható.")

    def _status(self, running):
        self.running = running
        self.status.set("Fut" if running else "Leállítva")
        self.status_chip.configure(text="●  Fut" if running else "●  Leállítva",
                                   fg=P["green"] if running else P["muted"])
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")

    def start(self):
        if self.proc and self.proc.poll() is None:
            return
        if not self.save():
            self.show_page("settings")
            return
        if getattr(sys, "frozen", False):
            engine = BASE / "TorrentMotor.exe"
            cmd = [str(engine)]
        else:
            engine = BASE / "motor.py"
            cmd = [sys.executable, "-X", "utf8", "-u", str(engine)]
        if not engine.exists():
            messagebox.showerror("Hiányzó motor", f"Nem található: {engine}", parent=self.root)
            return
        env = os.environ.copy()
        env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"})
        if getattr(sys, "frozen", False):
            browser = find_playwright_browsers()
            if not browser:
                messagebox.showerror("Hiányzó Chromium",
                                     "A program nem találja a Playwright Chromium böngészőt. "
                                     "Ellenőrizd a 'browsers' mappát a program mellett, "
                                     "vagy telepítsd a Playwright Chromiumot.", parent=self.root)
                return
            env["PLAYWRIGHT_BROWSERS_PATH"] = str(browser)
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            proc = subprocess.Popen(cmd, cwd=str(DATA_DIR), stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace", bufsize=1,
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), env=env)
            self.proc = proc
            self._status(True)
            self.append("Automatizálás elindítva. A BitHuMen szükség esetén bejelentkezést kérhet.")
            threading.Thread(target=self.reader, args=(proc,), daemon=True).start()
        except (OSError, ValueError) as exc:
            self._status(False)
            messagebox.showerror("Indítási hiba", str(exc), parent=self.root)

    def reader(self, proc):
        try:
            for line in proc.stdout:
                self.events.put(("line", line.rstrip()))
        except Exception as exc:
            self.events.put(("line", "Naplóolvasási hiba: " + str(exc)))
        self.events.put(("done", (proc, proc.wait())))

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "line":
                    self.append(data)
                elif kind == "count":
                    self.stat_total.set(data)
                elif kind == "done":
                    proc, code = data
                    if proc is self.proc:
                        self._status(False)
                        self.append(f"A háttérprogram leállt. Kilépési kód: {code}." +
                                    (" Ellenőrizd a fenti hibaüzeneteket." if code != 0 else ""))
                        self.proc = None
                        self.refresh_stats()
                elif kind == "update_ok":
                    self.release = data
                    if data["newer"]:
                        self.update_message.set(f"Új verzió érhető el: {data['version']}." +
                                                (" A telepítő letölthető." if data["installer"] and data["checksums"]
                                                 else " A kiadásban nincs ellenőrizhető telepítő."))
                        self.install_button.configure(state="normal" if data["installer"] and data["checksums"] else "disabled")
                    else:
                        self.update_message.set(f"A telepített v{VERSION} verzió naprakész (legutóbbi kiadás: {data['version']}).")
                        self.install_button.configure(state="disabled")
                    self.check_button.configure(state="normal")
                elif kind == "update_error":
                    self.update_message.set("Ellenőrzési hiba: " + str(data))
                    self.check_button.configure(state="normal")
                elif kind == "download_ok":
                    self.downloading = False
                    self.install_button.configure(state="normal")
                    self._run_installer(data)
                elif kind == "download_error":
                    self.downloading = False
                    self.install_button.configure(state="normal")
                    self.update_message.set("Letöltési hiba: " + str(data))
                    messagebox.showerror("Frissítési hiba", str(data), parent=self.root)
        except queue.Empty:
            pass
        self.root.after(150, self.poll)

    def stop(self):
        proc = self.proc
        if not proc or proc.poll() is not None:
            return
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=15)
            else:
                proc.terminate()
            self.append("Leállítás kérve.")
        except (OSError, subprocess.TimeoutExpired) as exc:
            messagebox.showerror("Leállítási hiba", str(exc), parent=self.root)

    def refresh_stats(self):
        try:
            own = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
            self.stat_owned.set(str(len(own)) if isinstance(own, dict) else "–")
        except (OSError, ValueError):
            self.stat_owned.set("–")
        self.stat_total.set("–")  # Az élő API-szám helyett nem mutatunk téves értéket.
        path = str(self.vars["qb_save_path"].get()).strip()
        try:
            if not path or not Path(path).is_dir():
                raise OSError("Nincs elérhető célmappa")
            disk = shutil.disk_usage(path)
            percent = disk.used / disk.total * 100
            limit = float(self.vars["max_disk_usage_percent"].get())
            self.stat_disk.set(f"{percent:.1f}%")
            self.disk_subtitle.configure(text=f"Lemez telítettsége: {percent:.1f}%  •  Hozzáadási korlát: {limit:g}%")
            self.disk_bar.place_configure(relwidth=max(0.0, min(1.0, percent / 100)))
            self.disk_bar.configure(bg=P["amber"] if percent >= limit else P["green"])
        except (OSError, ValueError, ZeroDivisionError):
            self.stat_disk.set("–")
            self.disk_subtitle.configure(text="A lemezhasználat a beállított letöltési mappa alapján jelenik meg.")
            self.disk_bar.place_configure(relwidth=0)
        minutes = self.vars["check_minutes"].get().strip()
        self.stat_interval.set(f"{minutes} perc" if minutes.isdigit() else "–")
        # Az összes qBittorrent torrent számát kizárólag sikeres API-válaszból számoljuk.
        self._refresh_total_async()

    def _refresh_total_async(self):
        cfg = dict(self.cfg)
        if not all(cfg.get(key) for key in ("qb_url", "qb_username", "qb_password")):
            return
        def run():
            try:
                import requests
                s = requests.Session()
                s.headers["Referer"] = cfg["qb_url"].rstrip("/") + "/"
                r = s.post(cfg["qb_url"].rstrip("/") + "/api/v2/auth/login",
                           data={"username": cfg["qb_username"], "password": cfg["qb_password"]}, timeout=6)
                if r.status_code != 200 or r.text.strip().lower() not in ("ok.", ""):
                    return
                result = s.get(cfg["qb_url"].rstrip("/") + "/api/v2/torrents/info", timeout=6)
                result.raise_for_status()
                torrents = result.json()
                if isinstance(torrents, list):
                    self.events.put(("count", str(len(torrents))))
            except Exception:
                pass  # A kezelőfelület használható marad akkor is, ha a Web UI nem elérhető.
        threading.Thread(target=run, daemon=True).start()

    def _periodic_stats(self):
        self.refresh_stats()
        self.root.after(30000, self._periodic_stats)

    def check_updates(self):
        try:
            repo = normalize_repo(self.repo_var.get())
        except UpdateError as exc:
            messagebox.showerror("GitHub-tároló hiányzik", str(exc), parent=self.root)
            return
        self.release = None
        self.install_button.configure(state="disabled")
        self.check_button.configure(state="disabled")
        self.update_message.set("Kapcsolódás a GitHubhoz…")
        def task():
            try:
                self.events.put(("update_ok", check_latest(repo)))
            except Exception as exc:
                self.events.put(("update_error", exc))
        threading.Thread(target=task, daemon=True).start()

    def install_update(self):
        if os.name != "nt":
            messagebox.showinfo("Csak Windows", "A telepítő Windows alatt használható.", parent=self.root)
            return
        if not self.release or not self.release.get("newer") or self.downloading:
            return
        if not messagebox.askyesno("Frissítés letöltése",
                                   f"Letöltöd a Torrent Manager {self.release['version']} telepítőjét?\n"
                                   "A letöltés után a SHA-256 ellenőrzőösszeget is ellenőrizzük.",
                                   parent=self.root):
            return
        self.downloading = True
        self.install_button.configure(state="disabled")
        self.update_message.set("Telepítő letöltése és ellenőrzése…")
        release = dict(self.release)
        def task():
            try:
                dest = download_installer(release, DATA_DIR / "updates")
                self.events.put(("download_ok", dest))
            except Exception as exc:
                self.events.put(("download_error", exc))
        threading.Thread(target=task, daemon=True).start()

    def _run_installer(self, path):
        if not messagebox.askyesno("Ellenőrzött telepítő",
                                   "A telepítő letöltése és SHA-256 ellenőrzése sikerült.\n"
                                   "Bezárjuk a Torrent Managert, majd elindítjuk a Windows-telepítőt?",
                                   parent=self.root):
            self.update_message.set(f"A telepítő letöltve ide: {path}")
            return
        try:
            if self.proc and self.proc.poll() is None:
                self.stop()
            subprocess.Popen([str(path)], close_fds=True,
                             creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
            self.root.destroy()
        except OSError as exc:
            messagebox.showerror("Telepítő indítása sikertelen", str(exc), parent=self.root)

    def open_release_page(self):
        import webbrowser
        url = self.release.get("url") if self.release else ""
        if not url:
            try:
                url = "https://github.com/" + normalize_repo(self.repo_var.get()) + "/releases"
            except UpdateError as exc:
                messagebox.showerror("Nincs GitHub-tároló", str(exc), parent=self.root)
                return
        from urllib.parse import urlparse
        if urlparse(url).scheme == "https" and urlparse(url).hostname == "github.com":
            webbrowser.open(url)

    def open_data_folder(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(DATA_DIR))
        else:
            messagebox.showinfo("Napló mappája", str(DATA_DIR), parent=self.root)

    def close(self):
        if self.proc and self.proc.poll() is None:
            if not messagebox.askyesno("Kilépés", "Leállítsuk az automatizálást is?", parent=self.root):
                return
            self.stop()
        self.root.destroy()


if __name__ == "__main__":
    migrate_old_data()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    App(root)
    root.mainloop()
