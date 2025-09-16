from app.routers import pets
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def read_health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


app.include_router(pets.router)
