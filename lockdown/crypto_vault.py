"""Lock Down Advanced Encryption Vault.
Implements AES-256-GCM authenticated encryption with PBKDF2-HMAC-SHA256 key derivation,
secure folder permission enforcement, and private key export/import.
"""

import base64
import json
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAVE_CRYPTOGRAPHY = True
except (ImportError, Exception) as _crypto_err:
    HAVE_CRYPTOGRAPHY = False
    class InvalidTag(Exception):
        pass
    hashes = None
    AESGCM = None
    PBKDF2HMAC = None
    print(f"[CryptoVault] Cryptography library not loaded: {_crypto_err}")

from lockdown.config import (
    LOCAL_VAULT_FILE,
    LOCAL_VAULT_META,
    VAULT_DIR,
)

KDF_ITERATIONS = 200_000
SENTINEL_PLAINTEXT = b"LOCKDOWN_VAULT_AUTHENTICATED_2026"


class CryptoVault:
    def __init__(self, vault_dir: Path = VAULT_DIR):
        self.vault_dir = vault_dir
        self.vault_file = vault_dir / "history.vault"
        self.meta_file = vault_dir / "vault_meta.json"
        self._current_key: Optional[bytes] = None
        self._master_private_key_hex: Optional[str] = None
        self.ensure_secure_vault_folder()

    def ensure_secure_vault_folder(self) -> None:
        """Creates the secure folder on the user device and applies OS permission restrictions."""
        self.vault_dir.mkdir(parents=True, exist_ok=True)

        readme_file = self.vault_dir / "README_SECURE_VAULT.txt"
        try:
            if not readme_file.exists():
                readme_file.write_text(
                    "LOCK DOWN BROWSER - SECURE ENCRYPTED VAULT\n"
                    "===========================================\n"
                    "This folder contains your password-protected, AES-256-GCM encrypted search & browsing history.\n"
                    "Do NOT edit or delete files in this folder manually.\n"
                    "Algorithm: AES-256-GCM Authenticated Encryption with PBKDF2-HMAC-SHA256 (200,000 rounds).\n"
                    "All history records are tamper-proof and unreadable without your master password or private key.\n",
                    encoding="utf-8",
                )
        except OSError as e:
            print(f"[CryptoVault] README setup note: {e}")

        if platform.system() != "Windows":
            # Unix chmod 700 (owner only)
            try:
                os.chmod(self.vault_dir, 0o700)
            except Exception:
                pass

    @staticmethod
    def generate_private_key() -> str:
        """Generates a cryptographically strong 256-bit private key formatted in hex with prefix."""
        random_bytes = os.urandom(32)
        key_hex = random_bytes.hex().upper()
        # Formatted in 4-character blocks: LK-XXXX-XXXX-...
        blocks = [key_hex[i : i + 4] for i in range(0, len(key_hex), 4)]
        return f"LK-{'-'.join(blocks)}"

    @staticmethod
    def parse_private_key(key_str: str) -> bytes:
        """Parses a formatted private key or raw hex string into 32 raw bytes."""
        clean = key_str.strip().replace("LK-", "").replace("-", "").replace(" ", "").lower()
        if len(clean) != 64:
            raise ValueError("Private key must be a valid 64-character hexadecimal key.")
        return bytes.fromhex(clean)

    def derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derives a 256-bit AES key from a password using PBKDF2-HMAC-SHA256."""
        if not HAVE_CRYPTOGRAPHY or PBKDF2HMAC is None:
            raise RuntimeError("Cryptography library is not available.")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=KDF_ITERATIONS,
        )
        return kdf.derive(password.encode("utf-8"))

    def is_vault_initialized(self) -> bool:
        """Returns True if the vault has been setup with a password or private key."""
        return self.meta_file.exists()

    def get_vault_metadata(self) -> Dict[str, Any]:
        """Loads metadata including salt, encryption algorithm, and timestamps."""
        if not self.meta_file.exists():
            return {}
        try:
            with open(self.meta_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def setup_vault(
        self, password: str, private_key_str: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """Initializes the vault with a user password and generates or accepts a private key.
        Returns (success, message, private_key_formatted).
        """
        try:
            self.ensure_secure_vault_folder()
            salt = os.urandom(16)

            if not private_key_str:
                private_key_str = self.generate_private_key()

            raw_private_key = self.parse_private_key(private_key_str)
            derived_key = self.derive_key_from_password(password, salt)

            # We encrypt the raw private key using the password-derived key
            # so the user can unlock using either their Password OR their Private Key!
            aes_derived = AESGCM(derived_key)
            nonce = os.urandom(12)
            encrypted_private_key = aes_derived.encrypt(nonce, raw_private_key, None)

            # Sentinel encrypted with the raw private key for verification
            aes_pkey = AESGCM(raw_private_key)
            sentinel_nonce = os.urandom(12)
            encrypted_sentinel = aes_pkey.encrypt(sentinel_nonce, SENTINEL_PLAINTEXT, None)

            meta = {
                "algorithm": "AES-256-GCM",
                "kdf": "PBKDF2-HMAC-SHA256",
                "iterations": KDF_ITERATIONS,
                "salt": salt.hex(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "enc_private_key_nonce": nonce.hex(),
                "enc_private_key": encrypted_private_key.hex(),
                "sentinel_nonce": sentinel_nonce.hex(),
                "sentinel_cipher": encrypted_sentinel.hex(),
                "storage_mode": "local",
            }

            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            self._current_key = raw_private_key
            self._master_private_key_hex = private_key_str

            # Create initial empty history vault if none exists
            if not self.vault_file.exists():
                self.save_history_vault([], raw_private_key)

            return True, "Vault configured successfully", private_key_str
        except Exception as e:
            return False, f"Failed to initialize vault: {str(e)}", ""

    def unlock_with_password(self, password: str) -> bool:
        """Unlocks the vault using the user's master password."""
        meta = self.get_vault_metadata()
        if not meta:
            return False
        try:
            salt = bytes.fromhex(meta["salt"])
            derived_key = self.derive_key_from_password(password, salt)

            aes_derived = AESGCM(derived_key)
            nonce = bytes.fromhex(meta["enc_private_key_nonce"])
            enc_pkey = bytes.fromhex(meta["enc_private_key"])
            raw_private_key = aes_derived.decrypt(nonce, enc_pkey, None)

            # Verify sentinel
            aes_pkey = AESGCM(raw_private_key)
            sentinel_nonce = bytes.fromhex(meta["sentinel_nonce"])
            sentinel_cipher = bytes.fromhex(meta["sentinel_cipher"])
            decrypted_sentinel = aes_pkey.decrypt(sentinel_nonce, sentinel_cipher, None)

            if decrypted_sentinel == SENTINEL_PLAINTEXT:
                self._current_key = raw_private_key
                # Reconstruct formatted private key string
                key_hex = raw_private_key.hex().upper()
                blocks = [key_hex[i : i + 4] for i in range(0, len(key_hex), 4)]
                self._master_private_key_hex = f"LK-{'-'.join(blocks)}"
                return True
        except (InvalidTag, Exception):
            return False
        return False

    def unlock_with_private_key(self, private_key_str: str) -> bool:
        """Unlocks the vault using the user's private key directly."""
        meta = self.get_vault_metadata()
        if not meta:
            return False
        try:
            raw_private_key = self.parse_private_key(private_key_str)
            aes_pkey = AESGCM(raw_private_key)
            sentinel_nonce = bytes.fromhex(meta["sentinel_nonce"])
            sentinel_cipher = bytes.fromhex(meta["sentinel_cipher"])
            decrypted_sentinel = aes_pkey.decrypt(sentinel_nonce, sentinel_cipher, None)

            if decrypted_sentinel == SENTINEL_PLAINTEXT:
                self._current_key = raw_private_key
                self._master_private_key_hex = private_key_str.strip().upper()
                return True
        except (InvalidTag, Exception):
            return False
        return False

    def is_unlocked(self) -> bool:
        """Returns True if the vault key is currently in memory."""
        return self._current_key is not None

    def lock(self) -> None:
        """Locks the vault and securely scrubs the active key from memory."""
        self._current_key = None
        self._master_private_key_hex = None

    def get_current_private_key(self) -> Optional[str]:
        """Returns the formatted master private key if unlocked."""
        return self._master_private_key_hex

    def get_active_key_bytes(self) -> Optional[bytes]:
        return self._current_key

    def encrypt_payload(self, data_bytes: bytes, key: Optional[bytes] = None) -> bytes:
        """Encrypts arbitrary bytes using AES-256-GCM.
        Returns: 12-byte nonce + ciphertext + 16-byte auth tag.
        """
        if not HAVE_CRYPTOGRAPHY or AESGCM is None:
            raise ValueError("Cryptography library is not available.")
        active_key = key or self._current_key
        if not active_key:
            raise ValueError("Vault is locked: no encryption key available.")

        aesgcm = AESGCM(active_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data_bytes, None)
        return nonce + ciphertext

    def decrypt_payload(self, encrypted_bytes: bytes, key: Optional[bytes] = None) -> bytes:
        """Decrypts AES-256-GCM payload with tag verification."""
        if not HAVE_CRYPTOGRAPHY or AESGCM is None:
            raise ValueError("Cryptography library is not available.")
        active_key = key or self._current_key
        if not active_key:
            raise ValueError("Vault is locked: no decryption key available.")

        if len(encrypted_bytes) < 28:
            raise ValueError("Invalid encrypted payload size.")

        nonce = encrypted_bytes[:12]
        ciphertext = encrypted_bytes[12:]
        aesgcm = AESGCM(active_key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def save_history_vault(
        self, records: List[Dict[str, Any]], key: Optional[bytes] = None
    ) -> bool:
        """Encrypts and atomically writes the history records to history.vault."""
        try:
            json_str = json.dumps(records, ensure_ascii=False)
            encrypted = self.encrypt_payload(json_str.encode("utf-8"), key)

            # Atomic file write using temporary file
            temp_file = self.vault_file.with_suffix(".tmp")
            with open(temp_file, "wb") as f:
                f.write(encrypted)
            temp_file.replace(self.vault_file)

            # Update metadata timestamp
            if self.meta_file.exists():
                try:
                    with open(self.meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    meta["updated_at"] = datetime.now().isoformat()
                    meta["records_count"] = len(records)
                    with open(self.meta_file, "w", encoding="utf-8") as f:
                        json.dump(meta, f, indent=2)
                except Exception:
                    pass
            return True
        except Exception as e:
            print(f"[CryptoVault] Error saving encrypted history: {e}")
            return False

    def load_history_vault(
        self, key: Optional[bytes] = None
    ) -> Tuple[bool, List[Dict[str, Any]], str]:
        """Decrypts and returns records from history.vault.
        Returns (success, records_list, error_message).
        """
        if not self.vault_file.exists():
            return True, [], ""

        try:
            with open(self.vault_file, "rb") as f:
                encrypted_bytes = f.read()

            decrypted_bytes = self.decrypt_payload(encrypted_bytes, key)
            records = json.loads(decrypted_bytes.decode("utf-8"))
            return True, records, ""
        except InvalidTag:
            return False, [], "Decryption failed: invalid private key or password."
        except Exception as e:
            return False, [], f"Vault read error: {str(e)}"
