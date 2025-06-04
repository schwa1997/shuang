from fastapi import APIRouter, HTTPException, Depends, Body, Header
from prisma import Prisma
from pydantic import BaseModel
from jose import jwt, JWTError
from typing import Optional, List
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import datetime
from enum import Enum

SECRET_KEY = "your-secret"
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
async def create_todo(data: TodoCreateRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = Prisma()
    await db.connect()
    
    # 获取category信息
    category = await db.todocategory.find_unique(where={"category_id": data.category_id})
    if not category:
        await db.disconnect()
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
    await db.disconnect()
    
    return {
        "todo_id": todo.todo_id,
        "base_coin_value": todo.base_coin_value,
        "difficulty_multiplier": category.difficulty_multiplier,
        "estimated_reward": estimated_reward
    }

@router.get("/", response_model=List[TodoResponse])
async def get_todos(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = Prisma()
    await db.connect()
    
    # 获取todos并包含关联的category信息
    todos = await db.todo.find_many(
        where={"user_id": user_id},
        include={"category": True}
    )
    
    await db.disconnect()
    return todos

@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = Prisma()
    await db.connect()
    
    # 获取单个todo并包含关联的category信息
    todo = await db.todo.find_unique(
        where={"todo_id": todo_id},
        include={"category": True}
    )
    
    await db.disconnect()
    
    if not todo or todo.user_id != user_id:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, data: TodoUpdateRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = Prisma()
    await db.connect()
    
    # 验证todo存在且属于用户
    todo = await db.todo.find_unique(
        where={"todo_id": todo_id},
        include={"category": True}
    )
    if not todo or todo.user_id != user_id:
        await db.disconnect()
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # 如果尝试更新分类，验证新分类存在
    if data.category_id is not None:
        category_exists = await db.todocategory.find_unique(where={"category_id": data.category_id})
        if not category_exists:
            await db.disconnect()
            raise HTTPException(status_code=400, detail="Category not found")
    
    # 更新todo
    updated = await db.todo.update(
        where={"todo_id": todo_id},
        data=data.dict(exclude_unset=True),
        include={"category": True}  # 返回更新后的todo并包含category信息
    )
    
    await db.disconnect()
    return updated

# @router.post("/{todo_id}/complete", response_model=CompleteTodoResponse)
# async def complete_todo(todo_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
#     token = credentials.credentials
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("user_id")
#         if not user_id:
#             raise HTTPException(status_code=403, detail="Forbidden")
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")
    
#     db = Prisma()
#     await db.connect()
    
#     todo = await db.todo.find_unique(
#         where={"todo_id": todo_id}
#     )
#     user = await db.user.find_unique(
#         where={"user_id": user_id}
#     )
#     if not todo or todo.user_id != user_id:
#         await db.disconnect()
#         raise HTTPException(status_code=404, detail="Todo not found")
    
#     if todo.completed:
#         await db.disconnect()
#         return CompleteTodoResponse(
#             todo=todo,
#             coins_earned=0,
#             total_coins=user.total_coins
#         )
    
#     # 计算奖励金额
#     multiplier = todo.category.difficulty_multiplier if todo.category else 1.0
#     coins_earned = int(todo.base_coin_value * multiplier)
    
#     # 获取当前时间
#     now = datetime.datetime.utcnow()
    
#     # 使用事务执行多个操作
#     try:
#         # 1. 更新todo状态为已完成
#         updated_todo = await db.todo.update(
#             where={"todo_id": todo_id},
#             data={
#                 "completed": True,
#                 "completion_date": now
#             },
#             include={"category": True}
#         )
        
#         # 2. 创建coin transaction记录
#         await db.cointransaction.create({
#             "user_id": user_id,
#             "amount": coins_earned,
#             "transaction_type": TransactionType.TASK_COMPLETION,
#             "transaction_time":  datetime.datetime.utcnow(),
#             "related_todo_id": todo_id
#         })
        
#         # 3. 更新用户总金币
#         updated_user = await db.user.update(
#             where={"user_id": user_id},
#             data={"total_coins": {"increment": coins_earned}}
#         )
        
#     except Exception as e:
#         await db.disconnect()
#         raise HTTPException(status_code=500, detail=f"Failed to complete todo: {str(e)}")
    
#     await db.disconnect()
#     return CompleteTodoResponse(
#         todo=updated_todo,
#         coins_earned=coins_earned,
#         total_coins=updated_user.total_coins
#     )

@router.post("/{todo_id}/complete", response_model=CompleteTodoResponse)
async def complete_todo(todo_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """标记todo为已完成并添加coin transaction"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = Prisma()
    await db.connect()
    
    # 获取todo（包含category）并验证
    todo = await db.todo.find_unique(
        where={"todo_id": todo_id},
        include={"category": True}
    )
    if not todo or todo.user_id != user_id:
        await db.disconnect()
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # 如果todo已经完成，直接返回
    if todo.completed:
        user = await db.user.find_unique(where={"user_id": user_id})
        await db.disconnect()
        # 将Prisma模型转换为Pydantic模型
        todo_response = TodoResponse(
            todo_id=todo.todo_id,
            user_id=todo.user_id,
            title=todo.title,
            description=todo.description,
            due_date=todo.due_date,
            base_coin_value=todo.base_coin_value,
            completed=todo.completed,
            completion_date=todo.completion_date,
            category=TodoCategoryResponse(
                category_id=todo.category.category_id,
                category_name=todo.category.category_name,
                difficulty_multiplier=todo.category.difficulty_multiplier
            ) if todo.category else None
        )
        return CompleteTodoResponse(
            todo=todo_response,
            coins_earned=0,
            total_coins=user.total_coins if user else 0
        )
    
    # 计算奖励金额
    multiplier = todo.category.difficulty_multiplier if todo.category else 1.0
    coins_earned = int(todo.base_coin_value * multiplier)
    
    # 获取当前时间
    now = datetime.datetime.utcnow()
    
    try:
        # 1. 更新todo状态为已完成
        updated_todo = await db.todo.update(
            where={"todo_id": todo_id},
            data={
                "completed": True,
                "completion_date": now
            },
            include={"category": True}
        )
        
        # 2. 创建coin transaction记录
        await db.cointransaction.create(data={
            "user_id": user_id,
            "amount": coins_earned,
            "transaction_type": TransactionType.TASK_COMPLETION,
            "transaction_time": now,
            "related_todo_id": todo_id
        })
        
        # 3. 更新用户总金币
        updated_user = await db.user.update(
            where={"user_id": user_id},
            data={"total_coins": {"increment": coins_earned}}
        )
        
    except Exception as e:
        await db.disconnect()
        raise HTTPException(status_code=500, detail=f"Failed to complete todo: {str(e)}")
    
    # 将Prisma模型转换为Pydantic模型
    todo_response = TodoResponse(
        todo_id=updated_todo.todo_id,
        user_id=updated_todo.user_id,
        title=updated_todo.title,
        description=updated_todo.description,
        due_date=updated_todo.due_date,
        base_coin_value=updated_todo.base_coin_value,
        completed=updated_todo.completed,
        completion_date=updated_todo.completion_date,
        category=TodoCategoryResponse(
            category_id=updated_todo.category.category_id,
            category_name=updated_todo.category.category_name,
            difficulty_multiplier=updated_todo.category.difficulty_multiplier
        ) if updated_todo.category else None
    )
    
    await db.disconnect()
    return CompleteTodoResponse(
        todo=todo_response,
        coins_earned=coins_earned,
        total_coins=updated_user.total_coins
    )

@router.delete("/{todo_id}")
async def delete_todo(todo_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = Prisma()
    await db.connect()
    
    todo = await db.todo.find_unique(where={"todo_id": todo_id})
    if not todo or todo.user_id != user_id:
        await db.disconnect()
        raise HTTPException(status_code=404, detail="Todo not found")
    
    await db.todo.delete(where={"todo_id": todo_id})
    await db.disconnect()
    return {"detail": "Todo deleted"}