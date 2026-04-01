# ============================================================
#  FreedomForge AI — core/crash_reporter.py
#  Crash reporting — local logs, optional anonymous send
# ============================================================

import os
import sys
import json
import hashlib
import platform
import traceback
import threading
from datetime import datetime, timezone
from typing import Callable, Optional

from utils.paths import CRASH_DIR as _CRASH_DIR_PATH
CRASH_DIR = str(_CRASH_DIR_PATH)
MAX_REPORTS     = 20
REPORT_ENDPOINT = "https://freedomforge.dev/crash"  # placeholder


def _system_info() -> dict:
    try:
        import psutil
        return {
            "os":        platform.system(),
            "os_ver":    platform.version()[:60],
            "python":    sys.version[:20],
            "ram_gb":    round(psutil.virtual_memory().total / (1024**3)),
            "cpu_count": os.cpu_count(),
        }
    except ImportError:
        return {"os": platform.system(), "python": sys.version[:20]}
    except Exception:
        return {"os": platform.system()}


def capture(exc: Exception, context: str = "",
            on_ready: Callable = None) -> str:
    os.makedirs(CRASH_DIR, exist_ok=True)
    ts        = datetime.now(timezone.utc).isoformat()
    report_id = hashlib.sha256(
        f"{ts}{type(exc).__name__}".encode()
    ).hexdigest()[:12]

    report = {
        "id":        report_id,
        "timestamp": ts,
        "version":   "0.1.0-alpha",
        "context":   context,
        "error":     type(exc).__name__,
        "message":   str(exc)[:500],
        "traceback": traceback.format_exc()[:3000],
        "system":    _system_info(),
    }

    path = os.path.join(CRASH_DIR, f"crash_{report_id}.json")
    try:
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
    except Exception:
        pass

    _prune()
    if on_ready:
        on_ready(report_id, path)
    return report_id


def send_anonymous(report_path: str,
                   on_result: Callable = None) -> None:
    def _send():
        try:
            import requests
            with open(report_path) as f:
                r = json.load(f)
            safe = {k: r[k] for k in
                    ["id","timestamp","version","error",
                     "message","traceback","system"] if k in r}
            resp = requests.post(REPORT_ENDPOINT, json=safe, timeout=10)
            ok   = resp.status_code == 200
            if on_result:
                on_result(ok, "Sent. Thank you!" if ok else f"Error {resp.status_code}")
        except Exception as e:
            if on_result:
                on_result(False, str(e))
    threading.Thread(target=_send, daemon=True).start()


def get_recent() -> list:
    if not os.path.exists(CRASH_DIR):
        return []
    reports = []
    for fname in sorted(os.listdir(CRASH_DIR), reverse=True)[:10]:
        if fname.endswith(".json"):
            try:
                with open(os.path.join(CRASH_DIR, fname)) as f:
                    r = json.load(f)
                reports.append({
                    "id":      r.get("id","?"),
                    "ts":      r.get("timestamp","?"),
                    "error":   r.get("error","?"),
                    "message": r.get("message","?")[:80],
                    "path":    os.path.join(CRASH_DIR, fname),
                })
            except Exception:
                pass
    return reports


def _prune():
    if not os.path.exists(CRASH_DIR):
        return
    files = sorted([
        os.path.join(CRASH_DIR, f)
        for f in os.listdir(CRASH_DIR) if f.endswith(".json")
    ])
    while len(files) > MAX_REPORTS:
        try:
            os.remove(files.pop(0))
        except Exception:
            break


def install_handler(app=None):
    def _handler(exc_type, exc_val, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_val, exc_tb)
            return
        rid = capture(exc_val, "Unhandled exception")
        if app:
            try:
                app.after(0, lambda: _crash_dialog(app, rid, exc_val))
            except Exception:
                pass
    sys.excepthook = _handler


def _crash_dialog(app, report_id: str, exc: Exception):
    try:
        import customtkinter as ctk
        win = ctk.CTkToplevel(app)
        win.title("FreedomForge AI — Crash")
        win.geometry("520x290")
        win.resizable(False, False)
        win.transient(app)
        win.lift()

        ctk.CTkLabel(win, text="⚠️  Something crashed",
                     font=("Arial", 16, "bold"),
                     text_color="#ffaa00").pack(pady=(22,4))
        ctk.CTkLabel(win,
                     text=f"{type(exc).__name__}: {str(exc)[:100]}",
                     font=("Arial", 11), text_color="#888888",
                     wraplength=480).pack(padx=20)
        ctk.CTkLabel(win,
                     text=(
                         "A crash report was saved locally.\n"
                         "Send it anonymously to help fix this bug?\n"
                         "No personal information is included."
                     ),
                     font=("Arial", 12), text_color="#cccccc",
                     justify="center").pack(pady=14, padx=20)
        ctk.CTkLabel(win, text=f"Report ID: {report_id}",
                     font=("Arial", 10),
                     text_color="#444444").pack()

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(pady=14)

        reports   = get_recent()
        rpath     = reports[0]["path"] if reports else None

        def _send():
            if rpath:
                send_anonymous(rpath)
            win.destroy()

        ctk.CTkButton(btns, text="Send Anonymous Report",
                      width=210, height=38,
                      fg_color="#1a4a7a", hover_color="#0d3360",
                      command=_send).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="No Thanks",
                      width=120, height=38,
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      command=win.destroy).pack(side="left", padx=8)
    except Exception:
        pass
