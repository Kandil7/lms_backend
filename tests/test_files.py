from tests.helpers import auth_headers, register_user
import pytest

from app.modules.files.service import FileService


def test_file_upload_list_and_download(client):
    student = register_user(
        client,
        email="files-student@example.com",
        password="StrongPass123",
        full_name="Files Student",
        role="student",
    )

    headers = auth_headers(student["tokens"]["access_token"])

    upload = client.post(
        "/api/v1/files/upload",
        headers=headers,
        data={"folder": "course-materials", "is_public": "false"},
        files={"file": ("notes.pdf", b"dummy-pdf-content", "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    uploaded_payload = upload.json()
    file_id = uploaded_payload["id"]
    assert uploaded_payload["file_url"].startswith("/api/v1/files/download/")
    assert client.get(f"/uploads/course-materials/{uploaded_payload['filename']}").status_code == 404

    list_files = client.get("/api/v1/files/my-files", headers=headers)
    assert list_files.status_code == 200, list_files.text
    assert list_files.json()["total"] == 1

    download = client.get(f"/api/v1/files/download/{file_id}", headers=headers)
    assert download.status_code == 200, download.text
    assert download.content == b"dummy-pdf-content"


def test_file_upload_rejects_path_traversal_folder(client):
    student = register_user(
        client,
        email="files-student-2@example.com",
        password="StrongPass123",
        full_name="Files Student 2",
        role="student",
    )

    headers = auth_headers(student["tokens"]["access_token"])
    upload = client.post(
        "/api/v1/files/upload",
        headers=headers,
        data={"folder": "../secrets", "is_public": "false"},
        files={"file": ("notes.pdf", b"dummy-pdf-content", "application/pdf")},
    )
    assert upload.status_code == 400, upload.text
    assert upload.json()["detail"] == "Invalid folder path"


def test_file_service_fail_closed_in_production_when_azure_unavailable(db_session, monkeypatch):
    monkeypatch.setattr("app.modules.files.service.settings.ENVIRONMENT", "production")
    monkeypatch.setattr("app.modules.files.service.settings.FILE_STORAGE_PROVIDER", "azure")
    monkeypatch.setattr("app.modules.files.service.settings.AZURE_STORAGE_CONTAINER_NAME", "lms-files")
    monkeypatch.setattr("app.modules.files.service.settings.AZURE_STORAGE_CONNECTION_STRING", "DefaultEndpointsProtocol=https")
    monkeypatch.setattr("app.modules.files.service.settings.AZURE_STORAGE_ACCOUNT_URL", "")
    monkeypatch.setattr("app.modules.files.service.settings.AZURE_STORAGE_ACCOUNT_NAME", "")
    monkeypatch.setattr("app.modules.files.service.settings.AZURE_STORAGE_ACCOUNT_KEY", "")
    monkeypatch.setattr("app.modules.files.service.settings.AZURE_STORAGE_CONTAINER_URL", "")

    class BrokenAzureBackend:
        def __init__(self, **kwargs):
            raise ValueError("simulated azure init failure")

    monkeypatch.setattr("app.modules.files.service.AzureBlobStorageBackend", BrokenAzureBackend)

    with pytest.raises(RuntimeError, match="Azure storage backend is not available in production"):
        FileService(db_session)
