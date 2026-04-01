# ============================================================
#  FreedomForge AI — core/encryption.py
#  Local data encryption — auto key for everyone,
#  manual key option for power users.
#  Nothing leaves your machine. Ever.
# ============================================================

import os
import json
import base64
import hashlib
import secrets
from typing import Optional
from core import logger

from utils.paths import KEY_FILE as _KEY_FILE_PATH
KEY_FILE  = str(_KEY_FILE_PATH)
SALT_FILE = KEY_FILE + ".salt"

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

_fernet = None
_key_hash: Optional[str] = None


# ── Key management ───────────────────────────────────────────

def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _get_or_create_salt() -> bytes:
    """Load existing salt or create a new random one.

    Each installation gets its own unique salt, stored next to
    the key file.  This prevents identical passphrases from
    producing identical keys across machines.
    """
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, "rb") as f:
            salt = f.read()
        if len(salt) >= 16:
            return salt

    salt = secrets.token_bytes(32)
    with open(SALT_FILE, "wb") as f:
        f.write(salt)
    try:
        os.chmod(SALT_FILE, 0o600)
    except OSError:
        pass
    return salt


def init_encryption(manual_key: Optional[str] = None) -> bool:
    """Initialise encryption.

    - manual_key provided  → derive key from passphrase (power user)
    - .forge_key exists    → load it (returning user)
    - otherwise            → generate + save new key (first run)

    Returns True when encryption is ready.
    """
    global _fernet, _key_hash

    if not CRYPTO_AVAILABLE:
        logger.warning(
            "cryptography not installed — encryption disabled. "
            "Run: pip install cryptography")
        return False

    try:
        if manual_key:
            salt = _get_or_create_salt()
            key  = _derive_key(manual_key, salt)
        elif os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                key = f.read().strip()
            if not key:
                raise ValueError("Key file is empty")
        else:
            key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as f:
                f.write(key)
            try:
                os.chmod(KEY_FILE, 0o600)
            except OSError:
                pass
            logger.info("Encryption key generated and saved")

        _fernet   = Fernet(key)
        _key_hash = hashlib.sha256(key).hexdigest()[:16]
        logger.info(
            f"Encryption initialised (key fingerprint: {_key_hash})")
        return True

    except Exception as e:
        logger.error(f"Encryption init failed: {e}")
        _fernet   = None
        _key_hash = None
        return False


def get_key_fingerprint() -> Optional[str]:
    """Return first 16 hex chars of the key hash for display."""
    return _key_hash


def is_enabled() -> bool:
    """True when encryption is initialised and ready."""
    return _fernet is not None


# ── Encrypt / Decrypt ────────────────────────────────────────

def encrypt(data: str) -> Optional[str]:
    """Encrypt a string.  Returns ciphertext or None on failure.

    Never silently returns plaintext — callers must check for None.
    """
    if not _fernet:
        logger.warning("encrypt() called but encryption is disabled")
        return None
    try:
        return _fernet.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Encrypt error: {e}")
        return None


def decrypt(data: str) -> Optional[str]:
    """Decrypt a string.  Returns plaintext or None on failure."""
    if not _fernet:
        logger.warning("decrypt() called but encryption is disabled")
        return None
    try:
        return _fernet.decrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Decrypt error: {e}")
        return None


def encrypt_file(path: str) -> bool:
    """Encrypt a file in-place.  Returns False on any failure."""
    if not _fernet:
        return False
    try:
        with open(path, "rb") as f:
            data = f.read()
        encrypted = _fernet.encrypt(data)
        with open(path, "wb") as f:
            f.write(encrypted)
        return True
    except Exception as e:
        logger.error(f"File encrypt error {path}: {e}")
        return False


def decrypt_file(path: str) -> Optional[bytes]:
    """Decrypt a file and return contents (file is not modified)."""
    if not _fernet:
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
        return _fernet.decrypt(data)
    except Exception as e:
        logger.error(f"File decrypt error {path}: {e}")
        return None


def encrypt_dict(d: dict) -> Optional[str]:
    """Encrypt a dictionary to a string, or None on failure."""
    return encrypt(json.dumps(d, separators=(",", ":")))


def decrypt_dict(s: str) -> Optional[dict]:
    """Decrypt a string back to a dictionary, or None on failure."""
    plaintext = decrypt(s)
    if plaintext is None:
        return None
    try:
        return json.loads(plaintext)
    except (json.JSONDecodeError, TypeError):
        return None
