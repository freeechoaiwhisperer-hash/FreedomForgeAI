# ============================================================
#  FreedomForge AI — ui/app.py
#  Main application window — complete final version
# ============================================================

import random
import threading

import customtkinter as ctk

from core import config, hardware, model_manager, tts
from core import logger, encryption
from core.metadata_stamp import stamp_response, should_stamp
import modules
import modules.video  as video_module
import modules.agent  as agent_module
from assets.i18n   import t, set_language, detect_system_language
from assets.themes import get as get_theme

from ui.chat        import ChatPanel
from ui.models_tab  import ModelsPanel
from ui.settings    import SettingsPanel
from ui.about import AboutPanel
from ui.wizard      import SetupWizard, MIRANDA_QUOTES
from ui.privacy_tab import PrivacyPanel
from ui.terms_tab   import TermsPanel, TermsDialog
from ui.system_tab  import SystemPanel
from ui.training_tab import TrainingPanel
from core.trainer    import start_idle_trainer, ping_activity

from utils.paths import APP_VERSION


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Language
        saved_lang = config.get("language", None)
        lang = saved_lang if saved_lang else detect_system_language()
        set_language(lang)
        config.set("language", lang)

        # Theme
        theme_name   = config.get("theme", "Midnight")
        self._theme  = get_theme(theme_name)

        # Register modules
        modules.register("video", video_module)
        modules.register("agent", agent_module)

        # Window
        self.title(f"FreedomForge AI  v{APP_VERSION}")
        self.geometry("1380x860")
        self.minsize(980, 640)

        mode = "dark" if self._theme["base"] == "dark" else "light"
        ctk.set_appearance_mode(mode)
        ctk.set_default_color_theme("blue")

        # State
        self._alive            = True
        self._logo_clicks      = 0
        self._logo_timer       = None
        self._current_panel    = "Chat"
        self._miranda_open     = False  # BUG FIX: track open popup

        # Bind activity events for idle trainer
        from core.trainer import ping_activity
        self.bind_all("<Key>", lambda e: ping_activity())
        self.bind_all("<Button>", lambda e: ping_activity())

        tts.init_tts()

        # Show splash → check terms → wizard/main
        from ui.splash import SplashScreen
        self.withdraw()
        SplashScreen(self, self._after_splash)

    # ── Splash → Terms → Wizard → Main ───────────────────────

    def _after_splash(self):
        terms_accepted = config.get("terms_accepted", False)
        if not terms_accepted:
            self._show_terms()
        else:
            self._check_models()

    def _show_terms(self):
        # Must deiconify before creating a child dialog — some WMs
        # immediately close transient windows whose parent is withdrawn.
        self.deiconify()
        self.geometry("1x1+-9999+-9999")  # off-screen until UI is built
        TermsDialog(
            self,
            on_accept=self._check_models,
            on_decline=self.destroy,
            theme=self._theme,
        )

    def _check_models(self):
        from ui.wizard import should_run_wizard
        if should_run_wizard():
            # First-ever launch — walk user through setup
            self.deiconify()
            theme_name = config.get("theme", "Midnight")
            SetupWizard(self, self._wizard_done, theme_name)
        else:
            # Setup already done — show main UI; user downloads models via Models tab
            self.deiconify()
            self._build_ui()
            self._auto_load()
            self._schedule_miranda()

    def _wizard_done(self):
        for w in self.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        # Restore proper window state — wizard may have altered these
        self.resizable(True, True)
        self.minsize(980, 640)
        self.geometry("1380x860")
        self.deiconify()
        self._build_ui()
        self._auto_load()
        self._schedule_miranda()

    def _auto_load(self):
        models = model_manager.get_model_list()
        last   = config.get("last_model")
        target = (last if last and last in models
                  else models[0] if models else None)
        if target:
            self.load_model(target)

    # ── Miranda popups — FIXED: one at a time ────────────────

    def _schedule_miranda(self):
        if not self._alive:
            return
        delay = random.randint(6 * 60_000, 18 * 60_000)
        self.after(delay, self._miranda_popup)

    def _miranda_popup(self):
        """Show Miranda popup — only one at a time."""
        if not self._alive:
            return

        # BUG FIX: Don't open a new popup if one is already open
        if self._miranda_open:
            # Reschedule and try again later
            self._schedule_miranda()
            return

        T = self._theme
        try:
            self._miranda_open = True

            win = ctk.CTkToplevel(self)
            win.title("✨  Miranda")
            win.geometry("500x180")
            win.resizable(False, False)
            win.configure(fg_color=T["bg_card"])
            # Return focus to main window so typing is not interrupted.
            # focus_force at 200 ms beats the WM's default focus-on-map.
            self.after(200, self.focus_force)

            # Accent border at top
            ctk.CTkFrame(
                win, height=3,
                fg_color=T["purple"],
            ).pack(fill="x", side="top")

            ctk.CTkLabel(
                win,
                text=random.choice(MIRANDA_QUOTES),
                font=("Arial", 13, "italic"),
                text_color=T["purple"],
                wraplength=460,
                justify="center",
            ).pack(pady=(20, 12), padx=22)

            def _close():
                self._miranda_open = False
                win.destroy()
                # Schedule next popup after this one closes
                self._schedule_miranda()

            ctk.CTkButton(
                win,
                text="🪄  Thanks Miranda",
                width=190, height=36,
                corner_radius=18,
                fg_color=T["bg_hover"],
                hover_color=T["bg_panel"],
                text_color=T["purple"],
                command=_close,
            ).pack()

            # Also handle window close button
            win.protocol("WM_DELETE_WINDOW", _close)

        except Exception:
            self._miranda_open = False
            self._schedule_miranda()

    # ── UI build ─────────────────────────────────────────────

    def _build_ui(self):
        T = self._theme

        # Ensure window is properly configured regardless of prior state
        self.resizable(True, True)
        self.minsize(980, 640)
        self.title(f"FreedomForge AI  v{APP_VERSION}")

        # Top bar
        top = ctk.CTkFrame(
            self, height=66, corner_radius=0,
            fg_color=T["bg_topbar"])
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        # Logo
        self.logo_lbl = ctk.CTkLabel(
            top,
            text="⚒️  FreedomForge AI",
            font=("Arial", 22, "bold"),
            text_color=T["gold"],
            cursor="hand2",
        )
        self.logo_lbl.pack(side="left", padx=24)
        self.logo_lbl.bind("<Button-1>", self._logo_click)

        # Mode badge
        self.mode_badge = ctk.CTkLabel(
            top, text="",
            font=("Arial", 12, "bold"),
            text_color=T["accent2"],
        )
        self.mode_badge.pack(side="left", padx=4)
        self.update_mode_badge()

        self._build_toggles(top)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self, width=204, corner_radius=0,
            fg_color=T["bg_sidebar"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkFrame(
            self.sidebar, height=2,
            fg_color=T["accent"],
        ).pack(fill="x")

        ctk.CTkLabel(
            self.sidebar, text="MENU",
            font=("Arial", 10, "bold"),
            text_color=T["text_dim"],
        ).pack(pady=(22, 6), padx=16, anchor="w")

        self.nav_btns: dict = {}
        nav_items = [
            ("💬", t("nav_chat"),     "Chat"),
            ("📦", t("nav_models"),   "Models"),
            ("🔒", "Privacy",         "Privacy"),
            ("🖥️", "System",          "System"),
            ("🎓", "Training",        "Training"),
            ("⚙️", t("nav_settings"), "Settings"),
            ("📋", "Terms",           "Terms"),
            ("🪄", t("nav_about"),    "About"),
        ]
        for icon, label, key in nav_items:
            b = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}   {label}",
                font=("Arial", 13),
                height=54,
                corner_radius=0,
                fg_color="transparent",
                anchor="w",
                hover_color=T["bg_hover"],
                text_color=T["text_secondary"],
                command=lambda k=key: self.switch_panel(k),
            )
            b.pack(fill="x")
            self.nav_btns[key] = b

        ctk.CTkLabel(
            self.sidebar,
            text=f"v{APP_VERSION}  •  alpha",
            font=("Arial", 9),
            text_color=T["text_dim"],
        ).pack(side="bottom", pady=12)

        # Content
        self.content_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color="transparent")
        self.content_frame.pack(
            side="left", fill="both", expand=True)

        # Bottom bar
        bot = ctk.CTkFrame(
            self, height=46, corner_radius=0,
            fg_color=T["bg_topbar"])
        bot.pack(side="bottom", fill="x")
        bot.pack_propagate(False)
        self._build_pulse(bot)

        # Build all panels
        self.panels: dict = {}
        self.chat_panel     = ChatPanel(self.content_frame, self, T)
        self.models_panel   = ModelsPanel(self.content_frame, self, T)
        self.privacy_panel  = PrivacyPanel(self.content_frame, self, T)
        self.system_panel    = SystemPanel(self.content_frame, self, T)
        self.training_panel  = TrainingPanel(self.content_frame, self, T)
        self.settings_panel = SettingsPanel(self.content_frame, self, T)
        self.terms_panel    = TermsPanel(self.content_frame, T)
        self.about_panel    = AboutPanel(self.content_frame, T)

        self.panels["Chat"]     = self.chat_panel
        self.panels["Models"]   = self.models_panel
        self.panels["Privacy"]  = self.privacy_panel
        self.panels["System"]    = self.system_panel
        self.panels["Training"]  = self.training_panel
        self.panels["Settings"] = self.settings_panel
        self.panels["Terms"]    = self.terms_panel
        self.panels["About"]    = self.about_panel

        self.switch_panel("Chat")

    def _build_toggles(self, top):
        T = self._theme
        # Compact: label text lives on the switch itself — no separate CTkLabel
        toggles = [
            ("🤖 Agent",  "agent_var", self._toggle_agent,  False),
            ("🔊 Voice",  "tts_var",   self._toggle_tts,    config.get("voice_out", False)),
            ("🎤 Mic",    "voice_var", self._toggle_voice,  config.get("voice_in", False)),
        ]
        # Container keeps all three switches together and prevents them
        # from overlapping the logo on narrow windows
        tog_frame = ctk.CTkFrame(top, fg_color="transparent")
        tog_frame.pack(side="right", padx=8)
        for label, attr, cmd, default in reversed(toggles):
            var = ctk.BooleanVar(value=default)
            setattr(self, attr, var)
            sw = ctk.CTkSwitch(
                tog_frame, text=label, variable=var,
                onvalue=True, offvalue=False,
                command=cmd,
                width=40, height=22,
                font=("Arial", 10),
                text_color=T["text_dim"],
                button_color=T["accent"],
                button_hover_color=T["accent_hover"],
            )
            sw.pack(side="right", padx=(0, 10))
            setattr(self, f"{attr[:-4]}_sw", sw)

    def _build_pulse(self, parent):
        T = self._theme
        import psutil
        from core.hardware import get_gpu_percent

        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="right", padx=20, pady=10)

        cpu_lbl = ctk.CTkLabel(frame, text="CPU: --%",
                                font=("Arial", 11),
                                text_color=T["text_dim"])
        cpu_lbl.pack(side="left", padx=4)
        cpu_bar = ctk.CTkProgressBar(frame, width=76, height=5,
                                      corner_radius=2,
                                      progress_color=T["accent"],
                                      fg_color=T["bg_card"])
        cpu_bar.set(0)
        cpu_bar.pack(side="left", padx=4)

        gpu_lbl = ctk.CTkLabel(frame, text="GPU: --%",
                                font=("Arial", 11),
                                text_color=T["text_dim"])
        gpu_lbl.pack(side="left", padx=(10, 4))
        gpu_bar = ctk.CTkProgressBar(frame, width=76, height=5,
                                      corner_radius=2,
                                      progress_color=T["accent2"],
                                      fg_color=T["bg_card"])
        gpu_bar.set(0)
        gpu_bar.pack(side="left", padx=4)

        # Encryption indicator
        enc_lbl = ctk.CTkLabel(
            frame,
            text="🔐" if encryption.is_enabled() else "",
            font=("Arial", 12),
            text_color=T["green"],
        )
        enc_lbl.pack(side="left", padx=(12, 0))

        def _tick():
            if not self._alive:
                return
            try:
                cpu = psutil.cpu_percent(interval=None)
                cpu_lbl.configure(text=f"CPU: {cpu:.0f}%")
                cpu_bar.set(cpu / 100)
                gpu = get_gpu_percent()
                gpu_lbl.configure(text=f"GPU: {gpu:.0f}%")
                gpu_bar.set(gpu / 100)
            except Exception:
                pass
            self.after(1000, _tick)

        _tick()

    # ── Navigation ───────────────────────────────────────────

    def switch_panel(self, name: str):
        T = self._theme
        for panel in self.panels.values():
            panel.pack_forget()
        self.panels[name].pack(fill="both", expand=True)
        self._current_panel = name
        for k, b in self.nav_btns.items():
            active = k == name
            b.configure(
                fg_color=T["bg_hover"] if active else "transparent",
                text_color=T["text_primary"] if active else T["text_secondary"],
                font=("Arial", 13, "bold") if active else ("Arial", 13),
            )

    # ── Theme ─────────────────────────────────────────────────

    def apply_theme(self, theme_name: str):
        self._theme = get_theme(theme_name)
        config.set("theme", theme_name)
        T    = self._theme
        mode = "dark" if T["base"] == "dark" else "light"
        ctk.set_appearance_mode(mode)

        for panel in self.panels.values():
            panel.pack_forget()
        self.panels.clear()

        for w in self.content_frame.winfo_children():
            w.destroy()

        self.chat_panel     = ChatPanel(self.content_frame, self, T)
        self.models_panel   = ModelsPanel(self.content_frame, self, T)
        self.privacy_panel  = PrivacyPanel(self.content_frame, self, T)
        self.system_panel    = SystemPanel(self.content_frame, self, T)
        self.training_panel  = TrainingPanel(self.content_frame, self, T)
        self.settings_panel = SettingsPanel(self.content_frame, self, T)
        self.terms_panel    = TermsPanel(self.content_frame, T)
        self.about_panel    = AboutPanel(self.content_frame, T)

        self.panels["Chat"]     = self.chat_panel
        self.panels["Models"]   = self.models_panel
        self.panels["Privacy"]  = self.privacy_panel
        self.panels["System"]    = self.system_panel
        self.panels["Training"]  = self.training_panel
        self.panels["Settings"] = self.settings_panel
        self.panels["Terms"]    = self.terms_panel
        self.panels["About"]    = self.about_panel

        self.switch_panel(self._current_panel)
        self.update_mode_badge()

    # ── Model loading ─────────────────────────────────────────

    def load_model(self, model_name: str):
        try:
            self.chat_panel.set_status("loading")
            self.chat_panel.model_var.set(model_name)
        except Exception:
            pass
        model_manager.load_model(
            model_name,
            on_complete=lambda ok, err: self.after(
                0, lambda: self._model_loaded(ok, err, model_name)),
        )

    def _model_loaded(self, ok: bool, err: str, name: str):
        if ok:
            self.chat_panel.set_status("idle")
            self.chat_panel.sys_message(f"✅  {name} loaded.")
            self.chat_panel.refresh_model_list()
            self.models_panel.refresh()
            logger.info(f"Model active: {name}")
        else:
            self.chat_panel.set_status("error")
            self.chat_panel.error_message(
                f"Failed to load {name}: {err}")
            logger.error(f"Model load failed: {name} — {err}")

    # ── Easter egg ───────────────────────────────────────────

    def _logo_click(self, _=None):
        self._logo_clicks += 1
        if self._logo_timer:
            self.after_cancel(self._logo_timer)
        self._logo_timer = self.after(
            2200, lambda: setattr(self, "_logo_clicks", 0))
        if self._logo_clicks >= 5:
            self._logo_clicks = 0
            self._cycle_personality()

    def _cycle_personality(self):
        if not config.get("unlocked"):
            self.chat_panel.sys_message(
                "🔒  Something's hidden here…\n"
                "Go to Settings → Special Features to find the unlock code.")
            return
        order   = ["normal", "unhinged", "focused"]
        current = config.get("personality", "normal")
        idx     = order.index(current) if current in order else 0
        next_p  = order[(idx + 1) % len(order)]
        config.set("personality", next_p)
        self.update_mode_badge()
        self.chat_panel._history = []
        msgs = {
            "normal":   "✨  Normal mode.",
            "unhinged": f"🔥  {t('badge_chaos')} — Zero filter.",
            "focused":  f"🎯  {t('badge_focused')} — Precision mode.",
        }
        self.chat_panel.sys_message(msgs.get(next_p, ""))

    def update_mode_badge(self):
        p = config.get("personality", "normal")
        badges = {
            "normal":   "",
            "unhinged": t("badge_chaos"),
            "focused":  t("badge_focused"),
        }
        try:
            self.mode_badge.configure(text=badges.get(p, ""))
        except Exception:
            pass

    # ── Toggles ──────────────────────────────────────────────

    def _toggle_agent(self):
        on = self.agent_var.get()
        agent_module.set_enabled(on)
        if on:
            self.chat_panel.sys_message(t("agent_on"))
        else:
            self.chat_panel.sys_message(t("agent_off"))

    def _toggle_tts(self):
        config.set("voice_out", self.tts_var.get())

    def _toggle_voice(self):
        config.set("voice_in", self.voice_var.get())

    # ── Close ─────────────────────────────────────────────────

    def on_closing(self):
        self._alive = False
        logger.info("FreedomForge AI shutting down")
        self.destroy()
