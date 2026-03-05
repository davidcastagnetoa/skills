"""AES-256-GCM encryption for biometric images stored in MinIO.

All images are encrypted before upload and decrypted after download.
The encryption key is managed by HashiCorp Vault.
"""

import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import structlog

logger = structlog.get_logger()

# Nonce size for AES-GCM (96 bits = 12 bytes, recommended by NIST)
_NONCE_SIZE = 12


class ImageEncryptor:
    """Encrypt and decrypt image data using AES-256-GCM."""

    def __init__(self, key: bytes | None = None) -> None:
        if key is None:
            from infrastructure.vault import get_vault
            key = get_vault().get_encryption_key()

        if len(key) != 32:
            raise ValueError("AES-256 key must be exactly 32 bytes")

        self._aesgcm = AESGCM(key)

    def encrypt(self, plaintext: bytes, associated_data: bytes | None = None) -> bytes:
        """Encrypt data with AES-256-GCM.

        Returns:
            nonce (12 bytes) + ciphertext + tag (16 bytes).
        """
        nonce = secrets.token_bytes(_NONCE_SIZE)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, associated_data)
        return nonce + ciphertext

    def decrypt(self, encrypted: bytes, associated_data: bytes | None = None) -> bytes:
        """Decrypt data encrypted with AES-256-GCM.

        Args:
            encrypted: nonce (12 bytes) + ciphertext + tag.
            associated_data: Optional AAD that was used during encryption.
        """
        if len(encrypted) < _NONCE_SIZE + 16:
            raise ValueError("Encrypted data too short")

        nonce = encrypted[:_NONCE_SIZE]
        ciphertext = encrypted[_NONCE_SIZE:]
        return self._aesgcm.decrypt(nonce, ciphertext, associated_data)


class EncryptedStorageService:
    """Wraps StorageService with transparent encryption/decryption."""

    def __init__(self, storage_service=None, encryptor: ImageEncryptor | None = None) -> None:
        if storage_service is None:
            from infrastructure.storage import StorageService
            storage_service = StorageService()
        self._storage = storage_service
        self._encryptor = encryptor or ImageEncryptor()

    def upload_encrypted(
        self, bucket: str, key: str, data: bytes, session_id: str = ""
    ) -> str:
        """Encrypt and upload data to MinIO."""
        aad = session_id.encode() if session_id else None
        encrypted = self._encryptor.encrypt(data, aad)
        return self._storage.upload(
            bucket, key, encrypted, content_type="application/octet-stream"
        )

    def download_decrypted(
        self, bucket: str, key: str, session_id: str = ""
    ) -> bytes:
        """Download and decrypt data from MinIO."""
        encrypted = self._storage.download(bucket, key)
        aad = session_id.encode() if session_id else None
        return self._encryptor.decrypt(encrypted, aad)

    def delete(self, bucket: str, key: str) -> None:
        """Delete an object from storage."""
        self._storage.delete(bucket, key)
