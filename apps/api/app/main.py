from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.database import Base, engine
from app.models.lead import Lead  # noqa: F401

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.on_event("startup")
def startup_event() -> None:
    """Initialize database resources when the app starts."""
    Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
