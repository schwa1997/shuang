# app/models/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserRegisterResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    total_coins: int

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserLoginResponse(BaseModel):
    user_id: int
    token: str
    token_type: str
    total_coins: int

class UserProfileResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    total_coins: int

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None