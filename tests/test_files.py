from pathlib import Path

from starlette.testclient import TestClient

# Test case to verify successful file upload with correct metadata and physical storage integration
def test_upload_file_success(
    client: TestClient,
    register_and_login,
    isolate_upload_storage: Path,
):
    # Setup authentication headers using the provided registration helper
    headers = register_and_login()

    # Perform a multipart form POST request to upload a text file stream
    response = client.post(
        "/files/upload",
        headers=headers,
        files={
            "file": (
                "hello.txt",
                b"Hello from ArcaFS tests",
                "text/plain",
            )
        },
    )

    # Assert that the upload request returns a 201 Created status
    assert response.status_code == 201

    data = response.json()

    # Assert that the database metadata object returns correct file characteristics
    assert data["id"] == 1
    assert data["original_filename"] == "hello.txt"
    assert data["content_type"] == "text/plain"
    assert data["size"] == len(b"Hello from ArcaFS tests")

    # Scan the isolated test file system storage directory recursively
    saved_files = list(isolate_upload_storage.rglob("*"))

    # Assert that the file binary was physically written and persisted to the local disk storage
    assert any(path.is_file() for path in saved_files)


# Test case to guarantee strict user isolation when querying and listing files
def test_list_files_returns_only_current_user_files(
    client: TestClient,
    register_and_login,
):
    # Setup authentication and register User A
    user_a_headers = register_and_login(
        name="User A",
        email="user-a@test.com",
    )

    # Upload a private file belonging exclusively to User A
    upload_a = client.post(
        "/files/upload",
        headers=user_a_headers,
        files={
            "file": (
                "user-a.txt",
                b"File from user A",
                "text/plain",
            )
        },
    )

    assert upload_a.status_code == 201

    # Setup authentication and register an isolated User B
    user_b_headers = register_and_login(
        name="User B",
        email="user-b@test.com",
    )

    # Upload a private file belonging exclusively to User B
    upload_b = client.post(
        "/files/upload",
        headers=user_b_headers,
        files={
            "file": (
                "user-b.txt",
                b"File from user B",
                "text/plain",
            )
        },
    )

    assert upload_b.status_code == 201

    # Perform a GET request as User A to list uploaded files
    response = client.get(
        "/files/",
        headers=user_a_headers,
    )

    # Assert that the request succeeds with a 200 OK status
    assert response.status_code == 200

    files = response.json()

    # Assert that User A can only see their own file, preventing multi-tenant data leaks
    assert len(files) == 1
    assert files[0]["original_filename"] == "user-a.txt"


# Test case to verify that file uploads without authentication credentials are blocked
def test_upload_file_without_token_returns_401(client: TestClient):
    # Attempt an unauthenticated multipart POST request to the upload route
    response = client.post(
        "/files/upload",
        files={
            "file": (
                "unauthorized.txt",
                b"Should not be uploaded",
                "text/plain",
            )
        },
    )

    # Assert that the route security interceptor blocks the request with a 401 Unauthorized status
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }

from starlette.testclient import TestClient

# Test case to verify that the file owner can successfully download their own file
def test_owner_can_download_file(
    client: TestClient,
    register_and_login,
):
    # Setup authentication headers for the file owner
    headers = register_and_login()

    # Upload a file to generate a target download record
    upload_response = client.post(
        "/files/upload",
        headers=headers,
        files={
            "file": (
                "download-test.txt",
                b"Content for download test",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201

    # Extract the resource identity from the created record payload
    file_id = upload_response.json()["id"]

    # Perform a GET request to download the specific file binary
    response = client.get(
        f"/files/{file_id}/download",
        headers=headers,
    )

    # Assert that the request succeeds and returns the exact file payload and headers
    assert response.status_code == 200
    assert response.content == b"Content for download test"
    assert response.headers["content-type"].startswith("text/plain")


# Test case to guarantee that a user is blocked from downloading another user's private file
def test_user_cannot_download_another_users_file(
    client: TestClient,
    register_and_login,
):
    # Setup authentication and upload a private file as Owner User
    owner_headers = register_and_login(
        name="Owner User",
        email="owner@test.com",
    )

    upload_response = client.post(
        "/files/upload",
        headers=owner_headers,
        files={
            "file": (
                "private.txt",
                b"Private owner content",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201

    file_id = upload_response.json()["id"]

    # Setup authentication for an isolated second user
    other_user_headers = register_and_login(
        name="Other User",
        email="other@test.com",
    )

    # Attempt a GET request to download the owner's file using the other user's session
    response = client.get(
        f"/files/{file_id}/download",
        headers=other_user_headers,
    )

    # Assert that the unauthorized download is obscured and rejected with a 404 Not Found error
    assert response.status_code == 404
    assert response.json() == {
        "detail": "File not found"
    }


# Test case to verify that the file owner can successfully purge metadata and physical storage
def test_owner_can_delete_file(
    client: TestClient,
    register_and_login,
    isolate_upload_storage: Path,
):
    # Setup authentication headers for the file owner
    headers = register_and_login()

    # Upload a file targeted for permanent removal
    upload_response = client.post(
        "/files/upload",
        headers=headers,
        files={
            "file": (
                "delete-test.txt",
                b"Content that will be deleted",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201

    file_id = upload_response.json()["id"]

    # Verify that the binary payload has been physically written to local storage before deletion
    uploaded_files_before_delete = [
        path
        for path in isolate_upload_storage.rglob("*")
        if path.is_file()
    ]

    assert len(uploaded_files_before_delete) == 1

    # Perform a DELETE request to purge the file resource from the system
    delete_response = client.delete(
        f"/files/{file_id}",
        headers=headers,
    )

    # Assert that the deletion confirms with a 204 No Content status
    assert delete_response.status_code == 204

    # Query the user's file registry list to ensure the metadata was removed
    list_response = client.get(
        "/files/",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []

    # Scan the isolated storage to verify that the binary file was unlinked from disk
    uploaded_files_after_delete = [
        path
        for path in isolate_upload_storage.rglob("*")
        if path.is_file()
    ]

    # Assert that no stray or orphaned binary records remain on disk
    assert uploaded_files_after_delete == []


# Test case to ensure that a user cannot delete a file belonging to another user
def test_user_cannot_delete_another_users_file(
    client: TestClient,
    register_and_login,
):
    # Setup authentication and upload a file as Owner User
    owner_headers = register_and_login(
        name="Owner User",
        email="owner@test.com",
    )

    upload_response = client.post(
        "/files/upload",
        headers=owner_headers,
        files={
            "file": (
                "private-delete.txt",
                b"Private file",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201

    file_id = upload_response.json()["id"]

    # Setup authentication for an isolated third-party user
    other_user_headers = register_and_login(
        name="Other User",
        email="other@test.com",
    )

    # Attempt a DELETE request on the owner's file using the unauthorized session
    delete_response = client.delete(
        f"/files/{file_id}",
        headers=other_user_headers,
    )

    # Assert that the destructive action is blocked and returns a 404 Not Found error
    assert delete_response.status_code == 404
    assert delete_response.json() == {
        "detail": "File not found"
    }

    # Query the owner's file registry to prove the target resource was untouched and remains intact
    owner_list_response = client.get(
        "/files/",
        headers=owner_headers,
    )

    assert owner_list_response.status_code == 200
    assert len(owner_list_response.json()) == 1
    assert owner_list_response.json()[0]["id"] == file_id