from starlette.testclient import TestClient

# Helper function to seed a user and retrieve a valid JWT access token for testing
def register_and_login(client: TestClient) -> str:
    # Register a new test user profile
    client.post(
        "/auth/register",
        json={
            "name": "Philipe Test",
            "email": "philipe@test.com",
            "password": "senhaSegura123",
        },
    )

    # Authenticate with the registered credentials to generate a session token
    login_response = client.post(
        "/auth/login",
        json={
            "email": "philipe@test.com",
            "password": "senhaSegura123",
        },
    )

    # Return the extracted string token from the login JSON response payload
    return login_response.json()["access_token"]


# Test case to verify retrieving the authenticated user profile using a valid token
def test_get_current_user_success(client: TestClient):
    # Setup authentication by obtaining a valid access token
    access_token = register_and_login(client)

    # Perform a GET request to the protected profile route with the authorization header
    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert that the profile request returns a 200 OK status
    assert response.status_code == 200

    data = response.json()

    # Assert that the returning profile accurately matches the logged-in user
    assert data["id"] == 1
    assert data["name"] == "Philipe Test"
    assert data["email"] == "philipe@test.com"

    # Assert that sensitive credential attributes are excluded from the user model payload
    assert "password" not in data
    assert "password_hash" not in data


# Test case to verify that accessing a protected route without a token is blocked
def test_get_current_user_without_token(client: TestClient):
    # Attempt an unauthenticated GET request to the protected profile endpoint
    response = client.get("/users/me")

    # Assert that the request is rejected with a 401 Unauthorized status
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }


# Test case to verify that an invalid or altered token is rejected by authentication guards
def test_get_current_user_with_invalid_token(client: TestClient):
    # Attempt an authenticated GET request using a malformed authorization header token
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    # Assert that the route security layer blocks the request with a credentials validation failure error
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }