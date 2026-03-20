from fastapi import APIRouter
from app.api.v1.chat import router as chat_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.applications import router as applications_router
from app.api.v1.voice import router as voice_router
from app.api.v1.profile import router as profile_router

api_router = APIRouter()

# Domain API routes
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(applications_router, prefix="/applications", tags=["applications"])
api_router.include_router(voice_router, prefix="/voice", tags=["voice"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
