# app/models/todo_category.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TodoCategoryCreate(BaseModel):
    category_name: str
    difficulty_multiplier: float = 1.0

class TodoCategoryResponse(BaseModel):
    category_id: int
    category_name: str
    difficulty_multiplier: float
    user_id: int
    created_at: datetime

class TodoCategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    difficulty_multiplier: Optional[float] = None