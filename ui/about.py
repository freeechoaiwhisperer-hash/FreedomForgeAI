# FreedomForge AI — ui/about.py
import customtkinter as ctk
from assets.i18n import t

from utils.paths import APP_VERSION

class AboutPanel(ctk.CTkFrame):
    def __init__(self, master, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.theme = theme
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        for w in self.winfo_children(): w.destroy()
        self._build()

    def _build(self):
        T = self.theme
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="⚒️", font=("Arial", 58)).pack(pady=(44,0))
        ctk.CTkLabel(scroll, text="FreedomForge AI", font=("Arial", 34, "bold"),
                     text_color=T["gold"]).pack(pady=(6,0))
        ctk.CTkLabel(scroll, text=f"{t('app_version')} {APP_VERSION}  —  {t('app_alpha')}",
                     font=("Arial", 13), text_color=T["text_dim"]).pack(pady=(2,0))

        self._divider(scroll)
        ctk.CTkLabel(scroll, text=t("about_mission"), font=("Arial", 14),
                     text_color=T["text_secondary"], justify="center",
                     wraplength=700).pack(pady=10, padx=50)

        self._divider(scroll)
        ctk.CTkLabel(scroll, text=t("about_miranda"), font=("Arial", 20, "bold"),
                     text_color=T["purple"]).pack(pady=(4,8))
        ctk.CTkLabel(scroll, text=t("about_miranda_body"), font=("Arial", 14, "italic"),
                     text_color="#665577", justify="center",
                     wraplength=600).pack(pady=4, padx=70)

        self._divider(scroll)
        ctk.CTkLabel(scroll, text=t("about_note"), font=("Arial", 15, "bold"),
                     text_color=T["text_secondary"]).pack(pady=(4,8))
        ctk.CTkLabel(scroll, text=t("about_note_body"), font=("Arial", 13),
                     text_color=T["text_dim"], justify="center",
                     wraplength=700).pack(pady=4, padx=60)

        self._divider(scroll)
        ctk.CTkLabel(scroll, text=t("about_built_with"), font=("Arial", 13, "bold"),
                     text_color=T["text_secondary"]).pack(pady=(4,8))

        credits = [
            ("CustomTkinter",        "Modern UI — Tom Schimansky"),
            ("llama-cpp-python",     "AI engine — Andrei Betlen"),
            ("SpeechRecognition",    "Voice input — Anthony Zhang"),
            ("pyttsx3",              "Voice output — Natesh M Bhat"),
            ("psutil",               "System monitoring — Giampaolo Rodola"),
            ("HuggingFace",          "Model hosting — Hugging Face Inc."),
            ("TheBloke / bartowski", "GGUF model conversions"),
        ]
        frame = ctk.CTkFrame(scroll, fg_color="transparent")
        frame.pack(pady=4)
        for name, credit in credits:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(pady=2)
            ctk.CTkLabel(row, text=name, font=("Arial", 12, "bold"),
                         text_color=T["text_secondary"], width=200, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"— {credit}", font=("Arial", 12),
                         text_color=T["text_dim"], anchor="w").pack(side="left", padx=4)

        self._divider(scroll)
        ctk.CTkLabel(scroll, text=t("about_credit"), font=("Arial", 13, "bold"),
                     text_color=T["purple"], justify="center").pack(pady=(4,48))

    def _divider(self, parent):
        ctk.CTkFrame(parent, height=1,
                     fg_color=self.theme["divider"]).pack(fill="x", padx=70, pady=18)
