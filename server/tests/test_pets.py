import pytest
from app.main import app
from app.routers import pets as pets_router
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_pets_state() -> None:
    """Ensure the in-memory store starts empty for each test."""

    pets_router._reset_state()
    yield
    pets_router._reset_state()


def test_pets_endpoint_returns_empty_list() -> None:
    response = client.get("/pets")
    assert response.status_code == 200
    assert response.json() == []


def test_create_pet_returns_created_pet_and_updates_list() -> None:
    payload = {"name": "Fido", "age": 4}
    response = client.post("/pets", json=payload)

    assert response.status_code == 201
    created_pet = response.json()
    assert created_pet["id"] == 1
    assert created_pet["name"] == payload["name"]
    assert created_pet["age"] == payload["age"]

    list_response = client.get("/pets")
    assert list_response.status_code == 200
    assert list_response.json() == [created_pet]


def test_get_pet_by_id_returns_existing_pet() -> None:
    creation = client.post("/pets", json={"name": "Milo", "age": 2})
    pet_id = creation.json()["id"]

    response = client.get(f"/pets/{pet_id}")
    assert response.status_code == 200
    assert response.json() == creation.json()


def test_get_pet_by_id_returns_404_for_missing_pet() -> None:
    response = client.get("/pets/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Pet not found"}
