from fastapi import APIRouter

from backend.api import admin, public

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(public.router)
api_router.include_router(admin.router)
