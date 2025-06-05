from fastapi import APIRouter
from app.db import prisma
from pydantic import BaseModel

router = APIRouter()

class UserOut(BaseModel):
    id: int
    email: str
    name: str | None = None

@router.get("/", response_model=list[UserOut])
async def get_users():
    users = await prisma.user.find_many()
    return users
