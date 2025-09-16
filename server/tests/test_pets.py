from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_pets_endpoint_returns_empty_list() -> None:
    response = client.get("/pets")
    assert response.status_code == 200
    assert response.json() == []
