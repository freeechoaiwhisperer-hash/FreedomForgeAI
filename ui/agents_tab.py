# ============================================================
#  FreedomForge AI — ui/agents_tab.py
#  Agents panel — run shell commands via the agent module
# ============================================================

import os
import datetime
import threading

import customtkinter as ctk

from modules import agent as agent_module


class AgentsPanel(ctk.CTkFrame):
    def __init__(self, master, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.theme = theme
        self._log: list[str] = []
        self._log_lock = threading.Lock()
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        # ── Top bar ──────────────────────────────────────────
        bar = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=T["bg_topbar"])
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(
            bar,
            text="🤖  Agent Console",
            font=("Arial", 15, "bold"),
            text_color=T["text_primary"],
        ).pack(side="left", padx=16)

        ctk.CTkButton(
            bar,
            text="Export",
            width=72,
            height=30,
            corner_radius=6,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            font=("Arial", 11),
            command=self._export,
        ).pack(side="right", padx=(0, 4))

        ctk.CTkButton(
            bar,
            text="Clear",
            width=72,
            height=30,
            corner_radius=6,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            font=("Arial", 11),
            command=self._clear,
        ).pack(side="right", padx=(0, 4))

        # ── Conversation log ─────────────────────────────────
        self.log_box = ctk.CTkTextbox(
            self,
            wrap="word",
            state="disabled",
            font=("Arial", 13),
            fg_color=T["bg_deep"],
            text_color=T["text_primary"],
            scrollbar_button_color=T["bg_card"],
            scrollbar_button_hover_color=T["bg_hover"],
        )
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        self.log_box.tag_config("you",   foreground=T["text_you"])
        self.log_box.tag_config("agent", foreground=T["text_ai"])
        self.log_box.tag_config("error", foreground=T["text_error"])
        self.log_box.tag_config("sys",   foreground=T["text_sys"])

        # ── Input row ────────────────────────────────────────
        inp = ctk.CTkFrame(self, height=58, fg_color="transparent")
        inp.pack(fill="x", padx=10, pady=8)
        inp.pack_propagate(False)

        self.input_box = ctk.CTkEntry(
            inp,
            placeholder_text="Enter command… (e.g. ls -la)",
            font=("Arial", 13),
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_color=T["border"],
            border_width=1,
        )
        self.input_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.input_box.bind("<Return>", lambda _e: self._run())

        ctk.CTkButton(
            inp,
            text="Run",
            width=80,
            height=40,
            corner_radius=8,
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            text_color="#ffffff",
            font=("Arial", 13, "bold"),
            command=self._run,
        ).pack(side="right")

        self._append("sys", "[Agent Console] Ready. Type a command and press Run.\n")

    # ── Helpers ──────────────────────────────────────────────

    def _append(self, tag: str, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text, tag)
        self.log_box.configure(state="disabled")
        self.log_box.see("end")
        with self._log_lock:
            self._log.append(text)

    def _run(self):
        command = self.input_box.get().strip()
        if not command:
            return
        self.input_box.delete(0, "end")
        self._append("you", f"$ {command}\n")

        def on_result(output: str):
            self.after(0, lambda: self._append("agent", output + "\n"))

        def on_error(msg: str):
            self.after(0, lambda: self._append("error", f"[Error] {msg}\n"))

        agent_module.run_command(command, on_result, on_error)

    def _clear(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        with self._log_lock:
            self._log.clear()

    def _export(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads, exist_ok=True)
        path = os.path.join(downloads, f"agents_{timestamp}.txt")

        with self._log_lock:
            content = "".join(self._log)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self._append("sys", f"[Export] Saved to {path}\n")
        except Exception as exc:
            self._append("error", f"[Export] Failed: {exc}\n")
