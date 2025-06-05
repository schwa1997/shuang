# app/routers/todo_category.py
from fastapi import APIRouter, HTTPException, Depends, status
from app.models.todo_category import TodoCategoryCreate, TodoCategoryResponse, TodoCategoryUpdate
from app.db import prisma
from app.dependencies import get_current_user
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=TodoCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category: TodoCategoryCreate, current_user=Depends(get_current_user)):
    # 检查类别名称是否唯一（同一用户下）
    existing = await prisma.todocategory.find_first(
        where={
            "user_id": current_user.user_id,
            "category_name": category.category_name
        }
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists for this user"
        )
    
    # 创建新类别
    new_category = await prisma.todocategory.create(
        data={
            "category_name": category.category_name,
            "difficulty_multiplier": category.difficulty_multiplier,
            "user_id": current_user.user_id,
            "created_at": datetime.now()
        }
    )
    return new_category

@router.get("/", response_model=list[TodoCategoryResponse])
async def get_user_categories(current_user=Depends(get_current_user)):
    categories = await prisma.todocategory.find_many(
        where={"user_id": current_user.user_id},
        order={"created_at": "desc"}
    )
    return categories

@router.get("/{category_id}", response_model=TodoCategoryResponse)
async def get_category(category_id: int, current_user=Depends(get_current_user)):
    category = await prisma.todocategory.find_unique(
        where={"category_id": category_id}
    )
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    if category.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this category"
        )
    
    return category

@router.put("/{category_id}", response_model=TodoCategoryResponse)
async def update_category(
    category_id: int, 
    update: TodoCategoryUpdate, 
    current_user=Depends(get_current_user)
):
    # 先获取现有类别
    existing = await prisma.todocategory.find_unique(
        where={"category_id": category_id}
    )
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    if existing.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this category"
        )
    
    update_data = {}
    
    # 更新类别名称
    if update.category_name is not None:
        # 检查新名称是否已被使用（同一用户下）
        name_exists = await prisma.todocategory.find_first(
            where={
                "user_id": current_user.user_id,
                "category_name": update.category_name,
                "NOT": {"category_id": category_id}
            }
        )
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name already exists for this user"
            )
        update_data["category_name"] = update.category_name
    
    # 更新难度系数
    if update.difficulty_multiplier is not None:
        if update.difficulty_multiplier <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Difficulty multiplier must be greater than 0"
            )
        update_data["difficulty_multiplier"] = update.difficulty_multiplier
    
    # 如果没有更新数据
    if not update_data:
        return existing
    
    # 执行更新
    updated_category = await prisma.todocategory.update(
        where={"category_id": category_id},
        data=update_data
    )
    return updated_category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, current_user=Depends(get_current_user)):
    # 先获取现有类别
    category = await prisma.todocategory.find_unique(
        where={"category_id": category_id},
        include={"todos": True}  # 检查是否有关联的待办事项
    )
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    if category.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this category"
        )
    
    # 检查是否有关联的待办事项
    if category.todos and len(category.todos) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with associated todos"
        )
    
    # 删除类别
    await prisma.todocategory.delete(where={"category_id": category_id})
    return