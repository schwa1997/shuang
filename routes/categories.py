from fastapi import APIRouter, HTTPException, Depends
from prisma_client import Prisma
from pydantic import BaseModel
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os

# 使用环境变量
SECRET_KEY = os.getenv("SECRET_KEY", "schwa")  # 默认值仅用于开发
ALGORITHM = "HS256"
security = HTTPBearer()

router = APIRouter(prefix="/api/categories", tags=["categories"])

class CategoryCreateRequest(BaseModel):
    category_name: str
    difficulty_multiplier: float = 1.0

class CategoryUpdateRequest(BaseModel):
    category_name: Optional[str]
    difficulty_multiplier: Optional[float]

# 获取所有分类
@router.get("/")
async def get_categories(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Prisma = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    categories = await db.todocategory.find_many()
    return categories

# 新建分类
@router.post("/")
async def create_category(
    data: CategoryCreateRequest, 
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Prisma = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    category = await db.todocategory.create(data={
        "user_id": user_id,
        "category_name": data.category_name,
        "difficulty_multiplier": data.difficulty_multiplier
    })
    
    return category

# 编辑分类
@router.patch("/{category_id}")
async def update_category(
    category_id: int, 
    data: CategoryUpdateRequest, 
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Prisma = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    category = await db.todocategory.find_unique(where={"category_id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    updated = await db.todocategory.update(
        where={"category_id": category_id}, 
        data=data.dict(exclude_unset=True)
    )
    
    return updated

# 删除分类
@router.delete("/{category_id}")
async def delete_category(
    category_id: int, 
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Prisma = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    category = await db.todocategory.find_unique(where={"category_id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    await db.todocategory.delete(where={"category_id": category_id})
    return {"detail": "Category deleted"}

# 添加依赖函数（在文件底部）
def get_db():
    from main import db
    return db