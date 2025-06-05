from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    password: str | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str | None
