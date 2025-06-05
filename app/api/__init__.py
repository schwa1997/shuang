# # app/routers/__init__.py
# from fastapi import APIRouter
# from .user import router as user_router
# from .todo_category import router as todo_category_router
# from .todo import router as todo_router
# router = APIRouter()

# router.include_router(user_router, prefix="/api/users", tags=["users"])
# router.include_router(todo_category_router, prefix="/api/todo-categories", tags=["todo_categories"])
# router.include_router(todo_router, prefix="/api/todos", tags=["todos"])