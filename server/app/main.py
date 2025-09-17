from app.db import init_db
from app.routers import pets
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def read_health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.on_event("startup")
def on_startup() -> None:
    """Initialize application resources."""

    init_db()


app.include_router(pets.router)
