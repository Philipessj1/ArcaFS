from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models.file_share import FileShare


# Helper function to seed a text file for testing share features
def upload_test_file(
    client: TestClient,
    headers: dict[str, str],
) -> int:
    # Perform a multipart form POST request to upload a text file stream
    response = client.post(
        "/files/upload",
        headers=headers,
        files={
            "file": (
                "shared-file.txt",
                b"Shared file content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    # Return the extracted file resource identifier
    return response.json()["id"]


# Helper function to generate a public share link for a specific file resource
def create_share(
    client: TestClient,
    headers: dict[str, str],
    file_id: int,
) -> dict:
    # Perform a POST request to generate a public share link with an expiration window
    response = client.post(
        f"/files/{file_id}/share",
        headers=headers,
        json={
            "expires_in_hours": 24,
        },
    )

    assert response.status_code == 201

    # Return the created file share dictionary payload
    return response.json()


# Test case to verify that unauthenticated anonymous clients can download files via active share links
def test_public_shared_link_downloads_file(
    client: TestClient,
    register_and_login,
):
    # Setup authentication headers for the file owner
    owner_headers = register_and_login()

    # Upload a file and establish a public share link resource
    file_id = upload_test_file(client, owner_headers)

    share = create_share(
        client,
        owner_headers,
        file_id,
    )

    # Perform an unauthenticated anonymous GET request to the public share URL
    response = client.get(share["share_url"])

    # Assert that the request succeeds, yielding correct content and no-store cache controls
    assert response.status_code == 200
    assert response.content == b"Shared file content"
    assert response.headers["content-type"].startswith("text/plain")
    assert "no-store" in response.headers["cache-control"]


# Test case to guarantee that revoking a share link immediately invalidates public access
def test_revoked_shared_link_returns_404(
    client: TestClient,
    register_and_login,
):
    # Setup authentication and build a shared resource payload as Owner User
    owner_headers = register_and_login()

    file_id = upload_test_file(client, owner_headers)

    share = create_share(
        client,
        owner_headers,
        file_id,
    )

    # Perform a DELETE request to revoke the specific file share link
    revoke_response = client.delete(
        f"/files/{file_id}/shares/{share['id']}",
        headers=owner_headers,
    )

    # Assert that the revocation confirms with a 204 No Content status
    assert revoke_response.status_code == 204

    # Attempt an unauthenticated anonymous GET request to the revoked share URL
    response = client.get(share["share_url"])

    # Assert that public access is blocked, returning a 404 Not Found error
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Shared file not found"
    }


# Test case to verify that public access is automatically blocked once a share link expires
def test_expired_shared_link_returns_404(
    client: TestClient,
    register_and_login,
    db_session: Session,
):
    # Setup authentication and build a shared resource payload as Owner User
    owner_headers = register_and_login()

    file_id = upload_test_file(client, owner_headers)

    share_response = create_share(
        client,
        owner_headers,
        file_id,
    )

    # Query the database directly to load the newly created share record
    share = db_session.scalar(
        select(FileShare).where(
            FileShare.id == share_response["id"]
        )
    )

    assert share is not None

    # Artificially shift the expiration timestamp into the past to simulate an expired link
    share.expires_at = (
        datetime.now(timezone.utc)
        - timedelta(minutes=1)
    )

    db_session.commit()

    # Attempt an unauthenticated anonymous GET request to the expired share URL
    response = client.get(share_response["share_url"])

    # Assert that the system intercepts the expiration, returning a 404 Not Found error
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Shared file not found"
    }


# Test case to ensure that users cannot list or revoke share links created by other users
def test_user_cannot_manage_another_users_shares(
    client: TestClient,
    register_and_login,
):
    # Setup authentication and build a shared resource payload as Owner User
    owner_headers = register_and_login(
        name="Owner User",
        email="owner@example.com",
    )

    file_id = upload_test_file(client, owner_headers)

    share = create_share(
        client,
        owner_headers,
        file_id,
    )

    # Setup authentication for an isolated second user
    other_user_headers = register_and_login(
        name="Other User",
        email="other@example.com",
    )

    # Attempt a GET request as the unauthorized user to list the owner's share entries
    list_response = client.get(
        f"/files/{file_id}/shares",
        headers=other_user_headers,
    )

    # Assert that the file resource is obscured, returning a 404 Not Found error
    assert list_response.status_code == 404
    assert list_response.json() == {
        "detail": "File not found"
    }

    # Attempt a DELETE request as the unauthorized user to revoke the owner's share link
    revoke_response = client.delete(
        f"/files/{file_id}/shares/{share['id']}",
        headers=other_user_headers,
    )

    # Assert that the share tracking record is obscured, returning a 404 Not Found error
    assert revoke_response.status_code == 404
    assert revoke_response.json() == {
        "detail": "File not found"
    }

    # Perform an anonymous unauthenticated GET request to verify the public link remains completely functional
    public_response = client.get(share["share_url"])

    # Assert that malicious interference failed and the public share link remains active
    assert public_response.status_code == 200