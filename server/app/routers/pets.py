from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class PetCreate(BaseModel):
    """Input model for creating a pet."""

    name: str
    age: int


class Pet(PetCreate):
    """Representation of a pet resource."""

    id: int


_PETS: dict[int, Pet] = {}
_NEXT_ID = 1


def _reset_state() -> None:
    """Reset the in-memory store. Intended for tests."""

    global _NEXT_ID
    _PETS.clear()
    _NEXT_ID = 1


@router.get("/pets", response_model=list[Pet])
def list_pets() -> list[Pet]:
    """Return the collection of pets."""

    return list(_PETS.values())


@router.post("/pets", response_model=Pet, status_code=status.HTTP_201_CREATED)
def create_pet(pet: PetCreate) -> Pet:
    """Create a new pet entry."""

    global _NEXT_ID
    pet_id = _NEXT_ID
    _NEXT_ID += 1

    new_pet = Pet(id=pet_id, **pet.model_dump())
    _PETS[pet_id] = new_pet
    return new_pet


@router.get("/pets/{pet_id}", response_model=Pet)
def get_pet(pet_id: int) -> Pet:
    """Retrieve a pet by its identifier."""

    try:
        return _PETS[pet_id]
    except KeyError as exc:  # pragma: no cover - defensive branch
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found"
        ) from exc
