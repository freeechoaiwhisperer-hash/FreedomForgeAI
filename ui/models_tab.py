# ============================================================
#  FreedomForge AI — ui/models_tab.py
#  Model browser — curated list + live HuggingFace search
# ============================================================

import os
import queue
import shutil
import threading
from tkinter import filedialog

import customtkinter as ctk
import requests

from core import model_manager
from assets.i18n import t

from utils.paths import MODELS_DIR as _MODELS_DIR_PATH
MODELS_DIR = str(_MODELS_DIR_PATH)

CURATED = [
    {
        "name":     "TinyLlama 1.1B",
        "badge":    "⚡ Best for low-end PCs",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size": "670 MB", "ram": "2 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Tiny but surprisingly capable. Runs on almost anything. Perfect starting point.",
    },
    {
        "name":     "Phi-2 2.7B",
        "badge":    "🧠 Smart and compact",
        "filename": "phi-2.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
        "size": "1.6 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "coding", "chat"],
        "desc": "Microsoft's compact powerhouse. Excellent at reasoning, coding, and writing.",
    },
    {
        "name":     "Llama 3.2 3B",
        "badge":    "🦙 Latest from Meta",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size": "2.0 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Meta's latest compact model. Fast, capable, and fully open source.",
    },
    {
        "name":     "Mistral 7B Instruct",
        "badge":    "⚖️ Best all-rounder",
        "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "The gold standard for local AI. Excellent at everything.",
    },
    {
        "name":     "Dolphin Mistral 7B",
        "badge":    "🐬 Uncensored",
        "filename": "dolphin-2.2.1-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/dolphin-2.2.1-mistral-7B-GGUF/resolve/main/dolphin-2.2.1-mistral-7b.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["uncensored", "chat", "large"],
        "desc": "Mistral fine-tuned to never refuse. Loyal, direct, completely open.",
    },
    {
        "name":     "Dolphin Llama 3 8B",
        "badge":    "🐬 Uncensored + Powerful",
        "filename": "dolphin-2.9-llama3-8b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/dolphin-2.9-llama3-8b-GGUF/resolve/main/dolphin-2.9-llama3-8b-Q4_K_M.gguf",
        "size": "4.9 GB", "ram": "10 GB+",
        "tags": ["uncensored", "chat", "large"],
        "desc": "Dolphin on Llama 3. Powerful, uncensored, deeply loyal.",
    },
    {
        "name":     "Llama 3.1 8B Instruct",
        "badge":    "🦙 Most powerful",
        "filename": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "size": "4.9 GB", "ram": "10 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "Meta's flagship open source model. State of the art.",
    },
    {
        "name":     "CodeLlama 7B",
        "badge":    "💻 Coding specialist",
        "filename": "codellama-7b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf",
        "size": "3.8 GB", "ram": "8 GB+",
        "tags": ["coding", "large"],
        "desc": "Fine-tuned specifically for code. Write, debug, and explain in any language.",
    },
    {
        "name":     "DeepSeek Coder 6.7B",
        "badge":    "💻 Best code model",
        "filename": "deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF/resolve/main/deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
        "size": "3.8 GB", "ram": "8 GB+",
        "tags": ["coding", "large"],
        "desc": "DeepSeek's dedicated coding model. Exceptional at writing and reviewing code.",
    },
    {
        "name":     "Gemma 2 2B",
        "badge":    "🔵 Google",
        "filename": "gemma-2-2b-it-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf",
        "size": "1.6 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Google's compact instruction model. Clean, fast, and capable.",
    },
    {
        "name":     "Qwen2.5 7B",
        "badge":    "🌏 Multilingual",
        "filename": "qwen2.5-7b-instruct-q4_k_m.gguf",
        "url":      "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "size": "4.7 GB", "ram": "8 GB+",
        "tags": ["multilingual", "chat", "large"],
        "desc": "Alibaba's multilingual powerhouse. English, Chinese, and many others.",
    },
    {
        "name":     "OpenHermes 2.5 Mistral",
        "badge":    "🧙 Smart assistant",
        "filename": "openhermes-2.5-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/resolve/main/openhermes-2.5-mistral-7b.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "Mistral fine-tuned on high quality instructions. Sharp and reliable.",
    },
    {
        "name":     "Mixtral 8x7B",
        "badge":    "🚀 Mixture of experts",
        "filename": "mixtral-8x7b-instruct-v0.1.Q3_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF/resolve/main/mixtral-8x7b-instruct-v0.1.Q3_K_M.gguf",
        "size": "19 GB", "ram": "24 GB+",
        "tags": ["popular", "large", "chat"],
        "desc": "Mistral's mixture-of-experts. GPT-4 level. Needs a powerful machine.",
    },
    {
        "name":     "Llava 1.6 Mistral 7B",
        "badge":    "👁️ Can see images",
        "filename": "llava-v1.6-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/cjpais/llava-1.6-mistral-7b-gguf/resolve/main/llava-v1.6-mistral-7b.Q4_K_M.gguf",
        "size": "4.4 GB", "ram": "8 GB+",
        "tags": ["vision", "large"],
        "desc": "Multimodal — can see and describe images. Show it a photo and ask questions.",
    },
]

def _ram_gb(ram_str: str) -> int:
    """Parse '8 GB+' → 8."""
    try:
        return int(ram_str.split()[0])
    except Exception:
        return 0

SMALL  = [m for m in CURATED if _ram_gb(m["ram"]) <= 4]
MEDIUM = [m for m in CURATED if 4 < _ram_gb(m["ram"]) <= 12]
LARGE  = [m for m in CURATED if _ram_gb(m["ram"]) > 12]


class ModelsPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app            = app
        self.theme          = theme
        self._ollama_models = []
        self._hf_loading    = False
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        self._rebuild()

    def _rebuild(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        # ── Header ───────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=56)
        hdr.pack(fill="x", padx=22, pady=(20, 0))
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="📦  Model Library",
            font=("Arial", 22, "bold"),
            text_color=T["text_primary"],
        ).pack(side="left", anchor="w")

        ctk.CTkLabel(
            hdr, text="Download once — runs 100% on your machine",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(side="left", padx=16, anchor="w")

        ctk.CTkButton(
            hdr, text="↻  Refresh",
            width=90, height=30,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            command=self._rebuild,
        ).pack(side="right", padx=4)

        # ── Scrollable model list ────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=12, pady=(10, 0))

        # ── Bottom search bar ────────────────────────────────
        bot = ctk.CTkFrame(self, fg_color=T["bg_topbar"], height=54)
        bot.pack(fill="x", pady=(4, 0))
        bot.pack_propagate(False)

        self._search_var = ctk.StringVar()
        self._search_entry = ctk.CTkEntry(
            bot,
            textvariable=self._search_var,
            placeholder_text="Find more models…",
            font=("Arial", 12), height=36,
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_color=T["border"],
            placeholder_text_color=T["text_secondary"],
        )
        self._search_entry.pack(
            side="left", fill="both", expand=True, padx=(16, 6), pady=9)
        self._search_entry.bind("<Return>", lambda _: self._do_search())

        ctk.CTkButton(
            bot, text="Search",
            width=90, height=36, corner_radius=8,
            fg_color=T["accent"], hover_color=T["accent_hover"],
            command=self._do_search,
        ).pack(side="left", padx=(0, 6), pady=9)

        ctk.CTkButton(
            bot, text="📁 Local File",
            width=114, height=36, corner_radius=8,
            fg_color=T["bg_card"], hover_color=T["bg_hover"],
            text_color=T["text_secondary"],
            command=self._add_local,
        ).pack(side="left", padx=(0, 16), pady=9)

        # Populate and auto-detect Ollama
        self._populate_list()
        threading.Thread(target=self._ollama_probe, daemon=True).start()

    # ── Populate list ────────────────────────────────────────

    def _populate_list(self, ollama_models=None):
        """Fill scroll with models grouped by size; optionally prepend Ollama models."""
        T = self.theme
        for w in self._scroll.winfo_children():
            w.destroy()

        # Installed models (Ollama) — no backend branding shown to user
        if ollama_models:
            self._section_header("✅  Available Now")
            for m in ollama_models:
                self._ollama_row(m)
            ctk.CTkFrame(
                self._scroll, height=2, fg_color=T["border"]
            ).pack(fill="x", pady=8, padx=4)

        # ── Small ──
        self._section_header("⚡  Small — Runs on anything  (2–4 GB RAM)")
        for m in SMALL:
            self._model_row(m)

        # ── Medium ──
        ctk.CTkFrame(
            self._scroll, height=2, fg_color=T["border"]
        ).pack(fill="x", pady=(10, 4), padx=4)
        self._section_header("⚖️  Medium — 8 GB RAM recommended")
        for m in MEDIUM:
            self._model_row(m)

        # ── Large ──
        ctk.CTkFrame(
            self._scroll, height=2, fg_color=T["border"]
        ).pack(fill="x", pady=(10, 4), padx=4)
        self._section_header("🚀  Large — 16 GB+ recommended")
        for m in LARGE:
            self._model_row(m)

    def _section_header(self, text: str):
        T = self.theme
        ctk.CTkLabel(
            self._scroll, text=text,
            font=("Arial", 13, "bold"),
            text_color=T["text_secondary"],
            anchor="w",
        ).pack(anchor="w", padx=10, pady=(10, 4))

    # ── Ollama auto-detection ────────────────────────────────

    def _ollama_probe(self):
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            r.raise_for_status()
            models = r.json().get("models", [])
            if models:
                self._ollama_models = models
                self.after(0, lambda: self._populate_list(models))
        except Exception:
            pass  # Ollama not running — that's fine

    def _ollama_row(self, m: dict):
        T      = self.theme
        name   = m.get("name", "unknown")
        size_b = m.get("size", 0)
        size_s = f"{size_b / (1024**3):.1f} GB" if size_b else ""
        family = m.get("details", {}).get("family", "")
        params = m.get("details", {}).get("parameter_size", "")
        loaded = (model_manager.get_current_model() == name)

        row = ctk.CTkFrame(self._scroll, corner_radius=10, fg_color=T["bg_card"])
        row.pack(fill="x", pady=3, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        ctk.CTkLabel(
            info, text=name,
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"], anchor="w",
        ).pack(anchor="w")

        detail = "  •  ".join(x for x in [family, params, size_s] if x) or "Installed"
        ctk.CTkLabel(
            info, text=detail,
            font=("Arial", 11),
            text_color=T["text_secondary"], anchor="w",
        ).pack(anchor="w")

        if loaded:
            ctk.CTkLabel(
                row, text="▶ Running",
                font=("Arial", 12, "bold"),
                text_color=T["gold"],
            ).pack(side="right", padx=12, pady=10)
        else:
            ctk.CTkButton(
                row, text="▶ Load",
                width=90, height=34, corner_radius=8,
                fg_color=T["accent"], hover_color=T["accent_hover"],
                text_color="#ffffff",
                command=lambda n=name: self._load_ollama(n),
            ).pack(side="right", padx=12, pady=10)

    def _load_ollama(self, name: str):
        try:
            self.app.chat_panel.sys_message(f"▶  Loading {name}…")
        except Exception:
            pass
        self.app.load_model(name)
        self.app.switch_panel("Chat")

    # ── Curated model row ────────────────────────────────────

    def _model_row(self, m: dict):
        T      = self.theme
        have   = os.path.exists(os.path.join(MODELS_DIR, m["filename"]))
        loaded = (model_manager.get_current_model() == m["filename"])

        row = ctk.CTkFrame(self._scroll, corner_radius=12, fg_color=T["bg_card"])
        row.pack(fill="x", pady=4, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        # Title row
        tr = ctk.CTkFrame(info, fg_color="transparent")
        tr.pack(anchor="w", fill="x")

        ctk.CTkLabel(
            tr, text=m["name"],
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"], anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            tr, text=f"  {m['badge']}",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(side="left")

        if loaded:
            ctk.CTkLabel(tr, text="  ▶ Active",
                         font=("Arial", 11, "bold"),
                         text_color=T["gold"]).pack(side="left")
        elif have:
            ctk.CTkLabel(tr, text="  ✅ Downloaded",
                         font=("Arial", 11),
                         text_color=T["green"]).pack(side="left")

        ctk.CTkLabel(
            info, text=m["desc"],
            font=("Arial", 11),
            text_color=T["text_secondary"],
            anchor="w", wraplength=560, justify="left",
        ).pack(anchor="w", pady=(2, 0))

        meta = ctk.CTkFrame(info, fg_color="transparent")
        meta.pack(anchor="w", pady=(5, 0))

        for label, val in [("Size", m["size"]), ("RAM", m["ram"])]:
            ctk.CTkLabel(
                meta, text=f"{label}: {val}",
                font=("Arial", 10),
                text_color=T["text_dim"],
                fg_color=T["bg_hover"],
                corner_radius=4, width=110,
            ).pack(side="left", padx=(0, 6))

        # Action button
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=124)
        btn_frame.pack(side="right", padx=12, pady=12)
        btn_frame.pack_propagate(False)

        if loaded:
            ctk.CTkLabel(
                btn_frame, text="▶ Running",
                font=("Arial", 12, "bold"),
                text_color=T["gold"],
            ).pack(expand=True)
        elif have:
            ctk.CTkButton(
                btn_frame, text="▶ Load",
                height=36, corner_radius=8,
                fg_color="#1a4a1a", hover_color="#0d2e0d",
                text_color="#ffffff",
                command=lambda fn=m["filename"]: self._load(fn),
            ).pack(fill="x", pady=(0, 4))
            ctk.CTkButton(
                btn_frame, text="🗑 Delete",
                height=22, corner_radius=6,
                fg_color="#2a1212", hover_color="#3a1a1a",
                text_color=T["text_secondary"],
                font=("Arial", 10),
                command=lambda fn=m["filename"]: self._delete(fn),
            ).pack(fill="x")
        else:
            ctk.CTkButton(
                btn_frame, text="⬇ Download",
                height=36, corner_radius=8,
                fg_color=T["accent"], hover_color=T["accent_hover"],
                text_color="#ffffff",
                command=lambda mo=m: self._download(mo),
            ).pack(fill="x")

    # ── Search (find more via HuggingFace) ───────────────────

    def _do_search(self):
        query = self._search_var.get().strip()
        if not query or self._hf_loading:
            return
        self._hf_loading = True
        T = self.theme

        for w in self._scroll.winfo_children():
            w.destroy()

        ctk.CTkButton(
            self._scroll, text="← Back to catalog",
            width=140, height=28,
            fg_color=T["bg_hover"], hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            font=("Arial", 11), anchor="w",
            command=self._back_to_catalog,
        ).pack(anchor="w", pady=(4, 8))

        status = ctk.CTkLabel(
            self._scroll,
            text=f"🔍  Searching for \"{query}\"…",
            font=("Arial", 13),
            text_color=T["text_secondary"],
        )
        status.pack(pady=40)

        def _search():
            try:
                url = (
                    f"https://huggingface.co/api/models"
                    f"?search={query}&filter=gguf"
                    f"&sort=downloads&limit=20&full=false"
                )
                r = requests.get(url, timeout=12)
                r.raise_for_status()
                results = r.json()
                self.after(0, lambda: self._render_search(results, query, status))
            except Exception as e:
                self.after(0, lambda: status.configure(
                    text=f"❌  Search failed: {e}\nCheck your connection.",
                    text_color=T.get("text_error", "#ff4444")))
            finally:
                self._hf_loading = False

        threading.Thread(target=_search, daemon=True).start()

    def _render_search(self, results: list, query: str, status):
        T = self.theme
        try:
            status.destroy()
        except Exception:
            pass

        if not results:
            ctk.CTkLabel(
                self._scroll,
                text=f"No GGUF models found for \"{query}\".",
                font=("Arial", 13),
                text_color=T["text_secondary"],
            ).pack(pady=20)
            return

        ctk.CTkLabel(
            self._scroll,
            text=f"{len(results)} models found — click View Files to download",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))

        for model in results:
            self._search_result_row(model)

    def _search_result_row(self, model: dict):
        T         = self.theme
        model_id  = model.get("modelId", model.get("id", "Unknown"))
        downloads = model.get("downloads", 0)

        row = ctk.CTkFrame(self._scroll, corner_radius=10, fg_color=T["bg_card"])
        row.pack(fill="x", pady=4, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        ctk.CTkLabel(
            info, text=model_id,
            font=("Arial", 13, "bold"),
            text_color=T["text_primary"], anchor="w",
        ).pack(anchor="w")

        if downloads:
            ctk.CTkLabel(
                info, text=f"⬇ {downloads:,} downloads",
                font=("Arial", 10),
                text_color=T["text_secondary"],
            ).pack(anchor="w")

        ctk.CTkButton(
            row, text="View Files",
            width=100, height=32, corner_radius=8,
            fg_color=T["accent"], hover_color=T["accent_hover"],
            text_color="#ffffff",
            command=lambda mid=model_id: self._show_files(mid),
        ).pack(side="right", padx=12, pady=10)

    def _back_to_catalog(self):
        self._populate_list(self._ollama_models or None)

    # ── HuggingFace file browser ─────────────────────────────

    def _show_files(self, model_id: str):
        T   = self.theme
        win = ctk.CTkToplevel(self)
        win.title(model_id)
        win.geometry("720x520")
        win.configure(fg_color=T["bg_panel"])
        # No grab_set — preserves main window WM decorations on Linux

        def _on_close():
            win.destroy()
            try:
                self.winfo_toplevel().focus_force()
            except Exception:
                pass

        win.protocol("WM_DELETE_WINDOW", _on_close)

        ctk.CTkLabel(
            win, text=model_id,
            font=("Arial", 15, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(18, 2), padx=22, anchor="w")

        ctk.CTkLabel(
            win, text=t("models_select_dl"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(padx=22, anchor="w")

        status = ctk.CTkLabel(
            win, text=t("models_loading_files"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        )
        status.pack(pady=20)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        def _fetch():
            try:
                r    = requests.get(
                    f"https://huggingface.co/api/models/{model_id}",
                    timeout=12)
                r.raise_for_status()
                data  = r.json()
                files = [
                    s for s in data.get("siblings", [])
                    if s.get("rfilename", "").endswith(".gguf")
                ]
                win.after(0, lambda: _show(files))
            except Exception as e:
                win.after(0, lambda: status.configure(
                    text=f"❌  {e}",
                    text_color=T.get("text_error", "#ff4444")))

        def _show(files: list):
            try:
                status.destroy()
            except Exception:
                pass

            if not files:
                ctk.CTkLabel(
                    scroll, text=t("models_no_files"),
                    text_color=T["text_secondary"],
                ).pack(pady=20)
                return

            for f in files:
                fname    = f.get("rfilename", "")
                size_b   = f.get("size", 0)
                size_str = (
                    f"{size_b/(1024**3):.1f} GB"
                    if size_b > 1024**3
                    else f"{size_b/(1024**2):.0f} MB"
                    if size_b else "?"
                )
                frow = ctk.CTkFrame(scroll, corner_radius=8, fg_color=T["bg_card"])
                frow.pack(fill="x", pady=4, padx=2)

                fi = ctk.CTkFrame(frow, fg_color="transparent")
                fi.pack(side="left", fill="both", expand=True, padx=12, pady=8)

                ctk.CTkLabel(
                    fi, text=fname,
                    font=("Arial", 12, "bold"),
                    text_color=T["text_primary"], anchor="w",
                ).pack(anchor="w")
                ctk.CTkLabel(
                    fi, text=size_str,
                    font=("Arial", 10),
                    text_color=T["text_secondary"], anchor="w",
                ).pack(anchor="w")

                dl_url = (
                    f"https://huggingface.co/{model_id}"
                    f"/resolve/main/{fname}"
                )
                have = os.path.exists(os.path.join(MODELS_DIR, fname))

                if have:
                    ctk.CTkLabel(
                        frow, text=t("models_downloaded"),
                        font=("Arial", 11),
                        text_color=T["green"],
                    ).pack(side="right", padx=12, pady=10)
                else:
                    ctk.CTkButton(
                        frow, text=t("models_download"),
                        width=116, height=32, corner_radius=8,
                        fg_color=T["accent"], hover_color=T["accent_hover"],
                        text_color="#ffffff",
                        command=lambda u=dl_url, fn=fname: (
                            _on_close(),
                            self._download({
                                "name":     fn,
                                "filename": fn,
                                "url":      u,
                                "size":     size_str,
                                "ram":      "?",
                                "desc":     f"From {model_id}",
                            })
                        ),
                    ).pack(side="right", padx=12, pady=8)

        threading.Thread(target=_fetch, daemon=True).start()

    # ── Actions ──────────────────────────────────────────────

    def _load(self, filename: str):
        self.app.load_model(filename)
        self.app.switch_panel("Chat")

    def _delete(self, filename: str):
        path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(path):
            os.remove(path)
        self.refresh()

    def _download(self, model: dict):
        DownloadWindow(self, model, self.theme, self.refresh)

    def _add_local(self):
        path = filedialog.askopenfilename(
            title=t("models_select_file"),
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")])
        if path:
            os.makedirs(MODELS_DIR, exist_ok=True)
            dest = os.path.join(MODELS_DIR, os.path.basename(path))
            shutil.copy2(path, dest)
            self.refresh()
            try:
                self.app.chat_panel.sys_message(
                    f"✅  {t('models_added')} {os.path.basename(path)}")
            except Exception:
                pass

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()


# ── Download window ──────────────────────────────────────────

class DownloadWindow(ctk.CTkToplevel):

    def __init__(self, parent, model: dict,
                 theme: dict, on_done=None):
        super().__init__(parent)
        self.on_done = on_done
        self._q      = queue.Queue()
        T            = theme

        self.title("Downloading")
        self.geometry("540x210")
        self.resizable(False, False)
        self.configure(fg_color=T["bg_panel"])
        # No grab_set — download window is non-modal; parent keeps WM decorations

        ctk.CTkLabel(
            self,
            text=f"⬇  {model.get('name', model['filename'])}",
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(22, 4))

        self.bar = ctk.CTkProgressBar(
            self, width=480,
            progress_color=T["accent"],
            fg_color=T["bg_card"],
        )
        self.bar.set(0)
        self.bar.pack(pady=8)

        self.lbl = ctk.CTkLabel(
            self,
            text=t("models_connecting"),
            font=("Arial", 11),
            text_color=T["text_secondary"],
        )
        self.lbl.pack()

        ctk.CTkLabel(
            self,
            text=t("models_minimize"),
            font=("Arial", 10),
            text_color=T["text_dim"],
        ).pack(pady=4)

        threading.Thread(
            target=self._dl, args=(model,), daemon=True).start()
        self._poll()

    def _dl(self, model: dict):
        try:
            os.makedirs(MODELS_DIR, exist_ok=True)
            r     = requests.get(
                model["url"], stream=True, timeout=60)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done  = 0
            dest  = os.path.join(MODELS_DIR, model["filename"])
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        self._q.put(("p", done / total, done, total))
            self._q.put(("done", None))
        except Exception as e:
            self._q.put(("error", str(e)))

    def _poll(self):
        try:
            while True:
                msg = self._q.get_nowait()
                if msg[0] == "p":
                    _, pct, done, total = msg
                    self.bar.set(pct)
                    self.lbl.configure(
                        text=f"{done/(1024**2):.1f} MB / "
                             f"{total/(1024**2):.1f} MB  "
                             f"({pct*100:.1f}%)"
                    )
                elif msg[0] == "done":
                    self.bar.set(1.0)
                    self.lbl.configure(text=t("models_complete"))
                    self.after(1400, self._finish)
                    return
                elif msg[0] == "error":
                    self.lbl.configure(text=f"❌  {msg[1]}")
                    return
        except queue.Empty:
            pass
        self.after(110, self._poll)

    def _finish(self):
        if self.on_done:
            self.on_done()
        try:
            self.destroy()
        except Exception:
            pass
