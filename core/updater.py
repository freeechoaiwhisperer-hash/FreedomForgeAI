# ============================================================
#  FreedomForge AI — core/updater.py
#  Check GitHub releases for updates — silent background check
# ============================================================

import threading
from typing import Dict, Callable, Optional


def _fetch_release(current_version: str) -> Optional[Dict]:
    """Fetch latest release info from GitHub API."""
    try:
        import requests
    except ImportError:
        return None

    try:
        resp = requests.get(
            "https://api.github.com/repos/"
            "YOURUSERNAME/FreedomForgeAI/releases/latest",
            timeout=5,
        )
        resp.raise_for_status()
        data   = resp.json()
        latest = data.get("tag_name", "").lstrip("v")
        if latest and latest != current_version:
            return {
                "update_available": True,
                "latest_version":   latest,
                "download_url":     data.get("html_url", ""),
                "release_notes":    data.get("body", "")[:300],
            }
    except Exception:
        pass
    return None


def check_for_update(
    current_version: str,
    on_result: Callable[[Dict], None],
) -> None:
    """Run update check in background thread."""
    def _check():
        info = _fetch_release(current_version)
        if info is None:
            info = {
                "update_available": False,
                "latest_version":   current_version,
                "download_url":     "",
                "release_notes":    "",
            }
        on_result(info)

    threading.Thread(target=_check, daemon=True).start()
