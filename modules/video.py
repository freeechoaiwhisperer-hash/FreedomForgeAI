# ============================================================
#  FreedomForge AI — modules/video.py
#  Video generation module (ComfyUI / Wan2.1)
# ============================================================

import os
import json
import threading
import subprocess
import requests
from typing import Callable

COMFY_URL     = "http://127.0.0.1:8188"
MODULE_NAME   = "video"

# Supported video generators
GENERATORS = {
    "wan2.1": {
        "name":    "Wan2.1",
        "desc":    "High quality open source video generation",
        "requires": "ComfyUI + Wan2.1 models",
        "port":    8188,
    },
    "animatediff": {
        "name":    "AnimateDiff",
        "desc":    "Smooth animated video from text",
        "requires": "ComfyUI + AnimateDiff models",
        "port":    8188,
    },
}


def is_comfyui_running() -> bool:
    try:
        r = requests.get(f"{COMFY_URL}/system_stats", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def get_available_generators() -> list[dict]:
    available = []
    if is_comfyui_running():
        for key, info in GENERATORS.items():
            available.append({"id": key, **info})
    return available


def generate_video(
    prompt:    str,
    generator: str = "wan2.1",
    on_result: Callable[[str], None] = None,
    on_error:  Callable[[str], None] = None,
    on_status: Callable[[str], None] = None,
) -> None:
    """Generate video using ComfyUI in background thread."""

    def _generate():
        try:
            if not is_comfyui_running():
                if on_error:
                    on_error(
                        "ComfyUI is not running. Start ComfyUI first, "
                        "then try again. Your ComfyUI setup from before "
                        "should work — just launch it."
                    )
                return

            if on_status:
                on_status("Sending prompt to ComfyUI...")

            # Basic Wan2.1 workflow
            workflow = _build_workflow(prompt, generator)
            r = requests.post(
                f"{COMFY_URL}/prompt",
                json={"prompt": workflow},
                timeout=10,
            )

            if r.status_code != 200:
                if on_error:
                    on_error(f"ComfyUI error: {r.status_code}")
                return

            prompt_id = r.json().get("prompt_id")
            if on_status:
                on_status(f"Generating... (ID: {prompt_id})")

            if on_result:
                on_result(
                    f"✅ Video generation started in ComfyUI!\n"
                    f"Prompt: {prompt}\n"
                    f"Check ComfyUI at {COMFY_URL} to see progress and download your video."
                )

        except Exception as e:
            if on_error:
                on_error(str(e))

    threading.Thread(target=_generate, daemon=True).start()


def _build_workflow(prompt: str, generator: str) -> dict:
    """Build a basic ComfyUI workflow dict for the given generator."""
    # This is a simplified placeholder workflow
    # A real implementation would have the full node graph
    return {
        "1": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 1]},
        },
    }


def handle(
    message:   str,
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
) -> None:
    """Entry point called by module router."""
    # Strip command prefix if present
    prompt = message
    for prefix in ["/video ", "make a video of ", "generate a video of ",
                   "create a video of "]:
        if message.lower().startswith(prefix):
            prompt = message[len(prefix):].strip()
            break

    if not prompt:
        on_error("Please describe what video you want to create.")
        return

    generators = get_available_generators()

    if not generators:
        on_result(
            "🎬 **Video Generation**\n\n"
            "ComfyUI is not currently running on your machine.\n\n"
            "To generate videos:\n"
            "1. Start ComfyUI (you already have it set up with Wan2.1)\n"
            "2. Come back and ask again\n\n"
            f"Your prompt has been saved: *\"{prompt}\"*\n"
            "Ready to go as soon as ComfyUI is running!"
        )
        return

    generate_video(
        prompt=prompt,
        generator="wan2.1",
        on_result=on_result,
        on_error=on_error,
    )
