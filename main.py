import os  # 添加这行
from dotenv import load_dotenv  # 添加这行
from typing import Union, List
from fastapi import FastAPI, Body, APIRouter, HTTPException, Depends
from prisma import Prisma
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import jwt, JWTError
from routes.users import router as users_router, get_current_user
from routes.todos import router as todos_router, create_todo
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from routes.categories import router as categories_router

# 加载环境变量
load_dotenv()  # 本地开发时加载 .env 文件

app = FastAPI()

# 允许所有来源跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 使用环境变量
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "schwa")  # 默认值仅用于开发

# 修复：初始化Prisma时传入数据库URL
db = Prisma(datasource={"url": DATABASE_URL})

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
security = HTTPBearer()

@app.on_event("startup")
async def startup():
    await db.connect()
    # 添加数据库迁移（关键！）
    await db.push()  # 自动创建数据库表

@app.on_event("shutdown")
async def shutdown():
    if db.is_connected():
        await db.disconnect()

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(users_router)
app.include_router(todos_router)
app.include_router(categories_router)