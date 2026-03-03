from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_debug: bool = False
    app_log_level: str = "INFO"

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    pipeline_timeout_seconds: int = 8

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://verifid:verifid_secret@localhost:5432/verifid"
    db_pool_size: int = 20
    db_pool_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_selfies: str = "selfie-images"
    minio_bucket_documents: str = "document-images"
    minio_bucket_processed: str = "processed-images"
    minio_image_ttl_minutes: int = 15

    # Security
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 30
    api_key_header: str = "X-API-Key"
    encryption_key: str = "change-me-32-byte-key-for-aes256"

    # Rate Limiting
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    rate_limit_verify_requests: int = 10
    rate_limit_verify_window_seconds: int = 60

    # ML Models
    models_dir: str = "./models"
    face_match_threshold: float = 0.85
    liveness_threshold: float = 0.7

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8081"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
