"""HashiCorp Vault integration for secret management.

In development mode, falls back to environment variables.
In production, fetches secrets from Vault at startup.
"""

import os

import structlog

logger = structlog.get_logger()


class VaultClient:
    """Manages secrets from HashiCorp Vault or environment fallback."""

    def __init__(
        self,
        vault_addr: str | None = None,
        vault_token: str | None = None,
        mount_path: str = "secret",
    ) -> None:
        self._addr = vault_addr or os.getenv("VAULT_ADDR", "")
        self._token = vault_token or os.getenv("VAULT_TOKEN", "")
        self._mount = mount_path
        self._client = None
        self._cache: dict[str, str] = {}

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self._addr or not self._token:
            logger.info("vault.using_env_fallback", reason="VAULT_ADDR or VAULT_TOKEN not set")
            return None

        try:
            import hvac
            self._client = hvac.Client(url=self._addr, token=self._token)
            if self._client.is_authenticated():
                logger.info("vault.authenticated", addr=self._addr)
            else:
                logger.warning("vault.auth_failed")
                self._client = None
        except ImportError:
            logger.info("vault.hvac_not_installed", msg="Using env fallback")
        except Exception:
            logger.exception("vault.connection_failed")

        return self._client

    def get_secret(self, path: str, key: str, default: str = "") -> str:
        """Get a secret value.

        Args:
            path: Secret path in Vault (e.g., "verifid/database").
            key: Key within the secret (e.g., "password").
            default: Default value if not found.
        """
        cache_key = f"{path}/{key}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        client = self._get_client()
        if client is not None:
            try:
                response = client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=self._mount,
                )
                value = response["data"]["data"].get(key, default)
                self._cache[cache_key] = value
                return value
            except Exception:
                logger.warning("vault.read_failed", path=path, key=key)

        # Fallback to environment variable
        env_key = f"{path.replace('/', '_').upper()}_{key.upper()}"
        return os.getenv(env_key, default)

    def get_database_url(self) -> str:
        """Get the database connection URL."""
        return self.get_secret("verifid/database", "url", os.getenv("DATABASE_URL", ""))

    def get_redis_url(self) -> str:
        """Get the Redis connection URL."""
        return self.get_secret("verifid/redis", "url", os.getenv("REDIS_URL", ""))

    def get_encryption_key(self) -> bytes:
        """Get the AES-256 encryption key for MinIO objects."""
        key_hex = self.get_secret("verifid/encryption", "aes_key", "")
        if key_hex and len(key_hex) == 64:
            return bytes.fromhex(key_hex)
        # Fallback: generate from env or use dev default
        import hashlib
        seed = os.getenv("ENCRYPTION_KEY", "verifid-dev-encryption-key-change-in-prod")
        return hashlib.sha256(seed.encode()).digest()

    def get_jwt_private_key(self) -> str:
        """Get the JWT RS256 private key."""
        return self.get_secret("verifid/jwt", "private_key", "")

    def get_jwt_public_key(self) -> str:
        """Get the JWT RS256 public key."""
        return self.get_secret("verifid/jwt", "public_key", "")


# Singleton
_vault: VaultClient | None = None


def get_vault() -> VaultClient:
    global _vault
    if _vault is None:
        _vault = VaultClient()
    return _vault
