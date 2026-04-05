# ============================================================
#  FreedomForge AI — modules/agent.py
#  Clean Claw — safe computer control, user confirmation
# ============================================================

import subprocess
import threading
import shlex
import logging
from typing import Callable
from core.metadata_stamp import stamp_code   # keep if you have it, or remove

MODULE_NAME = "agent"

# Strong but reasonable block list
DANGEROUS_PATTERNS = [
    r"rm\s+-rf", r"rm\s+-r\s+/", r"mkfs", r"dd\s+if=", r":\(\)\{\:\|\:&\};:",
    r"chmod\s+-R\s+777", r"> /dev/", r"format", r"diskpart",
    r"sudo\s+rm", r"sudo\s+dd", r"wget\s+http", r"curl\s+http",
    r"python\s+-c", r"python3\s+-c", r"bash\s+-c", r"nc\s+", r"netcat",
    r"telnet", r"shred", r"wipe", r"miner", r"crypto"
]

_agent_enabled = False
_logger = logging.getLogger("agent")

def set_enabled(enabled: bool) -> None:
    global _agent_enabled
    _agent_enabled = enabled

def is_enabled() -> bool:
    return _agent_enabled

def is_safe_command(command: str) -> tuple[bool, str]:
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        import re
        if re.search(pattern, cmd_lower):
            return False, f"Blocked dangerous pattern: {pattern}"
    if len(command) > 800:
        return False, "Command too long"
    return True, ""

def run_command(
    command: str,
    on_result: Callable[[str], None],
    on_error: Callable[[str], None],
) -> None:
    def _run():
        if not _agent_enabled:
            on_error("Agent Mode is OFF. Toggle it on first.")
            return

        safe, reason = is_safe_command(command)
        if not safe:
            on_error(f"❌ Command blocked: {reason}")
            return

        # User confirmation (simple for now - we can make GUI popup later)
        # For safety we ask here. In final version we'll use a real dialog.
        print(f"\n[CLAW] Run this command?\n$ {command}\nType 'yes' to run, anything else to cancel:")
        user_confirm = input().strip().lower()
        if user_confirm != "yes":
            on_error("Command cancelled by user.")
            return

        # Stamp if you want to keep it
        stamped = stamp_code(command, "shell") if 'stamp_code' in globals() else command

        try:
            args = shlex.split(stamped)
            result = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=25,
            )
            output = result.stdout.strip() or result.stderr.strip() or "(no output)"
            
            _logger.info(f"Claw executed: {command} | exit {result.returncode}")
            
            on_result(
                f"```\n$ {command}\n{output}\n```\n"
                f"Exit code: {result.returncode}\n"
                f"✅ Command completed safely."
            )
        except subprocess.TimeoutExpired:
            on_error("Command timed out (25s)")
        except Exception as e:
            on_error(f"Execution failed: {e}")

    threading.Thread(target=_run, daemon=True).start()


def handle(
    message: str,
    on_result: Callable[[str], None],
    on_error: Callable[[str], None],
) -> None:
    command = message
    for prefix in ["/run ", "/exec "]:
        if message.lower().startswith(prefix):
            command = message[len(prefix):].strip()
            break

    if not command:
        on_error("Provide a command to run.")
        return

    run_command(command, on_result, on_error)
