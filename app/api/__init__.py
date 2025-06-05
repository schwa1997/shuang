# app/api/__init__.py
from fastapi import APIRouter
from .user import router as user_router

api_router = APIRouter()
api_router.include_router(user_router, prefix="/users", tags=["Users"])
