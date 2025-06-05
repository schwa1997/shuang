from fastapi import APIRouter
from app.db import prisma

router = APIRouter()

@router.get("/")
async def get_users():
    users = await prisma.user.find_many()
    return users
