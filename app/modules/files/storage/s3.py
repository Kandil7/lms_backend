from __future__ import annotations

from app.modules.files.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    provider = "s3"

    def __init__(
        self,
        *,
        bucket: str,
        region: str | None = None,
        bucket_url: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ) -> None:
        if not bucket:
            raise ValueError("AWS_S3_BUCKET is required for S3 storage provider")

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except Exception as exc:
            raise ValueError("boto3 is required for S3 storage backend") from exc

        self._boto_core_errors = (BotoCoreError, ClientError)
        self.bucket = bucket
        self.region = region
        self.bucket_url = bucket_url.rstrip("/") if bucket_url else None

        session = boto3.session.Session(
            aws_access_key_id=aws_access_key_id or None,
            aws_secret_access_key=aws_secret_access_key or None,
            region_name=region or None,
        )
        self.client = session.client("s3", region_name=region or None)

    def save(self, *, folder: str, filename: str, content: bytes, content_type: str | None = None) -> str:
        key = f"{folder}/{filename}".strip("/")

        put_kwargs: dict[str, object] = {"Bucket": self.bucket, "Key": key, "Body": content}
        if content_type:
            put_kwargs["ContentType"] = content_type

        try:
            self.client.put_object(**put_kwargs)
        except self._boto_core_errors as exc:
            raise ValueError(f"S3 upload failed: {exc}") from exc

        return key

    def build_file_url(self, storage_path: str) -> str:
        if self.bucket_url:
            return f"{self.bucket_url}/{storage_path}"

        if self.region and self.region != "us-east-1":
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{storage_path}"
        return f"https://{self.bucket}.s3.amazonaws.com/{storage_path}"

    def resolve_local_path(self, storage_path: str):
        return None

    def create_download_url(self, storage_path: str, *, expires_seconds: int) -> str | None:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": storage_path},
                ExpiresIn=expires_seconds,
            )
        except self._boto_core_errors:
            return None
