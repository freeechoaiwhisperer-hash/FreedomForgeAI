# ============================================================
#  FreedomForge AI — ui/privacy_tab.py
#  Privacy & Security panel
# ============================================================

import threading
import customtkinter as ctk
from core import privacy
from core.crash_reporter import get_recent, send_anonymous


class PrivacyPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app       = app
        self.theme     = theme
        self._port_job = None
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

        ctk.CTkLabel(scroll, text="🔒  Privacy & Security",
                     font=("Arial", 22, "bold"),
                     text_color=T["text_primary"],
                     ).pack(pady=(24,2), padx=24, anchor="w")
        ctk.CTkLabel(scroll,
                     text="Your data stays on your machine. Always.",
                     font=("Arial", 12),
                     text_color=T["text_secondary"],
                     ).pack(padx=24, anchor="w", pady=(0,14))

        self._section(scroll, "🔑  Data Encryption")
        self._build_encryption(self._card(scroll))

        self._section(scroll, "🛡️  VPN Protection")
        self._build_vpn(self._card(scroll))

        self._section(scroll, "⚡  Network Kill Switch")
        self._build_kill(self._card(scroll))

        self._section(scroll, "📡  Port Monitor")
        self._build_ports(self._card(scroll))

        self._section(scroll, "🐛  Crash Reports")
        self._build_crashes(self._card(scroll))

    # ── Encryption ───────────────────────────────────────────

    def _build_encryption(self, p):
        T = self.theme
        if not privacy.CRYPTO_AVAILABLE:
            self._warn(p, "Run: pip install cryptography")
            return

        key = privacy.load_key()
        if key:
            fp  = privacy.get_key_fingerprint(key)
            row = self._row(p, "✅  Encryption Active",
                            f"Key fingerprint: {fp}")
            ctk.CTkButton(row, text="Rotate Key", width=110,
                          height=30, fg_color=T["bg_hover"],
                          hover_color=T["bg_card"],
                          text_color=T["text_secondary"],
                          command=self._rotate).pack(side="right")
        else:
            row = self._row(p, "🔓  Not Enabled",
                            "Encrypt all local data with a unique key.")
            ctk.CTkButton(row, text="Enable", width=100,
                          height=30, fg_color=T["accent"],
                          hover_color=T["accent_hover"],
                          text_color="#ffffff",
                          command=self._enable_enc).pack(side="right")

        adv = self._row(p, "🔧  Custom Passphrase",
                        "Advanced: set your own key passphrase.")
        ctk.CTkButton(adv, text="Set", width=80, height=28,
                      fg_color=T["bg_hover"],
                      hover_color=T["bg_card"],
                      text_color=T["text_secondary"],
                      command=self._custom_key).pack(side="right")

    def _enable_enc(self):
        key = privacy.generate_key()
        privacy.save_key(key)
        fp  = privacy.get_key_fingerprint(key)
        self._notify(
            f"✅  Encryption enabled!\n\nFingerprint: {fp}\n\n"
            f"Key saved at .forge_key — back it up somewhere safe.")
        self._rebuild()

    def _rotate(self):
        key = privacy.generate_key()
        privacy.save_key(key)
        self._notify(f"🔄  Key rotated.\n{privacy.get_key_fingerprint(key)}")
        self._rebuild()

    def _custom_key(self):
        dlg  = ctk.CTkInputDialog(
            text="Enter passphrase (min 12 chars):",
            title="Custom Passphrase")
        code = dlg.get_input()
        if code and len(code.strip()) >= 12:
            privacy.get_or_create_key(custom_key=code.strip())
            self._notify("✅  Custom passphrase set.")
            self._rebuild()
        elif code:
            self._notify("❌  Passphrase must be at least 12 characters.")

    # ── VPN ──────────────────────────────────────────────────

    def _build_vpn(self, p):
        T        = self.theme
        detected = privacy.detect_vpn()

        if detected:
            info = privacy.VPN_TOOLS[detected]
            row  = self._row(p, f"✅  {info['name']} found", info["note"])
            self.vpn_var = ctk.BooleanVar(value=False)
            ctk.CTkSwitch(row, text="Connect",
                          variable=self.vpn_var,
                          command=self._vpn_toggle,
                          ).pack(side="right")
        else:
            self._row(p, "No VPN installed",
                      "Install a VPN client for internet privacy.")
            for key, vpn in privacy.VPN_TOOLS.items():
                tag = "FREE tier" if vpn["free"] else "Paid"
                r   = self._row(p, vpn["name"],
                                f"{vpn['note']}  •  {tag}")
                ctk.CTkButton(r, text="Get it →", width=90, height=28,
                              fg_color=T["accent"],
                              hover_color=T["accent_hover"],
                              text_color="#ffffff",
                              command=lambda u=vpn["install"]: self._open(u),
                              ).pack(side="right")

    def _vpn_toggle(self):
        if self.vpn_var.get():
            privacy.vpn_connect(
                on_result=lambda ok, m: self.after(
                    0, lambda: self._notify(f"{'✅' if ok else '❌'}  {m}")))
        else:
            privacy.vpn_disconnect(
                on_result=lambda ok, m: self.after(
                    0, lambda: self._notify(f"{'✅' if ok else '❌'}  {m}")))

    def _open(self, url):
        try:
            import subprocess
            subprocess.Popen(["xdg-open", url])
        except Exception:
            import webbrowser
            webbrowser.open(url)

    # ── Kill switch ──────────────────────────────────────────

    def _build_kill(self, p):
        T = self.theme
        self._row(p, "⚡  Emergency Kill Switch",
                  "Cuts ALL internet instantly. Toggle again to restore. "
                  "Requires sudo password.")
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0,12))

        self.kill_btn = ctk.CTkButton(
            row, text="🔴  CUT ALL INTERNET",
            width=230, height=46,
            corner_radius=8,
            fg_color="#6a0000", hover_color="#8a0000",
            text_color="#ffffff",
            font=("Arial", 13, "bold"),
            command=self._kill_toggle)
        self.kill_btn.pack(side="left", padx=4)

        self.kill_lbl = ctk.CTkLabel(
            row, text="● Network: Normal",
            font=("Arial", 12), text_color=T["green"])
        self.kill_lbl.pack(side="left", padx=16)

    def _kill_toggle(self):
        T = self.theme
        if not privacy.is_kill_active():
            self.kill_btn.configure(
                text="🟢  RESTORE INTERNET",
                fg_color="#006a00")
            self.kill_lbl.configure(
                text="⚠️  Network: BLOCKED",
                text_color=T["red"])
            privacy.network_kill(
                on_result=lambda ok, m: self.after(
                    0, lambda: self._notify(m)))
        else:
            self.kill_btn.configure(
                text="🔴  CUT ALL INTERNET",
                fg_color="#6a0000")
            self.kill_lbl.configure(
                text="● Network: Normal",
                text_color=T["green"])
            privacy.network_restore(
                on_result=lambda ok, m: self.after(
                    0, lambda: self._notify(m)))

    # ── Port monitor ─────────────────────────────────────────

    def _build_ports(self, p):
        T = self.theme
        ctrl = ctk.CTkFrame(p, fg_color="transparent")
        ctrl.pack(fill="x", padx=16, pady=(8,4))
        ctk.CTkLabel(ctrl,
                     text="Live view of what's talking to the internet.",
                     font=("Arial", 11),
                     text_color=T["text_secondary"],
                     ).pack(side="left")
        self.mon_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(ctrl, text="Live", variable=self.mon_var,
                      command=self._mon_toggle).pack(side="right")

        self.port_box = ctk.CTkTextbox(
            p, height=150, font=("Courier", 10),
            fg_color=T["bg_deep"], text_color=T["green"],
            state="disabled")
        self.port_box.pack(fill="x", padx=16, pady=(0,12))

    def _mon_toggle(self):
        if self.mon_var.get():
            self._mon_tick()
        elif self._port_job:
            self.after_cancel(self._port_job)

    def _mon_tick(self):
        if not self.mon_var.get():
            return
        conns = privacy.get_active_connections()
        lines = [
            f"{c['process'][:18]:<18}  {c['local']:<22}  →  {c['remote']}"
            for c in conns[:18]
        ]
        text = "\n".join(lines) if lines else "No active connections."
        try:
            self.port_box.configure(state="normal")
            self.port_box.delete("1.0", "end")
            self.port_box.insert("end", text)
            self.port_box.configure(state="disabled")
        except Exception:
            pass
        self._port_job = self.after(3000, self._mon_tick)

    # ── Crash reports ────────────────────────────────────────

    def _build_crashes(self, p):
        T       = self.theme
        reports = get_recent()

        if not reports:
            ctk.CTkLabel(p, text="  ✅  No crash reports. All good!",
                         font=("Arial", 12),
                         text_color=T["green"],
                         ).pack(anchor="w", padx=16, pady=12)
            return

        ctk.CTkLabel(p,
                     text=f"  {len(reports)} report(s) saved locally.",
                     font=("Arial", 12),
                     text_color=T["yellow"],
                     ).pack(anchor="w", padx=16, pady=(12,4))

        for r in reports[:5]:
            row = ctk.CTkFrame(p, corner_radius=8,
                               fg_color=T["bg_hover"])
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row,
                         text=f"{r['error']}  —  {r['ts'][:19]}",
                         font=("Arial", 11),
                         text_color=T["text_secondary"],
                         anchor="w").pack(side="left", padx=10, pady=6)
            ctk.CTkButton(row, text="Send Anon",
                          width=90, height=26,
                          fg_color=T["accent"],
                          hover_color=T["accent_hover"],
                          text_color="#ffffff",
                          font=("Arial", 10),
                          command=lambda path=r["path"]: send_anonymous(
                              path,
                              on_result=lambda ok, m: self.after(
                                  0, lambda: self._notify(m))),
                          ).pack(side="right", padx=8, pady=6)

        ctk.CTkLabel(p,
                     text="  Reports contain no personal info — only error details and system specs.",
                     font=("Arial", 10),
                     text_color=T["text_secondary"],
                     ).pack(anchor="w", padx=16, pady=(4,12))

    # ── Helpers ──────────────────────────────────────────────

    def _rebuild(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _section(self, parent, title):
        T = self.theme
        ctk.CTkLabel(parent, text=title,
                     font=("Arial", 13, "bold"),
                     text_color=T["text_secondary"],
                     ).pack(anchor="w", padx=24, pady=(14,4))

    def _card(self, parent):
        T    = self.theme
        card = ctk.CTkFrame(parent, corner_radius=12,
                            fg_color=T["bg_card"])
        card.pack(fill="x", padx=20, pady=(0,4))
        return card

    def _row(self, parent, label, desc=""):
        T   = self.theme
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=9)
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(left, text=label,
                     font=("Arial", 14),
                     text_color=T["text_primary"],
                     anchor="w").pack(anchor="w")
        if desc:
            ctk.CTkLabel(left, text=desc,
                         font=("Arial", 11),
                         text_color=T["text_secondary"],
                         anchor="w", wraplength=560,
                         ).pack(anchor="w")
        return row

    def _warn(self, parent, msg):
        T = self.theme
        ctk.CTkLabel(parent, text=f"⚠️  {msg}",
                     font=("Arial", 12),
                     text_color=T["yellow"],
                     ).pack(anchor="w", padx=16, pady=12)

    def _notify(self, msg):
        T   = self.theme
        win = ctk.CTkToplevel(self)
        win.title("FreedomForge AI")
        win.geometry("460x200")
        win.resizable(False, False)
        win.configure(fg_color=T["bg_panel"])
        # No grab_set — prevents main window from losing WM decorations on Linux
        ctk.CTkLabel(win, text=msg,
                     font=("Arial", 12),
                     text_color=T["text_primary"],
                     wraplength=420, justify="center",
                     ).pack(pady=30, padx=20)
        ctk.CTkButton(win, text="OK", width=100, height=34,
                      fg_color=T["accent"],
                      hover_color=T["accent_hover"],
                      command=win.destroy).pack()
