# ============================================================
#  FreedomForge AI — ui/chat.py
#  Chat panel — streaming responses, themed, polished + BUG FIXES
# ============================================================

import os
import datetime
import threading
import customtkinter as ctk
from core import config, model_manager, tts
from assets.i18n import t
import modules
from core.metadata_stamp import stamp_response, should_stamp


class ChatPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app        = app
        self.theme      = theme
        self._history   = []
        self._streaming = False
        self._stop_event = threading.Event()   # NEW: for Stop button
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        self._rebuild()

    def _rebuild(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        # ── Top bar ──────────────────────────────────────────
        bar = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=T["bg_topbar"])
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text=t("chat_model_label"), font=("Arial", 12), text_color=T["text_secondary"]).pack(side="left", padx=(16, 4))

        self.model_var = ctk.StringVar(value="—")
        self.model_dd  = ctk.CTkOptionMenu(bar, variable=self.model_var, values=self._model_values(), command=self._model_changed, width=310, font=("Arial", 12), fg_color=T["bg_card"], button_color=T["accent"], button_hover_color=T["accent_hover"], text_color=T["text_primary"])
        self.model_dd.pack(side="left", padx=4)

        self.status_lbl = ctk.CTkLabel(bar, text=t("chat_status_idle"), font=("Arial", 12), text_color=T["green"])
        self.status_lbl.pack(side="left", padx=16)

        ctk.CTkButton(bar, text="Export", width=72, height=30, corner_radius=6, fg_color=T["bg_hover"], hover_color=T["bg_card"], text_color=T["text_secondary"], font=("Arial", 11), command=self._export).pack(side="right", padx=(0, 4))
        ctk.CTkButton(bar, text=t("chat_clear"), width=72, height=30, corner_radius=6, fg_color=T["bg_hover"], hover_color=T["bg_card"], text_color=T["text_secondary"], font=("Arial", 11), command=self.clear).pack(side="right", padx=12)

        # ── Chat display ─────────────────────────────────────
        font_size = config.get("font_size", 13)

        self.chat_box = ctk.CTkTextbox(self, wrap="word", state="disabled", font=("Arial", font_size), fg_color=T["bg_deep"], text_color=T["text_primary"], scrollbar_button_color=T["bg_card"], scrollbar_button_hover_color=T["bg_hover"])
        self.chat_box.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        self.chat_box.tag_config("you",   foreground=T["text_you"])
        self.chat_box.tag_config("ai",    foreground=T["text_ai"])
        self.chat_box.tag_config("sys",   foreground=T["text_sys"])
        self.chat_box.tag_config("error", foreground=T["text_error"])
        self.chat_box.tag_config("name_you", foreground=T["text_you"])
        self.chat_box.tag_config("name_ai",  foreground=T["accent2"])

        # RIGHT-CLICK MENU FOR BOTH TEXT BOXES
        self._create_context_menu()

        # ── Input area ───────────────────────────────────────
        inp = ctk.CTkFrame(self, height=86, fg_color="transparent")
        inp.pack(fill="x", padx=10, pady=8)
        inp.pack_propagate(False)

        self.input_box = ctk.CTkTextbox(inp, height=68, wrap="word", font=("Arial", 13), fg_color=T["bg_input"], text_color=T["text_primary"], border_width=1, border_color=T["border"])
        self.input_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.input_box.bind("<Return>", self._enter_key)
        self.input_box.bind("<Shift-Return>", lambda e: None)

        # Button column
        btn_col = ctk.CTkFrame(inp, fg_color="transparent", width=112)
        btn_col.pack(side="right", fill="y")
        btn_col.pack_propagate(False)

        self.send_btn = ctk.CTkButton(btn_col, text=t("chat_send"), height=42, corner_radius=8, fg_color=T["accent"], hover_color=T["accent_hover"], text_color="#ffffff", font=("Arial", 13, "bold"), command=self.send)
        self.send_btn.pack(fill="x", pady=(0, 4))

        # STOP BUTTON (appears only while generating)
        self.stop_btn = ctk.CTkButton(btn_col, text="⏹ Stop", height=42, corner_radius=8, fg_color="#c42b1c", hover_color="#a61f14", text_color="#ffffff", font=("Arial", 13, "bold"), command=self._stop_generation)
        self.stop_btn.pack(fill="x", pady=(0, 4))
        self.stop_btn.pack_forget()   # hidden by default

        self.mic_btn = ctk.CTkButton(btn_col, text=t("chat_speak"), height=24, corner_radius=6, fg_color=T["bg_hover"], hover_color=T["bg_card"], text_color=T["text_secondary"], font=("Arial", 11), command=self._voice_input)
        self.mic_btn.pack(fill="x")

        # Welcome
        self.sys_message(t("chat_welcome"))

    def _create_context_menu(self):
        """Adds right-click copy/paste menu to input_box and chat_box"""
        self.context_menu = ctk.CTkMenu(self, tearoff=0)
        self.context_menu.add_command(label="Copy",  command=self._copy_text)
        self.context_menu.add_command(label="Cut",   command=self._cut_text)
        self.context_menu.add_command(label="Paste", command=self._paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self._select_all)

        # Bind right-click to both boxes
        self.input_box.bind("<Button-3>", self._show_context_menu)
        self.chat_box.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass

    def _copy_text(self):
        try:
            widget = self.focus_get()
            if widget and hasattr(widget, "selection_get"):
                self.clipboard_clear()
                self.clipboard_append(widget.selection_get())
        except Exception:
            pass

    def _cut_text(self):
        try:
            widget = self.focus_get()
            if widget and hasattr(widget, "selection_get"):
                self.clipboard_clear()
                self.clipboard_append(widget.selection_get())
                widget.delete("sel.first", "sel.last")
        except Exception:
            pass

    def _paste_text(self):
        try:
            widget = self.focus_get()
            if widget and hasattr(widget, "insert"):
                widget.insert("insert", self.clipboard_get())
        except Exception:
            pass

    def _select_all(self):
        try:
            widget = self.focus_get()
            if widget and hasattr(widget, "tag_add"):
                widget.tag_add("sel", "1.0", "end")
        except Exception:
            pass

    # ── Helpers (unchanged) ──────────────────────────────────
    def _model_values(self) -> list:
        models = model_manager.get_model_list()
        return models if models else [t("chat_no_model")]

    def refresh_model_list(self):
        values = self._model_values()
        self.model_dd.configure(values=values)
        current = model_manager.get_current_model()
        if current and current in values:
            self.model_var.set(current)

    def _model_changed(self, choice: str):
        if t("chat_no_model") in choice or "go to" in choice.lower():
            self.app.switch_panel("Models")
            return
        self._history = []
        self.app.load_model(choice)

    def set_status(self, state: str):
        T = self.theme
        styles = {
            "idle":      (T["green"],  t("chat_status_idle")),
            "thinking":  (T["yellow"], t("chat_status_thinking")),
            "loading":   (T["text_secondary"], t("chat_status_loading")),
            "listening": (T["purple"], t("chat_status_listening")),
            "error":     (T["red"],    t("chat_status_error")),
        }
        color, text = styles.get(state, (T["text_secondary"], state))
        try:
            self.status_lbl.configure(text=text, text_color=color)
        except Exception:
            pass

    def sys_message(self, text: str):
        self._append(f"[{t('chat_system')}]  {text}\n\n", "sys
