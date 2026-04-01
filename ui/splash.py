# ============================================================
#  FreedomForge AI — ui/splash.py
#  Splash screen — shown while app initializes
# ============================================================

import threading
import customtkinter as ctk
from assets.i18n import t

from utils.paths import APP_VERSION

WAND_FRAMES = [
    "🪄          ",
    "  ✨        ",
    "    ✨      ",
    "      ✨    ",
    "        ✨  ",
    "      ✨    ",
    "    ✨      ",
    "  ✨        ",
]


class SplashScreen(ctk.CTkToplevel):
    """
    Branded splash screen shown during startup.
    Calls on_ready() when initialization is complete.
    """

    def __init__(self, parent, on_ready):
        super().__init__(parent)
        self.on_ready    = on_ready
        self._wand_idx   = 0
        self._wand_alive = True

        # Window setup — no title bar, centered
        self.overrideredirect(True)
        self.geometry("480x320")
        self._center()
        self.lift()
        self.focus_force()

        # Background
        self.configure(fg_color="#080808")

        # Border frame for polish
        border = ctk.CTkFrame(self, fg_color="#1a1a1a",
                               corner_radius=16)
        border.pack(fill="both", expand=True, padx=2, pady=2)

        inner = ctk.CTkFrame(border, fg_color="#0c0c0c",
                              corner_radius=14)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Wand animation
        self.wand_lbl = ctk.CTkLabel(
            inner, text=WAND_FRAMES[0],
            font=("Arial", 40))
        self.wand_lbl.pack(pady=(40, 0))

        # App name
        ctk.CTkLabel(
            inner,
            text="FreedomForge AI",
            font=("Arial", 28, "bold"),
            text_color="#FFD700",
        ).pack(pady=(8, 0))

        ctk.CTkLabel(
            inner,
            text=t("app_tagline"),
            font=("Arial", 13),
            text_color="#444444",
        ).pack(pady=(2, 0))

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            inner, width=340, height=4,
            corner_radius=2,
            progress_color="#1a5a9a",
            fg_color="#1a1a1a",
        )
        self.progress.set(0)
        self.progress.pack(pady=(28, 0))

        # Status text
        self.status_lbl = ctk.CTkLabel(
            inner,
            text=t("splash_init"),
            font=("Arial", 11),
            text_color="#333333",
        )
        self.status_lbl.pack(pady=(8, 0))

        # Version
        ctk.CTkLabel(
            inner,
            text=f"v{APP_VERSION}",
            font=("Arial", 9),
            text_color="#1e1e1e",
        ).pack(side="bottom", pady=12)

        # Start animations
        self._animate_wand()
        self._run_init()

    def _center(self):
        self.update_idletasks()
        w, h = 480, 320
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _animate_wand(self):
        if not self._wand_alive:
            return
        try:
            self._wand_idx = (self._wand_idx + 1) % len(WAND_FRAMES)
            self.wand_lbl.configure(
                text=WAND_FRAMES[self._wand_idx])
            self.after(120, self._animate_wand)
        except Exception:
            pass

    def _set_status(self, text: str, progress: float):
        try:
            self.status_lbl.configure(text=text)
            self.progress.set(progress)
        except Exception:
            pass

    def _run_init(self):
        """Simulate initialization steps with progress."""
        steps = [
            (t("splash_init"),     0.15, 200),
            (t("splash_checking"), 0.45, 400),
            (t("splash_loading"),  0.75, 300),
            (t("splash_ready"),    1.00, 400),
        ]

        def _step(idx):
            if idx >= len(steps):
                self._wand_alive = False
                self.after(300, self._finish)
                return
            label, pct, delay = steps[idx]
            self._set_status(label, pct)
            self.after(delay, lambda: _step(idx + 1))

        self.after(300, lambda: _step(0))

    def _finish(self):
        try:
            self.destroy()
        except Exception:
            pass
        self.on_ready()
