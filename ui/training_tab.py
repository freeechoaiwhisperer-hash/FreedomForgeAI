# ============================================================
#  FreedomForge AI — ui/training_tab.py
#  Training Center — teach your models while you sleep
#  Stupidly simple. Grandma can use it.
# ============================================================

import os
import queue
import subprocess
import sys
import threading
import customtkinter as ctk
from core import model_manager, logger
from core.trainer import get_idle_trainer, ModelTrainer
from utils.paths import MODELS_DIR

try:
    import peft        # noqa: F401
    import transformers  # noqa: F401
    PEFT_AVAILABLE = True
except Exception:
    PEFT_AVAILABLE = False


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

        # ── Advanced Training (LoRA) ─────────────────────────
        self._section(scroll, "🧬  Advanced Training (LoRA)")
        self._lora_card = self._card(scroll)
        self._build_lora_section()

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

    # ── LoRA section ─────────────────────────────────────────

    def _build_lora_section(self):
        T = self.theme
        for w in self._lora_card.winfo_children():
            w.destroy()

        if not PEFT_AVAILABLE:
            self._build_lora_unavailable()
        else:
            self._build_lora_ui()

    def _build_lora_unavailable(self):
        T = self.theme

        ctk.CTkLabel(
            self._lora_card,
            text="Advanced training requires extra packages.  (~2 GB download)",
            font=("Arial", 12),
            text_color=T["text_secondary"],
            anchor="w",
        ).pack(padx=16, pady=(14, 4), anchor="w")

        ctk.CTkLabel(
            self._lora_card,
            text="Installs: transformers  peft  datasets  accelerate",
            font=("Arial", 11),
            text_color=T["text_dim"],
            anchor="w",
        ).pack(padx=16, anchor="w")

        btn_row = ctk.CTkFrame(self._lora_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(10, 14))

        self._install_btn = ctk.CTkButton(
            btn_row,
            text="⬇  Install",
            width=120, height=36, corner_radius=8,
            font=("Arial", 13, "bold"),
            fg_color=T["accent"], hover_color=T["accent_hover"],
            command=self._install_lora_deps,
        )
        self._install_btn.pack(side="left")

        self._install_status = ctk.CTkLabel(
            btn_row, text="",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        )
        self._install_status.pack(side="left", padx=12)

    def _install_lora_deps(self):
        T = self.theme
        self._install_btn.configure(state="disabled", text="Installing…")
        self._install_status.configure(text="This may take a few minutes…")

        def _run():
            pkgs = ["transformers", "peft", "datasets", "accelerate"]
            cmd  = [sys.executable, "-m", "pip", "install"] + pkgs
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=600)
                if proc.returncode == 0:
                    self.after(0, self._on_install_done)
                else:
                    err = (proc.stderr or proc.stdout or "unknown error")[-200:]
                    self.after(0, lambda: self._on_install_error(err))
            except Exception as e:
                self.after(0, lambda: self._on_install_error(str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_install_done(self):
        global PEFT_AVAILABLE
        try:
            import peft        # noqa: F401
            import transformers  # noqa: F401
            PEFT_AVAILABLE = True
        except Exception:
            pass
        self._build_lora_section()

    def _on_install_error(self, err: str):
        try:
            self._install_btn.configure(state="normal", text="↻  Retry")
            self._install_status.configure(
                text=f"❌ Install failed: {err}",
                text_color=self.theme.get("red", "#ff4444"))
        except Exception:
            pass

    def _build_lora_ui(self):
        T = self.theme

        # ── Training examples ────────────────────────────────
        ctk.CTkLabel(
            self._lora_card,
            text="Training Examples",
            font=("Arial", 12, "bold"),
            text_color=T["text_primary"],
            anchor="w",
        ).pack(padx=16, pady=(14, 2), anchor="w")

        ctk.CTkLabel(
            self._lora_card,
            text="One example per line.  Format:  input|output",
            font=("Arial", 10),
            text_color=T["text_dim"],
            anchor="w",
        ).pack(padx=16, anchor="w")

        self._lora_examples = ctk.CTkTextbox(
            self._lora_card,
            height=120,
            font=("Arial", 12),
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_color=T["border"],
            border_width=1,
            wrap="word",
        )
        self._lora_examples.pack(fill="x", padx=16, pady=(6, 0))
        self._lora_examples.insert(
            "1.0",
            "What is 2+2?|The answer is 4.\n"
            "Translate to French: Hello|Bonjour\n")

        # ── Adapter name ─────────────────────────────────────
        name_row = ctk.CTkFrame(self._lora_card, fg_color="transparent")
        name_row.pack(fill="x", padx=16, pady=(10, 0))

        ctk.CTkLabel(
            name_row, text="Adapter Name:",
            font=("Arial", 12),
            text_color=T["text_primary"],
            width=120, anchor="w",
        ).pack(side="left")

        self._lora_name = ctk.CTkEntry(
            name_row,
            placeholder_text="my-custom-adapter",
            font=("Arial", 12), height=34,
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_color=T["border"],
        )
        self._lora_name.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # ── Start button + progress bar ───────────────────────
        ctrl_row = ctk.CTkFrame(self._lora_card, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=16, pady=(10, 0))

        self._lora_start_btn = ctk.CTkButton(
            ctrl_row,
            text="▶  Start Training",
            width=160, height=38, corner_radius=8,
            font=("Arial", 13, "bold"),
            fg_color=T["accent"], hover_color=T["accent_hover"],
            command=self._lora_start,
        )
        self._lora_start_btn.pack(side="left")

        self._lora_stop_btn = ctk.CTkButton(
            ctrl_row,
            text="⏹ Stop",
            width=80, height=38, corner_radius=8,
            font=("Arial", 12),
            fg_color="#3a1212", hover_color="#5a1a1a",
            text_color=T["text_secondary"],
            state="disabled",
            command=self._lora_stop,
        )
        self._lora_stop_btn.pack(side="left", padx=(8, 0))

        self._lora_status = ctk.CTkLabel(
            ctrl_row, text="",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        )
        self._lora_status.pack(side="left", padx=12)

        self._lora_bar = ctk.CTkProgressBar(
            self._lora_card, height=8,
            progress_color=T["accent"],
            fg_color=T["bg_hover"],
        )
        self._lora_bar.set(0)
        self._lora_bar.pack(fill="x", padx=16, pady=(8, 0))

        # ── Log output ────────────────────────────────────────
        ctk.CTkLabel(
            self._lora_card,
            text="Training Log",
            font=("Arial", 11, "bold"),
            text_color=T["text_secondary"],
            anchor="w",
        ).pack(padx=16, pady=(10, 2), anchor="w")

        self._lora_log = ctk.CTkTextbox(
            self._lora_card,
            height=130,
            font=("Courier", 10),
            fg_color=T["bg_deep"],
            text_color=T["text_secondary"],
            border_color=T["border"],
            border_width=1,
            state="disabled",
            wrap="word",
        )
        self._lora_log.pack(fill="x", padx=16, pady=(0, 14))

        self._lora_q      = queue.Queue()
        self._lora_thread = None

    # ── LoRA training logic ───────────────────────────────────

    def _lora_log_append(self, text: str):
        try:
            self._lora_log.configure(state="normal")
            self._lora_log.insert("end", text + "\n")
            self._lora_log.see("end")
            self._lora_log.configure(state="disabled")
        except Exception:
            pass

    def _lora_start(self):
        T = self.theme

        raw = self._lora_examples.get("1.0", "end").strip()
        if not raw:
            self._lora_status.configure(
                text="⚠ Add at least one training example.",
                text_color=T.get("yellow", "#ffcc00"))
            return

        examples = [
            line.split("|", 1)
            for line in raw.splitlines()
            if "|" in line
        ]
        if not examples:
            self._lora_status.configure(
                text="⚠ Format: input|output  (one per line)",
                text_color=T.get("yellow", "#ffcc00"))
            return

        adapter_name = self._lora_name.get().strip() or "my-adapter"
        model        = model_manager.get_current_model()

        self._lora_start_btn.configure(state="disabled", text="Training…")
        self._lora_stop_btn.configure(state="normal")
        self._lora_status.configure(
            text="Starting…", text_color=T["text_secondary"])
        self._lora_bar.set(0)

        try:
            self._lora_log.configure(state="normal")
            self._lora_log.delete("1.0", "end")
            self._lora_log.configure(state="disabled")
        except Exception:
            pass

        self._lora_running = True
        self._lora_thread  = threading.Thread(
            target=self._lora_worker,
            args=(examples, adapter_name, model),
            daemon=True)
        self._lora_thread.start()
        self.after(150, self._lora_poll)

    def _lora_stop(self):
        self._lora_running = False

    def _lora_worker(self, examples, adapter_name, model_name):
        q = self._lora_q
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
            from peft import get_peft_model, LoraConfig, TaskType
            from datasets import Dataset

            q.put(("log", "Loading tokenizer…"))
            model_path = str(MODELS_DIR / model_name) if hasattr(MODELS_DIR, "__truediv__") else os.path.join(str(MODELS_DIR), model_name)

            # Use a small base for LoRA if GGUF (quantized) — explain limitation
            if model_name.endswith(".gguf"):
                q.put(("log", "⚠ GGUF models can't be LoRA fine-tuned directly."))
                q.put(("log", "  Use a HuggingFace model ID instead (e.g. microsoft/phi-2)."))
                q.put(("log", "  Falling back to tiny demo model: sshleifer/tiny-gpt2"))
                hf_model = "sshleifer/tiny-gpt2"
            else:
                hf_model = model_name

            tokenizer = AutoTokenizer.from_pretrained(hf_model)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            q.put(("log", f"Loading base model: {hf_model}"))
            q.put(("progress", 0.1))
            base = AutoModelForCausalLM.from_pretrained(
                hf_model,
                torch_dtype=torch.float32,
            )

            lora_cfg = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=8, lora_alpha=16,
                target_modules=["q_proj", "v_proj"],
                lora_dropout=0.05,
                bias="none",
            )
            peft_model = get_peft_model(base, lora_cfg)
            q.put(("log", f"LoRA adapter attached. Trainable params: "
                          f"{sum(p.numel() for p in peft_model.parameters() if p.requires_grad):,}"))
            q.put(("progress", 0.2))

            # Build dataset
            texts = [f"{inp}\n{out}" for inp, out in examples]
            enc   = tokenizer(texts, truncation=True, padding=True,
                              max_length=128, return_tensors="pt")
            enc["labels"] = enc["input_ids"].clone()
            ds = Dataset.from_dict({k: v.tolist() for k, v in enc.items()})
            q.put(("log", f"Dataset ready: {len(ds)} example(s)"))
            q.put(("progress", 0.3))

            out_dir = os.path.join(os.path.expanduser("~"), ".freedomforge",
                                   "lora_adapters", adapter_name)
            os.makedirs(out_dir, exist_ok=True)

            args = TrainingArguments(
                output_dir=out_dir,
                num_train_epochs=3,
                per_device_train_batch_size=1,
                logging_steps=1,
                save_steps=999999,
                no_cuda=not torch.cuda.is_available(),
                report_to="none",
            )

            total_steps = max(len(ds) * args.num_train_epochs, 1)

            class _LogCb:
                def __init__(self, q, total, running_ref):
                    self.q = q; self.total = total; self.step = 0
                    self.running_ref = running_ref
                def on_log(self, a, state, control, logs=None, **kw):
                    if logs:
                        loss = logs.get("loss", "")
                        lr   = logs.get("learning_rate", "")
                        self.q.put(("log", f"  step {state.global_step}  loss={loss}  lr={lr}"))
                        self.step = state.global_step
                        pct = 0.3 + 0.65 * min(self.step / self.total, 1.0)
                        self.q.put(("progress", pct))
                    if not self.running_ref[0]:
                        control.should_training_stop = True

            running = [True]
            def _stop_check():
                running[0] = self._lora_running

            from transformers import TrainerCallback
            class _StopCb(TrainerCallback):
                def on_step_end(self, a, state, control, **kw):
                    _stop_check()
                    if not running[0]:
                        control.should_training_stop = True
                    return control

            log_cb  = _LogCb(q, total_steps, running)
            stop_cb = _StopCb()

            trainer_obj = Trainer(
                model=peft_model,
                args=args,
                train_dataset=ds,
                callbacks=[stop_cb],
            )
            # Monkey-patch log callback
            trainer_obj.add_callback(type("LC", (), {"on_log": log_cb.on_log})())

            q.put(("log", "Training started…"))
            trainer_obj.train()

            if self._lora_running:
                peft_model.save_pretrained(out_dir)
                q.put(("log", f"✅ Adapter saved → {out_dir}"))
                q.put(("progress", 1.0))
                q.put(("done", f"Done! Adapter saved to {out_dir}"))
            else:
                q.put(("log", "⏹ Training stopped by user."))
                q.put(("done", "Stopped."))

        except Exception as e:
            q.put(("log", f"❌ Error: {e}"))
            q.put(("done", f"Failed: {e}"))

    def _lora_poll(self):
        T = self.theme
        try:
            while True:
                msg = self._lora_q.get_nowait()
                if msg[0] == "log":
                    self._lora_log_append(msg[1])
                elif msg[0] == "progress":
                    self._lora_bar.set(msg[1])
                    self._lora_status.configure(
                        text=f"{int(msg[1]*100)}%",
                        text_color=T["text_secondary"])
                elif msg[0] == "done":
                    self._lora_start_btn.configure(
                        state="normal", text="▶  Start Training")
                    self._lora_stop_btn.configure(state="disabled")
                    self._lora_status.configure(
                        text=msg[1],
                        text_color=T["green"] if "Done" in msg[1] else T.get("red","#ff4444"))
                    return
        except queue.Empty:
            pass
        if getattr(self, "_lora_running", False):
            self.after(200, self._lora_poll)

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
