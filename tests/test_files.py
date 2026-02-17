from tests.helpers import auth_headers, register_user


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
    file_id = upload.json()["id"]

    list_files = client.get("/api/v1/files/my-files", headers=headers)
    assert list_files.status_code == 200, list_files.text
    assert list_files.json()["total"] == 1

    download = client.get(f"/api/v1/files/download/{file_id}", headers=headers)
    assert download.status_code == 200, download.text
    assert download.content == b"dummy-pdf-content"
