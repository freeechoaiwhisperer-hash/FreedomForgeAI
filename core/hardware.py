# ============================================================
#  FreedomForge AI — core/hardware.py
#  Hardware detection and model recommendations
# ============================================================

import subprocess

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUtil = None
    GPUTIL_AVAILABLE = False


def detect_gpu() -> dict:
    """Returns GPU info dict: {available, name, vram_gb, layers}"""
    result = {"available": False, "name": "None",
              "vram_gb": 0, "layers": 0}
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=5)
        if r.returncode == 0:
            parts = r.stdout.decode().strip().split(",")
            name  = parts[0].strip() if parts else "NVIDIA GPU"
            vram  = int(parts[1].strip()) // 1024 if len(parts) > 1 else 0
            result = {
                "available": True,
                "name":      name,
                "vram_gb":   vram,
                "layers":    -1,
            }
    except (FileNotFoundError, OSError):
        pass  # nvidia-smi not installed — no NVIDIA GPU
    except Exception:
        pass
    return result


def get_ram_gb() -> int:
    if not PSUTIL_AVAILABLE:
        return 0
    return round(psutil.virtual_memory().total / (1024 ** 3))


def get_cpu_percent() -> float:
    if not PSUTIL_AVAILABLE:
        return 0.0
    return psutil.cpu_percent(interval=None)


def get_gpu_percent() -> float:
    if not GPUTIL_AVAILABLE:
        return 0.0
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            return gpus[0].load * 100
    except Exception:
        pass
    return 0.0


def get_system_info() -> dict:
    gpu = detect_gpu()
    ram = get_ram_gb()
    return {"ram_gb": ram, "gpu": gpu}


def recommend_model(ram_gb: int = None) -> str:
    if ram_gb is None:
        ram_gb = get_ram_gb()
    if ram_gb >= 12:
        return "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    elif ram_gb >= 8:
        return "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    elif ram_gb >= 4:
        return "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    else:
        return "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"


def get_n_gpu_layers() -> int:
    gpu = detect_gpu()
    return gpu["layers"]
