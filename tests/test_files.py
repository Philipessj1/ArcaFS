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