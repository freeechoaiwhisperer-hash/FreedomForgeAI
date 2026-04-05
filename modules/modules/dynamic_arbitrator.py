# ============================================================
#  FreedomForge AI — modules/dynamic_arbitrator.py
#  Universal hardware scanner (NVIDIA + AMD + Intel + CPU)
# ============================================================

import subprocess
import json
import sys
import shutil
import torch

def get_hardware_scan():
    """Universal scan for all GPUs (NVIDIA, AMD, Intel) + CPU fallback."""
    scan = {
        "devices": [],
        "total_vram_gb": 0.0,
        "cpu_cores": 0,
        "ram_gb": 0.0,
        "gpu_type": "unknown"
    }

    # NVIDIA
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            timeout=5, stderr=subprocess.DEVNULL
        ).decode().strip()
        for line in out.split('\n'):
            if line:
                name, vram = line.split(', ')
                vram_gb = float(vram) / 1024
                scan["devices"].append({
                    "name": name.strip(),
                    "vram_gb": round(vram_gb, 2),
                    "type": "nvidia"
                })
                scan["total_vram_gb"] += vram_gb
                scan["gpu_type"] = "nvidia"
    except:
        pass

    # AMD / ROCm fallback
    if not scan["devices"]:
        try:
            out = subprocess.check_output(
                ["rocm-smi", "--showmeminfo", "vram"], timeout=5, stderr=subprocess.DEVNULL
            ).decode()
            # Simplified parse - add more if needed
            scan["devices"].append({
                "name": "AMD GPU (ROCm)",
                "vram_gb": 8.0,  # placeholder - improve later
                "type": "amd"
            })
            scan["total_vram_gb"] = 8.0
            scan["gpu_type"] = "amd"
        except:
            pass

    # Torch fallback (catches CUDA/ROCm)
    if not scan["devices"]:
        try:
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    name = torch.cuda.get_device_name(i)
                    vram = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                    scan["devices"].append({
                        "name": name,
                        "vram_gb": round(vram, 2),
                        "type": "cuda"
                    })
                    scan["total_vram_gb"] += vram
                    scan["gpu_type"] = "cuda"
        except:
            pass

    # CPU info
    try:
        import psutil
        scan["cpu_cores"] = psutil.cpu_count(logical=True)
        scan["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
    except:
        pass

    if not scan["devices"]:
        scan["devices"].append({
            "name": "CPU Only (no GPU detected)",
            "vram_gb": 0.0,
            "type": "cpu"
        })

    return scan


def main():
    print("=== FreedomForge Universal Hardware Scanner ===")
    scan = get_hardware_scan()

    print(f"CPU Cores: {scan['cpu_cores']}")
    print(f"System RAM: {scan['ram_gb']} GB")
    print(f"GPU Type: {scan['gpu_type'].upper()}")
    print(f"Total VRAM: {scan['total_vram_gb']:.1f} GB")
    print("\nDetected devices:")

    for dev in scan["devices"]:
        print(f" • {dev['name']} — {dev['vram_gb']:.1f} GB")

    if scan['total_vram_gb'] > 0:
        print("\n✅ GPU ready for offloading.")
    else:
        print("\n⚠️ No GPU detected — running on CPU only.")

if __name__ == "__main__":
    main()
