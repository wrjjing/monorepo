from fastapi import APIRouter

router = APIRouter()


@router.get("/pets")
def list_pets() -> list[dict]:
    """Return the collection of pets."""
    return []
