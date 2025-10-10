from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt
import hashlib
import secrets
from typing import Optional
import os

app = FastAPI(title="Fantasy Cricket API")

# Simple configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"

# In-memory storage for testing (replace with database later)
users_db = {}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fantcric.fun", "https://www.fantcric.fun", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: str

# Simple password hashing (SHA256 - secure enough for prototype)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

# Endpoints
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "production",
        "location": "Amsterdam, Netherlands",
        "powered_by": "LeafCloud sustainable infrastructure"
    }

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserRegister):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = secrets.token_urlsafe(16)
    users_db[user.email] = {
        "id": user_id,
        "email": user.email,
        "full_name": user.full_name,
        "password_hash": hash_password(user.password),
        "created_at": datetime.utcnow().isoformat()
    }
    
    return UserResponse(
        id=user_id,
        email=user.email,
        full_name=user.full_name,
        created_at=users_db[user.email]["created_at"]
    )

@app.post("/api/auth/login")
async def login(user: UserLogin):
    if user.email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    stored_user = users_db[user.email]
    if not verify_password(user.password, stored_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode(
        {"sub": stored_user["id"], "email": user.email, "exp": datetime.utcnow() + timedelta(days=30)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(
            id=stored_user["id"],
            email=stored_user["email"],
            full_name=stored_user["full_name"],
            created_at=stored_user["created_at"]
        )
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
