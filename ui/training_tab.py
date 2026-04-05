# ============================================================
#  FreedomForge AI — ui/training_tab.py
#  Training panel — fixed model list refresh
# ============================================================

import customtkinter as ctk
from core import model_manager

class TrainingPanel(ctk.CTkFrame):
    def __init__(self, master, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.theme = theme
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        ctk.CTkLabel(
            self,
            text="🎓  Training",
            font=("Arial", 22, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(24, 4), padx=24, anchor="w")

        ctk.CTkLabel(
            self,
            text="Train or fine-tune your local models",
            font=("Arial", 13),
            text_color=T["text_secondary"],
        ).pack(padx=24, anchor="w", pady=(0, 16))

        # Model list - now refreshes properly
        models = model_manager.get_model_list()
        if not models:
            ctk.CTkLabel(
                self,
                text="No models found.\nGo to the Models tab and download one first.",
                font=("Arial", 13),
                text_color=T["text_dim"],
                justify="center",
            ).pack(pady=40, padx=24)
            return

        ctk.CTkLabel(
            self,
            text="Available models for training:",
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(0, 8), padx=24, anchor="w")

        for model in models:
            frame = ctk.CTkFrame(self, fg_color=T["bg_card"], corner_radius=8)
            frame.pack(fill="x", padx=24, pady=4)

            ctk.CTkLabel(
                frame,
                text=model,
                font=("Arial", 13),
                text_color=T["text_primary"],
            ).pack(side="left", padx=16, pady=12)

            ctk.CTkButton(
                frame,
                text="Train",
                width=80,
                height=32,
                corner_radius=6,
                fg_color=T["accent"],
                hover_color=T["accent_hover"],
                text_color="#ffffff",
                command=lambda m=model: self._start_training(m),
            ).pack(side="right", padx=16, pady=8)

        ctk.CTkLabel(
            self,
            text="Note: Training features coming soon.\nThis tab will support LoRA fine-tuning on your models.",
            font=("Arial", 11),
            text_color=T["text_dim"],
            justify="center",
        ).pack(pady=30, padx=24)

    def _start_training(self, model_name: str):
        # Placeholder - will be expanded later
        print(f"Starting training on {model_name} (placeholder)")
        # In final version this would launch the trainer with the model
