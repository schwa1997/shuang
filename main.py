import os
from dotenv import load_dotenv
from prisma_client import Prisma
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi.security import HTTPBearer
from routes.users import router as users_router
from routes.todos import router as todos_router
from routes.categories import router as categories_router

# 加载环境变量
load_dotenv()

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

db = Prisma(datasource={"url": DATABASE_URL})

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
security = HTTPBearer()

@app.on_event("startup")
async def startup():
    await db.connect()
    await db.push()

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

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "database": "connected" if db.is_connected() else "disconnected"
    }
