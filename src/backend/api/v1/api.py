from fastapi import APIRouter
from src.backend.api.v1.endpoints import chat, sessions, health

api_router = APIRouter()

api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(sessions.router, tags=["sessions"])
api_router.include_router(health.router, tags=["health"])