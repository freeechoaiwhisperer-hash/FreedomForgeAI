# ============================================================
#  FreedomForge AI — ui/components/message_bubble.py
#  Chat message bubble widget
# ============================================================

# TODO: Extract message bubble rendering from ui/chat.py

import customtkinter as ctk


class MessageBubble(ctk.CTkFrame):
    """A single chat message bubble (user or assistant)."""

    def __init__(self, master, role: str, content: str, theme: dict, **kwargs):
        super().__init__(master, **kwargs)
        self.role = role
        self.content = content
        self.theme = theme
        # TODO: implement bubble layout
