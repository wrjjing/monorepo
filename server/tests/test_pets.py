from collections.abc import Generator
from pathlib import Path

import pytest
from app.db import get_session
from app.main import app
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine


@pytest.fixture(autouse=True)
def override_session_dependency(tmp_path: Path) -> Generator[None, None, None]:
    """Provide a fresh in-memory database for each test."""

    database_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_file}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    def _override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    yield
    app.dependency_overrides.pop(get_session, None)
    SQLModel.metadata.drop_all(engine)


client = TestClient(app)


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
