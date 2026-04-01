# ============================================================
#  FreedomForge AI — ui/training_tab.py
#  Training Center — teach your models while you sleep
#  Stupidly simple. Grandma can use it.
# ============================================================

import threading
import customtkinter as ctk
from core import model_manager, logger
from core.trainer import get_idle_trainer, ModelTrainer
from utils.paths import MODELS_DIR


SKILLS = [
    ("💻  Coding",       "coding"),
    ("🧠  Reasoning",    "reasoning"),
    ("📋  Instructions", "instructions"),
    ("🎨  Creative",     "creative"),
    ("🔢  Math",         "math"),
]

INTENSITIES = [
    ("Light — barely uses resources",   "light"),
    ("Medium — balanced",               "medium"),
    ("Heavy — trains as fast as possible", "heavy"),
]


class TrainingPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app   = app
        self.theme = theme
        self._model_vars   = {}
        self._skill_vars   = {}
        self._intensity_var = ctk.StringVar(value="light")
        self._enabled_var   = ctk.BooleanVar(value=False)
        self._status_labels = {}
        self._build()
        self._refresh_stats()

    def apply_theme(self, theme: dict):
        self.theme = theme
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def refresh(self):
        """Rebuild the UI to reflect new models or updated progress."""
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Header ───────────────────────────────────────────
        ctk.CTkLabel(
            scroll,
            text="🎓  Training Center",
            font=("Arial", 22, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(24, 2), padx=24, anchor="w")

        ctk.CTkLabel(
            scroll,
            text="Your models get smarter while you sleep. Set it and forget it.",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(padx=24, anchor="w", pady=(0, 16))

        # ── Auto-train toggle ────────────────────────────────
        self._section(scroll, "⚡  Auto-Train While Idle")
        auto_card = self._card(scroll)

        auto_row = ctk.CTkFrame(auto_card, fg_color="transparent")
        auto_row.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(
            auto_row,
            text="When my computer is sitting unused, train my models automatically",
            font=("Arial", 13),
            text_color=T["text_primary"],
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkSwitch(
            auto_row,
            text="",
            variable=self._enabled_var,
            command=self._on_toggle,
            width=52, height=26,
            button_color=T["accent"],
            button_hover_color=T["accent_hover"],
        ).pack(side="right")

        # ── Model selection ──────────────────────────────────
        self._section(scroll, "📦  Which Models to Train")
        model_card = self._card(scroll)

        models = model_manager.get_model_list()
        if not models:
            ctk.CTkLabel(
                model_card,
                text="No models downloaded yet. Go to Models tab to download one.",
                font=("Arial", 12),
                text_color=T["text_secondary"],
            ).pack(padx=16, pady=14, anchor="w")
        else:
            trainer = get_idle_trainer()
            saved_models = trainer._models

            for model in models:
                row = ctk.CTkFrame(model_card, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=4)

                var = ctk.BooleanVar(value=model in saved_models)
                self._model_vars[model] = var

                ctk.CTkCheckBox(
                    row,
                    text=model,
                    variable=var,
                    command=self._save_settings,
                    font=("Arial", 12),
                    text_color=T["text_primary"],
                    fg_color=T["accent"],
                    hover_color=T["accent_hover"],
                ).pack(side="left")

                # Status label for this model
                status = ctk.CTkLabel(
                    row,
                    text="",
                    font=("Arial", 10),
                    text_color=T["text_secondary"],
                )
                status.pack(side="right", padx=8)
                self._status_labels[model] = status

            ctk.CTkFrame(
                model_card, height=1,
                fg_color=T["divider"],
            ).pack(fill="x", padx=16, pady=8)

            # Select all / none buttons
            btn_row = ctk.CTkFrame(model_card, fg_color="transparent")
            btn_row.pack(fill="x", padx=16, pady=(0, 12))

            ctk.CTkButton(
                btn_row, text="Select All",
                width=100, height=28,
                fg_color=T["bg_hover"],
                hover_color=T["bg_card"],
                text_color=T["text_secondary"],
                font=("Arial", 11),
                command=lambda: self._select_all(True),
            ).pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                btn_row, text="Select None",
                width=100, height=28,
                fg_color=T["bg_hover"],
                hover_color=T["bg_card"],
                text_color=T["text_secondary"],
                font=("Arial", 11),
                command=lambda: self._select_all(False),
            ).pack(side="left")

        # ── Skill selection ──────────────────────────────────
        self._section(scroll, "🎯  What to Improve")
        skill_card = self._card(scroll)

        ctk.CTkLabel(
            skill_card,
            text="Pick which skills to focus on during training:",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(padx=16, pady=(12, 6), anchor="w")

        trainer     = get_idle_trainer()
        saved_skills = trainer._skills

        for label, key in SKILLS:
            var = ctk.BooleanVar(value=key in saved_skills or not saved_skills)
            self._skill_vars[key] = var

            ctk.CTkCheckBox(
                skill_card,
                text=label,
                variable=var,
                command=self._save_settings,
                font=("Arial", 13),
                text_color=T["text_primary"],
                fg_color=T["accent"],
                hover_color=T["accent_hover"],
            ).pack(anchor="w", padx=20, pady=4)

        ctk.CTkFrame(
            skill_card, height=1,
            fg_color=T["divider"],
        ).pack(fill="x", padx=16, pady=8)

        # ── Intensity ────────────────────────────────────────
        self._section(scroll, "⚡  Training Intensity")
        int_card = self._card(scroll)

        for label, key in INTENSITIES:
            ctk.CTkRadioButton(
                int_card,
                text=label,
                variable=self._intensity_var,
                value=key,
                command=self._save_settings,
                font=("Arial", 12),
                text_color=T["text_primary"],
                fg_color=T["accent"],
                hover_color=T["accent_hover"],
            ).pack(anchor="w", padx=20, pady=6)

        ctk.CTkFrame(
            int_card, height=4,
            fg_color="transparent",
        ).pack()

        # ── Manual train now ─────────────────────────────────
        self._section(scroll, "▶  Train Now")
        now_card = self._card(scroll)

        ctk.CTkLabel(
            now_card,
            text="Don't want to wait? Start a training session right now.",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(padx=16, pady=(12, 6), anchor="w")

        btn_row2 = ctk.CTkFrame(now_card, fg_color="transparent")
        btn_row2.pack(fill="x", padx=16, pady=(0, 14))

        self._train_btn = ctk.CTkButton(
            btn_row2,
            text="▶  Start Training Session",
            width=220, height=42,
            font=("Arial", 13, "bold"),
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            command=self._train_now,
        )
        self._train_btn.pack(side="left")

        self._now_status = ctk.CTkLabel(
            btn_row2, text="",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        )
        self._now_status.pack(side="left", padx=16)

        # ── Progress overview ────────────────────────────────
        self._section(scroll, "📊  Progress")
        self._progress_card = self._card(scroll)
        self._build_progress()

        # Wire up idle trainer callbacks
        trainer = get_idle_trainer()
        trainer.set_progress_callback(self._on_progress)
        trainer.set_done_callback(self._on_done)

        # Load saved settings
        self._load_settings()

    def _build_progress(self):
        T = self.theme
        for w in self._progress_card.winfo_children():
            w.destroy()

        models  = model_manager.get_model_list()
        trainer = get_idle_trainer()
        stats   = trainer.get_stats()

        if not models:
            ctk.CTkLabel(
                self._progress_card,
                text="Download a model to see training progress.",
                font=("Arial", 12),
                text_color=T["text_secondary"],
            ).pack(padx=16, pady=14)
            return

        for model in models:
            info     = stats.get(model, {"examples": 0, "training": False})
            examples = info["examples"]
            training = info["training"]

            row = ctk.CTkFrame(
                self._progress_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)

            name_lbl = ctk.CTkLabel(
                row,
                text=model[:35],
                font=("Arial", 12),
                text_color=T["text_primary"],
                anchor="w",
                width=280,
            )
            name_lbl.pack(side="left")

            # Progress bar
            pct = min(examples / 1000, 1.0)
            bar = ctk.CTkProgressBar(
                row, width=160, height=8,
                progress_color=T["accent"],
                fg_color=T["bg_card"],
            )
            bar.set(pct)
            bar.pack(side="left", padx=8)

            status_text = f"Training..." if training else f"+{examples} examples"
            status_color = T["green"] if training else T["text_secondary"]

            ctk.CTkLabel(
                row,
                text=status_text,
                font=("Arial", 10),
                text_color=status_color,
                width=120,
            ).pack(side="left")

        ctk.CTkLabel(
            self._progress_card,
            text="1000+ examples = fully trained",
            font=("Arial", 10),
            text_color=T["text_dim"],
        ).pack(anchor="w", padx=16, pady=(4, 12))

    # ── Actions ──────────────────────────────────────────────

    def _on_toggle(self):
        self._save_settings()
        if self._enabled_var.get():
            get_idle_trainer().start()

    def _select_all(self, value: bool):
        for var in self._model_vars.values():
            var.set(value)
        self._save_settings()

    def _save_settings(self):
        selected_models = [m for m, v in self._model_vars.items() if v.get()]
        selected_skills = [s for s, v in self._skill_vars.items() if v.get()]
        intensity       = self._intensity_var.get()
        enabled         = self._enabled_var.get()

        get_idle_trainer().set_config(
            enabled=enabled,
            models=selected_models,
            skills=selected_skills,
            intensity=intensity,
        )

    def _load_settings(self):
        trainer = get_idle_trainer()
        self._enabled_var.set(trainer._enabled)
        self._intensity_var.set(trainer._intensity)
        # Start the trainer if it was enabled in the saved config
        if trainer._enabled:
            trainer.start()

    def _train_now(self):
        selected_models = [m for m, v in self._model_vars.items() if v.get()]
        selected_skills = [s for s, v in self._skill_vars.items() if v.get()]

        if not selected_models:
            self._now_status.configure(
                text="Select at least one model first.",
                text_color=self.theme["text_error"])
            return

        if not selected_skills:
            self._now_status.configure(
                text="Select at least one skill first.",
                text_color=self.theme["text_error"])
            return

        self._train_btn.configure(state="disabled", text="Training...")
        self._now_status.configure(
            text=f"Training {len(selected_models)} model(s)...",
            text_color=self.theme["text_secondary"])

        intensity = self._intensity_var.get()
        trainer   = get_idle_trainer()

        for model in selected_models:
            mt = trainer.get_trainer(model)
            mt.run_practice(
                skills=selected_skills,
                intensity=intensity,
                on_progress=self._on_progress,
                on_done=self._on_done,
            )

    def _on_progress(self, model_name: str, examples: int):
        """Called from training thread — use after() for UI safety."""
        def _update():
            if model_name in self._status_labels:
                self._status_labels[model_name].configure(
                    text=f"+{examples} examples",
                    text_color=self.theme["green"])
            self._build_progress()
        try:
            self.after(0, _update)
        except Exception:
            pass

    def _on_done(self, model_name: str, trained: int):
        """Called when a training session finishes."""
        def _update():
            self._train_btn.configure(
                state="normal", text="▶  Start Training Session")
            self._now_status.configure(
                text=f"Done! +{trained} examples learned.",
                text_color=self.theme["green"])
            self.after(4000, lambda: self._now_status.configure(text=""))
            self._build_progress()
        try:
            self.after(0, _update)
        except Exception:
            pass

    def _refresh_stats(self):
        """Refresh progress display every 10 seconds."""
        try:
            self._build_progress()
        except Exception:
            pass
        try:
            self.after(10000, self._refresh_stats)
        except Exception:
            pass

    # ── Helpers ──────────────────────────────────────────────

    def _section(self, parent, title: str):
        T = self.theme
        ctk.CTkLabel(
            parent, text=title,
            font=("Arial", 13, "bold"),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(16, 4))

    def _card(self, parent) -> ctk.CTkFrame:
        T    = self.theme
        card = ctk.CTkFrame(
            parent, corner_radius=12,
            fg_color=T["bg_card"])
        card.pack(fill="x", padx=20, pady=(0, 4))
        return card
