from fastapi import APIRouter, HTTPException, Depends
from app.models.user import UserCreate, UserLogin, UserOut, UserUpdate
from app.db import prisma
from app.core.security import hash_password, verify_password, create_access_token
from app.dependencies import get_current_user
from datetime import timedelta

router = APIRouter()

@router.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    existing = await prisma.user.find_unique(where={"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = await prisma.user.create(
        data={
            "email": user.email,
            "password": hash_password(user.password),
            "name": user.name,
        }
    )
    return new_user

@router.post("/login")
async def login(user: UserLogin):
    db_user = await prisma.user.find_unique(where={"email": user.email})
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token({"sub": db_user.id})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def get_me(current_user=Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
async def update_me(update: UserUpdate, current_user=Depends(get_current_user)):
    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.password is not None:
        update_data["password"] = hash_password(update.password)
    updated_user = await prisma.user.update(
        where={"id": current_user.id},
        data=update_data
    )
    return updated_user
