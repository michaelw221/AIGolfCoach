# backend/db/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- SWING JOB SCHEMAS ---
class SwingJobResponse(BaseModel):
    id: str
    status: str
    analysis_results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True