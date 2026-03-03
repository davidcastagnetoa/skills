import io
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from api.config import settings


def get_minio_client() -> Minio:
    """Create a MinIO client instance."""
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


class StorageService:
    """Object storage service backed by MinIO (S3-compatible)."""

    BUCKETS = [
        settings.minio_bucket_selfies,
        settings.minio_bucket_documents,
        settings.minio_bucket_processed,
    ]

    def __init__(self, client: Minio | None = None) -> None:
        self._client = client or get_minio_client()

    def ensure_buckets(self) -> None:
        """Create required buckets if they don't exist."""
        for bucket in self.BUCKETS:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)

    def upload(self, bucket: str, key: str, data: bytes, content_type: str = "image/jpeg") -> str:
        """Upload an object and return its key."""
        stream = io.BytesIO(data)
        self._client.put_object(
            bucket,
            key,
            stream,
            length=len(data),
            content_type=content_type,
        )
        return key

    def download(self, bucket: str, key: str) -> bytes:
        """Download an object and return its bytes."""
        response = self._client.get_object(bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, bucket: str, key: str) -> None:
        """Delete an object."""
        self._client.remove_object(bucket, key)

    def generate_presigned_url(self, bucket: str, key: str, expiry_seconds: int = 900) -> str:
        """Generate a presigned URL for temporary access."""
        return self._client.presigned_get_object(
            bucket,
            key,
            expires=timedelta(seconds=expiry_seconds),
        )

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        """List object keys in a bucket with optional prefix."""
        objects = self._client.list_objects(bucket, prefix=prefix)
        return [obj.object_name for obj in objects if obj.object_name]

    def health_check(self) -> bool:
        """Check if MinIO is reachable."""
        try:
            self._client.list_buckets()
            return True
        except S3Error:
            return False
