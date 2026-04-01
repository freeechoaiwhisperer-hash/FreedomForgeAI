# ============================================================
#  FreedomForge AI — ui/components/sidebar.py
#  Navigation sidebar widget
# ============================================================

# TODO: Extract sidebar navigation from ui/app_window.py

import customtkinter as ctk


class Sidebar(ctk.CTkFrame):
    """Left-side navigation panel."""

    def __init__(self, master, on_tab_change, theme: dict, **kwargs):
        super().__init__(master, **kwargs)
        self.on_tab_change = on_tab_change
        self.theme = theme
        # TODO: implement sidebar layout
