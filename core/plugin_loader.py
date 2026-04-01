# ============================================================
#  FreedomForge AI — core/plugin_loader.py
#  Scans plugins/ folder and auto-loads anything it finds
#  Each plugin needs: TRIGGERS list, handle() function
#  DESCRIPTION string is optional but recommended
# ============================================================

import importlib.util
import os
from pathlib import Path
from typing import Optional
from core import logger

_plugins: dict = {}
_plugins_dir: str = ""


def load_plugins(plugins_dir: str = "plugins") -> None:
    """Scan plugins folder and load all valid plugins."""
    global _plugins, _plugins_dir
    _plugins = {}
    _plugins_dir = plugins_dir

    path = Path(plugins_dir)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created plugins folder: {plugins_dir}")
        return

    for py_file in sorted(path.glob("*.py")):
        _load_one(py_file)

    logger.info(f"Plugins loaded: {len(_plugins)} — {list(_plugins.keys())}")


def _load_one(py_file: Path) -> None:
    mod_name = py_file.stem
    try:
        spec = importlib.util.spec_from_file_location(mod_name, py_file)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        triggers = getattr(mod, "TRIGGERS", [])
        handler  = getattr(mod, "handle", None)
        desc     = getattr(mod, "DESCRIPTION", "No description")

        if not triggers or not callable(handler):
            logger.debug(f"Plugin skipped (missing TRIGGERS or handle): {mod_name}")
            return

        _plugins[mod_name] = {
            "triggers":    [t.lower() for t in triggers],
            "handler":     handler,
            "description": desc,
        }
        logger.info(f"Plugin loaded: {mod_name} — {desc}")

    except Exception as e:
        logger.error(f"Plugin failed to load ({mod_name}): {e}")


def route(message: str) -> Optional[str]:
    """Check message against all plugin triggers. Returns result or None."""
    if not message or not isinstance(message, str):
        return None
    msg_lower = message.lower().strip()
    for plugin in _plugins.values():
        for trigger in plugin["triggers"]:
            if msg_lower.startswith(trigger):
                try:
                    return plugin["handler"](message)
                except Exception as e:
                    logger.error(f"Plugin handler error: {e}")
                    return f"❌  Plugin error: {e}"
    return None


def list_plugins() -> list:
    """Return list of loaded plugins with metadata."""
    return [
        {
            "name":        name,
            "description": p["description"],
            "triggers":    p["triggers"],
        }
        for name, p in _plugins.items()
    ]


def reload_plugins() -> None:
    """Reload all plugins from disk."""
    load_plugins(_plugins_dir or "plugins")
