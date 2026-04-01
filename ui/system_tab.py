# ============================================================
#  FreedomForge AI — ui/system_tab.py
#  Phase 3: System Intelligence Panel
# ============================================================

import threading
import customtkinter as ctk
from core import system_tools


class SystemPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app   = app
        self.theme = theme
        self._scan_running = False
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Title
        ctk.CTkLabel(scroll,
                     text="🖥️  System Intelligence",
                     font=("Arial", 22, "bold"),
                     text_color=T["text_primary"],
                     ).pack(pady=(24, 2), padx=24, anchor="w")
        ctk.CTkLabel(scroll,
                     text="Know exactly what your computer is doing. No tech degree needed.",
                     font=("Arial", 12),
                     text_color=T["text_secondary"],
                     ).pack(padx=24, anchor="w", pady=(0, 14))

        # ── Health Check ──────────────────────────────────────
        self._section(scroll, "📋  Full Health Check")
        health_card = self._card(scroll)

        ctrl = ctk.CTkFrame(health_card, fg_color="transparent")
        ctrl.pack(fill="x", padx=16, pady=(12, 8))

        self._scan_btn = ctk.CTkButton(
            ctrl,
            text="🔍  Scan My Computer",
            width=200, height=40,
            font=("Arial", 13, "bold"),
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            command=self._run_scan,
        )
        self._scan_btn.pack(side="left")

        self._scan_status = ctk.CTkLabel(
            ctrl, text="",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        )
        self._scan_status.pack(side="left", padx=16)

        self._health_box = ctk.CTkTextbox(
            health_card,
            height=320,
            font=("Courier", 11),
            fg_color=T["bg_deep"],
            text_color=T["green"],
            state="disabled",
        )
        self._health_box.pack(fill="x", padx=16, pady=(0, 16))

        # ── Live Stats ───────────────────────────────────────
        self._section(scroll, "⚡  Live Stats")
        live_card = self._card(scroll)
        self._build_live_stats(live_card, T)

        # ── Startup Programs ─────────────────────────────────
        self._section(scroll, "🚀  Startup Programs")
        start_card = self._card(scroll)
        self._build_startup_section(start_card, T)

        # ── Disk Cleaner ─────────────────────────────────────
        self._section(scroll, "🧹  Disk Space Cleaner")
        disk_card = self._card(scroll)
        self._build_disk_cleaner(disk_card, T)

    # ── Health scan ──────────────────────────────────────────

    def _run_scan(self):
        if self._scan_running:
            return
        self._scan_running = True
        self._scan_btn.configure(state="disabled", text="Scanning…")
        self._scan_status.configure(text="Gathering system info…")

        def _do():
            try:
                summary = system_tools.get_system_summary()
                report  = system_tools.get_health_report(summary)
                self.after(0, self._show_report, report)
            except Exception as e:
                self.after(0, self._show_report, f"Scan failed: {e}")

        threading.Thread(target=_do, daemon=True).start()

    def _show_report(self, text: str):
        self._scan_running = False
        self._scan_btn.configure(state="normal", text="🔍  Scan My Computer")
        self._scan_status.configure(text="Scan complete")
        try:
            self._health_box.configure(state="normal")
            self._health_box.delete("1.0", "end")
            self._health_box.insert("end", text)
            self._health_box.configure(state="disabled")
        except Exception:
            pass

    # ── Live stats ───────────────────────────────────────────

    def _build_live_stats(self, parent, T):
        import psutil
        from core.hardware import get_gpu_percent, detect_gpu

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=12)

        def _stat_box(label):
            box = ctk.CTkFrame(grid, corner_radius=8,
                               fg_color=T["bg_deep"], width=170)
            box.pack(side="left", padx=6, pady=4)
            box.pack_propagate(False)
            lbl = ctk.CTkLabel(box, text=label,
                               font=("Arial", 10),
                               text_color=T["text_secondary"])
            lbl.pack(pady=(8, 0))
            val = ctk.CTkLabel(box, text="—",
                               font=("Arial", 18, "bold"),
                               text_color=T["accent2"])
            val.pack(pady=(2, 6))
            return val

        cpu_val  = _stat_box("CPU Usage")
        ram_val  = _stat_box("RAM Usage")
        gpu_val  = _stat_box("GPU Usage")
        disk_val = _stat_box("Disk I/O")

        def _tick():
            if not self.winfo_exists():
                return
            try:
                cpu_val.configure(
                    text=f"{psutil.cpu_percent(interval=None):.0f}%")
                vm = psutil.virtual_memory()
                ram_val.configure(text=f"{vm.percent:.0f}%")
                gpu_val.configure(text=f"{get_gpu_percent():.0f}%")
                io = psutil.disk_io_counters()
                if io:
                    mb_s = round(
                        (io.read_bytes + io.write_bytes) / (1024**2), 1)
                    disk_val.configure(text=f"{mb_s} MB")
                else:
                    disk_val.configure(text="—")
            except Exception:
                pass
            try:
                self.after(1500, _tick)
            except Exception:
                pass

        _tick()

    # ── Startup programs ─────────────────────────────────────

    def _build_startup_section(self, parent, T):
        ctrl = ctk.CTkFrame(parent, fg_color="transparent")
        ctrl.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkButton(
            ctrl,
            text="🔄  Refresh List",
            width=140, height=32,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            command=lambda: self._load_startup(parent, T),
        ).pack(side="left")

        ctk.CTkLabel(
            ctrl,
            text="These apps launch every time you start your computer.",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(side="left", padx=12)

        self._startup_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._startup_frame.pack(fill="x", padx=12, pady=(0, 12))

        self._load_startup(parent, T)

    def _load_startup(self, parent, T):
        for w in self._startup_frame.winfo_children():
            w.destroy()

        def _do():
            items = system_tools.get_startup_programs()
            self.after(0, self._show_startup, items, T)

        threading.Thread(target=_do, daemon=True).start()

    def _show_startup(self, items, T):
        for w in self._startup_frame.winfo_children():
            w.destroy()

        if not items:
            ctk.CTkLabel(
                self._startup_frame,
                text="No startup programs found (or none detected on this system).",
                font=("Arial", 11),
                text_color=T["text_secondary"],
            ).pack(anchor="w", padx=4, pady=8)
            return

        for item in items[:20]:
            row = ctk.CTkFrame(
                self._startup_frame, corner_radius=8,
                fg_color=T["bg_hover"])
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row,
                text=item["name"][:46],
                font=("Arial", 12),
                text_color=T["text_primary"],
                anchor="w",
            ).pack(side="left", padx=12, pady=8)

            src = ctk.CTkLabel(
                row,
                text=item["source"],
                font=("Arial", 10),
                text_color=T["text_dim"],
            )
            src.pack(side="left", padx=4)

            if item["enabled"] and item["source"] in ("autostart",):
                ctk.CTkButton(
                    row,
                    text="Disable",
                    width=80, height=26,
                    fg_color="#3a1212",
                    hover_color="#5a1a1a",
                    text_color="#ffffff",
                    font=("Arial", 10),
                    command=lambda i=item, r=row: self._disable_startup(i, r, T),
                ).pack(side="right", padx=10, pady=6)

    def _disable_startup(self, item, row, T):
        ok = system_tools.disable_startup_item(item)
        if ok:
            for w in row.winfo_children():
                w.destroy()
            ctk.CTkLabel(
                row,
                text=f"✅  {item['name']} — disabled (takes effect on next login)",
                font=("Arial", 11),
                text_color=T["green"],
            ).pack(padx=12, pady=8)
        else:
            self._notify(f"Could not disable {item['name']}.\nYou may need to do it manually.", T)

    # ── Disk cleaner ─────────────────────────────────────────

    def _build_disk_cleaner(self, parent, T):
        ctrl = ctk.CTkFrame(parent, fg_color="transparent")
        ctrl.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkButton(
            ctrl,
            text="🔍  Find Large Files",
            width=170, height=36,
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            command=lambda: self._scan_large(parent, T),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            ctrl,
            text="🗑️  Find Junk / Cache",
            width=170, height=36,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            command=lambda: self._scan_junk(parent, T),
        ).pack(side="left")

        self._disk_status = ctk.CTkLabel(
            ctrl, text="",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        )
        self._disk_status.pack(side="left", padx=12)

        self._disk_results = ctk.CTkFrame(parent, fg_color="transparent")
        self._disk_results.pack(fill="x", padx=12, pady=(0, 12))

    def _scan_large(self, parent, T):
        self._disk_status.configure(text="Scanning (this may take a moment)…")
        for w in self._disk_results.winfo_children():
            w.destroy()

        def _do():
            files = system_tools.find_large_files(min_mb=50)
            self.after(0, self._show_large_files, files, T)

        threading.Thread(target=_do, daemon=True).start()

    def _show_large_files(self, files, T):
        self._disk_status.configure(
            text=f"Found {len(files)} files over 50 MB")
        for w in self._disk_results.winfo_children():
            w.destroy()

        if not files:
            ctk.CTkLabel(
                self._disk_results,
                text="No large files found in your home folder.",
                font=("Arial", 11),
                text_color=T["text_secondary"],
            ).pack(anchor="w", padx=4, pady=6)
            return

        for f in files[:15]:
            row = ctk.CTkFrame(
                self._disk_results, corner_radius=6,
                fg_color=T["bg_hover"])
            row.pack(fill="x", pady=1)

            size_color = T["red"] if f["size_mb"] > 1000 else \
                         T["yellow"] if f["size_mb"] > 200 else \
                         T["text_secondary"]

            ctk.CTkLabel(
                row,
                text=f["path"][:70],
                font=("Arial", 10),
                text_color=T["text_primary"],
                anchor="w",
            ).pack(side="left", padx=10, pady=6, fill="x", expand=True)

            ctk.CTkLabel(
                row,
                text=f"{f['size_mb']} MB",
                font=("Arial", 11, "bold"),
                text_color=size_color,
                width=90,
            ).pack(side="right", padx=10)

    def _scan_junk(self, parent, T):
        self._disk_status.configure(text="Scanning for junk files…")
        for w in self._disk_results.winfo_children():
            w.destroy()

        def _do():
            items = system_tools.find_temp_files()
            self.after(0, self._show_junk, items, T)

        threading.Thread(target=_do, daemon=True).start()

    def _show_junk(self, items, T):
        for w in self._disk_results.winfo_children():
            w.destroy()
        total_mb = sum(i["size_mb"] for i in items)
        self._disk_status.configure(
            text=f"Found {total_mb:.0f} MB that could be freed")

        if not items:
            ctk.CTkLabel(
                self._disk_results,
                text="Nothing to clean up. Your system is tidy!",
                font=("Arial", 11),
                text_color=T["green"],
            ).pack(anchor="w", padx=4, pady=6)
            return

        for item in items:
            row = ctk.CTkFrame(
                self._disk_results, corner_radius=8,
                fg_color=T["bg_hover"])
            row.pack(fill="x", pady=2)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True,
                      padx=12, pady=8)
            ctk.CTkLabel(
                left,
                text=item["label"],
                font=("Arial", 13),
                text_color=T["text_primary"],
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                left,
                text=item["path"],
                font=("Arial", 10),
                text_color=T["text_secondary"],
                anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                row,
                text=f"{item['size_mb']:.0f} MB",
                font=("Arial", 13, "bold"),
                text_color=T["yellow"],
                width=80,
            ).pack(side="right", padx=10)

        ctk.CTkLabel(
            self._disk_results,
            text=(
                "ℹ️  These are safe to delete but always review before removing. "
                "Open your file manager to delete them."
            ),
            font=("Arial", 10),
            text_color=T["text_secondary"],
            wraplength=700,
        ).pack(anchor="w", padx=4, pady=(6, 4))

    # ── Helpers ──────────────────────────────────────────────

    def _section(self, parent, title):
        T = self.theme
        ctk.CTkLabel(
            parent, text=title,
            font=("Arial", 13, "bold"),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(14, 4))

    def _card(self, parent):
        T    = self.theme
        card = ctk.CTkFrame(parent, corner_radius=12,
                            fg_color=T["bg_card"])
        card.pack(fill="x", padx=20, pady=(0, 4))
        return card

    def _notify(self, msg, T):
        win = ctk.CTkToplevel(self)
        win.title("FreedomForge AI")
        win.geometry("420x170")
        win.resizable(False, False)
        win.configure(fg_color=T["bg_panel"])
        # No grab_set — prevents main window from losing WM decorations on Linux
        ctk.CTkLabel(win, text=msg,
                     font=("Arial", 12),
                     text_color=T["text_primary"],
                     wraplength=380, justify="center",
                     ).pack(pady=28, padx=20)
        ctk.CTkButton(win, text="OK", width=100, height=34,
                      fg_color=T["accent"],
                      hover_color=T["accent_hover"],
                      command=win.destroy).pack()
