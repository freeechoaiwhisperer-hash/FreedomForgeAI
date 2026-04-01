# ============================================================
#  FreedomForge AI — modules/agent.py
#  Computer control / agent module
# ============================================================

import subprocess
import threading
import shlex
from typing import Callable

MODULE_NAME = "agent"

# Commands that are always blocked regardless of agent mode
BLOCKED_COMMANDS = [
    "rm -rf /",
    "mkfs",
    "dd if=",
    ":(){:|:&};:",
    "chmod -R 777 /",
    "wget http",
    "curl http",
]

_agent_enabled = False


def set_enabled(enabled: bool) -> None:
    global _agent_enabled
    _agent_enabled = enabled


def is_enabled() -> bool:
    return _agent_enabled


def is_safe_command(command: str) -> tuple[bool, str]:
    """Check if a command is safe to run. Returns (safe, reason)."""
    cmd_lower = command.lower().strip()

    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return False, f"Command contains blocked pattern: {blocked}"

    if cmd_lower.startswith("sudo rm"):
        return False, "Recursive deletion with sudo is blocked"

    return True, ""


def run_command(
    command:   str,
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
) -> None:
    """Execute a shell command safely in a background thread."""

    def _run():
        if not _agent_enabled:
            on_error(
                "Agent Mode is OFF. Toggle it on in the top bar "
                "to allow command execution."
            )
            return

        safe, reason = is_safe_command(command)
        if not safe:
            on_error(f"Command blocked for safety: {reason}")
            return

        try:
            args = shlex.split(command)
            result = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout.strip() or result.stderr.strip() or "(no output)"
            on_result(
                f"```\n$ {command}\n{output}\n```\n"
                f"Exit code: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            on_error("Command timed out after 30 seconds")
        except Exception as e:
            on_error(f"Command failed: {e}")

    threading.Thread(target=_run, daemon=True).start()


def handle(
    message:   str,
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
) -> None:
    """Entry point called by module router."""
    command = message
    for prefix in ["/run ", "/exec "]:
        if message.lower().startswith(prefix):
            command = message[len(prefix):].strip()
            break

    if not command:
        on_error("Please provide a command to run.")
        return

    run_command(command, on_result, on_error)
