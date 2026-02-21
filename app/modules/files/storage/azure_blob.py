from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.modules.files.storage.base import StorageBackend


class AzureBlobStorageBackend(StorageBackend):
    provider = "azure"

    def __init__(
        self,
        *,
        container_name: str,
        connection_string: str | None = None,
        account_url: str | None = None,
        account_name: str | None = None,
        account_key: str | None = None,
        container_url: str | None = None,
    ) -> None:
        if not container_name:
            raise ValueError("AZURE_STORAGE_CONTAINER_NAME is required for Azure storage provider")
        if not connection_string and not account_url:
            raise ValueError("Either AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL is required")

        try:
            from azure.core.exceptions import AzureError
            from azure.storage.blob import BlobServiceClient
        except Exception as exc:
            raise ValueError("azure-storage-blob is required for Azure Blob storage backend") from exc

        self._azure_error = AzureError
        self.account_name = account_name
        self.account_key = account_key
        self.container_name = container_name
        self.container_url = container_url.rstrip("/") if container_url else None

        if connection_string:
            self.service_client = BlobServiceClient.from_connection_string(connection_string)
            parsed = self._parse_connection_string(connection_string)
            if not self.account_name:
                self.account_name = parsed.get("accountname")
            if not self.account_key:
                self.account_key = parsed.get("accountkey")
        else:
            self.service_client = BlobServiceClient(account_url=account_url, credential=account_key or None)

        self.container_client = self.service_client.get_container_client(container_name)

    def save(self, *, folder: str, filename: str, content: bytes, content_type: str | None = None) -> str:
        blob_path = f"{folder}/{filename}".strip("/")

        try:
            from azure.storage.blob import ContentSettings

            upload_kwargs: dict[str, object] = {}
            if content_type:
                upload_kwargs["content_settings"] = ContentSettings(content_type=content_type)
            self.container_client.upload_blob(name=blob_path, data=content, overwrite=True, **upload_kwargs)
        except self._azure_error as exc:
            raise ValueError(f"Azure Blob upload failed: {exc}") from exc

        return blob_path

    def build_file_url(self, storage_path: str) -> str:
        if self.container_url:
            return f"{self.container_url}/{storage_path}"
        return f"{self.container_client.url}/{storage_path}"

    def resolve_local_path(self, storage_path: str):
        return None

    def create_download_url(self, storage_path: str, *, expires_seconds: int) -> str | None:
        if not self.account_name or not self.account_key:
            return None

        try:
            from azure.storage.blob import BlobSasPermissions, generate_blob_sas

            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=storage_path,
                account_key=self.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(seconds=expires_seconds),
            )
        except Exception:
            return None

        return f"{self.container_client.url}/{storage_path}?{sas_token}"

    @staticmethod
    def _parse_connection_string(connection_string: str) -> dict[str, str]:
        parts: dict[str, str] = {}
        for item in connection_string.split(";"):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            key = key.strip().lower()
            value = value.strip()
            if key and value:
                parts[key] = value
        return parts
