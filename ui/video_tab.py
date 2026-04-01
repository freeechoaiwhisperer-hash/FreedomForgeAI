# ============================================================
#  FreedomForge AI — ui/video_tab.py
#  Video generation panel — install, status, generate
# ============================================================

import threading
import customtkinter as ctk
from core import config
from utils.paths import APP_ROOT


class VideoPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app   = app
        self.T     = theme
        self._build()
        self._refresh_status()

    # ── Build ─────────────────────────────────────────────────

    def _build(self):
        T = self.T

        # Header
        ctk.CTkLabel(
            self,
            text="🎬  Video Generation",
            font=("Arial", 20, "bold"),
            text_color=T["gold"],
        ).pack(pady=(24, 4), padx=24, anchor="w")

        ctk.CTkLabel(
            self,
            text="Generate AI videos locally using ComfyUI + LTX-Video.",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(padx=24, anchor="w")

        ctk.CTkFrame(self, height=1, fg_color=T["divider"]).pack(
            fill="x", padx=24, pady=12)

        # Status card
        status_card = ctk.CTkFrame(self, fg_color=T["bg_card"], corner_radius=10)
        status_card.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(
            status_card,
            text="Status",
            font=("Arial", 12, "bold"),
            text_color=T["text_dim"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self._install_lbl = ctk.CTkLabel(
            status_card,
            text="Checking…",
            font=("Arial", 13),
            text_color=T["text_primary"],
        )
        self._install_lbl.pack(anchor="w", padx=16)

        self._comfy_lbl = ctk.CTkLabel(
            status_card,
            text="",
            font=("Arial", 13),
            text_color=T["text_primary"],
        )
        self._comfy_lbl.pack(anchor="w", padx=16, pady=(2, 12))

        # Install row
        install_row = ctk.CTkFrame(self, fg_color="transparent")
        install_row.pack(fill="x", padx=24, pady=(0, 12))

        self._install_btn = ctk.CTkButton(
            install_row,
            text="⬇  Install Video Module",
            width=220, height=40,
            corner_radius=20,
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            font=("Arial", 13, "bold"),
            command=self._start_install,
        )
        self._install_btn.pack(side="left")

        ctk.CTkButton(
            install_row,
            text="↺  Refresh Status",
            width=140, height=40,
            corner_radius=20,
            fg_color=T["bg_hover"],
            hover_color=T["bg_panel"],
            text_color=T["text_secondary"],
            font=("Arial", 12),
            command=self._refresh_status,
        ).pack(side="left", padx=10)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=T["divider"]).pack(
            fill="x", padx=24, pady=12)

        # Generate section
        ctk.CTkLabel(
            self,
            text="Generate a Video",
            font=("Arial", 15, "bold"),
            text_color=T["text_primary"],
        ).pack(anchor="w", padx=24, pady=(0, 6))

        ctk.CTkLabel(
            self,
            text="Describe the video you want — be specific about action, style, and lighting.",
            font=("Arial", 12),
            text_color=T["text_secondary"],
            wraplength=700,
        ).pack(anchor="w", padx=24)

        self._prompt_box = ctk.CTkTextbox(
            self,
            height=80,
            font=("Arial", 13),
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_color=T["border"],
            border_width=1,
            wrap="word",
        )
        self._prompt_box.pack(fill="x", padx=24, pady=10)
        self._prompt_box.insert("1.0",
            "A golden retriever running through a sunlit forest in slow motion, "
            "cinematic, 4K, shallow depth of field")

        neg_row = ctk.CTkFrame(self, fg_color="transparent")
        neg_row.pack(fill="x", padx=24, pady=(0, 10))

        ctk.CTkLabel(
            neg_row, text="Negative:",
            font=("Arial", 11),
            text_color=T["text_dim"],
        ).pack(side="left", padx=(0, 6))

        self._neg_box = ctk.CTkEntry(
            neg_row,
            placeholder_text="blurry, low quality, distorted…",
            font=("Arial", 12),
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_color=T["border"],
        )
        self._neg_box.pack(side="left", fill="x", expand=True)

        self._gen_btn = ctk.CTkButton(
            self,
            text="🎬  Generate Video",
            width=200, height=44,
            corner_radius=22,
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            font=("Arial", 14, "bold"),
            command=self._generate,
        )
        self._gen_btn.pack(pady=12)

        # Progress / output log
        ctk.CTkFrame(self, height=1, fg_color=T["divider"]).pack(
            fill="x", padx=24, pady=8)

        ctk.CTkLabel(
            self,
            text="Output",
            font=("Arial", 12, "bold"),
            text_color=T["text_dim"],
        ).pack(anchor="w", padx=24)

        self._log = ctk.CTkTextbox(
            self,
            height=160,
            font=("Courier", 11),
            fg_color=T["bg_deep"],
            text_color=T["text_secondary"],
            state="disabled",
        )
        self._log.pack(fill="both", expand=True, padx=24, pady=(4, 24))

    # ── Status ─────────────────────────────────────────────────

    def _refresh_status(self):
        installed = config.get("video_enabled", False)
        comfy_dir = config.get("comfy_dir", str(APP_ROOT / "ComfyUI"))

        if installed:
            self._install_lbl.configure(
                text="✅  Video module installed",
                text_color=self.T["green"],
            )
            self._install_btn.configure(
                text="⬇  Re-install / Update",
                fg_color=self.T["bg_hover"],
                text_color=self.T["text_secondary"],
            )
        else:
            self._install_lbl.configure(
                text="⚠️  Video module not installed",
                text_color=self.T["yellow"],
            )
            self._install_btn.configure(
                text="⬇  Install Video Module",
                fg_color=self.T["accent"],
                text_color="#ffffff",
            )

        # Check ComfyUI live status in background
        def _check():
            try:
                from modules.comfy_client import get_client
                running = get_client(comfy_dir).is_running()
            except Exception:
                running = False
            self.after(0, lambda: self._comfy_lbl.configure(
                text=(
                    "🟢  ComfyUI is running"
                    if running else
                    "🔴  ComfyUI not running (will auto-start on generate)"
                ),
                text_color=self.T["green"] if running else self.T["text_dim"],
            ))

        threading.Thread(target=_check, daemon=True).start()

    # ── Install ────────────────────────────────────────────────

    def _start_install(self):
        self._install_btn.configure(state="disabled", text="Installing…")
        self._log_clear()
        self._log_append("🎬 Starting installation…\n")

        from modules.video_installer import VideoInstaller

        def _on_status(msg):
            self.after(0, lambda m=msg: self._log_append(m + "\n"))

        def _on_complete(ok, msg):
            def _done():
                self._log_append(f"\n{'✅' if ok else '❌'} {msg}\n")
                self._install_btn.configure(state="normal")
                self._refresh_status()
                if ok:
                    self._log_append(
                        "\n⚡ Video module ready! Try generating a video below.\n"
                    )
            self.after(0, _done)

        VideoInstaller(on_status=_on_status, on_complete=_on_complete).run()

    # ── Generate ───────────────────────────────────────────────

    def _generate(self):
        if not config.get("video_enabled", False):
            self._log_append(
                "⚠️ Video module not installed. Click 'Install Video Module' above.\n"
            )
            return

        prompt = self._prompt_box.get("1.0", "end").strip()
        if not prompt:
            self._log_append("⚠️ Please enter a prompt first.\n")
            return

        negative = self._neg_box.get().strip()

        self._gen_btn.configure(state="disabled", text="Generating…")
        self._log_clear()
        self._log_append(f"Prompt: {prompt}\n\n")

        from modules.comfy_client import get_client
        client = get_client()

        def _on_status(msg):
            self.after(0, lambda m=msg: self._log_append(m + "\n"))

        def _on_complete(files):
            def _done():
                self._gen_btn.configure(state="normal", text="🎬  Generate Video")
                if files:
                    self._log_append("\n✅ Video generation complete!\n\n")
                    for f in files:
                        self._log_append(f"📹 {f}\n")
                else:
                    self._log_append("\n⚠️ No output files found. Check ComfyUI.\n")
            self.after(0, _done)

        def _on_error(msg):
            self.after(0, lambda m=msg: (
                self._log_append(f"\n❌ {m}\n"),
                self._gen_btn.configure(state="normal", text="🎬  Generate Video"),
            ))

        client.generate(
            prompt=prompt,
            negative_prompt=negative or "blurry, low quality, distorted, watermark",
            on_status=_on_status,
            on_complete=_on_complete,
            on_error=_on_error,
        )

    # ── Log helpers ────────────────────────────────────────────

    def _log_clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _log_append(self, text: str):
        self._log.configure(state="normal")
        self._log.insert("end", text)
        self._log.see("end")
        self._log.configure(state="disabled")
