# ============================================================
#  FreedomForge AI — core/metadata_stamp.py
#  Silent metadata stamping for AI-generated code
#
#  When the AI generates code during agent or red team mode,
#  a silent signature is embedded. This creates an audit trail
#  that helps protect legitimate users and deters misuse.
#
#  This is disclosed in the Terms of Service.
#  Legitimate red teamers benefit from this — it proves
#  authorized testing. Bad actors leave their own evidence.
# ============================================================

import hashlib
import datetime
import secrets
import os
from typing import Optional

# Session ID — unique per app launch, never stored permanently
_SESSION_ID = secrets.token_hex(8)
_LAUNCH_TIME = datetime.datetime.utcnow().isoformat()


def _get_stamp_comment(language: str = "python") -> str:
    """
    Generate a silent metadata comment for the given language.
    Looks like a normal auto-generated comment.
    """
    ts       = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    sig      = hashlib.sha256(
        f"{_SESSION_ID}{ts}".encode()
    ).hexdigest()[:16]

    stamps = {
        "python": (
            f"# Generated: {ts} | "
            f"Ref: {sig} | "
            f"FFA-v1"
        ),
        "javascript": (
            f"// Generated: {ts} | "
            f"Ref: {sig} | "
            f"FFA-v1"
        ),
        "bash": (
            f"# Generated: {ts} | "
            f"Ref: {sig} | "
            f"FFA-v1"
        ),
        "powershell": (
            f"# Generated: {ts} | "
            f"Ref: {sig} | "
            f"FFA-v1"
        ),
        "c": (
            f"/* Generated: {ts} | "
            f"Ref: {sig} | "
            f"FFA-v1 */"
        ),
        "cpp": (
            f"// Generated: {ts} | "
            f"Ref: {sig} | "
            f"FFA-v1"
        ),
        "rust": (
            f"// Generated: {ts} | "
            f"Ref: {sig} | "
            f"FFA-v1"
        ),
        "go": (
            f"// Generated: {ts} | "
            f"Ref: {sig} | "
            f"FFA-v1"
        ),
    }
    return stamps.get(language, stamps["python"])


def _detect_language(code: str) -> str:
    """Detect programming language from code content."""
    code_lower = code.lower()
    if "#!/bin/bash" in code or "#!/bin/sh" in code:
        return "bash"
    if "#!/usr/bin/env python" in code or "def " in code or "import " in code:
        return "python"
    if "function " in code and ("{" in code or "=>" in code):
        return "javascript"
    if "#include" in code and "int main" in code:
        return "c"
    if "fn main()" in code or "let mut" in code:
        return "rust"
    if "package main" in code or "func main()" in code:
        return "go"
    if "public static void main" in code:
        return "java"
    if code.strip().startswith("#") and "param" in code_lower:
        return "powershell"
    return "python"


def stamp_code(code: str, language: Optional[str] = None) -> str:
    """
    Embed a silent metadata stamp into generated code.
    The stamp looks like a normal auto-generated comment.
    """
    if not code or len(code.strip()) < 10:
        return code

    lang    = language or _detect_language(code)
    comment = _get_stamp_comment(lang)
    lines   = code.split("\n")

    # Insert after shebang if present, otherwise at top
    if lines and lines[0].startswith("#!"):
        lines.insert(1, comment)
        lines.insert(2, "")
    else:
        lines.insert(0, comment)
        lines.insert(1, "")

    return "\n".join(lines)


def should_stamp(message: str) -> bool:
    """
    Determine if a message response should receive a stamp.
    Only stamps when it looks like actual executable code.
    """
    code_indicators = [
        "```python", "```bash", "```javascript",
        "```js", "```sh", "```c", "```cpp",
        "```rust", "```go", "```powershell",
        "#!/", "def ", "function ", "import ",
        "public class", "fn main",
    ]
    msg_lower = message.lower()
    return any(ind.lower() in msg_lower for ind in code_indicators)


def stamp_response(response: str) -> str:
    """
    Scan a full AI response and stamp any code blocks found.
    Leaves non-code content untouched.
    """
    if not should_stamp(response):
        return response

    import re
    # Find fenced code blocks
    pattern = r'(```(\w+)?\n)(.*?)(```)'

    def _stamp_block(match):
        fence_open = match.group(1)
        lang_hint  = match.group(2) or ""
        code       = match.group(3)
        fence_close = match.group(4)
        stamped    = stamp_code(code, lang_hint.lower() or None)
        return f"{fence_open}{stamped}{fence_close}"

    return re.sub(pattern, _stamp_block, response, flags=re.DOTALL)


def get_session_id() -> str:
    return _SESSION_ID


def get_launch_time() -> str:
    return _LAUNCH_TIME
