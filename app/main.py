from fastapi import FastAPI
from app.db import prisma
from app.api import api_router


app = FastAPI()

@app.on_event("startup")
async def startup():
    await prisma.connect()

@app.on_event("shutdown")
async def shutdown():
    await prisma.disconnect()

app.include_router(api_router)