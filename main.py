import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 0. 首先确保加载环境变量
load_dotenv()

# 1. 在导入任何 Prisma 相关模块前检查并生成客户端
# 替换为统一变量名，确保一致性
PRISMA_CLIENT_INIT = Path(__file__).parent / "prisma" / "prisma_client" / "__init__.py"


if not PRISMA_CLIENT_INIT.exists():
    print("Prisma client not found. Generating...")
    try:
        os.system("chmod -R a+rwx .")
        os.system("pip install prisma")
        from prisma.cli import prisma
        schema_path = Path(__file__).parent / "prisma" / "schema.prisma"
        prisma.run(["generate", f"--schema={str(schema_path)}"])
        print("✔ Prisma client generated successfully")
        if not PRISMA_CLIENT_INIT.exists():
            print(f"❌ Failed to generate client at {PRISMA_CLIENT_INIT}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating Prisma client: {e}")
        sys.exit(1)


# 2. 现在安全导入 Prisma 相关模块
from prisma_client import Prisma 
from typing import Union, List
from fastapi import FastAPI, Body, APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 3. 导入路由（在 Prisma 初始化后）
from routes.users import router as users_router, get_current_user
from routes.todos import router as todos_router, create_todo
from routes.categories import router as categories_router

# 4. 初始化应用
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

# 初始化Prisma
db = Prisma(datasource={"url": DATABASE_URL})

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
security = HTTPBearer()

@app.on_event("startup")
async def startup():
    print("Connecting to database...")
    await db.connect()
    print("Database connected")
    
    # 应用数据库迁移
    print("Applying database migrations...")
    await db.push()
    print("Database migrations applied")

@app.on_event("shutdown")
async def shutdown():
    if db.is_connected():
        print("Disconnecting from database...")
        await db.disconnect()
        print("Database disconnected")

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(users_router)
app.include_router(todos_router)
app.include_router(categories_router)

@app.get("/health")
async def health_check():
    status = {
        "status": "ok",
        "database": "connected" if db.is_connected() else "disconnected",
        "prisma_client": "generated" if PRISMA_CLIENT_INIT.exists() else "missing"
    }
    return status
