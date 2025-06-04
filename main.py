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

import os
from dotenv import load_dotenv

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

db = Prisma()

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "schwa")
DATABASE_URL = os.getenv("DATABASE_URL")
ALGORITHM = "HS256"
security = HTTPBearer()

db = Prisma(datasource={"url": DATABASE_URL})

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


@app.get("/")
def read_root():
    return {"Hello": "World"}


app.include_router(users_router)
app.include_router(todos_router)
app.include_router(categories_router)
