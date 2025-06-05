# app/models/todo.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class TransactionType(str, Enum):
    TASK_COMPLETION = "TASK_COMPLETION"
    STREAK_BONUS = "STREAK_BONUS"
    REDEEM_REWARD = "REDEEM_REWARD"
    PENALTY = "PENALTY"

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    category_id: Optional[int] = None

class TodoResponse(BaseModel):
    todo_id: int
    user_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    base_coin_value: int = Field(default=5)
    completed: bool = Field(default=False)
    completion_date: Optional[datetime] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None  # 用于显示类别名称
    difficulty_multiplier: Optional[float] = None  # 用于显示难度系数

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    category_id: Optional[int] = None

class TodoComplete(BaseModel):
    completed: bool = True