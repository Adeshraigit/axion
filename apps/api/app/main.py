from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.scheduler.daily_jobs import scheduler_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Start scheduler on app boot for daily recommendations.
    settings = get_settings()
    if settings.scheduler_enabled:
        scheduler_service.start()
    try:
        yield
    finally:
        scheduler_service.shutdown()


settings = get_settings()
app = FastAPI(title="AI Career Mentor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix="/api/v1")
