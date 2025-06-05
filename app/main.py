from fastapi import FastAPI
from app.api import user
from app.api import todo_category
from app.db import prisma

app = FastAPI()

@app.on_event("startup")
async def startup():
    await prisma.connect()

@app.on_event("shutdown")
async def shutdown():
    await prisma.disconnect()

app.include_router(user.router, prefix="/api/users", tags=["Users"])
app.include_router(todo_category.router, prefix="/api/todo-categories", tags=["Todo Categories"])