# ============================================================
#  FreedomForge AI — modules/video.py
#  Video generation module - ComfyUI installer + placeholder
# ============================================================

import subprocess
import os
from typing import Callable

MODULE_NAME = "video"

COMFY_PATH = os.path.expanduser("~/ComfyUI")

def is_comfy_installed() -> bool:
    return os.path.exists(COMFY_PATH)

def install_comfy() -> str:
    """One-click ComfyUI install for video generation."""
    try:
        if not is_comfy_installed():
            print("[Video] Installing ComfyUI...")
            subprocess.run(["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git", COMFY_PATH], check=True)
            subprocess.run(["pip", "install", "-r", os.path.join(COMFY_PATH, "requirements.txt")], check=True)
            return "✅ ComfyUI installed successfully. Restart the app and try again."
        return "✅ ComfyUI is already installed."
    except Exception as e:
        return f"❌ ComfyUI install failed: {str(e)[:100]}"

def handle(
    message: str,
    on_result: Callable[[str], None],
    on_error: Callable[[str], None],
) -> None:
    if not is_comfy_installed():
        on_result("ComfyUI not found.\n" + install_comfy())
        return

    # Placeholder for actual video generation (ComfyUI workflow)
    on_result("🎬 Video generation started.\nFull ComfyUI workflow support coming soon.\nFor now, ComfyUI is ready in ~/ComfyUI")
