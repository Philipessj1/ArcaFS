from starlette.testclient import TestClient

# Test case to verify the application health check endpoint
def test_health_check(client: TestClient):
    response = client.get("/health")
    
    # Assert that the endpoint returns a 200 OK status and the correct payload
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}