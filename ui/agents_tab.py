# ============================================================
#  FreedomForge AI — ui/agents_tab.py
#  Agents panel — configure and monitor agent mode
# ============================================================

import customtkinter as ctk
from core import config
import modules.agent as agent_module


class AgentsPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self.T   = theme
        self._build()

    # ── Build ─────────────────────────────────────────────────

    def _build(self):
        T = self.T

        # Header
        ctk.CTkLabel(
            self,
            text="🤖  Agents",
            font=("Arial", 20, "bold"),
            text_color=T["gold"],
        ).pack(anchor="w", padx=28, pady=(28, 4))

        ctk.CTkLabel(
            self,
            text="Configure and monitor AI agent mode.",
            font=("Arial", 13),
            text_color=T["text_dim"],
        ).pack(anchor="w", padx=28, pady=(0, 18))

        ctk.CTkFrame(self, height=1, fg_color=T["divider"]).pack(
            fill="x", padx=28, pady=(0, 18)
        )

        # Agent mode status
        card = ctk.CTkFrame(self, fg_color=T["bg_card"], corner_radius=10)
        card.pack(fill="x", padx=28, pady=(0, 14))

        ctk.CTkLabel(
            card,
            text="Agent Mode",
            font=("Arial", 14, "bold"),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=18, pady=(14, 4))

        status_text = "✅  Enabled" if agent_module.is_enabled() else "⛔  Disabled"
        self._status_lbl = ctk.CTkLabel(
            card,
            text=status_text,
            font=("Arial", 13),
            text_color=T["text_dim"],
        )
        self._status_lbl.pack(anchor="w", padx=18, pady=(0, 14))

        # Blocked commands info
        card2 = ctk.CTkFrame(self, fg_color=T["bg_card"], corner_radius=10)
        card2.pack(fill="x", padx=28, pady=(0, 14))

        ctk.CTkLabel(
            card2,
            text="Blocked Commands",
            font=("Arial", 14, "bold"),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=18, pady=(14, 4))

        ctk.CTkLabel(
            card2,
            text="\n".join(f"  • {cmd}" for cmd in agent_module.BLOCKED_COMMANDS),
            font=("Arial", 12),
            text_color=T["text_dim"],
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 14))

    def refresh(self):
        status_text = "✅  Enabled" if agent_module.is_enabled() else "⛔  Disabled"
        self._status_lbl.configure(text=status_text)
