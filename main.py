import os
import sys
from dotenv import load_dotenv
from prisma_client import Prisma
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi.security import HTTPBearer
from routes.users import router as users_router
from routes.todos import router as todos_router
from routes.categories import router as categories_router

# 添加生成的客户端目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

app = FastAPI()

# 创建全局数据库实例
db = Prisma()

# 允许所有来源跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 使用环境变量
SECRET_KEY = os.getenv("SECRET_KEY", "schwa")  # 默认值仅用于开发

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
security = HTTPBearer()

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    if db.is_connected():
        await db.disconnect()

# 添加全局数据库依赖
async def get_db():
    return db

app.dependency_overrides[get_db] = get_db

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(users_router)
app.include_router(todos_router)
app.include_router(categories_router)

@app.get("/health")
async def health_check(db: Prisma = Depends(get_db)):
    return {
        "status": "ok",
        "database": "connected" if db.is_connected() else "disconnected"
    }