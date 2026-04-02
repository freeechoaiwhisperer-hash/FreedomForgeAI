# ============================================================
#  FreedomForge AI — training/trainer.py
#  LocalTrainer: LoRA fine-tuning via PEFT + HuggingFace
# ============================================================

from __future__ import annotations

import gc
import os
import queue
import threading
from pathlib import Path
from typing import Callable, List, Optional, Tuple

ADAPTERS_DIR    = Path.home() / ".freedomforge" / "lora_adapters"
LOCAL_ADAPTERS  = Path(__file__).parent / "adapters"   # training/adapters/


class LocalTrainer:
    """
    Runs LoRA fine-tuning in the calling thread (launch via threading.Thread).

    Parameters
    ----------
    examples     : list of (instruction, output) string pairs
    adapter_name : name for the saved adapter folder
    model_id     : HuggingFace model ID or local path.
                   GGUF paths are detected and rejected gracefully.
    progress_q   : queue.Queue for progress messages sent back to the UI
                   Message tuples: ("log", str) | ("progress", float 0-1) | ("done", str)
    stop_event   : threading.Event — set it to request an early stop
    epochs       : number of training epochs (default 3)
    max_length   : tokenizer max sequence length (default 128)
    lora_r       : LoRA rank (default 8)
    lora_alpha   : LoRA alpha (default 16)
    """

    def __init__(
        self,
        examples: List[Tuple[str, str]],
        adapter_name: str,
        model_id: str,
        progress_q: queue.Queue,
        stop_event: threading.Event,
        *,
        epochs: int = 3,
        max_length: int = 128,
        lora_r: int = 8,
        lora_alpha: int = 16,
    ):
        self.examples     = examples
        self.adapter_name = adapter_name.strip() or "my-adapter"
        self.model_id     = model_id
        self.q            = progress_q
        self.stop         = stop_event
        self.epochs       = epochs
        self.max_length   = max_length
        self.lora_r       = lora_r
        self.lora_alpha   = lora_alpha

        self._model     = None
        self._tokenizer = None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start training. Call from a daemon thread."""
        try:
            self._train()
        except Exception as exc:
            self._log(f"❌ Error: {exc}")
            self._done(f"Failed: {exc}")
        finally:
            self._cleanup()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, text: str) -> None:
        self.q.put(("log", text))

    def _progress(self, pct: float) -> None:
        self.q.put(("progress", max(0.0, min(1.0, pct))))

    def _done(self, text: str) -> None:
        self.q.put(("done", text))

    def _stopped(self) -> bool:
        return self.stop.is_set()

    # ------------------------------------------------------------------
    # Core training logic
    # ------------------------------------------------------------------

    def _train(self) -> None:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            Trainer,
            TrainerCallback,
            TrainerControl,
            TrainerState,
            TrainingArguments,
        )

        # ── 1. Resolve model ──────────────────────────────────
        model_id = self.model_id or ""
        if model_id.lower().endswith(".gguf"):
            self._log("⚠ GGUF models cannot be LoRA fine-tuned directly.")
            self._log("  Enter a HuggingFace model ID instead (e.g. microsoft/phi-2).")
            self._log("  Using sshleifer/tiny-gpt2 as a demo run.")
            model_id = "sshleifer/tiny-gpt2"

        self._log(f"Loading tokenizer: {model_id}")
        self._progress(0.05)

        self._tokenizer = AutoTokenizer.from_pretrained(model_id)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        if self._stopped():
            self._log("⏹ Stopped before model load.")
            self._done("Stopped.")
            return

        # ── 2. Load base model ────────────────────────────────
        self._log(f"Loading base model…")
        self._progress(0.10)
        use_gpu = torch.cuda.is_available()
        self._model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if use_gpu else torch.float32,
            device_map="auto" if use_gpu else None,
            low_cpu_mem_usage=True,
        )
        self._log(f"  Device: {'GPU' if use_gpu else 'CPU'}")
        self._progress(0.20)

        # ── 3. Attach LoRA adapter ────────────────────────────
        lora_cfg = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=self.lora_r,
            lora_alpha=self.lora_alpha,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
        )
        peft_model = get_peft_model(self._model, lora_cfg)
        trainable  = sum(p.numel() for p in peft_model.parameters() if p.requires_grad)
        total      = sum(p.numel() for p in peft_model.parameters())
        self._log(f"LoRA attached — trainable: {trainable:,} / {total:,} params "
                  f"({100*trainable/max(total,1):.2f}%)")
        self._progress(0.25)

        if self._stopped():
            self._log("⏹ Stopped before training.")
            self._done("Stopped.")
            return

        # ── 4. Build dataset ──────────────────────────────────
        self._log(f"Preparing dataset ({len(self.examples)} examples)…")
        texts = [
            f"Instruction: {inp.strip()}\nOutput: {out.strip()}"
            for inp, out in self.examples
            if inp.strip() and out.strip()
        ]
        if not texts:
            self._log("❌ No valid examples found after filtering.")
            self._done("Failed: empty dataset.")
            return

        enc = self._tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        enc["labels"] = enc["input_ids"].clone()
        dataset = Dataset.from_dict({k: v.tolist() for k, v in enc.items()})
        self._log(f"  {len(dataset)} token-encoded row(s), max_length={self.max_length}")
        self._progress(0.30)

        # ── 5. Output directory ───────────────────────────────
        out_dir = str(ADAPTERS_DIR / self.adapter_name)
        os.makedirs(out_dir, exist_ok=True)

        # ── 6. Training arguments ─────────────────────────────
        total_steps = max(len(dataset) * self.epochs, 1)
        train_args  = TrainingArguments(
            output_dir=out_dir,
            num_train_epochs=self.epochs,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=1,
            learning_rate=2e-4,
            warmup_steps=max(1, total_steps // 10),
            logging_steps=1,
            save_steps=999_999,           # don't auto-save checkpoints
            no_cuda=not use_gpu,
            report_to="none",
            disable_tqdm=True,
        )

        # ── 7. Callbacks ──────────────────────────────────────
        trainer_ref   = [None]
        stop_ref      = self.stop
        q_ref         = self.q

        class _ProgressCallback(TrainerCallback):
            def on_log(
                self,
                args: TrainingArguments,
                state: TrainerState,
                control: TrainerControl,
                logs=None,
                **kwargs,
            ):
                if logs:
                    step = state.global_step
                    loss = logs.get("loss", "—")
                    lr   = logs.get("learning_rate", "—")
                    q_ref.put(("log", f"  step {step}  loss={loss}  lr={lr}"))
                    pct = 0.30 + 0.65 * min(step / total_steps, 1.0)
                    q_ref.put(("progress", pct))

            def on_step_end(
                self,
                args: TrainingArguments,
                state: TrainerState,
                control: TrainerControl,
                **kwargs,
            ):
                if stop_ref.is_set():
                    control.should_training_stop = True
                return control

        # ── 8. Run Trainer ────────────────────────────────────
        trainer = Trainer(
            model=peft_model,
            args=train_args,
            train_dataset=dataset,
            callbacks=[_ProgressCallback()],
        )
        trainer_ref[0] = trainer

        self._log("Training started…")
        trainer.train()

        # ── 9. Save or report stop ────────────────────────────
        if self._stopped():
            self._log("⏹ Training stopped by user.")
            self._done("Stopped.")
            return

        self._progress(0.97)
        self._log("Saving adapter weights…")
        peft_model.save_pretrained(out_dir)
        self._log(f"✅ Adapter saved → {out_dir}")
        self._progress(1.0)
        self._done(f"Done! Adapter saved to:\n{out_dir}")

    # ------------------------------------------------------------------
    # Memory cleanup
    # ------------------------------------------------------------------

    def _cleanup(self) -> None:
        """Release model/tokenizer from memory and free GPU cache."""
        try:
            if self._model is not None:
                del self._model
                self._model = None
            if self._tokenizer is not None:
                del self._tokenizer
                self._tokenizer = None
        except Exception:
            pass

        gc.collect()

        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass


# ==============================================================
#  Module-level helpers (no training required)
# ==============================================================

def get_available_adapters() -> List[Path]:
    """
    Return a sorted list of adapter directories found in:
      1. training/adapters/   (project-local, version-controlled)
      2. ~/.freedomforge/lora_adapters/  (user-trained adapters)

    A directory is considered a valid adapter if it contains
    an ``adapter_config.json`` file (PEFT convention).
    """
    dirs: List[Path] = []
    for base in (LOCAL_ADAPTERS, ADAPTERS_DIR):
        if base.exists():
            for p in sorted(base.iterdir()):
                if p.is_dir() and (p / "adapter_config.json").exists():
                    dirs.append(p)
    return dirs


def load_adapter(model, adapter_path: str | Path):
    """
    Load a LoRA adapter onto *model* using ``peft.PeftModel.from_pretrained``.

    Parameters
    ----------
    model        : a HuggingFace ``PreTrainedModel`` already loaded in memory
    adapter_path : path to the saved adapter directory

    Returns
    -------
    The PEFT-wrapped model with the adapter loaded, or the original *model*
    unchanged if PEFT is not installed or loading fails.
    """
    try:
        from peft import PeftModel
    except ImportError:
        print(
            "[FreedomForge] Warning: 'peft' is not installed. "
            "Cannot load LoRA adapter. Run: pip install peft"
        )
        return model

    adapter_path = Path(adapter_path)
    if not adapter_path.exists():
        print(f"[FreedomForge] Warning: adapter path not found: {adapter_path}")
        return model

    try:
        peft_model = PeftModel.from_pretrained(model, str(adapter_path))
        print(f"[FreedomForge] LoRA adapter loaded from: {adapter_path}")
        return peft_model
    except Exception as exc:
        print(f"[FreedomForge] Failed to load adapter '{adapter_path}': {exc}")
        return model
