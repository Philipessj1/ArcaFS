from starlette.testclient import TestClient

# Test case to verify successful user registration with valid credentials
def test_register_user_success(client: TestClient):
    # Perform a POST request to register a new unique user
    response = client.post(
        "/auth/register",
        json={
            "name": "Philipe Test",
            "email": "philipe@test.com",
            "password": "SenhaSegura123",
        },
    )

    # Assert that the endpoint returns a 201 Created status
    assert response.status_code == 201

    data = response.json()

    # Assert that the returning payload contains correct user profile information
    assert data["id"] == 1
    assert data["name"] == "Philipe Test"
    assert data["email"] == "philipe@test.com"

    # Assert that sensitive data fields are never leaked in the response payload
    assert "password" not in data
    assert "password_hash" not in data

# Test case to ensure duplicate email addresses are rejected during registration
def test_register_user_with_duplicate_email(client: TestClient):
    # Setup user registration payload data
    user_data = {
        "name": "Philipe Test",
        "email": "philipe@test.com",
        "password": "senhaSegura123",
    }

    # Register the initial user in the system
    first_response = client.post(
        "/auth/register",
        json=user_data,
    )

    # Attempt to register a different user using the exact same email address
    second_response = client.post(
        "/auth/register",
        json={
            "name": "Another User",
            "email": "philipe@test.com",
            "password": "senhaSegura456",
        },
    )

    # Assert the first request succeeds and the second request is rejected with a conflict error
    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Email already registered"
    }

# Test case to verify successful user login and JWT token issuance
def test_login_success(client: TestClient):
    # Register a new user to populate the database credentials
    client.post(
        "/auth/register",
        json={
            "name": "Philipe Test",
            "email": "philipe@test.com",
            "password": "senhaSegura123",
        },
    )

    # Perform a POST request to authenticate with the matching valid credentials
    response = client.post(
        "/auth/login",
        json={
            "email": "philipe@test.com",
            "password": "senhaSegura123",
        },
    )

    # Assert that the endpoint returns a 200 OK status
    assert response.status_code == 200

    data = response.json()

    # Assert that a valid Bearer access token is successfully generated and issued
    assert "access_token" in data
    assert data["access_token"]
    assert data["token_type"] == "bearer"    

# Test case to verify that logging in with incorrect credentials is blocked
def test_login_with_invalid_password(client: TestClient):
    # Register a new user to populate the database credentials
    client.post(
        "/auth/register",
        json={
            "name": "Philipe Test",
            "email": "philipe@test.com",
            "password": "senhaSegura123",
        },
    )

    # Attempt to authenticate with a valid email address but an incorrect password
    response = client.post(
        "/auth/login",
        json={
            "email": "philipe@test.com",
            "password": "senhaErrada123",
        },
    )

    # Assert that the authentication request is rejected with a 401 Unauthorized error
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password"
    }