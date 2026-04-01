# ============================================================
#  FreedomForge AI — core/privacy.py
#  Privacy and security — encryption, VPN, network control
# ============================================================

import os
import hashlib
import subprocess
import threading
import platform
from pathlib import Path
from typing import Callable, Optional
from core import logger

from utils.paths import KEY_FILE as _KEY_FILE_PATH, APP_ROOT as _APP_ROOT
KEY_FILE = str(_KEY_FILE_PATH)
DATA_DIR = str(_APP_ROOT)

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


def generate_key() -> bytes:
    """Generate a new Fernet encryption key."""
    if not CRYPTO_AVAILABLE:
        return b""
    return Fernet.generate_key()


def save_key(key: bytes, path: str = KEY_FILE) -> None:
    """Save encryption key to file with restricted permissions."""
    with open(path, "wb") as f:
        f.write(key)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def load_key(path: str = KEY_FILE) -> Optional[bytes]:
    """Load encryption key from file."""
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read().strip()
            return data if data else None
    except Exception:
        pass
    return None


def get_or_create_key(custom_key: str = None) -> Optional[bytes]:
    """Get existing key or create new one.

    If custom_key provided, derive a Fernet key from it using
    the same PBKDF2 path as core/encryption.py.
    """
    if not CRYPTO_AVAILABLE:
        return None

    if custom_key:
        # Delegate to encryption module for consistent derivation
        from core.encryption import _derive_key, _get_or_create_salt
        salt = _get_or_create_salt()
        return _derive_key(custom_key, salt)

    existing = load_key()
    if existing:
        return existing

    key = generate_key()
    save_key(key)
    logger.info("New encryption key generated")
    return key


def get_key_fingerprint(key: bytes) -> str:
    """Return a short human-readable fingerprint of the key."""
    h = hashlib.sha256(key).hexdigest()
    return f"{h[:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}".upper()


# ── Network kill switch ───────────────────────────────────────

_kill_active = False
_kill_lock   = threading.Lock()


def is_kill_active() -> bool:
    with _kill_lock:
        return _kill_active


def network_kill(
    on_result: Callable[[bool, str], None] = None
) -> None:
    """Cut ALL internet traffic immediately."""
    def _kill():
        global _kill_active
        system = platform.system()
        try:
            if system == "Linux":
                subprocess.run(
                    ["sudo", "iptables", "-P", "INPUT", "DROP"],
                    check=True, capture_output=True, timeout=10)
                subprocess.run(
                    ["sudo", "iptables", "-P", "OUTPUT", "DROP"],
                    check=True, capture_output=True, timeout=10)
                subprocess.run(
                    ["sudo", "iptables", "-P", "FORWARD", "DROP"],
                    check=True, capture_output=True, timeout=10)
            elif system == "Windows":
                subprocess.run(
                    ["netsh", "advfirewall", "set",
                     "allprofiles", "firewallpolicy",
                     "blockinbound,blockoutbound"],
                    check=True, capture_output=True, timeout=10)
            elif system == "Darwin":
                # Write a block-all ruleset then enable pf
                subprocess.run(
                    ["sudo", "sh", "-c",
                     'echo "block all" | pfctl -ef -'],
                    check=True, capture_output=True, timeout=10)
            else:
                if on_result:
                    on_result(False, f"Unsupported OS: {system}")
                return

            with _kill_lock:
                _kill_active = True
            logger.warning("NETWORK KILL SWITCH ACTIVATED")
            if on_result:
                on_result(True, "All network traffic blocked.")

        except Exception as e:
            logger.error(f"Kill switch failed: {e}")
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_kill, daemon=True).start()


def network_restore(
    on_result: Callable[[bool, str], None] = None
) -> None:
    """Restore normal network traffic."""
    def _restore():
        global _kill_active
        system = platform.system()
        try:
            if system == "Linux":
                subprocess.run(
                    ["sudo", "iptables", "-P", "INPUT", "ACCEPT"],
                    check=True, capture_output=True, timeout=10)
                subprocess.run(
                    ["sudo", "iptables", "-P", "OUTPUT", "ACCEPT"],
                    check=True, capture_output=True, timeout=10)
                subprocess.run(
                    ["sudo", "iptables", "-P", "FORWARD", "ACCEPT"],
                    check=True, capture_output=True, timeout=10)
                subprocess.run(
                    ["sudo", "iptables", "-F"],
                    capture_output=True, timeout=10)
            elif system == "Windows":
                # Restore Windows default: block inbound, allow outbound
                subprocess.run(
                    ["netsh", "advfirewall", "set",
                     "allprofiles", "firewallpolicy",
                     "blockinbound,allowoutbound"],
                    check=True, capture_output=True, timeout=10)
            elif system == "Darwin":
                # Flush rules and disable pf
                subprocess.run(
                    ["sudo", "pfctl", "-F", "all"],
                    capture_output=True, timeout=10)
                subprocess.run(
                    ["sudo", "pfctl", "-d"],
                    capture_output=True, timeout=10)
            else:
                if on_result:
                    on_result(False, f"Unsupported OS: {system}")
                return

            with _kill_lock:
                _kill_active = False
            logger.info("Network restored")
            if on_result:
                on_result(True, "Network traffic restored.")

        except Exception as e:
            logger.error(f"Network restore failed: {e}")
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_restore, daemon=True).start()


# ── Port monitor ──────────────────────────────────────────────

def get_active_connections() -> list:
    """Return list of active ESTABLISHED network connections."""
    try:
        import psutil
    except ImportError:
        logger.warning("psutil not installed — port monitor unavailable")
        return []

    results = []
    try:
        for c in psutil.net_connections(kind="inet"):
            if c.status != "ESTABLISHED":
                continue
            try:
                proc = (psutil.Process(c.pid).name()
                        if c.pid else "Unknown")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                proc = "Unknown"
            results.append({
                "pid":     c.pid or 0,
                "process": proc,
                "local":   (f"{c.laddr.ip}:{c.laddr.port}"
                            if c.laddr else "—"),
                "remote":  (f"{c.raddr.ip}:{c.raddr.port}"
                            if c.raddr else "—"),
                "status":  c.status,
            })
    except Exception as e:
        logger.error(f"Port monitor error: {e}")
    return results


# ── VPN helper ────────────────────────────────────────────────

VPN_TOOLS = {
    "mullvad": {
        "name":       "Mullvad VPN",
        "install":    "https://mullvad.net/download",
        "connect":    ["mullvad", "connect"],
        "disconnect": ["mullvad", "disconnect"],
        "status":     ["mullvad", "status"],
        "free":       False,
        "note":       "Best for privacy. Paid service (~$5/mo). No logs.",
    },
    "protonvpn": {
        "name":       "ProtonVPN",
        "install":    "https://protonvpn.com/download",
        "connect":    ["protonvpn-cli", "connect", "--fastest"],
        "disconnect": ["protonvpn-cli", "disconnect"],
        "status":     ["protonvpn-cli", "status"],
        "free":       True,
        "note":       "Has a free tier. Open source. No logs.",
    },
}


def detect_vpn() -> Optional[str]:
    """Return name of installed VPN tool or None."""
    for key, vpn in VPN_TOOLS.items():
        cmd = vpn["connect"][0]
        try:
            if subprocess.run(
                    ["which", cmd],
                    capture_output=True, timeout=3).returncode == 0:
                return key
        except Exception:
            pass
    return None


def vpn_connect(
    tool: str = None,
    on_result: Callable[[bool, str], None] = None,
) -> None:
    """Connect VPN in background thread."""
    if tool is None:
        tool = detect_vpn()
    if tool is None or tool not in VPN_TOOLS:
        if on_result:
            on_result(False,
                      "No VPN client found. "
                      "Install ProtonVPN or Mullvad first.")
        return

    def _connect():
        try:
            r = subprocess.run(
                VPN_TOOLS[tool]["connect"],
                capture_output=True, text=True, timeout=30)
            ok  = r.returncode == 0
            msg = r.stdout.strip() or r.stderr.strip() or "Connected"
            logger.info(f"VPN connect: {tool} — {msg}")
            if on_result:
                on_result(ok, msg)
        except Exception as e:
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_connect, daemon=True).start()


def vpn_disconnect(
    tool: str = None,
    on_result: Callable[[bool, str], None] = None,
) -> None:
    """Disconnect VPN in background thread."""
    if tool is None:
        tool = detect_vpn()
    if tool is None or tool not in VPN_TOOLS:
        if on_result:
            on_result(False, "No VPN client found.")
        return

    def _disconnect():
        try:
            r = subprocess.run(
                VPN_TOOLS[tool]["disconnect"],
                capture_output=True, text=True, timeout=15)
            ok = r.returncode == 0
            logger.info(f"VPN disconnect: {tool}")
            if on_result:
                on_result(ok, "Disconnected")
        except Exception as e:
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_disconnect, daemon=True).start()
