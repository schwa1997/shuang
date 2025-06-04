from fastapi import APIRouter, HTTPException, Depends
from prisma_client import Prisma
from pydantic import BaseModel
from jose import jwt, JWTError
from typing import Optional, List
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import datetime
from enum import Enum
import os

# 使用环境变量
SECRET_KEY = os.getenv("SECRET_KEY", "schwa")  # 默认值仅用于开发
ALGORITHM = "HS256"
security = HTTPBearer()

router = APIRouter(prefix="/api/todos", tags=["todos"])

class TransactionType(str, Enum):
    TASK_COMPLETION = "TASK_COMPLETION"
    STREAK_BONUS = "STREAK_BONUS"
    REDEEM_REWARD = "REDEEM_REWARD"
    PENALTY = "PENALTY"

class TodoCategoryResponse(BaseModel):
    category_id: int
    category_name: str
    difficulty_multiplier: float

class TodoCreateRequest(BaseModel):
    title: str
    description: str = ""
    due_date: str
    category_id: int

class TodoUpdateRequest(BaseModel):
    title: Optional[str]
    description: Optional[str]
    due_date: Optional[str]
    category_id: Optional[int]
    completed: Optional[bool]

class TodoResponse(BaseModel):
    todo_id: int
    user_id: int
    title: str
    description: str
    due_date: datetime.datetime
    completed: bool
    base_coin_value: int
    category: TodoCategoryResponse

class CompleteTodoResponse(BaseModel):
    todo: TodoResponse
    coins_earned: int
    total_coins: int

@router.post("/", response_model=dict)
async def create_todo(
    data: TodoCreateRequest, 
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
    
    # 获取category信息
    category = await db.todocategory.find_unique(where={"category_id": data.category_id})
    if not category:
        raise HTTPException(400, "Category not found")
    
    # 创建todo
    todo = await db.todo.create(data={
        "user_id": user_id,
        "title": data.title,
        "description": data.description,
        "due_date": data.due_date,
        "category_id": data.category_id
    })
    
    estimated_reward = int(todo.base_coin_value * category.difficulty_multiplier)
    
    return {
        "todo_id": todo.todo_id,
        "base_coin_value": todo.base_coin_value,
        "difficulty_multiplier": category.difficulty_multiplier,
        "estimated_reward": estimated_reward
    }

@router.get("/", response_model=List[TodoResponse])
async def get_todos(
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
    
    # 获取todos并包含关联的category信息
    todos = await db.todo.find_many(
        where={"user_id": user_id},
        include={"category": True}
    )
    
    return todos

@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: int, 
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
    
    # 获取单个todo并包含关联的category信息
    todo = await db.todo.find_unique(
        where={"todo_id": todo_id},
        include={"category": True}
    )
    
    if not todo or todo.user_id != user_id:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int, 
    data: TodoUpdateRequest, 
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
    
    # 验证todo存在且属于用户
    todo = await db.todo.find_unique(
        where={"todo_id": todo_id},
        include={"category": True}
    )
    if not todo or todo.user_id != user_id:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # 如果尝试更新分类，验证新分类存在
    if data.category_id is not None:
        category_exists = await db.todocategory.find_unique(where={"category_id": data.category_id})
        if not category_exists:
            raise HTTPException(status_code=400, detail="Category not found")
    
    # 更新todo
    updated = await db.todo.update(
        where={"todo_id": todo_id},
        data=data.dict(exclude_unset=True),
        include={"category": True}  # 返回更新后的todo并包含category信息
    )
    
    return updated

# ... complete_todo 和 delete_todo 方法也需要类似修改 ...

# 添加依赖函数（在文件底部）
def get_db():
    from main import db
    return db