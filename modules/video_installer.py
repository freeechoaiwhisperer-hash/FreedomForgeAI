# ============================================================
#  FreedomForge AI — modules/video_installer.py
#  Downloads and configures ComfyUI + video models
# ============================================================

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile
from pathlib import Path
from typing import Callable

from utils.paths import APP_ROOT

# ── Download targets ──────────────────────────────────────────────────────────

COMFY_ZIP_URL = (
    "https://github.com/comfyanonymous/ComfyUI/archive/refs/heads/master.zip"
)

CUSTOM_NODE_URLS = {
    "ComfyUI-LTXVideo": (
        "https://github.com/Lightricks/ComfyUI-LTXVideo"
        "/archive/refs/heads/main.zip"
    ),
    "ComfyUI-VideoHelperSuite": (
        "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite"
        "/archive/refs/heads/main.zip"
    ),
}

# Models ordered by VRAM requirement (smallest first as fallback)
MODEL_OPTIONS = [
    {
        "id":       "ltx_quant",
        "label":    "LTX-Video 2b (quantised, ~4 GB VRAM)",
        "url":      (
            "https://huggingface.co/Lightricks/LTX-Video/resolve/main"
            "/ltx-video-2b-v0.9.safetensors"
        ),
        "filename": "ltx-video-2b-v0.9.safetensors",
        "dest":     "checkpoints",
        "vram_min": 4,
    },
    {
        "id":       "ltx_standard",
        "label":    "LTX-Video 2b v0.9.1 (standard, ~8 GB VRAM)",
        "url":      (
            "https://huggingface.co/Lightricks/LTX-Video/resolve/v0.9.1"
            "/ltx-video-2b-v0.9.1.safetensors"
        ),
        "filename": "ltx-video-2b-v0.9.1.safetensors",
        "dest":     "checkpoints",
        "vram_min": 8,
    },
]


# ── VRAM detection ────────────────────────────────────────────────────────────

def detect_vram_gb() -> float:
    """Return detected GPU VRAM in GB, or 0.0 if undetectable."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total",
             "--format=csv,noheader,nounits"],
            timeout=5, stderr=subprocess.DEVNULL,
        ).decode().strip().split("\n")[0]
        return float(out) / 1024
    except Exception:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    except Exception:
        pass
    return 0.0


def pick_model(vram_gb: float) -> dict:
    """Choose the best model variant for the detected VRAM."""
    best = MODEL_OPTIONS[0]  # smallest as safe default
    for option in MODEL_OPTIONS:
        if vram_gb >= option["vram_min"]:
            best = option
    return best


# ── Download helper ───────────────────────────────────────────────────────────

def _download(
    url:       str,
    dest_path: Path,
    label:     str,
    on_status: Callable[[str], None],
) -> bool:
    """Download url to dest_path with progress reporting. Returns True on success."""
    try:
        import requests
    except ImportError:
        on_status("❌ 'requests' not installed. Run: pip install requests")
        return False

    try:
        on_status(f"Downloading {label}…")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = int(downloaded / total * 100)
                        on_status(f"Downloading {label}… {pct}%")
        on_status(f"✅ {label} downloaded.")
        return True
    except Exception as e:
        on_status(f"❌ Failed to download {label}: {e}")
        return False


def _extract_zip(zip_path: Path, dest_dir: Path, on_status: Callable) -> bool:
    try:
        on_status(f"Extracting {zip_path.name}…")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(dest_dir)
        on_status(f"✅ Extracted.")
        return True
    except Exception as e:
        on_status(f"❌ Extraction failed: {e}")
        return False


def _pip_install(packages: list, python: str, on_status: Callable) -> bool:
    """Install packages into the given Python environment."""
    try:
        on_status(f"Installing Python deps: {', '.join(packages)}")
        subprocess.check_call(
            [python, "-m", "pip", "install", "--quiet", "--upgrade"] + packages,
            timeout=300,
        )
        on_status("✅ Dependencies installed.")
        return True
    except Exception as e:
        on_status(f"❌ pip install failed: {e}")
        return False


# ── Main installer ────────────────────────────────────────────────────────────

class VideoInstaller:
    """
    Installs the FreedomForge video module:
      1. Download + extract ComfyUI
      2. Install ComfyUI Python deps
      3. Download + install custom nodes (LTX-Video, VideoHelperSuite)
      4. Download the appropriate video model (VRAM-aware)
      5. Write default workflow JSON
      6. Update app config

    All network I/O happens in a background thread; progress is reported
    via the on_status callback (called from that thread — must be thread-safe).
    """

    def __init__(
        self,
        install_dir: str = None,
        on_status:   Callable[[str], None] = None,
        on_complete: Callable[[bool, str], None] = None,
    ):
        self.install_dir = Path(install_dir) if install_dir else APP_ROOT / "ComfyUI"
        self.on_status   = on_status or (lambda msg: print(msg))
        self.on_complete = on_complete  # (success: bool, message: str)
        self._cancelled  = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        """Start installation in a background thread."""
        threading.Thread(target=self._install, daemon=True).start()

    # ── Internal steps ────────────────────────────────────────

    def _status(self, msg: str):
        if not self._cancelled:
            self.on_status(msg)

    def _fail(self, msg: str):
        self._status(f"❌ Installation failed: {msg}")
        if self.on_complete:
            self.on_complete(False, msg)

    def _install(self):
        try:
            self._status("🎬 Starting video module installation…")

            # ── Step 1: ComfyUI ───────────────────────────────
            if not (self.install_dir / "main.py").exists():
                self._status("Step 1/5 — Downloading ComfyUI…")
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_zip = Path(tmp) / "comfyui.zip"
                    if not _download(COMFY_ZIP_URL, tmp_zip, "ComfyUI", self._status):
                        return self._fail("ComfyUI download failed.")
                    if self._cancelled:
                        return

                    # Extract
                    if not _extract_zip(tmp_zip, Path(tmp), self._status):
                        return self._fail("ComfyUI extraction failed.")

                    # The archive extracts to ComfyUI-master/
                    extracted = next(Path(tmp).glob("ComfyUI-*"), None)
                    if not extracted or not extracted.is_dir():
                        return self._fail("Could not locate extracted ComfyUI directory.")

                    self._status(f"Moving ComfyUI to {self.install_dir}…")
                    if self.install_dir.exists():
                        shutil.rmtree(self.install_dir)
                    shutil.move(str(extracted), str(self.install_dir))
                    self._status("✅ ComfyUI installed.")
            else:
                self._status("Step 1/5 — ComfyUI already present, skipping download.")

            if self._cancelled:
                return

            # ── Step 2: ComfyUI Python deps ───────────────────
            self._status("Step 2/5 — Installing ComfyUI dependencies…")
            req_file = self.install_dir / "requirements.txt"
            if req_file.exists():
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "--quiet",
                         "-r", str(req_file)],
                        timeout=300,
                    )
                    self._status("✅ ComfyUI deps installed.")
                except Exception as e:
                    self._status(f"⚠️ Some ComfyUI deps failed (continuing): {e}")
            else:
                self._status("No requirements.txt found — skipping.")

            if self._cancelled:
                return

            # ── Step 3: Custom nodes ──────────────────────────
            self._status("Step 3/5 — Installing custom nodes…")
            nodes_dir = self.install_dir / "custom_nodes"
            nodes_dir.mkdir(exist_ok=True)

            for node_name, url in CUSTOM_NODE_URLS.items():
                if self._cancelled:
                    return
                node_dest = nodes_dir / node_name
                if node_dest.exists():
                    self._status(f"  {node_name} already installed, skipping.")
                    continue
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_zip = Path(tmp) / f"{node_name}.zip"
                    if not _download(url, tmp_zip, node_name, self._status):
                        self._status(f"⚠️ Could not install {node_name} (continuing).")
                        continue
                    if not _extract_zip(tmp_zip, Path(tmp), self._status):
                        continue
                    # Archive extracts to NodeName-main/
                    extracted = next(
                        Path(tmp).glob(f"{node_name}-*"), None
                    ) or next(Path(tmp).iterdir(), None)
                    if extracted and extracted.is_dir():
                        shutil.move(str(extracted), str(node_dest))
                        self._status(f"  ✅ {node_name} installed.")

                    # Install node's own deps if present
                    node_req = node_dest / "requirements.txt"
                    if node_req.exists():
                        try:
                            subprocess.check_call(
                                [sys.executable, "-m", "pip", "install",
                                 "--quiet", "-r", str(node_req)],
                                timeout=120,
                            )
                        except Exception:
                            pass

            if self._cancelled:
                return

            # ── Step 4: Model download (VRAM-aware) ───────────
            self._status("Step 4/5 — Detecting GPU and selecting model…")
            vram = detect_vram_gb()
            model = pick_model(vram)
            self._status(
                f"  Detected VRAM: {vram:.1f} GB → using {model['label']}")

            model_dir = self.install_dir / "models" / model["dest"]
            model_dir.mkdir(parents=True, exist_ok=True)
            model_path = model_dir / model["filename"]

            if model_path.exists():
                self._status(f"  Model already downloaded, skipping.")
            else:
                if not _download(
                        model["url"], model_path, model["label"], self._status):
                    self._status(
                        "⚠️ Model download failed. You can download it manually "
                        "and place it in ComfyUI/models/checkpoints/")

            if self._cancelled:
                return

            # ── Step 5: Write workflow + update config ─────────
            self._status("Step 5/5 — Writing workflow and updating config…")
            self._write_workflow(model["filename"])
            self._update_config(model["filename"])
            self._status("✅ Configuration saved.")

            if self.on_complete:
                self.on_complete(
                    True,
                    "Video module installed! Restart FreedomForge to activate it.",
                )

        except Exception as e:
            self._fail(str(e))

    def _write_workflow(self, model_filename: str):
        """Write a workflow JSON that references the downloaded model."""
        wf_dir = self.install_dir / "workflows"
        wf_dir.mkdir(exist_ok=True)
        workflow = {
            "1": {
                "class_type": "LTXVModelLoader",
                "_meta": {"title": "LTX-Video Model"},
                "inputs": {"model": model_filename},
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "Positive Prompt"},
                "inputs": {"text": "", "clip": ["1", 1]},
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "Negative Prompt"},
                "inputs": {"text": "blurry, low quality, distorted, watermark",
                           "clip": ["1", 1]},
            },
            "4": {
                "class_type": "LTXVScheduler",
                "_meta": {"title": "Scheduler"},
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "steps": 25,
                    "cfg": 3.0,
                    "width": 704,
                    "height": 480,
                    "num_frames": 97,
                },
            },
            "5": {
                "class_type": "VHS_VideoCombine",
                "_meta": {"title": "Save Video"},
                "inputs": {
                    "images": ["4", 0],
                    "frame_rate": 24,
                    "format": "video/h264-mp4",
                    "save_output": True,
                    "filename_prefix": "FreedomForge",
                },
            },
        }
        with open(wf_dir / "ltx_video.json", "w") as f:
            json.dump(workflow, f, indent=2)

    def _update_config(self, model_filename: str):
        """Enable video in the app config."""
        from core import config
        from utils.paths import APP_ROOT
        config.set("video_enabled", True)
        config.set("comfy_dir", str(self.install_dir))
        config.set("video_model", model_filename)


# ── Convenience function ──────────────────────────────────────────────────────

def install(
    install_dir: str = None,
    on_status:   Callable[[str], None] = None,
    on_complete: Callable[[bool, str], None] = None,
):
    """Start the video module installation in a background thread."""
    VideoInstaller(install_dir, on_status, on_complete).run()
