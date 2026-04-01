"""
Mousewheel scroll fix for customtkinter on Linux/Windows/macOS.

CTkScrollableFrame on Linux uses Button-4/Button-5 (X11 scroll events)
but child widgets don't bubble these up to the scrollable canvas.
This module patches scroll events globally so every CTkScrollableFrame
in the app responds to the mouse wheel no matter what's under the cursor.
"""
import sys
import customtkinter as ctk


def _get_scroll_parent(widget):
    """Walk up the widget tree to find the nearest CTkScrollableFrame."""
    w = widget
    while w is not None:
        if isinstance(w, ctk.CTkScrollableFrame):
            return w
        try:
            w = w.master
        except Exception:
            break
    return None


def _scroll_canvas(frame: ctk.CTkScrollableFrame, delta: int):
    """Scroll the internal canvas of a CTkScrollableFrame."""
    try:
        # CTkScrollableFrame stores its canvas as _parent_canvas
        canvas = frame._parent_canvas
        canvas.yview_scroll(delta, "units")
    except Exception:
        pass


def _bind_widget(widget, root):
    """Recursively bind scroll events to a widget and all its children."""
    if sys.platform.startswith("linux"):
        widget.bind("<Button-4>",
                    lambda e: _on_scroll_linux(e, -1), add="+")
        widget.bind("<Button-5>",
                    lambda e: _on_scroll_linux(e, 1), add="+")
    else:
        widget.bind("<MouseWheel>",
                    lambda e: _on_scroll_win_mac(e), add="+")

    for child in widget.winfo_children():
        try:
            _bind_widget(child, root)
        except Exception:
            pass


def _on_scroll_linux(event, direction):
    frame = _get_scroll_parent(event.widget)
    if frame:
        _scroll_canvas(frame, direction)


def _on_scroll_win_mac(event):
    frame = _get_scroll_parent(event.widget)
    if frame:
        delta = -1 if event.delta > 0 else 1
        _scroll_canvas(frame, delta)


def enable_mousewheel_scroll(root: ctk.CTk):
    """
    Call once after building the UI.
    Binds scroll events on all current AND future CTkScrollableFrame widgets.
    Also patches CTkScrollableFrame.__init__ so newly created ones are
    automatically covered.
    """
    # Bind on everything already built
    _bind_widget(root, root)

    # Patch CTkScrollableFrame so future instances auto-register
    _orig_init = ctk.CTkScrollableFrame.__init__

    def _patched_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        # Bind after a short delay so children have time to be added
        try:
            self.after(100, lambda: _bind_widget(self, root))
        except Exception:
            pass

    ctk.CTkScrollableFrame.__init__ = _patched_init
