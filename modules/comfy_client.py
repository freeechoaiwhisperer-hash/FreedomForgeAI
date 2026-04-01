# ============================================================
#  FreedomForge AI — modules/comfy_client.py
#  Robust ComfyUI process manager + HTTP API client
# ============================================================

import json
import os
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional

try:
    import requests as _requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


def _get_vram_gb() -> float:
    """Return available GPU VRAM in GB, or 0 if undetectable."""
    # Try nvidia-smi first (no torch required)
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            timeout=5, stderr=subprocess.DEVNULL,
        ).decode().strip().split("\n")[0]
        return float(out) / 1024
    except Exception:
        pass
    # Try torch
    try:
        import torch
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return props.total_memory / (1024 ** 3)
    except Exception:
        pass
    # Try Metal (macOS)
    try:
        import subprocess as sp
        result = sp.check_output(
            ["system_profiler", "SPDisplaysDataType"], timeout=5,
            stderr=sp.DEVNULL,
        ).decode()
        for line in result.split("\n"):
            if "VRAM" in line or "vram" in line:
                nums = [s for s in line.split() if s.replace(".", "").isdigit()]
                if nums:
                    return float(nums[0]) / 1024
    except Exception:
        pass
    return 0.0


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _default_workflow() -> dict:
    """
    Minimal ComfyUI workflow for LTX-Video 2b.
    Works with the standard ComfyUI-LTXVideo custom node.
    Node IDs are stable strings so inject_prompt() can find them.
    """
    return {
        "1": {
            "class_type": "LTXVModelLoader",
            "_meta": {"title": "LTX-Video Model"},
            "inputs": {"model": "ltx-video-2b-v0.9.1.safetensors"},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Positive Prompt"},
            "inputs": {"text": "PLACEHOLDER_POSITIVE", "clip": ["1", 1]},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Negative Prompt"},
            "inputs": {"text": "PLACEHOLDER_NEGATIVE", "clip": ["1", 1]},
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


class ComfyUIClient:
    """
    Manages a ComfyUI subprocess and wraps its HTTP API.

    Usage:
        client = ComfyUIClient("/path/to/ComfyUI")
        client.generate("a dog running on a beach", on_complete=..., on_error=...)
    """

    DEFAULT_PORT     = 8188
    STARTUP_TIMEOUT  = 90    # seconds to wait for ComfyUI to start
    GEN_TIMEOUT      = 300   # max seconds per generation

    def __init__(
        self,
        comfy_dir: str,
        port: int = DEFAULT_PORT,
        workflow_dir: str = None,
    ):
        self.comfy_dir    = Path(comfy_dir)
        self.port         = port
        self.workflow_dir = Path(workflow_dir) if workflow_dir else self.comfy_dir / "workflows"
        self.base_url     = f"http://127.0.0.1:{port}"
        self._process: Optional[subprocess.Popen] = None
        self._lock        = threading.Lock()

    # ── Status ────────────────────────────────────────────────

    def is_running(self) -> bool:
        if not REQUESTS_OK:
            return False
        try:
            r = _requests.get(f"{self.base_url}/system_stats", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def is_installed(self) -> bool:
        return (self.comfy_dir / "main.py").exists()

    # ── Lifecycle ─────────────────────────────────────────────

    def start(self, on_status: Callable[[str], None] = None) -> bool:
        """Start ComfyUI if not already running. Returns True when ready."""
        with self._lock:
            if self.is_running():
                return True

            if not self.is_installed():
                if on_status:
                    on_status("ComfyUI not installed. Run the video installer first.")
                return False

            # Resolve port conflict
            if _port_in_use(self.port):
                if on_status:
                    on_status(f"Port {self.port} busy — trying {self.port + 1}")
                self.port    += 1
                self.base_url = f"http://127.0.0.1:{self.port}"

            # Find Python executable (portable install has its own)
            python_exe = self._find_python()

            cmd = [python_exe, "main.py", "--port", str(self.port), "--headless"]
            if on_status:
                on_status("Starting ComfyUI…")
            try:
                self._process = subprocess.Popen(
                    cmd,
                    cwd=str(self.comfy_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
            except Exception as e:
                if on_status:
                    on_status(f"Could not launch ComfyUI: {e}")
                return False

            # Poll until responsive
            deadline = time.time() + self.STARTUP_TIMEOUT
            while time.time() < deadline:
                if self._process.poll() is not None:
                    if on_status:
                        on_status("ComfyUI exited unexpectedly during startup.")
                    return False
                if self.is_running():
                    if on_status:
                        on_status("✅ ComfyUI ready.")
                    return True
                elapsed = int(time.time() - (deadline - self.STARTUP_TIMEOUT))
                if on_status:
                    on_status(f"Starting ComfyUI… ({elapsed}s)")
                time.sleep(2)

            if on_status:
                on_status("ComfyUI startup timed out.")
            return False

    def stop(self):
        """Terminate the ComfyUI process if we started it."""
        with self._lock:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                self._process = None

    def _find_python(self) -> str:
        for candidate in [
            self.comfy_dir / "python_embeded" / "python.exe",  # Windows portable
            self.comfy_dir / "python_embeded" / "python",
            self.comfy_dir / "venv" / "bin" / "python",
        ]:
            if Path(str(candidate)).exists():
                return str(candidate)
        return "python3" if os.name != "nt" else "python"

    # ── Workflow helpers ──────────────────────────────────────

    def load_workflow(self, name: str) -> dict:
        """Load workflow JSON from the workflow directory."""
        path = self.workflow_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Workflow not found: {path}")
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def inject_prompt(
        workflow: dict,
        positive: str,
        negative: str = "blurry, low quality, distorted, watermark",
    ) -> dict:
        """
        Find CLIPTextEncode nodes and inject positive/negative prompts.
        Uses _meta.title hints first, falls back to insertion order.
        """
        workflow = json.loads(json.dumps(workflow))  # deep copy
        positive_filled = False
        negative_filled = False

        # First pass: use title metadata
        for node in workflow.values():
            if node.get("class_type") != "CLIPTextEncode":
                continue
            title = node.get("_meta", {}).get("title", "").lower()
            if "negative" in title:
                node["inputs"]["text"] = negative
                negative_filled = True
            elif "positive" in title or "prompt" in title:
                node["inputs"]["text"] = positive
                positive_filled = True

        # Second pass: fill any remaining CLIPTextEncode by order
        for node in workflow.values():
            if node.get("class_type") != "CLIPTextEncode":
                continue
            if not positive_filled:
                node["inputs"]["text"] = positive
                positive_filled = True
            elif not negative_filled:
                node["inputs"]["text"] = negative
                negative_filled = True

        return workflow

    # ── API calls ─────────────────────────────────────────────

    def queue_prompt(self, workflow: dict) -> Optional[str]:
        r = _requests.post(
            f"{self.base_url}/prompt",
            json={"prompt": workflow},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("prompt_id")

    def wait_for_completion(
        self,
        prompt_id: str,
        on_status: Callable[[str], None] = None,
    ) -> Optional[dict]:
        """Poll /history until complete. Returns history entry or None on timeout."""
        deadline = time.time() + self.GEN_TIMEOUT
        while time.time() < deadline:
            try:
                r = _requests.get(
                    f"{self.base_url}/history/{prompt_id}", timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if prompt_id in data:
                        return data[prompt_id]

                # Report queue position
                q = _requests.get(f"{self.base_url}/queue", timeout=5).json()
                running = q.get("queue_running", [])
                pending = q.get("queue_pending", [])
                if any(item[1] == prompt_id for item in running):
                    if on_status:
                        on_status("🎬 Generating video…")
                else:
                    pos = next(
                        (i + 1 for i, item in enumerate(pending)
                         if item[1] == prompt_id), "?")
                    if on_status:
                        on_status(f"⏳ Queued (position {pos})…")

            except Exception as e:
                if on_status:
                    on_status(f"Polling… ({e})")

            time.sleep(3)

        return None

    def get_output_files(self, history_entry: dict) -> List[str]:
        """Extract output file paths from a completed history entry."""
        files = []
        for node_output in history_entry.get("outputs", {}).values():
            for key in ("videos", "images", "gifs"):
                for item in node_output.get(key, []):
                    fname     = item.get("filename")
                    subfolder = item.get("subfolder", "")
                    if fname:
                        path = self.comfy_dir / "output" / subfolder / fname
                        if path.exists():
                            files.append(str(path))
        return files

    # ── High-level generate ───────────────────────────────────

    def generate(
        self,
        prompt:          str,
        workflow_name:   str = "ltx_video",
        negative_prompt: str = "blurry, low quality, distorted, watermark",
        on_status:       Callable[[str], None] = None,
        on_complete:     Callable[[List[str]], None] = None,
        on_error:        Callable[[str], None] = None,
    ) -> None:
        """Full pipeline in a background thread: start → load → inject → queue → poll → files."""

        def _run():
            try:
                if not self.start(on_status=on_status):
                    if on_error:
                        on_error(
                            "ComfyUI could not start. "
                            "Check your video module installation.")
                    return

                try:
                    workflow = self.load_workflow(workflow_name)
                except FileNotFoundError:
                    workflow = _default_workflow()

                workflow = self.inject_prompt(workflow, prompt, negative_prompt)

                if on_status:
                    on_status("Sending prompt to ComfyUI…")
                prompt_id = self.queue_prompt(workflow)
                if not prompt_id:
                    if on_error:
                        on_error("ComfyUI accepted the request but returned no prompt ID.")
                    return

                if on_status:
                    on_status(f"Queued (ID: {prompt_id[:8]}…)")
                entry = self.wait_for_completion(prompt_id, on_status=on_status)

                if entry is None:
                    if on_error:
                        on_error(
                            "Generation timed out. "
                            "ComfyUI may be busy or your GPU is too slow.")
                    return

                files = self.get_output_files(entry)
                if on_complete:
                    on_complete(files)

            except Exception as e:
                if on_error:
                    on_error(f"Unexpected error: {e}")

        threading.Thread(target=_run, daemon=True).start()


# ── Module-level singleton ────────────────────────────────────────────────────
# Resolved lazily so the app can start even if ComfyUI isn't installed.

_client: Optional[ComfyUIClient] = None
_client_lock = threading.Lock()


def get_client(comfy_dir: str = None) -> ComfyUIClient:
    global _client
    with _client_lock:
        if _client is None:
            from core import config
            from utils.paths import APP_ROOT
            _dir = comfy_dir or config.get("comfy_dir") or str(APP_ROOT / "ComfyUI")
            _client = ComfyUIClient(_dir)
        return _client
