# app/routers/todo.py
from fastapi import APIRouter, HTTPException, Depends, status
from app.models.todo import TodoCreate, TodoResponse, TodoUpdate, TodoComplete, TransactionType
from app.db import prisma
from app.dependencies import get_current_user
from datetime import datetime
from app.core.security import calculate_coins_for_todo
from typing import Optional

router = APIRouter()

@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate, current_user=Depends(get_current_user)):
    # 验证类别是否属于当前用户（如果提供了类别ID）
    category = None
    if todo.category_id:
        category = await prisma.todocategory.find_unique(
            where={"category_id": todo.category_id}
        )
        if not category or category.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category or category does not belong to current user"
            )
    
    # 创建新待办事项
    new_todo = await prisma.todo.create(
        data={
            "user_id": current_user.user_id,
            "title": todo.title,
            "description": todo.description,
            "due_date": todo.due_date,
            "category_id": todo.category_id,
            "base_coin_value": 5  # 固定基础值
        }
    )
    
    # 添加类别信息到响应
    todo_response = TodoResponse(**new_todo.dict())
    if category:
        todo_response.category_name = category.category_name
        todo_response.difficulty_multiplier = category.difficulty_multiplier
    
    return todo_response

@router.get("/", response_model=list[TodoResponse])
async def get_user_todos(
    completed: Optional[bool] = None,
    category_id: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    # 构建查询条件
    where_conditions = {"user_id": current_user.user_id}
    
    if completed is not None:
        where_conditions["completed"] = completed
    
    if category_id is not None:
        where_conditions["category_id"] = category_id
    
    # 获取待办事项
    todos = await prisma.todo.find_many(
        where=where_conditions,
        include={"category": True},
        order={"due_date": "asc"}  # 按截止日期升序排列
    )
    
    # 转换为响应模型
    response_todos = []
    for todo in todos:
        todo_data = todo.dict()
        todo_data["category_name"] = todo.category.category_name if todo.category else None
        todo_data["difficulty_multiplier"] = todo.category.difficulty_multiplier if todo.category else 1.0
        response_todos.append(TodoResponse(**todo_data))
    
    return response_todos

@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int, current_user=Depends(get_current_user)):
    # 获取待办事项
    todo = await prisma.todo.find_unique(
        where={"todo_id": todo_id},
        include={"category": True}
    )
    
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    if todo.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this todo"
        )
    
    # 转换为响应模型
    todo_data = todo.dict()
    todo_data["category_name"] = todo.category.category_name if todo.category else None
    todo_data["difficulty_multiplier"] = todo.category.difficulty_multiplier if todo.category else 1.0
    
    return TodoResponse(**todo_data)

@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int, 
    update: TodoUpdate, 
    current_user=Depends(get_current_user)
):
    # 获取现有待办事项
    existing = await prisma.todo.find_unique(
        where={"todo_id": todo_id}
    )
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    if existing.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this todo"
        )
    
    # 验证类别（如果提供了类别ID）
    category = None
    if update.category_id:
        category = await prisma.todocategory.find_unique(
            where={"category_id": update.category_id}
        )
        if not category or category.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category or category does not belong to current user"
            )
    
    update_data = {}
    
    # 更新标题
    if update.title is not None:
        update_data["title"] = update.title
    
    # 更新描述
    if update.description is not None:
        update_data["description"] = update.description
    
    # 更新截止日期
    if update.due_date is not None:
        update_data["due_date"] = update.due_date
    
    # 更新类别
    if update.category_id is not None:
        update_data["category_id"] = update.category_id
    
    # 如果没有更新数据
    if not update_data:
        return await get_todo(todo_id, current_user)
    
    # 执行更新
    updated_todo = await prisma.todo.update(
        where={"todo_id": todo_id},
        data=update_data,
        include={"category": True}
    )
    
    # 转换为响应模型
    todo_data = updated_todo.dict()
    todo_data["category_name"] = updated_todo.category.category_name if updated_todo.category else None
    todo_data["difficulty_multiplier"] = updated_todo.category.difficulty_multiplier if updated_todo.category else 1.0
    
    return TodoResponse(**todo_data)

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int, current_user=Depends(get_current_user)):
    # 获取现有待办事项
    todo = await prisma.todo.find_unique(
        where={"todo_id": todo_id}
    )
    
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    if todo.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this todo"
        )
    
    # 删除待办事项
    await prisma.todo.delete(where={"todo_id": todo_id})
    return

@router.put("/{todo_id}/complete", response_model=TodoResponse)
async def complete_todo(
    todo_id: int, 
    complete: TodoComplete = TodoComplete(),
    current_user=Depends(get_current_user)
):
    # 获取现有待办事项
    todo = await prisma.todo.find_unique(
        where={"todo_id": todo_id},
        include={"category": True}
    )
    
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    if todo.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to complete this todo"
        )
    
    if todo.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Todo is already completed"
        )
    
    # 计算金币
    multiplier = todo.category.difficulty_multiplier if todo.category else 1.0
    coins_earned = calculate_coins_for_todo(todo.base_coin_value, multiplier)
    
    # 更新待办事项状态
    updated_todo = await prisma.todo.update(
        where={"todo_id": todo_id},
        data={
            "completed": True,
            "completion_date": datetime.utcnow()
        },
        include={"category": True}
    )
    
    # 创建金币交易记录
    await prisma.cointransaction.create(
        data={
            "user_id": current_user.user_id,
            "amount": coins_earned,
            "transaction_type": TransactionType.TASK_COMPLETION,
            "related_todo_id": todo_id
        }
    )
    
    # 更新用户总金币
    await prisma.user.update(
        where={"user_id": current_user.user_id},
        data={"total_coins": {"increment": coins_earned}}
    )
    
    # 转换为响应模型
    todo_data = updated_todo.dict()
    todo_data["category_name"] = updated_todo.category.category_name if updated_todo.category else None
    todo_data["difficulty_multiplier"] = updated_todo.category.difficulty_multiplier if updated_todo.category else 1.0
    
    return TodoResponse(**todo_data)