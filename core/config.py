# ============================================================
#  FreedomForge AI — core/config.py
#  Configuration management with debounced disk writes
# ============================================================

import os
import json
import threading
from utils.paths import CONFIG_FILE as _CONFIG_PATH

_CONFIG_FILE = str(_CONFIG_PATH)

DEFAULTS = {
    "last_model":     None,
    "n_ctx":          4096,
    "voice_in":       False,
    "voice_out":      False,
    "dark_mode":      True,
    "font_size":      13,
    "unlocked":       False,
    "personality":    "normal",
    "agent_enabled":  False,
    "theme":          "dark",
    "language":       "en",
    "lora_adapter":   "",
}

_config: dict = {}
_save_timer: threading.Timer = None
_save_lock = threading.Lock()

_DEBOUNCE_SEC = 0.5


def load_config() -> dict:
    global _config
    try:
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            _config = {**DEFAULTS, **saved}
        else:
            _config = dict(DEFAULTS)
    except (json.JSONDecodeError, OSError):
        _config = dict(DEFAULTS)
    return _config


def _write_now() -> None:
    """Perform the actual disk write (called by debounce timer)."""
    with _save_lock:
        try:
            with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(_config, f, indent=2)
        except OSError:
            pass


def save_config() -> None:
    """Schedule a debounced config write.

    Rapid calls (e.g. slider drags) collapse into a single write.
    """
    global _save_timer
    with _save_lock:
        if _save_timer is not None:
            _save_timer.cancel()
        _save_timer = threading.Timer(_DEBOUNCE_SEC, _write_now)
        _save_timer.daemon = True
        _save_timer.start()


def flush() -> None:
    """Force an immediate write — call on shutdown."""
    global _save_timer
    with _save_lock:
        if _save_timer is not None:
            _save_timer.cancel()
            _save_timer = None
    _write_now()


def get(key: str, fallback=None):
    return _config.get(key, DEFAULTS.get(key, fallback))


def set(key: str, value) -> None:
    _config[key] = value
    save_config()


def get_all() -> dict:
    return dict(_config)
