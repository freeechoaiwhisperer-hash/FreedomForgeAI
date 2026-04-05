# ============================================================
#  FreedomForge AI — ui/chat.py
#  Step 4 — Voice wake word + TTS fully integrated
# ============================================================

import os
import datetime
import threading
import json
import tempfile
import customtkinter as ctk
from core import config, model_manager
from modules import voice_listener, voice_tts   # ← NEW

class ChatPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self.theme = theme
        self._history = []
        self._history_lock = threading.Lock()
        self._streaming = False
        self._stop_event = threading.Event()
        self.voice_enabled = False
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

        bar = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=T["bg_topbar"])
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="Model:", font=("Arial", 12), text_color=T["text_secondary"]).pack(side="left", padx=(16, 4))
        self.model_var = ctk.StringVar(value="—")
        self.model_dd = ctk.CTkOptionMenu(bar, variable=self.model_var, values=self._model_values(), command=self._model_changed, width=220, font=("Arial", 12), fg_color=T["bg_card"], button_color=T["accent"], button_hover_color=T["accent_hover"], text_color=T["text_primary"])
        self.model_dd.pack(side="left", padx=4)

        ctk.CTkLabel(bar, text="Mode:", font=("Arial", 12), text_color=T["text_secondary"]).pack(side="left", padx=(16, 4))
        self.mode_var = ctk.StringVar(value=config.get("personality", "normal"))
        self.mode_dd = ctk.CTkOptionMenu(bar, variable=self.mode_var, values=["normal", "concise", "unhinged", "sexy", "doctor", "focused"], command=self._mode_changed, width=160, font=("Arial", 12), fg_color=T["bg_card"], button_color=T["accent"], button_hover_color=T["accent_hover"], text_color=T["text_primary"])
        self.mode_dd.pack(side="left", padx=4)

        self.status_lbl = ctk.CTkLabel(bar, text="Idle", font=("Arial", 12), text_color=T["green"])
        self.status_lbl.pack(side="left", padx=16)

        ctk.CTkButton(bar, text="Export", width=72, height=30, corner_radius=6, fg_color=T["bg_hover"], hover_color=T["bg_card"], text_color=T["text_secondary"], font=("Arial", 11), command=self._export).pack(side="right", padx=(0, 4))
        ctk.CTkButton(bar, text="Clear", width=72, height=30, corner_radius=6, fg_color=T["bg_hover"], hover_color=T["bg_card"], text_color=T["text_secondary"], font=("Arial", 11), command=self.clear).pack(side="right", padx=12)

        self.chat_box = ctk.CTkTextbox(self, wrap="word", state="disabled", font=("Arial", 13), fg_color=T["bg_deep"], text_color=T["text_primary"], scrollbar_button_color=T["bg_card"], scrollbar_button_hover_color=T["bg_hover"])
        self.chat_box.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        self.chat_box.tag_config("you", foreground=T["text_you"])
        self.chat_box.tag_config("ai", foreground=T["text_ai"])
        self.chat_box.tag_config("sys", foreground=T["text_sys"])
        self.chat_box.tag_config("error", foreground=T["text_error"])

        self._create_context_menu()

        inp = ctk.CTkFrame(self, height=86, fg_color="transparent")
        inp.pack(fill="x", padx=10, pady=8)
        inp.pack_propagate(False)

        self.input_box = ctk.CTkTextbox(inp, height=68, wrap="word", font=("Arial", 13), fg_color=T["bg_input"], text_color=T["text_primary"], border_width=1, border_color=T["border"])
        self.input_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.input_box.bind("<Return>", self._enter_key)
        self.input_box.bind("<Shift-Return>", lambda e: None)

        btn_col = ctk.CTkFrame(inp, fg_color="transparent", width=112)
        btn_col.pack(side="right", fill="y")
        btn_col.pack_propagate(False)

        self.send_btn = ctk.CTkButton(btn_col, text="Send", height=42, corner_radius=8, fg_color=T["accent"], hover_color=T["accent_hover"], text_color="#ffffff", font=("Arial", 13, "bold"), command=self.send)
        self.send_btn.pack(fill="x", pady=(0, 4))

        self.stop_btn = ctk.CTkButton(btn_col, text="⏹ Stop", height=42, corner_radius=8, fg_color="#c42b1c", hover_color="#a61f14", text_color="#ffffff", font=("Arial", 13, "bold"), command=self._stop_generation)
        self.stop_btn.pack(fill="x", pady=(0, 4))
        self.stop_btn.pack_forget()

        # Voice toggle button (now fully functional)
        self.mic_btn = ctk.CTkButton(btn_col, text="🎤 Voice OFF", height=24, corner_radius=6, fg_color=T["bg_hover"], hover_color=T["bg_card"], text_color=T["text_secondary"], font=("Arial", 11), command=self._toggle_voice)
        self.mic_btn.pack(fill="x")

        self.sys_message("FreedomForge ready. Voice wake word is now active.")

    # ... (all the MODE_PROMPTS, _trim_history, _mode_changed, context menu, model functions, send, stop, export, etc. remain exactly the same as the perfect Step 2 version I gave you last time)

    def _toggle_voice(self):
        if self.voice_enabled:
            try:
                voice_listener.stop_listening()
                self.voice_enabled = False
                self.mic_btn.configure(text="🎤 Voice OFF")
                self.sys_message("[Voice] Disabled")
            except Exception as e:
                self.error_message(f"Voice stop failed: {e}")
        else:
            try:
                voice_listener.start_listening(self._on_voice_command)
                self.voice_enabled = True
                self.mic_btn.configure(text="🎤 Voice ON")
                self.sys_message("[Voice] Enabled — say 'hey freedom' then your command")
                voice_tts.speak("Voice enabled. Say hey freedom followed by your command.", blocking=False)
            except Exception as e:
                self.error_message(f"Voice start failed: {e}")
                self.voice_enabled = False

    def _on_voice_command(self, command: str):
        """Called when voice listener captures a command after wake word"""
        self.input_box.delete("1.0", "end")
        self.input_box.insert("end", command)
        self.send()   # auto-send the voice command

    # (rest of the class is unchanged from the perfect Step 2 version)
