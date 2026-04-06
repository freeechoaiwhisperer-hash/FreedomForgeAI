# ============================================================
#  FreedomForge AI — core/system_tools.py
#  Phase 3: System Intelligence
#  Hardware health, disk cleanup, startup programs
# ============================================================

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set
from core import logger

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# ── System Summary ─────────────────────────────────────────────

def get_system_summary() -> Dict:
    """Full system health snapshot — CPU, RAM, disk, GPU."""
    result = {
        "platform": platform.system(),
        "hostname": platform.node(),
        "cpu":  _get_cpu_info(),
        "ram":  _get_ram_info(),
        "disk": _get_disk_info(),
        "gpu":  _get_gpu_info(),
        "temps": _get_temps(),
    }
    return result


def _get_cpu_info() -> Dict:
    if not PSUTIL_AVAILABLE:
        return {}
    try:
        freq = psutil.cpu_freq()
        return {
            "percent":    psutil.cpu_percent(interval=0.5),
            "count_phys": psutil.cpu_count(logical=False) or 0,
            "count_logi": psutil.cpu_count(logical=True)  or 0,
            "freq_mhz":   round(freq.current) if freq else 0,
            "model":      _get_cpu_model(),
        }
    except Exception as e:
        logger.error(f"CPU info error: {e}")
        return {}


def _get_cpu_model() -> str:
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
        elif platform.system() == "Darwin":
            r = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True)
            return r.stdout.strip()
        elif platform.system() == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return winreg.QueryValueEx(key, "ProcessorNameString")[0]
    except Exception:
        pass
    return platform.processor() or "Unknown CPU"


def _get_ram_info() -> Dict:
    if not PSUTIL_AVAILABLE:
        return {}
    try:
        vm = psutil.virtual_memory()
        return {
            "total_gb":     round(vm.total     / (1024**3), 1),
            "used_gb":      round(vm.used      / (1024**3), 1),
            "available_gb": round(vm.available / (1024**3), 1),
            "percent":      vm.percent,
        }
    except Exception as e:
        logger.error(f"RAM info error: {e}")
        return {}


def _get_disk_info() -> List[Dict]:
    if not PSUTIL_AVAILABLE:
        return []
    results = []
    try:
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                results.append({
                    "mount":    part.mountpoint,
                    "device":   part.device,
                    "fstype":   part.fstype,
                    "total_gb": round(usage.total / (1024**3), 1),
                    "used_gb":  round(usage.used  / (1024**3), 1),
                    "free_gb":  round(usage.free  / (1024**3), 1),
                    "percent":  usage.percent,
                })
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Disk info error: {e}")
    return results


def _get_gpu_info() -> Dict:
    try:
        r = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=4)
        if r.returncode == 0 and r.stdout.strip():
            parts = [p.strip() for p in r.stdout.strip().split(",")]
            return {
                "available":   True,
                "name":        parts[0] if len(parts) > 0 else "GPU",
                "vram_total":  round(int(parts[1]) / 1024, 1) if len(parts) > 1 else 0,
                "vram_used":   round(int(parts[2]) / 1024, 1) if len(parts) > 2 else 0,
                "utilization": int(parts[3]) if len(parts) > 3 else 0,
                "temp_c":      int(parts[4]) if len(parts) > 4 else 0,
            }
    except Exception:
        pass
    return {"available": False}


def _get_temps() -> Dict:
    if not PSUTIL_AVAILABLE:
        return {}
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return {}
        result = {}
        for name, entries in temps.items():
            if entries:
                result[name] = round(entries[0].current, 1)
        return result
    except Exception:
        return {}


# ── Plain-language health report ──────────────────────────────

def get_health_report(summary: Dict) -> str:
    """Turn raw system data into plain English for non-technical users."""
    lines = ["Your System Health Report", "=" * 34, ""]

    cpu = summary.get("cpu", {})
    if cpu:
        pct = cpu.get("percent", 0)
        model = cpu.get("model", "Unknown")
        cores = cpu.get("count_phys", "?")
        feel = "running smoothly" if pct < 40 else \
               "a bit busy" if pct < 75 else "working very hard"
        lines.append(f"Processor ({model})")
        lines.append(f"  {cores} cores  •  {pct:.0f}% busy  •  {feel}")
        lines.append("")

    ram = summary.get("ram", {})
    if ram:
        used = ram.get("used_gb", 0)
        total = ram.get("total_gb", 0)
        pct = ram.get("percent", 0)
        feel = "plenty of room" if pct < 60 else \
               "getting full" if pct < 85 else "almost full — close some apps"
        lines.append(f"Memory (RAM)")
        lines.append(f"  {used} GB used of {total} GB  •  {feel}")
        lines.append("")

    disks = summary.get("disk", [])
    if disks:
        lines.append("Storage")
        for d in disks:
            feel = "lots of space" if d["percent"] < 70 else \
                   "filling up" if d["percent"] < 90 else "almost full!"
            lines.append(
                f"  {d['mount']}  —  "
                f"{d['free_gb']} GB free of {d['total_gb']} GB  •  {feel}")
        lines.append("")

    gpu = summary.get("gpu", {})
    if gpu.get("available"):
        lines.append(f"Graphics Card ({gpu['name']})")
        lines.append(
            f"  VRAM: {gpu['vram_used']} / {gpu['vram_total']} GB used  •  "
            f"{gpu['utilization']}% load  •  {gpu.get('temp_c', '?')}°C")
        lines.append("")

    temps = summary.get("temps", {})
    if temps:
        lines.append("Temperatures")
        for sensor, temp in list(temps.items())[:4]:
            feel = "cool" if temp < 60 else "warm" if temp < 80 else "hot!"
            lines.append(f"  {sensor}: {temp}°C  ({feel})")
        lines.append("")

    return "\n".join(lines)


# ── Startup programs ──────────────────────────────────────────

def get_startup_programs() -> List[Dict]:
    """List startup programs (Linux: systemd user services + autostart)."""
    results = []
    system = platform.system()

    if system == "Linux":
        # ~/.config/autostart (XDG)
        autostart = Path.home() / ".config" / "autostart"
        if autostart.exists():
            for f in autostart.glob("*.desktop"):
                try:
                    name = f.stem
                    enabled = True
                    with open(f) as fp:
                        for line in fp:
                            if line.startswith("Hidden=true"):
                                enabled = False
                            if line.startswith("Name="):
                                name = line.split("=", 1)[1].strip()
                    results.append({
                        "name":    name,
                        "path":    str(f),
                        "enabled": enabled,
                        "source":  "autostart",
                    })
                except Exception:
                    pass

        # systemd user services (enabled)
        try:
            r = subprocess.run(
                ["systemctl", "--user", "list-unit-files",
                 "--state=enabled", "--no-legend"],
                capture_output=True, text=True, timeout=5)
            for line in r.stdout.splitlines():
                parts = line.split()
                if parts:
                    results.append({
                        "name":    parts[0],
                        "path":    "",
                        "enabled": True,
                        "source":  "systemd-user",
                    })
        except Exception:
            pass

    elif system == "Windows":
        import winreg
        for hive, path in [
            (winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE,
             r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]:
            try:
                key = winreg.OpenKey(hive, path)
                i = 0
                while True:
                    try:
                        name, data, _ = winreg.EnumValue(key, i)
                        results.append({
                            "name":    name,
                            "path":    data,
                            "enabled": True,
                            "source":  "registry",
                        })
                        i += 1
                    except OSError:
                        break
            except Exception:
                pass

    elif system == "Darwin":
        for p in [Path.home() / "Library" / "LaunchAgents",
                  Path("/Library/LaunchAgents"),
                  Path("/Library/LaunchDaemons")]:
            if p.exists():
                for f in p.glob("*.plist"):
                    results.append({
                        "name":    f.stem,
                        "path":    str(f),
                        "enabled": True,
                        "source":  str(p.name),
                    })

    return results


def disable_startup_item(item: Dict) -> bool:
    """Disable a startup item. Returns True on success."""
    try:
        if item["source"] == "autostart":
            p = Path(item["path"])
            text = p.read_text()
            if "Hidden=true" not in text:
                p.write_text(text + "\nHidden=true\n")
            return True
        elif item["source"] == "systemd-user":
            r = subprocess.run(
                ["systemctl", "--user", "disable", item["name"]],
                capture_output=True, timeout=10)
            return r.returncode == 0
    except Exception as e:
        logger.error(f"Disable startup error: {e}")
    return False


# ── Large file finder / disk cleaner ─────────────────────────

def find_large_files(
    root: str = None,
    min_mb: float = 100,
    max_results: int = 50,
) -> List[Dict]:
    """Find large files under root directory."""
    if root is None:
        root = str(Path.home())
    results = []
    min_bytes = int(min_mb * 1024 * 1024)
    skip_dirs = {".git", "venv", "__pycache__", "node_modules",
                 ".cache", "proc", "sys", "dev"}
    try:
        for entry in _walk_files(Path(root), skip_dirs):
            try:
                size = entry.stat().st_size
                if size >= min_bytes:
                    results.append({
                        "path":    str(entry),
                        "size_mb": round(size / (1024**2), 1),
                        "name":    entry.name,
                    })
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Large file scan error: {e}")
    results.sort(key=lambda x: x["size_mb"], reverse=True)
    return results[:max_results]


def _walk_files(root: Path, skip_dirs: set):
    try:
        for item in root.iterdir():
            if item.name.startswith(".") and item.name not in {".forge_key"}:
                continue
            if item.is_symlink():
                continue
            if item.is_dir() and item.name not in skip_dirs:
                yield from _walk_files(item, skip_dirs)
            elif item.is_file():
                yield item
    except PermissionError:
        pass
    except Exception:
        pass


def find_temp_files() -> List[Dict]:
    """Find common temporary / cache files that are safe to delete."""
    results = []
    temp_patterns = [
        (Path.home() / ".cache",   "User cache"),
        (Path("/tmp"),             "Temp files"),
        (Path.home() / ".thumbnails", "Thumbnails"),
        (Path.home() / ".local" / "share" / "Trash", "Trash"),
    ]
    for p, label in temp_patterns:
        if p.exists():
            try:
                size = _dir_size_mb(p)
                results.append({
                    "path":    str(p),
                    "label":   label,
                    "size_mb": size,
                })
            except Exception:
                pass
    return results


# ── AI Model Scanner ─────────────────────────────────────────

_MODEL_EXTENSIONS = {".gguf", ".bin", ".safetensors", ".ggml"}

_BASE_MODEL_PATHS = [
    Path.home() / ".ollama" / "models",
    Path.home() / ".cache" / "lm-studio" / "models",
    Path.home() / ".cache" / "huggingface" / "hub",
    Path("/usr/share/ollama/models"),
    Path("/var/lib/ollama/models"),
]


def _model_source_app(path_str: str) -> str:
    parts = set(Path(path_str).parts)
    if ".ollama" in parts:
        return "Ollama"
    if "lm-studio" in parts:
        return "LM Studio"
    if "huggingface" in parts:
        return "HuggingFace"
    return "Found"


def scan_for_models() -> List[Dict]:
    """Scan well-known locations for AI model files.

    Returns a list of dicts with keys:
        path, name, size_gb, format, source_app
    """
    search_roots: List[Path] = list(_BASE_MODEL_PATHS)

    # Add all immediate subdirectories of /mnt/ and /media/
    for mount_parent in (Path("/mnt"), Path("/media")):
        if mount_parent.exists():
            try:
                for sub in mount_parent.iterdir():
                    if sub.is_dir():
                        search_roots.append(sub)
            except PermissionError:
                pass

    results: List[Dict] = []
    seen: Set[str] = set()

    for root in search_roots:
        if not root.exists():
            continue
        try:
            for entry in root.rglob("*"):
                try:
                    if not entry.is_file():
                        continue
                    if entry.suffix.lower() not in _MODEL_EXTENSIONS:
                        continue
                    resolved = str(entry.resolve())
                    if resolved in seen:
                        continue
                    seen.add(resolved)
                    size_bytes = entry.stat().st_size
                    results.append({
                        "path":       str(entry),
                        "name":       entry.name,
                        "size_gb":    round(size_bytes / (1024 ** 3), 3),
                        "format":     entry.suffix.lstrip(".").lower(),
                        "source_app": _model_source_app(str(entry)),
                    })
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass

    results.sort(key=lambda x: x["size_gb"], reverse=True)
    return results


def _dir_size_mb(path: Path) -> float:
    total = 0
    try:
        for entry in path.rglob("*"):
            try:
                if entry.is_file():
                    total += entry.stat().st_size
            except Exception:
                pass
    except Exception:
        pass
    return round(total / (1024**2), 1)
