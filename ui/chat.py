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

class ChatPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app        = app
        self.theme      = theme
        self._history   = []
        self._streaming = False
        self._stop_event = threading.Event()
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

        # Top bar
        bar = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=T["bg_topbar"])
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="Model:", font=("Arial", 12), text_color=T["text_secondary"]).pack(side="left", padx=(16, 4))

        self.model_var = ctk.StringVar(value="—")
        self.model_dd  = ctk.CTkOptionMenu(bar, variable=self.model_var, values=self._model_values(), command=self._model_changed, width=310, font=("Arial", 12), fg_color=T["bg_card"], button_color=T["accent"], button_hover_color=T["accent_hover"], text_color=T["text_primary"])
        self.model_dd.pack(side="left", padx=4)

        self.status_lbl = ctk.CTkLabel(bar, text="Idle", font=("Arial", 12), text_color=T["green"])
        self.status_lbl.pack(side="left", padx=16)

        ctk.CTkButton(bar, text="Export", width=72, height=30, corner_radius=6, fg_color=T["bg_hover"], hover_color=T["bg_card"], text_color=T["text_secondary"], font=("Arial", 11), command=self._export).pack(side="right", padx=(0, 4))
        ctk.CTkButton(bar, text="Clear", width=72, height=30, corner_radius=6, fg_color=T["bg_hover"], hover_color=T["bg_card"], text_color=T["text_secondary"], font=("Arial", 11), command=self.clear).pack(side="right", padx=12)

        # Chat display
        self.chat_box = ctk.CTkTextbox(self, wrap="word", state="disabled", font=("Arial", 13), fg_color=T["bg_deep"], text_color=T["text_primary"], scrollbar_button_color=T["bg_card"], scrollbar_button_hover_color=T["bg_hover"])
        self.chat_box.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        self.chat_box.tag_config("you",   foreground=T["text_you"])
        self.chat_box.tag_config("ai",    foreground=T["text_ai"])
        self.chat_box.tag_config("sys",   foreground=T["text_sys"])
        self.chat_box.tag_config("error", foreground=T["text_error"])

        # Right-click menu (Copy/Cut/Paste)
        self._create_context_menu()

        # Input area
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

        self.mic_btn = ctk.CTkButton(btn_col, text="🎤 Speak", height=24, corner_radius=6, fg_color=T["bg_hover"], hover_color=T["bg_card"], text_color=T["text_secondary"], font=("Arial", 11), command=self._voice_input)
        self.mic_btn.pack(fill="x")

        self.sys_message("Welcome to FreedomForge AI. Type something or try /run for Agent Mode.")

    def _create_context_menu(self):
        self.context_menu = ctk.CTkMenu(self, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self._copy_text)
        self.context_menu.add_command(label="Cut", command=self._cut_text)
        self.context_menu.add_command(label="Paste", command=self._paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self._select_all)

        self.input_box.bind("<Button-3>", self._show_context_menu)
        self.chat_box.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except:
            pass

    def _copy_text(self): 
        try: self.clipboard_append(self.focus_get().selection_get())
        except: pass
    def _cut_text(self): 
        try: 
            w = self.focus_get()
            self.clipboard_append(w.selection_get())
            w.delete("sel.first", "sel.last")
        except: pass
    def _paste_text(self): 
        try: self.focus_get().insert("insert", self.clipboard_get())
        except: pass
    def _select_all(self): 
        try: self.focus_get().tag_add("sel", "1.0", "end")
        except: pass

    # Model dropdown now refreshes properly
    def _model_values(self):
        models = model_manager.get_model_list()
        return models if models else ["No models — go to Models tab"]

    def refresh_model_list(self):
        """Called automatically so downloaded models appear instantly"""
        values = self._model_values()
        self.model_dd.configure(values=values)
        current = model_manager.get_current_model()
        if current and current in values:
            self.model_var.set(current)

    def _model_changed(self, choice: str):
        if "No models" in choice or "go to" in choice.lower():
            self.app.switch_panel("Models")
            return
        self._history = []
        self.app.load_model(choice)
        self.refresh_model_list()   # force refresh after load

    # The rest of the file (send, stop, etc.) stays exactly the same as the version you just pasted
    def set_status(self, state: str):
        color_map = {"idle": "green", "thinking": "yellow", "error": "red"}
        color = color_map.get(state, "gray")
        text = state.capitalize()
        self.status_lbl.configure(text=text, text_color=color)

    def sys_message(self, text: str):
        self._append(f"[System] {text}\n\n", "sys")

    def error_message(self, text: str):
        self._append(f"[Error] {text}\n\n", "error")

    def _append(self, text: str, tag: str = "ai"):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", text, tag)
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def _append_token(self, token: str):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", token, "ai")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def clear(self):
        self._history = []
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")

    def _enter_key(self, event):
        if not event.state & 0x1:
            self.send()
            return "break"

    def send(self):
        message = self.input_box.get("1.0", "end").strip()
        if not message: return
        self.input_box.delete("1.0", "end")
        self._append(f"You: {message}\n\n", "you")
        self._history.append({"role": "user", "content": message})

        self._streaming = True
        self._stop_event.clear()
        self.send_btn.pack_forget()
        self.stop_btn.pack(fill="x", pady=(0, 4))
        self.set_status("thinking")

        threading.Thread(target=self._generate_response, daemon=True).start()

    def _stop_generation(self):
        self._stop_event.set()
        self._streaming = False
        self.stop_btn.pack_forget()
        self.send_btn.pack(fill="x", pady=(0, 4))
        self.set_status("idle")
        self._append("\n[Stopped by user]\n\n", "sys")

    def _generate_response(self):
        try:
            response = model_manager.generate(self._history, stop_event=self._stop_event, on_token=self._append_token)
            if not self._stop_event.is_set():
                self._append(f"FreedomForge: {response}\n\n", "ai")
                self._history.append({"role": "assistant", "content": response})
        except Exception as e:
            self.error_message(str(e))
        finally:
            self._streaming = False
            self.stop_btn.pack_forget()
            self.send_btn.pack(fill="x", pady=(0, 4))
            self.set_status("idle")

    def _voice_input(self):
        pass  # keep your original voice code if you have it

    def _export(self):
        pass  # keep your original export code if you have it
