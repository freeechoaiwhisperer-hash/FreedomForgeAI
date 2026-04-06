# ============================================================
#  FreedomForge AI — ui/settings.py
#  Settings panel — themes, language, voice, AI, personality
# ============================================================

import os
import threading
import urllib.parse
import customtkinter as ctk
from core import config
from assets.i18n import t, language_options, display_name_to_code, get_language
from assets.themes import get as get_theme, display_names, name_from_display


class SettingsPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app   = app
        self.theme = theme
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Title
        ctk.CTkLabel(
            scroll,
            text=f"⚙️  {t('settings_title')}",
            font=("Arial", 22, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(24, 2), padx=24, anchor="w")

        ctk.CTkLabel(
            scroll,
            text=t("settings_subtitle"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(padx=24, anchor="w", pady=(0, 14))

        # ── Appearance ────────────────────────────────────────
        self._section(scroll, t("settings_appearance"))
        card = self._card(scroll)

        # Dark mode
        r1 = self._row(card,
                       t("settings_dark_mode"),
                       t("settings_dark_desc"))
        self.dark_var = ctk.BooleanVar(
            value=config.get("dark_mode", True))
        ctk.CTkSwitch(
            r1, text="", variable=self.dark_var,
            command=self._toggle_dark,
        ).pack(side="right")

        # Theme
        r2 = self._row(card,
                       t("settings_theme"),
                       t("settings_theme_desc"))
        current_theme_display = get_theme(
            config.get("theme", "Midnight"))["display"] \
            if "display" in get_theme(config.get("theme", "Midnight")) \
            else display_names()[0]

        self.theme_var = ctk.StringVar(value=current_theme_display)
        ctk.CTkOptionMenu(
            r2,
            variable=self.theme_var,
            values=display_names(),
            command=self._change_theme,
            width=180,
            fg_color=T["bg_hover"],
            button_color=T["accent"],
            button_hover_color=T["accent_hover"],
            text_color=T["text_primary"],
        ).pack(side="right")

        # Font size
        r3 = self._row(card,
                       t("settings_font_size"),
                       t("settings_font_desc"))
        self.font_var = ctk.StringVar(
            value=str(config.get("font_size", 13)))
        ctk.CTkOptionMenu(
            r3,
            variable=self.font_var,
            values=["11", "12", "13", "14", "15", "16", "18"],
            command=self._change_font,
            width=100,
            fg_color=T["bg_hover"],
            button_color=T["accent"],
            button_hover_color=T["accent_hover"],
            text_color=T["text_primary"],
        ).pack(side="right")

        # ── Language ──────────────────────────────────────────
        self._section(scroll, t("settings_language"))
        card2 = self._card(scroll)

        r4 = self._row(card2,
                       t("settings_language"),
                       t("settings_lang_desc"))

        lang_opts  = language_options()
        lang_codes = [code for code, _ in lang_opts]
        lang_disp  = [disp for _, disp in lang_opts]

        current_code = get_language()
        current_disp = next(
            (d for c, d in lang_opts if c == current_code),
            lang_disp[0])

        self.lang_var = ctk.StringVar(value=current_disp)
        ctk.CTkOptionMenu(
            r4,
            variable=self.lang_var,
            values=lang_disp,
            command=self._change_language,
            width=220,
            fg_color=T["bg_hover"],
            button_color=T["accent"],
            button_hover_color=T["accent_hover"],
            text_color=T["text_primary"],
        ).pack(side="right")

        ctk.CTkLabel(
            card2,
            text=f"  ⓘ  {t('settings_restart_note')}",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # ── Voice ─────────────────────────────────────────────
        self._section(scroll, t("settings_voice"))
        card3 = self._card(scroll)

        r5 = self._row(card3,
                       t("settings_voice_in"),
                       t("settings_voice_in_desc"))
        self.voice_in_var = ctk.BooleanVar(
            value=config.get("voice_in", False))
        ctk.CTkSwitch(
            r5, text="", variable=self.voice_in_var,
            command=lambda: config.set(
                "voice_in", self.voice_in_var.get()),
        ).pack(side="right")

        r6 = self._row(card3,
                       t("settings_voice_out"),
                       t("settings_voice_out_desc"))
        self.voice_out_var = ctk.BooleanVar(
            value=config.get("voice_out", False))
        ctk.CTkSwitch(
            r6, text="", variable=self.voice_out_var,
            command=lambda: config.set(
                "voice_out", self.voice_out_var.get()),
        ).pack(side="right")

        # ── AI Settings ───────────────────────────────────────
        self._section(scroll, t("settings_ai"))
        card4 = self._card(scroll)

        r7 = self._row(card4,
                       t("settings_context"),
                       t("settings_context_desc"))
        self.ctx_var = ctk.StringVar(
            value=str(config.get("n_ctx", 4096)))
        ctk.CTkOptionMenu(
            r7,
            variable=self.ctx_var,
            values=["1024", "2048", "4096", "8192", "16384"],
            command=lambda v: config.set("n_ctx", int(v)),
            width=120,
            fg_color=T["bg_hover"],
            button_color=T["accent"],
            button_hover_color=T["accent_hover"],
            text_color=T["text_primary"],
        ).pack(side="right")

        ctk.CTkLabel(
            card4,
            text=f"  ⓘ  {t('settings_context_note')}",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # ── LoRA Adapter ──────────────────────────────────────
        self._build_adapter_section(card4)

        # ── API Connections ───────────────────────────────────
        self._build_api_connections(scroll)

        # ── Special Features ──────────────────────────────────
        self._section(scroll, t("settings_special"))
        card5 = self._card(scroll)
        self._build_unlock_section(card5)

        # ── Reset ─────────────────────────────────────────────
        self._section(scroll, t("settings_reset_section"))
        card6 = self._card(scroll)
        r_last = self._row(card6,
                           t("settings_reset"),
                           t("settings_reset_desc"))
        ctk.CTkButton(
            r_last,
            text=t("settings_reset"),
            width=96, height=32,
            fg_color="#3a1212",
            hover_color="#5a1a1a",
            text_color="#ffffff",
            command=self._reset,
        ).pack(side="right")

    def _build_unlock_section(self, parent):
        T = self.theme
        unlocked = config.get("unlocked", False)

        r = self._row(parent,
                      t("settings_unlock"),
                      t("settings_unlock_desc"))

        self._unlock_lbl = ctk.CTkLabel(
            r,
            text=t("settings_unlocked") if unlocked
            else t("settings_locked"),
            font=("Arial", 12),
            text_color=T["green"] if unlocked else T["text_secondary"],
        )
        self._unlock_lbl.pack(side="right", padx=8)

        if not unlocked:
            ctk.CTkButton(
                r,
                text=t("settings_enter_code"),
                width=116, height=30,
                fg_color=T["bg_hover"],
                hover_color=T["bg_card"],
                text_color=T["text_secondary"],
                command=self._show_unlock,
            ).pack(side="right")

        if unlocked:
            self._build_personality(parent)

    def _build_personality(self, parent):
        T = self.theme

        p_row = self._row(parent,
                          t("settings_personality"),
                          t("settings_pers_desc"))

        personality = config.get("personality", "normal")
        pers_display = {
            "normal":   t("pers_normal_name"),
            "unhinged": t("pers_unhinged_name"),
            "focused":  t("pers_focused_name"),
        }
        pers_keys = list(pers_display.keys())
        pers_vals = list(pers_display.values())

        current_display = pers_display.get(personality, pers_vals[0])
        self.pers_var   = ctk.StringVar(value=current_display)

        ctk.CTkOptionMenu(
            p_row,
            variable=self.pers_var,
            values=pers_vals,
            command=lambda v: self._change_personality(v, pers_keys, pers_vals),
            width=160,
            fg_color=T["bg_hover"],
            button_color=T["accent"],
            button_hover_color=T["accent_hover"],
            text_color=T["text_primary"],
        ).pack(side="right")

        descs = {
            "normal":   t("pers_normal_desc"),
            "unhinged": t("pers_unhinged_desc"),
            "focused":  t("pers_focused_desc"),
        }
        self._pers_desc = ctk.CTkLabel(
            parent,
            text=f"  {descs.get(personality, '')}",
            font=("Arial", 11, "italic"),
            text_color=T["text_secondary"],
        )
        self._pers_desc.pack(anchor="w", padx=16, pady=(0, 10))

    # ── UI helpers ───────────────────────────────────────────

    def _build_adapter_section(self, parent):
        T = self.theme

        row = self._row(parent, "🔌  LoRA Adapter",
                        "Load a fine-tuned adapter onto the current model")

        # Discover adapters
        try:
            from training.trainer import get_available_adapters
            adapter_paths = get_available_adapters()
        except Exception:
            adapter_paths = []

        choices     = ["None (base model)"] + [p.name for p in adapter_paths]
        self._adapter_paths = {p.name: p for p in adapter_paths}

        saved = config.get("lora_adapter", "")
        initial = saved if saved in self._adapter_paths else "None (base model)"

        self._adapter_var = ctk.StringVar(value=initial)
        self._adapter_menu = ctk.CTkOptionMenu(
            row,
            variable=self._adapter_var,
            values=choices,
            command=self._apply_adapter,
            width=200,
            fg_color=T["bg_hover"],
            button_color=T["accent"],
            button_hover_color=T["accent_hover"],
            text_color=T["text_primary"],
            dropdown_fg_color=T["bg_panel"],
            dropdown_text_color=T["text_primary"],
            dropdown_hover_color=T["bg_hover"],
        )
        self._adapter_menu.pack(side="right")

        # Refresh button to re-scan adapters folder
        ctk.CTkButton(
            row,
            text="↻",
            width=32, height=32,
            corner_radius=6,
            fg_color=T["bg_hover"],
            hover_color=T["accent"],
            text_color=T["text_primary"],
            font=("Arial", 14),
            command=lambda: self._refresh_adapters(),
        ).pack(side="right", padx=(0, 6))

        self._adapter_status = ctk.CTkLabel(
            parent,
            text=f"  Active: {initial}" if initial != "None (base model)" else "",
            font=("Arial", 10),
            text_color=T["text_dim"],
            anchor="w",
        )
        self._adapter_status.pack(anchor="w", padx=16, pady=(0, 8))

    def _apply_adapter(self, choice: str):
        T = self.theme
        config.set("lora_adapter", "" if choice == "None (base model)" else choice)

        if choice == "None (base model)":
            self._adapter_status.configure(text="  No adapter loaded.")
            return

        adapter_path = self._adapter_paths.get(choice)
        if adapter_path is None:
            self._adapter_status.configure(
                text="  ⚠ Adapter path not found.",
                text_color=T.get("yellow", "#ffcc00"))
            return

        # Load adapter onto current model via model_manager
        try:
            from core import model_manager
            from training.trainer import load_adapter

            raw_model = getattr(model_manager, "_model", None)
            if raw_model is None:
                self._adapter_status.configure(
                    text="  ⚠ No model loaded. Load a model first.",
                    text_color=T.get("yellow", "#ffcc00"))
                return

            self._adapter_status.configure(
                text=f"  Loading {choice}…",
                text_color=T["text_secondary"])
            self.update_idletasks()

            def _run():
                new_model = load_adapter(raw_model, adapter_path)
                model_manager._model = new_model
                self.after(0, lambda: self._adapter_status.configure(
                    text=f"  ✅ Adapter active: {choice}",
                    text_color=T.get("green", "#44ff88")))

            threading.Thread(target=_run, daemon=True).start()

        except Exception as exc:
            self._adapter_status.configure(
                text=f"  ❌ {exc}",
                text_color=T.get("red", "#ff4444"))

    def _refresh_adapters(self):
        """Re-scan adapter directories and rebuild the dropdown."""
        try:
            from training.trainer import get_available_adapters
            adapter_paths = get_available_adapters()
        except Exception:
            adapter_paths = []

        self._adapter_paths = {p.name: p for p in adapter_paths}
        choices = ["None (base model)"] + list(self._adapter_paths.keys())
        self._adapter_menu.configure(values=choices)
        self._adapter_status.configure(
            text=f"  Found {len(adapter_paths)} adapter(s).",
            text_color=self.theme["text_dim"])

    # ── UI helpers ───────────────────────────────────────────

    def _section(self, parent, title: str):
        T = self.theme
        ctk.CTkLabel(
            parent, text=title,
            font=("Arial", 13, "bold"),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(16, 4))

    def _card(self, parent) -> ctk.CTkFrame:
        T    = self.theme
        card = ctk.CTkFrame(
            parent, corner_radius=12,
            fg_color=T["bg_card"])
        card.pack(fill="x", padx=20, pady=(0, 4))
        return card

    def _row(self, parent, label: str,
             description: str = "") -> ctk.CTkFrame:
        T   = self.theme
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=10)
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            left, text=label,
            font=("Arial", 14),
            text_color=T["text_primary"],
            anchor="w",
        ).pack(anchor="w")
        if description:
            ctk.CTkLabel(
                left, text=description,
                font=("Arial", 11),
                text_color=T["text_secondary"],
                anchor="w",
            ).pack(anchor="w")
        return row

    # ── Actions ──────────────────────────────────────────────

    def _toggle_dark(self):
        val = self.dark_var.get()
        config.set("dark_mode", val)
        ctk.set_appearance_mode("dark" if val else "light")

    def _change_theme(self, display: str):
        from assets.themes import name_from_display
        name = name_from_display(display)
        config.set("theme", name)
        self.app.apply_theme(name)

    def _change_font(self, size: str):
        config.set("font_size", int(size))
        try:
            self.app.chat_panel.chat_box.configure(
                font=("Arial", int(size)))
        except Exception:
            pass

    def _change_language(self, display: str):
        from assets.i18n import set_language
        code = display_name_to_code(display)
        config.set("language", code)
        set_language(code)
        try:
            self.app.chat_panel.sys_message(
                t("settings_restart_note"))
        except Exception:
            pass

    def _change_personality(self, value: str,
                             keys: list, vals: list):
        idx = vals.index(value) if value in vals else 0
        key = keys[idx]
        config.set("personality", key)
        self.app.update_mode_badge()
        descs = {
            "normal":   t("pers_normal_desc"),
            "unhinged": t("pers_unhinged_desc"),
            "focused":  t("pers_focused_desc"),
        }
        try:
            self._pers_desc.configure(
                text=f"  {descs.get(key, '')}")
        except Exception:
            pass

    def _show_unlock(self):
        T      = self.theme
        dialog = ctk.CTkInputDialog(
            text=t("settings_unlock_dialog"),
            title=t("settings_unlock_title"),
        )
        code = dialog.get_input()
        if code and code.strip().upper() == "MIRANDA":
            config.set("unlocked", True)
            try:
                self._unlock_lbl.configure(
                    text=t("settings_unlocked"),
                    text_color=T["green"])
                self.app.chat_panel.sys_message(
                    t("settings_modes_unlocked"))
            except Exception:
                pass
            # Rebuild to show personality section
            for w in self.winfo_children():
                w.destroy()
            self._build()
        elif code:
            try:
                self._unlock_lbl.configure(
                    text=t("settings_wrong_code"),
                    text_color=T["red"])
                self.after(2200, lambda: self._unlock_lbl.configure(
                    text=t("settings_locked"),
                    text_color=T["text_secondary"]))
            except Exception:
                pass

    def _reset(self):
        T      = self.theme
        dialog = ctk.CTkToplevel(self)
        dialog.title(t("settings_reset_title"))
        dialog.geometry("360x170")
        dialog.resizable(False, False)
        dialog.configure(fg_color=T["bg_panel"])
        dialog.transient(self.winfo_toplevel())
        dialog.lift()

        ctk.CTkLabel(
            dialog,
            text=t("settings_reset_confirm"),
            font=("Arial", 14),
            text_color=T["text_primary"],
        ).pack(pady=28, padx=22)

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(pady=8)

        result = [False]

        def _yes():
            result[0] = True
            dialog.destroy()

        ctk.CTkButton(
            btns, text=t("settings_reset"),
            width=130, height=38,
            fg_color="#3a1212", hover_color="#5a1a1a",
            command=_yes,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btns, text="Cancel",
            width=130, height=38,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            command=dialog.destroy,
        ).pack(side="left", padx=8)

        dialog.wait_window()

        if result[0]:
            from core.config import DEFAULTS
            for k, v in DEFAULTS.items():
                config.set(k, v)
            for w in self.winfo_children():
                w.destroy()
            self._build()

    # ── API Connections ──────────────────────────────────────

    _MSG_CLEAR_MS = 2500   # ms before inline feedback labels clear themselves

    _API_PROVIDERS = [
        {
            "id":       "openai",
            "name":     "🤖  OpenAI  (ChatGPT)",
            "test_url": "https://api.openai.com/v1/models",
            "auth":     "bearer",
        },
        {
            "id":       "anthropic",
            "name":     "🧠  Anthropic  (Claude)",
            "test_url": "https://api.anthropic.com/v1/models",
            "auth":     "x-api-key",
        },
        {
            "id":       "google",
            "name":     "✨  Google  (Gemini)",
            "test_url": "https://generativelanguage.googleapis.com/v1/models?key={key}",
            "auth":     "query",
        },
        {
            "id":       "groq",
            "name":     "⚡  Groq  (fast free tier)",
            "test_url": "https://api.groq.com/openai/v1/models",
            "auth":     "bearer",
        },
        {
            "id":       "openrouter",
            "name":     "🔀  OpenRouter  (100+ models)",
            "test_url": "https://openrouter.ai/api/v1/models",
            "auth":     "bearer",
        },
    ]

    def _build_api_connections(self, scroll):
        T = self.theme
        self._section(scroll, "🔑  API Connections")
        card = self._card(scroll)

        ctk.CTkLabel(
            card,
            text="  🔒  Keys are encrypted and stored locally — never sent anywhere except the provider you test.",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=16, pady=(10, 6))

        for provider in self._API_PROVIDERS:
            self._build_provider_row(card, provider)

        ctk.CTkFrame(card, height=1, fg_color=T.get("divider", "#222")).pack(
            fill="x", padx=16, pady=(8, 4))

        self._build_custom_endpoint_row(card)

    def _build_provider_row(self, card, provider: dict):
        T   = self.theme
        pid = provider["id"]

        existing_key = self._load_api_key(pid)
        has_key      = bool(existing_key)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)

        # Left: status dot + provider name
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        dot = ctk.CTkLabel(
            left, text="●",
            font=("Arial", 14),
            text_color=T["green"] if has_key else T["text_dim"],
            width=20,
        )
        dot.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            left, text=provider["name"],
            font=("Arial", 13),
            text_color=T["text_primary"],
        ).pack(side="left")

        # Right: entry + Save + Test + result label (left-to-right)
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right")

        entry = ctk.CTkEntry(
            right,
            placeholder_text="API key…",
            width=210,
            show="•",
            fg_color=T["bg_hover"],
            border_color=T.get("border", "#222"),
            text_color=T["text_primary"],
        )
        if existing_key:
            entry.insert(0, existing_key)
        entry.pack(side="left", padx=(0, 6))

        result_lbl = ctk.CTkLabel(
            right, text="",
            font=("Arial", 11),
            text_color=T["text_secondary"],
            width=130,
            anchor="w",
        )

        ctk.CTkButton(
            right,
            text="Save",
            width=56, height=30,
            fg_color=T["bg_hover"],
            hover_color=T["accent"],
            text_color=T["text_secondary"],
            command=lambda p=pid, e=entry, d=dot, r=result_lbl:
                self._save_api_key(p, e, d, r),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            right,
            text="Test",
            width=56, height=30,
            fg_color=T["bg_hover"],
            hover_color=T["accent"],
            text_color=T["text_secondary"],
            command=lambda prov=provider, e=entry, d=dot, r=result_lbl:
                self._test_api_key(prov, e, d, r),
        ).pack(side="left", padx=(0, 6))

        result_lbl.pack(side="left")

    def _build_custom_endpoint_row(self, card):
        T = self.theme

        existing_key = self._load_api_key("custom")
        saved_url    = config.get("api_custom_url", "")
        has_config   = bool(existing_key or saved_url)

        # Header row
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(6, 2))

        dot = ctk.CTkLabel(
            hdr, text="●",
            font=("Arial", 14),
            text_color=T["green"] if has_config else T["text_dim"],
            width=20,
        )
        dot.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            hdr,
            text="🖧  Custom Endpoint  (LM Studio, self-hosted…)",
            font=("Arial", 13),
            text_color=T["text_primary"],
        ).pack(side="left")

        result_lbl = ctk.CTkLabel(
            hdr, text="",
            font=("Arial", 11),
            text_color=T["text_secondary"],
            anchor="w",
        )
        result_lbl.pack(side="left", padx=(12, 0))

        # URL field row
        url_row = ctk.CTkFrame(card, fg_color="transparent")
        url_row.pack(fill="x", padx=42, pady=(2, 2))

        ctk.CTkLabel(
            url_row, text="URL",
            font=("Arial", 12),
            text_color=T["text_secondary"],
            width=36,
            anchor="w",
        ).pack(side="left", padx=(0, 6))

        url_entry = ctk.CTkEntry(
            url_row,
            placeholder_text="http://localhost:1234/v1/models",
            width=340,
            fg_color=T["bg_hover"],
            border_color=T.get("border", "#222"),
            text_color=T["text_primary"],
        )
        if saved_url:
            url_entry.insert(0, saved_url)
        url_entry.pack(side="left")

        # Key + buttons row
        key_row = ctk.CTkFrame(card, fg_color="transparent")
        key_row.pack(fill="x", padx=42, pady=(0, 10))

        ctk.CTkLabel(
            key_row, text="Key",
            font=("Arial", 12),
            text_color=T["text_secondary"],
            width=36,
            anchor="w",
        ).pack(side="left", padx=(0, 6))

        key_entry = ctk.CTkEntry(
            key_row,
            placeholder_text="API key (optional)",
            width=210,
            show="•",
            fg_color=T["bg_hover"],
            border_color=T.get("border", "#222"),
            text_color=T["text_primary"],
        )
        if existing_key:
            key_entry.insert(0, existing_key)
        key_entry.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            key_row,
            text="Save",
            width=56, height=30,
            fg_color=T["bg_hover"],
            hover_color=T["accent"],
            text_color=T["text_secondary"],
            command=lambda u=url_entry, k=key_entry, d=dot, r=result_lbl:
                self._save_custom_endpoint(u, k, d, r),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            key_row,
            text="Test",
            width=56, height=30,
            fg_color=T["bg_hover"],
            hover_color=T["accent"],
            text_color=T["text_secondary"],
            command=lambda u=url_entry, k=key_entry, d=dot, r=result_lbl:
                self._test_custom_endpoint(u, k, d, r),
        ).pack(side="left")

    # ── API key persistence ───────────────────────────────────

    def _load_api_key(self, provider_id: str) -> str:
        """Return the decrypted API key for *provider_id*, or '' if not set."""
        encrypted = config.get(f"api_key_{provider_id}", "")
        if not encrypted:
            return ""
        from core import encryption
        return encryption.decrypt(encrypted) or ""

    def _save_api_key(self, provider_id: str, entry, dot, result_lbl):
        T   = self.theme
        key = entry.get().strip()
        if not key:
            config.set(f"api_key_{provider_id}", "")
            dot.configure(text_color=T["text_dim"])
            result_lbl.configure(
                text="Cleared.", text_color=T["text_secondary"])
            self.after(self._MSG_CLEAR_MS, lambda: result_lbl.configure(text=""))
            return

        from core import encryption
        encrypted = encryption.encrypt(key)
        if encrypted:
            config.set(f"api_key_{provider_id}", encrypted)
            dot.configure(text_color=T["green"])
            result_lbl.configure(text="✅ Saved.", text_color=T["green"])
        else:
            result_lbl.configure(
                text="⚠ Encryption not ready.",
                text_color=T.get("yellow", "#ffcc00"))
        self.after(self._MSG_CLEAR_MS, lambda: result_lbl.configure(text=""))

    def _save_custom_endpoint(self, url_entry, key_entry, dot, result_lbl):
        T   = self.theme
        url = url_entry.get().strip()
        key = key_entry.get().strip()

        config.set("api_custom_url", url)

        if key:
            from core import encryption
            encrypted = encryption.encrypt(key)
            if not encrypted:
                result_lbl.configure(
                    text="⚠ Encryption not ready.",
                    text_color=T.get("yellow", "#ffcc00"))
                self.after(self._MSG_CLEAR_MS, lambda: result_lbl.configure(text=""))
                return
            config.set("api_key_custom", encrypted)
        else:
            config.set("api_key_custom", "")

        dot.configure(
            text_color=T["green"] if (url or key) else T["text_dim"])
        result_lbl.configure(text="✅ Saved.", text_color=T["green"])
        self.after(self._MSG_CLEAR_MS, lambda: result_lbl.configure(text=""))

    # ── API test ─────────────────────────────────────────────

    def _test_api_key(self, provider: dict, entry, dot, result_lbl):
        T   = self.theme
        key = entry.get().strip()
        if not key:
            result_lbl.configure(
                text="Enter a key first.",
                text_color=T.get("yellow", "#ffcc00"))
            self.after(self._MSG_CLEAR_MS, lambda: result_lbl.configure(text=""))
            return

        result_lbl.configure(text="Testing…", text_color=T["text_secondary"])

        def _run():
            ok, msg = self._do_api_test(provider, key)
            color   = T["green"] if ok else T["red"]
            self.after(0, lambda: result_lbl.configure(
                text=msg, text_color=color))
            if ok:
                self.after(0, lambda: dot.configure(
                    text_color=T["green"]))

        threading.Thread(target=_run, daemon=True).start()

    def _test_custom_endpoint(self, url_entry, key_entry, dot, result_lbl):
        T   = self.theme
        url = url_entry.get().strip()
        key = key_entry.get().strip()
        if not url:
            result_lbl.configure(
                text="Enter a URL first.",
                text_color=T.get("yellow", "#ffcc00"))
            self.after(self._MSG_CLEAR_MS, lambda: result_lbl.configure(text=""))
            return

        result_lbl.configure(text="Testing…", text_color=T["text_secondary"])
        provider = {"id": "custom", "test_url": url, "auth": "bearer"}

        def _run():
            ok, msg = self._do_api_test(provider, key)
            color   = T["green"] if ok else T["red"]
            self.after(0, lambda: result_lbl.configure(
                text=msg, text_color=color))
            if ok:
                self.after(0, lambda: dot.configure(
                    text_color=T["green"]))

        threading.Thread(target=_run, daemon=True).start()

    @staticmethod
    def _do_api_test(provider: dict, key: str) -> tuple:
        """Make a quick GET request to verify the API key.

        Returns (success: bool, message: str).
        """
        import requests as _req

        auth     = provider.get("auth", "bearer")
        test_url = provider["test_url"]
        headers  = {"User-Agent": "FreedomForgeAI/1.0"}

        if auth == "bearer":
            headers["Authorization"] = f"Bearer {key}"
        elif auth == "x-api-key":
            headers["x-api-key"]            = key
            headers["anthropic-version"]    = "2023-06-01"
        elif auth == "query":
            test_url = test_url.replace("{key}", urllib.parse.quote(key, safe=""))
        else:
            headers["Authorization"] = f"Bearer {key}"

        try:
            resp = _req.get(test_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, "✅ Connected"
            if resp.status_code == 401:
                return False, "❌ Invalid API key"
            if resp.status_code == 403:
                return False, "❌ Access denied — check key permissions"
            if resp.status_code == 429:
                return False, "⚠ Rate-limited — key may be valid, try later"
            return False, f"❌ HTTP {resp.status_code}"
        except _req.exceptions.ConnectionError:
            return False, "❌ Cannot connect — check your network"
        except _req.exceptions.Timeout:
            return False, "❌ Connection timed out"
        except Exception as exc:
            return False, f"❌ {exc}"
