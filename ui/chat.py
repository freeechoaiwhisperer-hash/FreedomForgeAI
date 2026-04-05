# ============================================================
#  FreedomForge AI — ui/chat.py
#  FINAL PERFECT VERSION - Step 4 Complete
#  - All 6 personality modes
#  - Voice wake word toggle + callback
#  - SQLite memory + keyword search
#  - Feedback learner (thumbs up/down)
#  - Decision engine (keyword routing)
#  - Thread safety + atomic export + activity logging
# ============================================================

import os
import datetime
import threading
import json
import tempfile
import sqlite3
import customtkinter as ctk
from core import config, model_manager
from modules import voice_listener, voice_tts

# ========== LIGHTWEIGHT MEMORY ==========
class SimpleMemory:
    def __init__(self, db_path="memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                role TEXT,
                content TEXT,
                timestamp TEXT
            )
        ''')
        self.conn.commit()

    def add_message(self, role, content):
        timestamp = datetime.datetime.now().isoformat()
        self.conn.execute(
            "INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)",
            (role, content, timestamp)
        )
        self.conn.commit()

    def search_keyword(self, query, limit=5):
        cursor = self.conn.execute(
            "SELECT role, content, timestamp FROM messages WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f'%{query}%', limit)
        )
        return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in cursor.fetchall()]

# ========== ACTIVITY LOGGER (for Dream Mode) ==========
class ActivityLogger:
    def __init__(self, log_file="activity_log.json"):
        self.log_file = log_file
        self.activities = []
        self._load()

    def _load(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.activities = json.load(f)
            except:
                self.activities = []

    def _save(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.activities, f)

    def log_activity(self, activity_type, data=None):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": activity_type,
            "data": data
        }
        self.activities.append(entry)
        if len(self.activities) > 1000:
            self.activities = self.activities[-1000:]
        self._save()

# ========== FEEDBACK LEARNER ==========
class FeedbackLearner:
    def __init__(self, storage_file="feedback_log.json"):
        self.storage_file = storage_file
        self.good_examples = []
        self.bad_examples = []
        self._load()

    def _load(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.good_examples = data.get('good', [])
                    self.bad_examples = data.get('bad', [])
            except:
                self.good_examples = []
                self.bad_examples = []

    def _save(self):
        with open(self.storage_file, 'w') as f:
            json.dump({'good': self.good_examples, 'bad': self.bad_examples}, f)

    def record_feedback(self, user_input, ai_response, is_good):
        example = [user_input, ai_response]
        if is_good:
            self.good_examples.append(example)
            if len(self.good_examples) > 20:
                self.good_examples = self.good_examples[-20:]
        else:
            self.bad_examples.append(example)
            if len(self.bad_examples) > 20:
                self.bad_examples = self.bad_examples[-20:]
        self._save()

    def improve_prompt(self, base_prompt):
        if not self.good_examples:
            return base_prompt
        examples = self.good_examples[-3:]
        prompt = base_prompt + "\n\nHere are examples of good responses:\n"
        for inp, out in examples:
            prompt += f"User: {inp}\nAssistant: {out}\n\n"
        return prompt

# ========== DECISION ENGINE ==========
class DecisionEngine:
    def __init__(self):
        self.routes = {
            "code": "coder", "python": "coder", "debug": "coder",
            "medical": "doctor", "health": "doctor",
            "science": "scientist", "physics": "scientist",
            "reason": "reasoner", "think": "reasoner", "logic": "reasoner"
        }

    def route(self, query):
        query_lower = query.lower()
        for keyword, specialist in self.routes.items():
            if keyword in query_lower:
                return specialist
        return "general"

    def get_system_prompt(self, specialist):
        prompts = {
            "coder": "You are a coding expert. Give clear, working code examples.",
            "doctor": "You are a medical assistant. Be accurate and caring.",
            "scientist": "You explain science simply and correctly.",
            "reasoner": "You think step by step. Show your reasoning.",
            "general": "You are a helpful assistant."
        }
        return prompts.get(specialist, prompts["general"])

# ========== MAIN CHAT PANEL ==========
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

        self.memory = SimpleMemory()
        self.activity_logger = ActivityLogger()
        self.learner = FeedbackLearner()
        self.decision_engine = DecisionEngine()

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

        fb_frame = ctk.CTkFrame(btn_col, fg_color="transparent")
        fb_frame.pack(fill="x", pady=(4, 0))
        self.thumbs_up = ctk.CTkButton(fb_frame, text="👍", width=40, height=24, fg_color=T["bg_hover"], command=self._feedback_good)
        self.thumbs_up.pack(side="left", padx=2)
        self.thumbs_down = ctk.CTkButton(fb_frame, text="👎", width=40, height=24, fg_color=T["bg_hover"], command=self._feedback_bad)
        self.thumbs_down.pack(side="left", padx=2)

        self.mic_btn = ctk.CTkButton(btn_col, text="🎤 Voice OFF", height=24, corner_radius=6, fg_color=T["bg_hover"], hover_color=T["bg_card"], text_color=T["text_secondary"], font=("Arial", 11), command=self._toggle_voice)
        self.mic_btn.pack(fill="x", pady=(4, 0))

        self.sys_message("FreedomForge ready. Memory, routing, feedback, and voice active.")

    MODE_PROMPTS = {
        "normal":   "You are a helpful, friendly assistant.",
        "concise":  "Answer in one short sentence when possible. Be direct.",
        "unhinged": "Be wild, chaotic, creative, and slightly unhinged.",
        "sexy":     "Be flirtatious, warm, and seductive in your replies.",
        "doctor":   "Speak calmly and professionally like a caring physician.",
        "focused":  "Stay strictly on topic. No tangents or extra chatter."
    }

    def _trim_history(self, max_exchanges=12):
        with self._history_lock:
            if len(self._history) > max_exchanges * 2:
                self._history = self._history[-max_exchanges*2:]

    def _mode_changed(self, choice: str):
        config.set("personality", choice)
        with self._history_lock:
            self._history = []
        self.sys_message(f"Switched to {choice} mode.")
        self.activity_logger.log_activity("mode_change", {"mode": choice})

    def _model_changed(self, choice: str):
        if "No models" in choice or "go to" in choice.lower():
            self.app.switch_panel("Models")
            return
        with self._history_lock:
            self._history = []
        self.app.load_model(choice)
        self.refresh_model_list()
        self.activity_logger.log_activity("model_change", {"model": choice})

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

    def _model_values(self):
        models = model_manager.get_model_list()
        return models if models else ["No models — go to Models tab"]

    def refresh_model_list(self):
        values = self._model_values()
        self.model_dd.configure(values=values)
        current = model_manager.get_current_model()
        if current and current in values:
            self.model_var.set(current)

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
        with self._history_lock:
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

        with self._history_lock:
            self._history.append({"role": "user", "content": message})

        self.memory.add_message("user", message)
        self.activity_logger.log_activity("query", {"message": message[:100]})

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
        self._trim_history()

        with self._history_lock:
            last_user_msg = self._history[-1]["content"] if self._history else ""

        relevant = self.memory.search_keyword(last_user_msg, limit=2)
        context_str = ""
        if relevant:
            context_str = "\n\nRelevant past conversation:\n"
            for item in relevant:
                context_str += f"{item['role'].capitalize()}: {item['content']}\n"
            with self._history_lock:
                self._history[-1]["content"] = last_user_msg + context_str

        specialist = self.decision_engine.route(last_user_msg)
        specialist_prompt = self.decision_engine.get_system_prompt(specialist)
        self.sys_message(f"Routing to {specialist} specialist")

        mode = self.mode_var.get()
        personality_prompt = self.MODE_PROMPTS.get(mode, self.MODE_PROMPTS["normal"])
        combined_system = f"{specialist_prompt}\n\n{personality_prompt}"
        improved_system = self.learner.improve_prompt(combined_system)

        with self._history_lock:
            full_history = [{"role": "system", "content": improved_system}] + self._history[:]

        try:
            response = model_manager.generate(full_history, stop_event=self._stop_event, on_token=self._append_token)
            if not self._stop_event.is_set():
                self._append(f"FreedomForge: {response}\n\n", "ai")
                with self._history_lock:
                    self._history.append({"role": "assistant", "content": response})
                self.memory.add_message("assistant", response)
                self.activity_logger.log_activity("response", {"length": len(response)})
        except Exception as e:
            self.error_message(f"{type(e).__name__}: {e}")
        finally:
            self._streaming = False
            self.stop_btn.pack_forget()
            self.send_btn.pack(fill="x", pady=(0, 4))
            self.set_status("idle")

    def _feedback_good(self):
        with self._history_lock:
            if len(self._history) >= 2 and self._history[-1]["role"] == "assistant":
                last_user = self._history[-2]["content"]
                last_ai = self._history[-1]["content"]
                self.learner.record_feedback(last_user, last_ai, is_good=True)
                self.sys_message("Thanks for the positive feedback!")
                self.activity_logger.log_activity("feedback", {"type": "good"})

    def _feedback_bad(self):
        with self._history_lock:
            if len(self._history) >= 2 and self._history[-1]["role"] == "assistant":
                last_user = self._history[-2]["content"]
                last_ai = self._history[-1]["content"]
                self.learner.record_feedback(last_user, last_ai, is_good=False)
                self.sys_message("Thanks for the feedback – I'll try to improve.")
                self.activity_logger.log_activity("feedback", {"type": "bad"})

    def _toggle_voice(self):
        if self.voice_enabled:
            try:
                voice_listener.stop_listening()
                self.voice_enabled = False
                self.mic_btn.configure(text="🎤 Voice OFF")
                self.sys_message("[Voice] Disabled")
                self.activity_logger.log_activity("voice_toggle", {"enabled": False})
            except Exception as e:
                self.error_message(f"Voice stop failed: {e}")
        else:
            try:
                voice_listener.start_listening(self._on_voice_command)
                self.voice_enabled = True
                self.mic_btn.configure(text="🎤 Voice ON")
                self.sys_message("[Voice] Enabled - say 'hey freedom' then your command")
                self.activity_logger.log_activity("voice_toggle", {"enabled": True})
            except Exception as e:
                self.error_message(f"Voice start failed: {e}")
                self.voice_enabled = False

    def _on_voice_command(self, command: str):
        with self._history_lock:
            self.input_box.delete("1.0", "end")
            self.input_box.insert("end", command)
            self.activity_logger.log_activity("voice_command", {"command": command})
        self.send()

    def _export(self):
        with self._history_lock:
            if not self._history:
                self.sys_message("Nothing to export.")
                return
            history_copy = self._history[:]

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"freedomforge_chat_{timestamp}.json"

        try:
            fd, temp_path = tempfile.mkstemp(suffix=".json")
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(history_copy, f, indent=2, ensure_ascii=False)
                os.replace(temp_path, filename)
                self.sys_message(f"Chat exported to {filename}")
                self.activity_logger.log_activity("export", {"filename": filename})
            except:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
        except Exception as e:
            self.error_message(f"Export failed: {e}")

    def _trim_history(self, max_exchanges=12):
        with self._history_lock:
            if len(self._history) > max_exchanges * 2:
                self._history = self._history[-max_exchanges*2:]

    MODE_PROMPTS = {
        "normal":   "You are a helpful, friendly assistant.",
        "concise":  "Answer in one short sentence when possible. Be direct.",
        "unhinged": "Be wild, chaotic, creative, and slightly unhinged.",
        "sexy":     "Be flirtatious, warm, and seductive in your replies.",
        "doctor":   "Speak calmly and professionally like a caring physician.",
        "focused":  "Stay strictly on topic. No tangents or extra chatter."
    }
