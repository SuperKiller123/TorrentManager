# -*- coding: utf-8 -*-
"""Torrent Manager 0.5 – letisztult, magyar nyelvű Windows kezelőfelület."""
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
from updater import VERSION, check_latest, download_installer, UpdateError
from policy import DEFAULT, MODES, TOP_URL, GITHUB_REPO, normalize_settings, validate_settings
from windows_integration import remove_legacy_windows_startup, launch_qbittorrent

def read_settings():
    if SETTINGS.exists():
        return normalize_settings(json.loads(SETTINGS.read_text(encoding="utf-8")))
    return normalize_settings({})


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
        self.stat_disk = tk.StringVar(value="–")
        self.home_details = tk.StringVar(value="")
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
        threading.Thread(target=self._try_start_qb, daemon=True).start()
        threading.Thread(target=self._remove_old_startup, daemon=True).start()
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
        b = tk.Button(parent, text=text, command=command, bg=normal if state == "normal" else P["line"], fg=P["white"],
                      activebackground=active, activeforeground=P["white"],
                      disabledforeground=P["muted"], relief="flat", bd=0,
                      cursor="hand2", font=(FONT, 10, "bold"), highlightthickness=0,
                      padx=19, pady=11, width=width, state=state)
        b.bind("<Enter>", lambda _e: b.configure(bg=active) if str(b.cget("state")) == "normal" else None)
        b.bind("<Leave>", lambda _e: b.configure(bg=normal if str(b.cget("state")) == "normal" else P["line"]))
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
        self._label(titles, "MANAGER  /  0.5", 9, color="muted", bold=True).pack(anchor="w")
        self._label(self.sidebar, "MENÜ", 9, color="muted", bold=True).pack(anchor="w", padx=26, pady=(0, 11))
        for key, text in (
            ("dashboard", "▦    Kezdőlap"), ("settings", "⚙    Beállítások"),
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
        self._label(bottom, "SEEDEREK SZERINT", 9, color="green", bold=True).pack(anchor="w", pady=(0, 7))
        self._label(bottom, "Biztonságos próbaüzem az alapérték.", 9, color="muted").pack(anchor="w")
        self._label(bottom, "A bezárás leállítja a motort.", 9, color="muted").pack(anchor="w")

        main = tk.Frame(self.root, bg=P["bg"])
        main.pack(side="left", fill="both", expand=True)
        top = tk.Frame(main, bg=P["bg"], height=90)
        top.pack(fill="x", padx=29, pady=(24, 12))
        self.top_frame = top
        self.heading = self._label(top, "", 23, bold=True)
        self.heading.pack(side="left", anchor="center")
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
        if page == "dashboard":
            self.top_frame.pack_forget()
        elif not self.top_frame.winfo_manager():
            self.top_frame.pack(fill="x", padx=29, pady=(24, 12), before=self.body)
        self.heading.configure(text={"dashboard": "", "settings": "Beállítások",
                                     "activity": "Napló és események", "updates": "Frissítések"}[page])
        for name, button in self.nav_buttons.items():
            active = name == page
            button.configure(bg=P["panel_hi"] if active else P["sidebar"],
                             fg=P["white"] if active else P["muted"],
                             font=(FONT, 11, "bold" if active else "normal"))
        if page == "dashboard":
            self.refresh_stats()

    def _dashboard(self, page):
        hero = self._card(page, 17)
        hero.pack(fill="x", pady=(0, 14))
        self._label(hero, "Legtöbbet seedelt torrentek kezelése", 17, bold=True).pack(anchor="w")
        self._label(hero, "A BitHuMen toplistájának figyelése és a torrentek biztonságos kezelése.",
                    10, "muted").pack(anchor="w", pady=(4, 13))
        controls = tk.Frame(hero, bg=P["panel"])
        controls.pack(anchor="w")
        self.start_btn = self._button(controls, "Indítás", self.start, width=13)
        self.start_btn.pack(side="left", padx=(0, 10))
        self.stop_btn = self._button(controls, "Leállítás", self.stop, "secondary", width=13, state="disabled")
        self.stop_btn.pack(side="left")
        self.home_status = self._label(hero, "●  Leállítva", 10, "muted", bold=True)
        self.home_status.pack(anchor="w", pady=(12, 0))

        overview = tk.Frame(page, bg=P["bg"])
        overview.pack(fill="x", pady=(0, 14))
        overview.columnconfigure(0, weight=1, uniform="overview")
        overview.columnconfigure(1, weight=1, uniform="overview")
        disk = self._card(overview, 18)
        disk.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self._label(disk, "Tárhelyhasználat", 13, bold=True).pack(anchor="w")
        tk.Label(disk, textvariable=self.stat_disk, fg=P["white"], bg=P["panel"],
                 font=(FONT, 25, "bold"), anchor="w").pack(anchor="w", pady=(8, 6))
        self.disk_subtitle = self._label(disk, "", 10, "muted")
        self.disk_subtitle.pack(anchor="w", pady=(0, 8))
        barbg = tk.Frame(disk, bg=P["input"], height=8)
        barbg.pack(fill="x")
        barbg.pack_propagate(False)
        self.disk_bar = tk.Frame(barbg, bg=P["green"], width=1, height=8)
        self.disk_bar.place(x=0, y=0, relheight=1, relwidth=0)
        modecard = self._card(overview, 18)
        modecard.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self._label(modecard, "Működési mód", 13, bold=True).pack(anchor="w")
        self.home_mode = tk.StringVar(value="Próbaüzem")
        tk.Label(modecard, textvariable=self.home_mode, fg=P["white"], bg=P["panel"],
                 font=(FONT, 19, "bold"), anchor="w").pack(anchor="w", pady=(13, 6))
        self._label(modecard, "A tényleges műveleteket a naplóban követheted.", 9, "muted").pack(anchor="w")

        details = self._card(page, 17)
        details.pack(fill="x", pady=(0, 14))
        self._label(details, "Aktuális korlátok", 13, bold=True).pack(anchor="w", pady=(0, 8))
        tk.Label(details, textvariable=self.home_details, bg=P["panel"], fg=P["text"],
                 font=(FONT, 11), justify="left", anchor="w").pack(fill="x")
        recent = self._card(page, 16)
        recent.pack(fill="both", expand=True)
        self._label(recent, "Legutóbbi műveletek", 13, bold=True).pack(anchor="w", pady=(0, 8))
        self.preview = tk.Text(recent, bg=P["input"], fg=P["text"], bd=0,
                               selectbackground=P["panel_hi"], highlightthickness=0,
                               font=(FONT, 10), height=7, wrap="word", state="disabled")
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
            toggle = self._button(entryrow, "Mutatás", lambda: None, "secondary")
            def show_hide(e=entry, button=toggle):
                shown = bool(e.cget("show"))
                e.configure(show="" if shown else "•")
                button.configure(text="Elrejtés" if shown else "Mutatás")
            toggle.configure(command=show_hide)
            toggle.pack(side="left", padx=(8, 0))
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
        self.save_btn = self._button(toolbar, "✓  Beállítások mentése", self.save, state="disabled")
        self.save_btn.configure(bg=P["line"])
        self.save_btn.pack(side="right")
        inner = self._scroll_page(page)
        group = self._group(inner, "qBittorrent kapcsolat")
        self._input(group, "qb_url", "Web UI címe", 0)
        self._input(group, "qb_username", "Felhasználónév", 1)
        self._input(group, "qb_password", "Jelszó", 2, secret=True)
        self._input(group, "qb_save_path", "Letöltési mappa", 3, folder=True)

        group = self._group(inner, "Automatizálási korlátok")
        for i,(key,label) in enumerate((
            ("check_minutes", "Ellenőrzési időköz (perc)"),
            ("max_managed_torrents", "Torrentek száma (darab)"),
            ("max_disk_usage_percent", "Tárhelykorlát (%)"),
            ("min_size_gb", "Minimális torrentméret (GB)"),
            ("max_size_gb", "Maximális torrentméret (GB)"),
        )):
            self._input(group,key,label,i)

        safety = self._card(inner,22)
        safety.pack(fill="x",pady=(0,16))
        self._label(safety,"Biztonság és működés",14,bold=True).pack(anchor="w",pady=(0,10))
        mode = tk.StringVar(value=self.cfg.get("mode","dry"))
        self.vars["mode"] = mode
        for key,label in (
            ("dry","Próbaüzem"),
            ("add","Csak új torrentek hozzáadása"),
            ("full","Új torrentek hozzáadása és törlése (fájlokkal együtt)"),
        ):
            tk.Radiobutton(safety,text=label,variable=mode,value=key,
                           bg=P["panel"],fg=P["white"],activeforeground=P["white"],
                           activebackground=P["panel"],selectcolor=P["input"],
                           font=(FONT,11),cursor="hand2",anchor="w").pack(anchor="w",pady=5)

        self._saved_signature = self._form_signature()
        for var in self.vars.values():
            var.trace_add("write",lambda *_: self._sync_dirty())
        self._sync_dirty()

    def _form_signature(self):
        return tuple((key, var.get()) for key,var in sorted(self.vars.items()))

    def _sync_dirty(self):
        dirty=self._form_signature()!=self._saved_signature
        self.save_btn.configure(state="normal" if dirty else "disabled",
                                bg=P["blue"] if dirty else P["line"])

    def _activity(self, page):
        box = self._card(page, 18)
        box.pack(fill="both", expand=True)
        top = tk.Frame(box, bg=P["panel"])
        top.pack(fill="x", pady=(0, 15))
        self._label(top, "Élő eseménynapló", 14, bold=True).pack(side="left")
        self._button(top, "Napló mappa megnyitása", self.open_data_folder, "secondary").pack(side="right")
        self.logbox = tk.Text(box, wrap="word", bg=P["input"], fg=P["text"],
                              insertbackground=P["text"], selectbackground=P["panel_hi"],
                              font=(FONT, 11), bd=0, padx=14, pady=14, state="disabled")
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
        hero = self._card(page, 22)
        hero.pack(fill="x", pady=(0, 13))
        self._label(hero, "Telepített verzió", 10, "muted", True).pack(anchor="w")
        self._label(hero, f"Torrent Manager v{VERSION}", 22, bold=True).pack(anchor="w", pady=(7, 8))
        self._label(hero, "Frissítések a hivatalos GitHub-kiadásokból.", 10, "muted").pack(anchor="w")

        result = self._card(page, 22)
        result.pack(fill="x", pady=(0, 13))
        self._label(result, "Szoftverfrissítés", 14, bold=True).pack(anchor="w")
        tk.Label(result, textvariable=self.update_message, bg=P["panel"], fg=P["muted"],
                 font=(FONT, 11), anchor="w", justify="left", wraplength=690).pack(fill="x", pady=(9, 14))
        self.check_button = self._button(result, "Frissítés keresése", self.check_updates)
        self.check_button.pack(anchor="w", pady=(0, 9))
        self.install_button = self._button(result, "Frissítés letöltése és telepítése", self.install_update,
                                          state="disabled")
        self.install_button.pack(anchor="w")
        self._label(result, "A fájl épségét SHA-256 ellenőrzés védi; Windows-jogosultságkérés megjelenhet.",
                    9, "muted", wraplength=680, justify="left").pack(anchor="w", pady=(13, 0))

        about = self._card(page, 19)
        about.pack(fill="x")
        self._label(about, "A Torrent Managerről", 13, bold=True).pack(anchor="w", pady=(0, 8))
        self._label(about, "A Torrent Manager a BitHuMen legtöbbet seedelt torrentjeit figyeli, és a "
                    "qBittorrent segítségével kezeli a letöltéseket. Beállítható a torrentszám, "
                    "a tárhelyhatár, valamint a minimális és maximális méret.",
                    10, "text", wraplength=670, justify="left").pack(anchor="w", pady=(0, 7))
        self._label(about, "Próbaüzem, csak hozzáadás és ellenőrzött hozzáadás/törlés módokkal, "
                    "naplózással és beépített frissítéssel.",
                    10, "muted", wraplength=670, justify="left").pack(anchor="w")

    def choose_folder(self):
        folder = filedialog.askdirectory(parent=self.root)
        if folder:
            self.vars["qb_save_path"].set(folder)

    def _validated_settings(self):
        cfg = dict(self.cfg)
        for key,var in self.vars.items():
            cfg[key]=var.get().strip() if isinstance(var,tk.StringVar) else var.get()
        cfg=validate_settings(cfg)
        for key,label in (("qb_url","Web UI címe"),("qb_username","Felhasználónév"),
                          ("qb_password","Jelszó"),("qb_save_path","Letöltési mappa")):
            if not str(cfg[key]).strip():
                raise ValueError("Hiányzó beállítás: "+label)
        if not Path(cfg["qb_save_path"].strip()).is_dir():
            raise ValueError("A letöltési mappa nem létezik.")

        return cfg

    def _write_config(self,cfg):
        DATA_DIR.mkdir(parents=True,exist_ok=True)
        tmp=SETTINGS.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding="utf-8")
        tmp.replace(SETTINGS)
        self.cfg=cfg

    def save(self):
        try:
            cfg=self._validated_settings()
            if cfg["mode"]=="full" and self.cfg.get("mode")!="full":
                if not messagebox.askyesno("Végleges fájltörlés",
                    "Ebben az üzemmódban a kezelt torrentek és a letöltött fájljaik is véglegesen törlődhetnek. Engedélyezed?",
                    parent=self.root):
                    return False
            self._write_config(cfg)
            self._saved_signature=self._form_signature()
            self._sync_dirty()
            self.append("Beállítások mentve.")
            self.refresh_stats()
            return True
        except (ValueError,OSError,UpdateError) as exc:
            messagebox.showerror("Beállítási hiba",str(exc),parent=self.root)
            return False

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
        import re
        event = re.search(r"(?:^|\s)(Letöltve|Eltávolítva|Hozzáadva és ellenőrizve):\s*(.+)$",line)
        if event:
            verb="Letöltve" if event.group(1).startswith(("Let", "Hoz")) else "Eltávolítva"
            title=event.group(2).split(" | ")[0].split(" (fájlok")[0]
            self.preview.configure(state="normal")
            self.preview.insert("end", f"{verb}: {title}\n")
            if int(self.preview.index("end-1c").split(".")[0]) > 18:
                self.preview.delete("1.0","5.0")
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
            lines = data.splitlines()
            if size > 24000 and lines:
                lines = lines[1:]
            for line in lines[-70:]:
                self.append(line)
        except OSError:
            self.append("A korábbi napló nem olvasható.")

    def _status(self, running):
        self.running = running
        self.status.set("Fut" if running else "Leállítva")
        self.home_status.configure(text="●  Fut" if running else "●  Leállítva",
                                   fg=P["green"] if running else P["muted"])
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")

    def start(self):
        if self.proc and self.proc.poll() is None:
            return
        if (self._form_signature()!=self._saved_signature or not SETTINGS.exists()) and not self.save():
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
        threading.Thread(target=self._try_start_qb,daemon=True).start()
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

    def _set_install_enabled(self, enabled):
        self.install_button.configure(state="normal" if enabled else "disabled",
                                      bg=P["blue"] if enabled else P["line"])

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "line":
                    self.append(data)
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
                        self._set_install_enabled(bool(data["installer"] and data["checksums"]))
                    else:
                        self.update_message.set(f"A telepített v{VERSION} verzió naprakész (legutóbbi kiadás: {data['version']}).")
                        self._set_install_enabled(False)
                    self.check_button.configure(state="normal")
                elif kind == "update_error":
                    self.update_message.set("Ellenőrzési hiba: " + str(data))
                    self.check_button.configure(state="normal")
                elif kind == "download_ok":
                    self.downloading = False
                    self._set_install_enabled(True)
                    self._run_installer(data)
                elif kind == "download_error":
                    self.downloading = False
                    self._set_install_enabled(True)
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
        cfg = self.cfg
        path=str(cfg.get("qb_save_path", "")).strip()
        try:
            if not path or not Path(path).is_dir():
                raise OSError("Nincs célmappa")
            disk=shutil.disk_usage(path)
            percent=disk.used / disk.total*100
            limit=int(cfg["max_disk_usage_percent"])
            self.stat_disk.set(f"{percent:.1f}%")
            self.disk_subtitle.configure(text=f"{percent:.1f}% / {limit}%")
            self.disk_bar.place_configure(relwidth=max(0.0,min(1.0,percent/100)))
            self.disk_bar.configure(bg=P["amber"] if percent>=limit else P["green"])
        except (OSError,ValueError,ZeroDivisionError):
            self.stat_disk.set("–")
            self.disk_subtitle.configure(text="Nem elérhető")
            self.disk_bar.place_configure(relwidth=0)
        modes={"dry":"Próbaüzem","add":"Csak hozzáadás","full":"Hozzáadás és fájltörlés"}
        minimum=cfg.get("min_size_gb", "")
        maximum=cfg.get("max_size_gb", "")
        self.home_mode.set(modes.get(cfg["mode"], "–"))
        size_label = (f"{minimum or '–'} – {maximum or '–'} GB" if minimum or maximum
                      else "Nincs méretkorlát")
        self.home_details.set(
            f"Torrentek száma: {cfg['max_managed_torrents']} darab    •    "
            f"Ellenőrzés: {cfg['check_minutes']} percenként\n"
            f"Torrentméret: {size_label}    •    "
            f"Tárhelykorlát: {cfg['max_disk_usage_percent']}%")

    def _remove_old_startup(self):
        try:
            remove_legacy_windows_startup()
        except Exception as exc:
            self.events.put(("line", "Régi Windows-indítási bejegyzés eltávolítása sikertelen: " + str(exc)))

    def _try_start_qb(self):
        try:
            launch_qbittorrent()
            self.events.put(("line","qBittorrent indítási kérés elküldve."))
        except Exception as exc:
            self.events.put(("line","qBittorrent automatikus indítása nem sikerült: "+str(exc)))

    def _periodic_stats(self):
        self.refresh_stats()
        self.root.after(30000, self._periodic_stats)

    def check_updates(self):
        repo = GITHUB_REPO
        self.release = None
        self._set_install_enabled(False)
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
        self.downloading = True
        self._set_install_enabled(False)
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
        """A segédindító az alkalmazás bezárása után csendesen telepít."""
        import shutil
        try:
            if getattr(sys, "frozen", False):
                helper = BASE / "TorrentUpdater.exe"
                if not helper.is_file():
                    raise FileNotFoundError("Hiányzik a TorrentUpdater.exe a telepítésből.")
                copied = DATA_DIR / "updates" / "TorrentUpdater.exe"
                shutil.copy2(helper, copied)
                cmd = [str(copied)]
            else:
                helper = BASE / "update_helper.py"
                cmd = [sys.executable, str(helper)]
            app_exe = BASE / "TorrentManager.exe" if getattr(sys, "frozen", False) else BASE / "TorrentManager.py"
            if self.proc and self.proc.poll() is None:
                self.stop()
                if self.proc.poll() is None:
                    raise RuntimeError("Az automatizálási folyamat nem állt le, a frissítés megszakadt.")
            subprocess.Popen(cmd + [str(path), str(app_exe), str(os.getpid())],
                             cwd=str(DATA_DIR / "updates"), stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), close_fds=True)
            self.root.destroy()
        except (OSError, RuntimeError) as exc:
            self.update_message.set("Telepítő indítása sikertelen: " + str(exc))
            messagebox.showerror("Frissítési hiba", str(exc), parent=self.root)

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
