# app/routers/user.py
from fastapi import APIRouter, HTTPException, Depends, status
from app.models.user import UserRegisterRequest, UserRegisterResponse, UserLoginRequest, UserLoginResponse, UserProfileResponse, UserUpdate
from app.db import prisma
from app.core.security import hash_password, verify_password, create_access_token, verify_token
from app.dependencies import get_current_user
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegisterRequest):
    # 检查邮箱是否已存在
    existing_email = await prisma.user.find_unique(where={"email": user.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 检查用户名是否已存在
    existing_username = await prisma.user.find_unique(where={"username": user.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # 创建新用户
    new_user = await prisma.user.create(
        data={
            "email": user.email,
            "password_hash": hash_password(user.password),
            "username": user.username,
            "total_coins": 0,
        }
    )
    return new_user

@router.post("/login", response_model=UserLoginResponse)
async def login(user: UserLoginRequest):
    # 查找用户
    db_user = await prisma.user.find_unique(where={"email": user.email})
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # 验证密码 - 直接比较明文密码和哈希密码
    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # 创建访问令牌
    token = create_access_token(
        data={"sub": str(db_user.user_id)},
        expires_delta=timedelta(days=30)
    )
    
    # 存储访问令牌到数据库
    await prisma.accesstoken.create(
        data={
            "token": token,
            "user_id": db_user.user_id,
            "expires_at": datetime.utcnow() + timedelta(days=30)
        }
    )
    
    return {
        "user_id": db_user.user_id,
        "token": token,
        "token_type": "bearer",
        "total_coins": db_user.total_coins
    }

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme), current_user=Depends(get_current_user)):
    # 从数据库中删除访问令牌
    await prisma.accesstoken.delete_many(where={"token": token})
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user=Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserProfileResponse)
async def update_me(update: UserUpdate, current_user=Depends(get_current_user)):
    update_data = {}
    
    # 更新用户名
    if update.username is not None:
        # 检查用户名是否已被使用
        existing = await prisma.user.find_first(
            where={
                "username": update.username,
                "NOT": {"user_id": current_user.user_id}
            }
        )
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        update_data["username"] = update.username
    
    # 更新密码
    if update.password is not None:
        update_data["password_hash"] = hash_password(update.password)
        # 密码更新后使所有令牌失效
        await prisma.accesstoken.delete_many(where={"user_id": current_user.user_id})
    
    # 如果没有更新数据
    if not update_data:
        return current_user
    
    # 执行更新
    updated_user = await prisma.user.update(
        where={"user_id": current_user.user_id},
        data=update_data
    )
    return updated_user