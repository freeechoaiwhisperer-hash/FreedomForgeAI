# ============================================================
#  FreedomForge AI — ui/components/toolbar.py
#  Top toolbar widget
# ============================================================

# TODO: Implement top toolbar with model selector and controls

import customtkinter as ctk


class Toolbar(ctk.CTkFrame):
    """Top application toolbar."""

    def __init__(self, master, theme: dict, **kwargs):
        super().__init__(master, **kwargs)
        self.theme = theme
        # TODO: implement toolbar layout
