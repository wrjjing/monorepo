from app.db import get_session
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Field, Session, SQLModel, select

router = APIRouter()


class PetBase(SQLModel):
    """Shared attributes for pet representations."""

    name: str
    age: int


class Pet(PetBase, table=True):
    """Database model for a pet."""

    id: int | None = Field(default=None, primary_key=True)


class PetCreate(PetBase):
    """Input model for creating a pet."""


class PetRead(PetBase):
    """Representation of a pet resource returned by the API."""

    id: int


@router.get("/pets", response_model=list[PetRead])
def list_pets(session: Session = Depends(get_session)) -> list[PetRead]:
    """Return the collection of pets."""

    pets = session.exec(select(Pet)).all()
    return pets


@router.post("/pets", response_model=PetRead, status_code=status.HTTP_201_CREATED)
def create_pet(pet: PetCreate, session: Session = Depends(get_session)) -> PetRead:
    """Create a new pet entry."""

    new_pet = Pet(**pet.model_dump())
    session.add(new_pet)
    session.commit()
    session.refresh(new_pet)
    return new_pet


@router.get("/pets/{pet_id}", response_model=PetRead)
def get_pet(pet_id: int, session: Session = Depends(get_session)) -> PetRead:
    """Retrieve a pet by its identifier."""

    pet = session.get(Pet, pet_id)
    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found"
        )
    return pet
