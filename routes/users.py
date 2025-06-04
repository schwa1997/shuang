from fastapi import APIRouter, HTTPException, Depends, Body
from prisma_client import Prisma
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# 使用环境变量
SECRET_KEY = os.getenv("SECRET_KEY", "schwa")  # 默认值仅用于开发
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/api/users", tags=["users"])

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Body(...), db: Prisma = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.user.find_unique(where={"user_id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class RegisterResponse(BaseModel):
    user_id: int
    total_coins: int
    streak_count: int

@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(data: RegisterRequest, db: Prisma = Depends(get_db)):
    if await db.user.find_first(where={"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    if await db.user.find_first(where={"username": data.username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed = get_password_hash(data.password)
    user = await db.user.create(data={
        "username": data.username,
        "email": data.email,
        "password_hash": hashed
    })
    
    return RegisterResponse(
        user_id=user.user_id, 
        total_coins=user.total_coins, 
        streak_count=user.streak_count
    )

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    token: str
    streak_count: int
    total_coins: int

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: Prisma = Depends(get_db)):
    user = await db.user.find_first(where={"email": data.email})
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"user_id": user.user_id})
    
    return LoginResponse(
        user_id=user.user_id,
        token=token,
        streak_count=user.streak_count,
        total_coins=user.total_coins
    )

class UserProfileResponse(BaseModel):
    username: str
    email: str
    total_coins: int
    streak_count: int
    last_active: Optional[str]

security = HTTPBearer()

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int, 
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Prisma = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.user.find_unique(where={"user_id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfileResponse(
        username=user.username,
        email=user.email,
        total_coins=user.total_coins,
        streak_count=user.streak_count,
        last_active=user.last_active_date.isoformat() if user.last_active_date else None
    )

# 添加依赖函数（在文件底部）
def get_db():
    from main import db
    return db