from starlette.testclient import TestClient


# Helper function to perform the core initialization of a file record (Version 1)
def upload_initial_file(
    client: TestClient,
    headers: dict[str, str],
    filename: str = "document.txt",
    content: bytes = b"Version 1 content",
) -> int:
    # Perform a multipart form POST request to upload the original file binary
    response = client.post(
        "/files/upload",
        headers=headers,
        files={
            "file": (
                filename,
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    # Return the extracted base file resource identity
    return response.json()["id"]


# Helper function to append a sequential new file change mutation to an existing file record
def upload_new_version(
    client: TestClient,
    headers: dict[str, str],
    file_id: int,
    filename: str,
    content: bytes,
):
    # Perform a multipart form POST request targeting the specific file's version sub-route
    response = client.post(
        f"/files/{file_id}/versions",
        headers=headers,
        files={
            "file": (
                filename,
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    # Return the newly appended file version tracking dictionary payload
    return response.json()


# Test case to verify that the initial upload automatically spawns a tracking entry for version 1
def test_initial_upload_creates_version_one(
    client: TestClient,
    register_and_login,
):
    # Setup authentication headers for the session owner
    headers = register_and_login()

    # Upload the root file resource to ignite tracking
    file_id = upload_initial_file(client, headers)

    # Perform a GET request to query the complete history log of the file resource
    response = client.get(
        f"/files/{file_id}/versions",
        headers=headers,
    )

    # Assert that the registry tracker initializes with a single valid historical version
    assert response.status_code == 200

    versions = response.json()

    assert len(versions) == 1
    assert versions[0]["version_number"] == 1
    assert versions[0]["original_filename"] == "document.txt"
    assert versions[0]["size"] == len(b"Version 1 content")


# Test case to verify that uploading subsequent changes creates sequential version entries in descending order
def test_upload_new_version_creates_version_two(
    client: TestClient,
    register_and_login,
):
    # Setup authentication headers for the session owner
    headers = register_and_login()

    # Provision the core root file snapshot (Version 1)
    file_id = upload_initial_file(client, headers)

    # Push a subsequent file modification stream onto the file stack
    version_two = upload_new_version(
        client=client,
        headers=headers,
        file_id=file_id,
        filename="document-v2.txt",
        content=b"Version 2 content",
    )

    # Assert that the modification layer correctly registers as version number 2
    assert version_two["file_id"] == file_id
    assert version_two["version_number"] == 2
    assert version_two["original_filename"] == "document-v2.txt"

    # Query the comprehensive chronological history list of the mutated file
    versions_response = client.get(
        f"/files/{file_id}/versions",
        headers=headers,
    )

    assert versions_response.status_code == 200

    versions = versions_response.json()

    # Assert that history records are appended and sorted by most recent entry first
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2
    assert versions[1]["version_number"] == 1


# Test case to ensure old historical file snapshots can be directly targeted and downloaded
def test_can_download_old_file_version(
    client: TestClient,
    register_and_login,
):
    # Setup authentication headers for the session owner
    headers = register_and_login()

    # Push the baseline file layer (Version 1)
    file_id = upload_initial_file(
        client,
        headers,
        content=b"Original version content",
    )

    # Overwrite the active layer by stacking a newer mutation (Version 2)
    upload_new_version(
        client=client,
        headers=headers,
        file_id=file_id,
        filename="document-v2.txt",
        content=b"New version content",
    )

    # Perform a GET request explicitly targeting the historical index 1 download route
    response = client.get(
        f"/files/{file_id}/versions/1/download",
        headers=headers,
    )

    # Assert that the engine reconstructs and returns the original historic binary payload intact
    assert response.status_code == 200
    assert response.content == b"Original version content"
    assert response.headers["content-type"].startswith("text/plain")


# Test case to ensure that restoring a historical index appends a new state rather than deleting history
def test_restore_old_version_creates_new_current_version(
    client: TestClient,
    register_and_login,
):
    # Setup authentication headers for the session owner
    headers = register_and_login()

    # Seed chronological historical file states (Version 1 and Version 2)
    file_id = upload_initial_file(
        client,
        headers,
        filename="document-v1.txt",
        content=b"Version 1 content",
    )

    upload_new_version(
        client=client,
        headers=headers,
        file_id=file_id,
        filename="document-v2.txt",
        content=b"Version 2 content",
    )

    # Perform a POST request to restore historical entry 1 to the top active position
    restore_response = client.post(
        f"/files/{file_id}/versions/1/restore",
        headers=headers,
    )

    # Assert that the restoration registers as a forward-moving increment (Version 3)
    assert restore_response.status_code == 201

    restored_version = restore_response.json()

    assert restored_version["file_id"] == file_id
    assert restored_version["version_number"] == 3
    assert restored_version["original_filename"] == "document-v1.txt"

    # Query the global history list to investigate history preservation characteristics
    versions_response = client.get(
        f"/files/{file_id}/versions",
        headers=headers,
    )

    assert versions_response.status_code == 200

    versions = versions_response.json()

    # Assert that all historical states survive the rollout, sorted chronologically descending
    assert len(versions) == 3
    assert [version["version_number"] for version in versions] == [
        3,
        2,
        1,
    ]

    # Perform a GET request to the baseline download endpoint to verify active tracking state
    current_download = client.get(
        f"/files/{file_id}/download",
        headers=headers,
    )

    # Assert that the top global active data pointer matches the restored version content
    assert current_download.status_code == 200
    assert current_download.content == b"Version 1 content"


# Test case to guarantee tight tenant separation across tracking log records and asset rollbacks
def test_user_cannot_access_another_users_versions(
    client: TestClient,
    register_and_login,
):
    # Setup authentication and save a versioned asset under Owner User
    owner_headers = register_and_login(
        name="Owner User",
        email="owner@test.com",
    )

    file_id = upload_initial_file(
        client,
        owner_headers,
        content=b"Private version content",
    )

    # Setup authentication for an isolated third-party user
    other_user_headers = register_and_login(
        name="Other User",
        email="other@test.com",
    )

    # Attempt a GET request as the unauthorized user to inspect the file's mutation log
    list_response = client.get(
        f"/files/{file_id}/versions",
        headers=other_user_headers,
    )

    # Assert that the history record tree is obscured with a 404 Not Found error
    assert list_response.status_code == 404
    assert list_response.json() == {
        "detail": "File not found"
    }

    # Attempt a GET request as the unauthorized user to access a specific history payload
    download_response = client.get(
        f"/files/{file_id}/versions/1/download",
        headers=other_user_headers,
    )

    # Assert that historical asset fragments are obscured with a 404 Not Found error
    assert download_response.status_code == 404
    assert download_response.json() == {
        "detail": "File version not found"
    }

    # Attempt a POST request as the unauthorized user to force an asset rollback state change
    restore_response = client.post(
        f"/files/{file_id}/versions/1/restore",
        headers=other_user_headers,
    )

    # Assert that the destructive rollback vector is blocked and returns a 404 Not Found error
    assert restore_response.status_code == 404
    assert restore_response.json() == {
        "detail": "File not found"
    }