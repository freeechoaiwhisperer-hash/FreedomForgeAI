"""Tests for core/encryption.py — encryption system."""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from core import encryption


class TestInitEncryption:
    """Tests for init_encryption()."""

    def test_init_auto_generates_key(self, tmp_path):
        """First run: generates and saves a new key."""
        key_file = str(tmp_path / ".forge_key")
        salt_file = key_file + ".salt"

        with patch.object(encryption, 'KEY_FILE', key_file), \
             patch.object(encryption, 'SALT_FILE', salt_file), \
             patch.object(encryption, '_fernet', None), \
             patch.object(encryption, '_key_hash', None):
            result = encryption.init_encryption()
            assert result is True
            assert encryption._fernet is not None
            assert encryption._key_hash is not None
            assert os.path.exists(key_file)

    def test_init_loads_existing_key(self, tmp_path):
        """Returning user: loads key from file."""
        from cryptography.fernet import Fernet

        key_file = str(tmp_path / ".forge_key")
        salt_file = key_file + ".salt"
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)

        with patch.object(encryption, 'KEY_FILE', key_file), \
             patch.object(encryption, 'SALT_FILE', salt_file), \
             patch.object(encryption, '_fernet', None), \
             patch.object(encryption, '_key_hash', None):
            result = encryption.init_encryption()
            assert result is True
            assert encryption._fernet is not None

    def test_init_with_manual_key(self, tmp_path):
        """Power user: derives key from passphrase."""
        key_file = str(tmp_path / ".forge_key")
        salt_file = key_file + ".salt"

        with patch.object(encryption, 'KEY_FILE', key_file), \
             patch.object(encryption, 'SALT_FILE', salt_file), \
             patch.object(encryption, '_fernet', None), \
             patch.object(encryption, '_key_hash', None):
            result = encryption.init_encryption(manual_key="my-secret-passphrase")
            assert result is True
            assert encryption._fernet is not None

    def test_init_with_empty_key_file(self, tmp_path):
        """Empty key file triggers failure."""
        key_file = str(tmp_path / ".forge_key")
        salt_file = key_file + ".salt"
        with open(key_file, "wb") as f:
            f.write(b"")

        with patch.object(encryption, 'KEY_FILE', key_file), \
             patch.object(encryption, 'SALT_FILE', salt_file), \
             patch.object(encryption, '_fernet', None), \
             patch.object(encryption, '_key_hash', None):
            result = encryption.init_encryption()
            assert result is False

    def test_init_without_crypto_lib(self):
        """Without cryptography library, returns False."""
        with patch.object(encryption, 'CRYPTO_AVAILABLE', False), \
             patch.object(encryption, '_fernet', None), \
             patch.object(encryption, '_key_hash', None):
            result = encryption.init_encryption()
            assert result is False


class TestEncryptDecrypt:
    """Tests for encrypt() and decrypt()."""

    @pytest.fixture(autouse=True)
    def setup_encryption(self, tmp_path):
        """Init encryption for each test."""
        key_file = str(tmp_path / ".forge_key")
        salt_file = key_file + ".salt"

        self._orig_fernet = encryption._fernet
        self._orig_hash = encryption._key_hash

        with patch.object(encryption, 'KEY_FILE', key_file), \
             patch.object(encryption, 'SALT_FILE', salt_file):
            encryption._fernet = None
            encryption._key_hash = None
            encryption.init_encryption()

        yield

        encryption._fernet = self._orig_fernet
        encryption._key_hash = self._orig_hash

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted data can be decrypted back to original."""
        original = "Hello, World! 🔒"
        encrypted = encryption.encrypt(original)
        assert encrypted is not None
        assert encrypted != original
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_returns_none_when_disabled(self):
        """encrypt() returns None when encryption is disabled."""
        encryption._fernet = None
        assert encryption.encrypt("test") is None

    def test_decrypt_returns_none_when_disabled(self):
        """decrypt() returns None when encryption is disabled."""
        encryption._fernet = None
        assert encryption.decrypt("test") is None

    def test_decrypt_invalid_data(self):
        """decrypt() returns None for invalid ciphertext."""
        result = encryption.decrypt("not-valid-ciphertext!!!")
        assert result is None

    def test_encrypt_empty_string(self):
        """Encrypting empty string should work."""
        encrypted = encryption.encrypt("")
        assert encrypted is not None
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == ""

    def test_encrypt_unicode(self):
        """Unicode strings encrypt/decrypt correctly."""
        original = "日本語テスト 🇯🇵 Ελληνικά"
        encrypted = encryption.encrypt(original)
        assert encrypted is not None
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original


class TestEncryptDecryptDict:
    """Tests for encrypt_dict() and decrypt_dict()."""

    @pytest.fixture(autouse=True)
    def setup_encryption(self, tmp_path):
        key_file = str(tmp_path / ".forge_key")
        salt_file = key_file + ".salt"

        self._orig_fernet = encryption._fernet
        self._orig_hash = encryption._key_hash

        with patch.object(encryption, 'KEY_FILE', key_file), \
             patch.object(encryption, 'SALT_FILE', salt_file):
            encryption._fernet = None
            encryption._key_hash = None
            encryption.init_encryption()

        yield

        encryption._fernet = self._orig_fernet
        encryption._key_hash = self._orig_hash

    def test_dict_roundtrip(self):
        """Dictionary encrypts/decrypts to same value."""
        original = {"name": "test", "value": 42, "nested": {"key": "val"}}
        encrypted = encryption.encrypt_dict(original)
        assert encrypted is not None
        decrypted = encryption.decrypt_dict(encrypted)
        assert decrypted == original

    def test_decrypt_dict_invalid_json(self):
        """decrypt_dict returns None for non-JSON plaintext."""
        encrypted = encryption.encrypt("not-json")
        assert encrypted is not None
        result = encryption.decrypt_dict(encrypted)
        assert result is None


class TestEncryptDecryptFile:
    """Tests for encrypt_file() and decrypt_file()."""

    @pytest.fixture(autouse=True)
    def setup_encryption(self, tmp_path):
        key_file = str(tmp_path / ".forge_key")
        salt_file = key_file + ".salt"

        self._orig_fernet = encryption._fernet
        self._orig_hash = encryption._key_hash

        with patch.object(encryption, 'KEY_FILE', key_file), \
             patch.object(encryption, 'SALT_FILE', salt_file):
            encryption._fernet = None
            encryption._key_hash = None
            encryption.init_encryption()

        yield

        encryption._fernet = self._orig_fernet
        encryption._key_hash = self._orig_hash

    def test_file_encrypt_decrypt_roundtrip(self, tmp_path):
        """File encrypts in-place and can be decrypted."""
        test_file = tmp_path / "secret.txt"
        test_file.write_bytes(b"Top secret data!")

        assert encryption.encrypt_file(str(test_file)) is True
        # File content should be changed
        assert test_file.read_bytes() != b"Top secret data!"
        # Decrypt should return original
        decrypted = encryption.decrypt_file(str(test_file))
        assert decrypted == b"Top secret data!"

    def test_encrypt_file_disabled(self):
        """encrypt_file returns False when disabled."""
        encryption._fernet = None
        assert encryption.encrypt_file("/nonexistent") is False

    def test_decrypt_file_disabled(self):
        """decrypt_file returns None when disabled."""
        encryption._fernet = None
        assert encryption.decrypt_file("/nonexistent") is None


class TestHelpers:
    """Tests for helper functions."""

    def test_is_enabled_false_by_default(self):
        orig = encryption._fernet
        try:
            encryption._fernet = None
            assert encryption.is_enabled() is False
        finally:
            encryption._fernet = orig

    def test_is_enabled_true_after_init(self, tmp_path):
        key_file = str(tmp_path / ".forge_key")
        salt_file = key_file + ".salt"

        orig_fernet = encryption._fernet
        orig_hash = encryption._key_hash

        try:
            with patch.object(encryption, 'KEY_FILE', key_file), \
                 patch.object(encryption, 'SALT_FILE', salt_file):
                encryption._fernet = None
                encryption._key_hash = None
                encryption.init_encryption()
                assert encryption.is_enabled() is True
        finally:
            encryption._fernet = orig_fernet
            encryption._key_hash = orig_hash

    def test_get_key_fingerprint(self, tmp_path):
        key_file = str(tmp_path / ".forge_key")
        salt_file = key_file + ".salt"

        orig_fernet = encryption._fernet
        orig_hash = encryption._key_hash

        try:
            with patch.object(encryption, 'KEY_FILE', key_file), \
                 patch.object(encryption, 'SALT_FILE', salt_file):
                encryption._fernet = None
                encryption._key_hash = None
                encryption.init_encryption()
                fp = encryption.get_key_fingerprint()
                assert fp is not None
                assert len(fp) == 16
                assert all(c in "0123456789abcdef" for c in fp)
        finally:
            encryption._fernet = orig_fernet
            encryption._key_hash = orig_hash


class TestSaltManagement:
    """Tests for salt creation and loading."""

    def test_creates_new_salt(self, tmp_path):
        salt_file = str(tmp_path / "test.salt")
        with patch.object(encryption, 'SALT_FILE', salt_file):
            salt = encryption._get_or_create_salt()
            assert len(salt) == 32
            assert os.path.exists(salt_file)

    def test_loads_existing_salt(self, tmp_path):
        salt_file = str(tmp_path / "test.salt")
        original_salt = os.urandom(32)
        with open(salt_file, "wb") as f:
            f.write(original_salt)

        with patch.object(encryption, 'SALT_FILE', salt_file):
            salt = encryption._get_or_create_salt()
            assert salt == original_salt

    def test_regenerates_short_salt(self, tmp_path):
        """Salt shorter than 16 bytes is regenerated."""
        salt_file = str(tmp_path / "test.salt")
        with open(salt_file, "wb") as f:
            f.write(b"short")

        with patch.object(encryption, 'SALT_FILE', salt_file):
            salt = encryption._get_or_create_salt()
            assert len(salt) == 32


class TestDeriveKey:
    """Tests for _derive_key()."""

    def test_same_password_same_salt_same_key(self):
        salt = os.urandom(32)
        key1 = encryption._derive_key("password123", salt)
        key2 = encryption._derive_key("password123", salt)
        assert key1 == key2

    def test_different_password_different_key(self):
        salt = os.urandom(32)
        key1 = encryption._derive_key("password1", salt)
        key2 = encryption._derive_key("password2", salt)
        assert key1 != key2

    def test_different_salt_different_key(self):
        key1 = encryption._derive_key("password", os.urandom(32))
        key2 = encryption._derive_key("password", os.urandom(32))
        assert key1 != key2
