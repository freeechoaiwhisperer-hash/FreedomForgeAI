# ============================================================
#  FreedomForge AI — modules/video.py
#  Video generation module — uses ComfyUIClient
# ============================================================

from typing import Callable

MODULE_NAME = "video"

# Trigger patterns matched by the module router
TRIGGERS = [
    r"^/video\b",
    r"\b(make|create|generate|render)\s+a\s+video\b",
    r"\bgenerate\s+video\b",
]


def handle(
    message:   str,
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
) -> None:
    """Entry point called by the module router."""
    from core import config

    # Strip common command prefixes to get the bare prompt
    prompt = message
    for prefix in [
        "/video ", "make a video of ", "generate a video of ",
        "create a video of ", "render a video of ",
        "make a video ", "generate a video ", "create a video ",
    ]:
        if message.lower().startswith(prefix.lower()):
            prompt = message[len(prefix):].strip()
            break

    if not prompt:
        on_error("Please describe what you want in the video, e.g. '/video a cat on a surfboard'")
        return

    if not config.get("video_enabled", False):
        on_result(
            "🎬 **Video Generation**\n\n"
            "The video module isn't installed yet.\n\n"
            "Go to the **🎬 Video** tab and click **Install Video Module** to set it up.\n\n"
            f"Your prompt is ready: *\"{prompt}\"*"
        )
        return

    from modules.comfy_client import get_client
    client = get_client()

    if not client.is_installed():
        on_result(
            "🎬 **Video Generation**\n\n"
            "ComfyUI is not installed at the configured path.\n"
            "Go to **🎬 Video** → **Install Video Module** to fix this."
        )
        return

    def _on_complete(files):
        if files:
            paths = "\n".join(f"📹 `{f}`" for f in files)
            on_result(
                f"🎬 **Video ready!**\n\n"
                f"Prompt: *{prompt}*\n\n"
                f"{paths}"
            )
        else:
            on_result(
                "🎬 Generation finished, but no output files were found.\n"
                "Check ComfyUI's output folder manually."
            )

    def _on_error(msg):
        on_error(f"🎬 Video error: {msg}")

    def _on_status(msg):
        on_result(f"🎬 {msg}")

    client.generate(
        prompt=prompt,
        workflow_name="ltx_video",
        on_status=_on_status,
        on_complete=_on_complete,
        on_error=_on_error,
    )
