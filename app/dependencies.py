# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.db import prisma
from app.core.security import verify_token
from app.models.user import UserProfileResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 1. 验证JWT令牌
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. 检查令牌是否在数据库中有效
    access_token = await prisma.accesstoken.find_unique(where={"token": token})
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. 获取用户信息
    user_id = int(payload.get("sub"))
    user = await prisma.user.find_unique(where={"user_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 返回用户对象（包含必要的字段）
    return UserProfileResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        total_coins=user.total_coins
    )