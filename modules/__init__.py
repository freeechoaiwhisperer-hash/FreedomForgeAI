# ============================================================
#  FreedomForge AI — modules/__init__.py
#  Module registry and message router
# ============================================================

import re
from typing import Optional, Callable

# Module trigger patterns
_TRIGGERS = {
    "video": [
        r"\bmake\s+(a\s+)?video\b",
        r"\bgenerate\s+(a\s+)?video\b",
        r"\bcreate\s+(a\s+)?video\b",
        r"\bvideo\s+of\b",
        r"^/video\b",
    ],
    "image": [
        r"\bmake\s+(a[n]?\s+)?image\b",
        r"\bgenerate\s+(a[n]?\s+)?image\b",
        r"\bdraw\b",
        r"\bpaint\b",
        r"^/image\b",
    ],
    "agent": [
        r"^/run\b",
        r"^/exec\b",
        r"\brun\s+this\s+command\b",
        r"\bexecute\s+on\s+my\s+computer\b",
    ],
}

_registry: dict = {}


def register(name: str, module) -> None:
    _registry[name] = module


def get(name: str):
    return _registry.get(name)


def route(message: str) -> Optional[str]:
    """
    Check if a message should be routed to a module.
    Returns module name string or None if regular chat.
    """
    msg_lower = message.lower()
    for module_name, patterns in _TRIGGERS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return module_name
    return None


def handle(
    module_name: str,
    message: str,
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
) -> bool:
    """
    Route a message to the appropriate module.
    Returns True if handled, False if module not available.
    """
    module = _registry.get(module_name)
    if module is None:
        on_error(
            f"The {module_name} module is not available yet. "
            f"It's coming in a future update!"
        )
        return False
    try:
        module.handle(message, on_result, on_error)
        return True
    except Exception as e:
        on_error(f"Module error: {e}")
        return False
