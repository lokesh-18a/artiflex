from pydantic import BaseModel, EmailStr
from typing import Optional
from models import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProductCreate(BaseModel):
    name: str
    category: str
    artist_notes: str
    price_usd: float
    stock: int
    ai_generated_description: str
    image_filename: str

class Token(BaseModel):
    access_token: str
    token_type: str