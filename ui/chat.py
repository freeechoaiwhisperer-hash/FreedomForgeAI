# ============================================================
#  FreedomForge AI — ui/chat.py
#  Chat panel — streaming responses, themed, polished
# ============================================================

import os
import datetime
import customtkinter as ctk
from core import config, model_manager, tts
from assets.i18n import t
import modules
from core.metadata_stamp import stamp_response, should_stamp


class ChatPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app      = app
        self.theme    = theme
        self._history = []
        self._streaming = False
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
        bar = ctk.CTkFrame(
            self, height=50, corner_radius=0,
            fg_color=T["bg_topbar"])
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(
            bar, text=t("chat_model_label"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(side="left", padx=(16, 4))

        self.model_var = ctk.StringVar(value="—")
        self.model_dd  = ctk.CTkOptionMenu(
            bar,
            variable=self.model_var,
            values=self._model_values(),
            command=self._model_changed,
            width=310,
            font=("Arial", 12),
            fg_color=T["bg_card"],
            button_color=T["accent"],
            button_hover_color=T["accent_hover"],
            text_color=T["text_primary"],
        )
        self.model_dd.pack(side="left", padx=4)

        self.status_lbl = ctk.CTkLabel(
            bar,
            text=t("chat_status_idle"),
            font=("Arial", 12),
            text_color=T["green"],
        )
        self.status_lbl.pack(side="left", padx=16)

        ctk.CTkButton(
            bar,
            text="💾 Export",
            width=72, height=30,
            corner_radius=6,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            font=("Arial", 11),
            command=self._export,
        ).pack(side="right", padx=(0, 4))

        ctk.CTkButton(
            bar,
            text=t("chat_clear"),
            width=72, height=30,
            corner_radius=6,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            font=("Arial", 11),
            command=self.clear,
        ).pack(side="right", padx=12)

        # ── Chat display ─────────────────────────────────────
        font_size = config.get("font_size", 13)

        self.chat_box = ctk.CTkTextbox(
            self,
            wrap="word",
            state="disabled",
            font=("Arial", font_size),
            fg_color=T["bg_deep"],
            text_color=T["text_primary"],
            scrollbar_button_color=T["bg_card"],
            scrollbar_button_hover_color=T["bg_hover"],
        )
        self.chat_box.pack(
            fill="both", expand=True, padx=10, pady=(8, 0))

        # Color tags
        self.chat_box.tag_config("you",   foreground=T["text_you"])
        self.chat_box.tag_config("ai",    foreground=T["text_ai"])
        self.chat_box.tag_config("sys",   foreground=T["text_sys"])
        self.chat_box.tag_config("error", foreground=T["text_error"])
        self.chat_box.tag_config("name_you",
                                  foreground=T["text_you"])
        self.chat_box.tag_config("name_ai",
                                  foreground=T["accent2"])

        # ── Input area ───────────────────────────────────────
        inp = ctk.CTkFrame(
            self, height=86, fg_color="transparent")
        inp.pack(fill="x", padx=10, pady=8)
        inp.pack_propagate(False)

        self.input_box = ctk.CTkTextbox(
            inp, height=68, wrap="word",
            font=("Arial", 13),
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_width=1,
            border_color=T["border"],
        )
        self.input_box.pack(
            side="left", fill="both",
            expand=True, padx=(0, 8))
        self.input_box.bind("<Return>",       self._enter_key)
        self.input_box.bind("<Shift-Return>", lambda e: None)

        # Button column
        btn_col = ctk.CTkFrame(
            inp, fg_color="transparent", width=112)
        btn_col.pack(side="right", fill="y")
        btn_col.pack_propagate(False)

        self.send_btn = ctk.CTkButton(
            btn_col,
            text=t("chat_send"),
            height=42, corner_radius=8,
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            text_color="#ffffff",
            font=("Arial", 13, "bold"),
            command=self.send,
        )
        self.send_btn.pack(fill="x", pady=(0, 4))

        self.mic_btn = ctk.CTkButton(
            btn_col,
            text=t("chat_speak"),
            height=24, corner_radius=6,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            font=("Arial", 11),
            command=self._voice_input,
        )
        self.mic_btn.pack(fill="x")

        # Welcome — show first-time guidance only when no model is available yet
        if model_manager.get_model_list():
            self.sys_message(t("chat_welcome_ready"))
        else:
            self.sys_message(t("chat_welcome"))

    # ── Helpers ──────────────────────────────────────────────

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

    # ── Status ───────────────────────────────────────────────

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

    # ── Chat output ──────────────────────────────────────────

    def sys_message(self, text: str):
        self._append(f"[{t('chat_system')}]  {text}\n\n", "sys")

    def error_message(self, text: str):
        self._append(f"[Error]  {text}\n\n", "error")

    def _append(self, text: str, tag: str = "ai"):
        try:
            self.chat_box.configure(state="normal")
            self.chat_box.insert("end", text, tag)
            self.chat_box.configure(state="disabled")
            self.chat_box.see("end")
        except Exception:
            pass

    def _append_token(self, token: str):
        """Append a single streaming token without newline."""
        try:
            self.chat_box.configure(state="normal")
            self.chat_box.insert("end", token, "ai")
            self.chat_box.configure(state="disabled")
            self.chat_box.see("end")
        except Exception:
            pass

    def clear(self):
        self._history = []
        try:
            self.chat_box.configure(state="normal")
            self.chat_box.delete("1.0", "end")
            self.chat_box.configure(state="disabled")
        except Exception:
            pass

    def _export(self):
        """Save the full conversation text to ~/Downloads/chat_TIMESTAMP.txt"""
        try:
            text = self.chat_box.get("1.0", "end").strip()
            if not text:
                self.sys_message("💾 Nothing to export yet.")
                return
            ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(
                os.path.expanduser("~"), "Downloads", f"chat_{ts}.txt")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.sys_message(f"💾 Saved → {path}")
        except Exception as e:
            self.sys_message(f"❌ Export failed: {e}")

    # ── Send message ─────────────────────────────────────────

    def _enter_key(self, event):
        if not (event.state & 0x1):
            self.send()
            return "break"

    def send(self):
        if self._streaming:
            return

        user_msg = self.input_box.get("1.0", "end-1c").strip()
        if not user_msg:
            return

        self.input_box.delete("1.0", "end")

        # Show user message with name label
        self._append(f"\n{t('chat_you')}:  ", "name_you")
        self._append(f"{user_msg}\n\n", "you")

        # Module routing
        module_name = modules.route(user_msg)
        if module_name:
            self._handle_module(module_name, user_msg)
            return

        if not model_manager.is_model_loaded():
            self.sys_message(t("chat_no_model"))
            return

        self._history.append({"role": "user", "content": user_msg})
        self._start_stream(list(self._history))

    def _start_stream(self, history: list):
        """Start streaming response."""
        self._streaming = True
        self.set_status("thinking")
        self.send_btn.configure(state="disabled")

        personality  = config.get("personality", "normal")
        full_reply   = []

        # Write AI name label before streaming starts
        self._append(f"\n{t('chat_ai')}:  ", "name_ai")

        def on_token(token: str):
            full_reply.append(token)
            self.after(0, lambda t=token: self._append_token(t))

        def on_complete():
            reply = "".join(full_reply)
            stamped = stamp_response(reply) if should_stamp(reply) else reply
            self._history.append(
                {"role": "assistant", "content": stamped})
            self.after(0, self._stream_done)
            if config.get("voice_out") and stamped:
                tts.speak(stamped)

        def on_error(err: str):
            self.after(0, lambda: self._stream_error(err))

        model_manager.generate_stream(
            messages=history,
            personality=personality,
            on_token=on_token,
            on_complete=on_complete,
            on_error=on_error,
        )

    def _stream_done(self):
        self._streaming = False
        self._append("\n\n", "ai")
        self.set_status("idle")
        try:
            self.send_btn.configure(state="normal")
        except Exception:
            pass

    def _stream_error(self, err: str):
        self._streaming = False
        self._append("\n", "ai")
        self.error_message(err)
        self.set_status("error")
        try:
            self.send_btn.configure(state="normal")
        except Exception:
            pass

    # ── Module routing ───────────────────────────────────────

    def _handle_module(self, module_name: str, message: str):
        self._streaming = True
        self.send_btn.configure(state="disabled")
        self.set_status("thinking")
        self.sys_message(
            t("module_routing", module=module_name))

        def on_result(result: str):
            self.after(0, lambda: (
                self._append(f"\n{t('chat_ai')}:  ", "name_ai"),
                self._append(f"{result}\n\n", "ai"),
                self.set_status("idle"),
                self.send_btn.configure(state="normal"),
                setattr(self, "_streaming", False),
            ))

        def on_error(err: str):
            self.after(0, lambda: (
                self.error_message(err),
                self.set_status("idle"),
                self.send_btn.configure(state="normal"),
                setattr(self, "_streaming", False),
            ))

        modules.handle(module_name, message, on_result, on_error)

    # ── Voice input ──────────────────────────────────────────

    def _voice_input(self):
        if not tts.sr_available():
            self.sys_message(t("chat_voice_missing"))
            return

        self.set_status("listening")
        self.mic_btn.configure(
            text=t("chat_listening"),
            fg_color="#6a0000")

        def on_result(text: str):
            self.after(0, lambda: self._voice_done(text))

        def on_error(err: str):
            self.after(0, lambda: self._voice_failed(err))

        tts.listen(on_result, on_error)

    def _voice_done(self, text: str):
        self.mic_btn.configure(
            text=t("chat_speak"),
            fg_color=self.theme["bg_hover"])
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", text)
        self.send()

    def _voice_failed(self, error: str):
        self.mic_btn.configure(
            text=t("chat_speak"),
            fg_color=self.theme["bg_hover"])
        self.set_status("idle")
        self.sys_message(f"Voice: {error}")
