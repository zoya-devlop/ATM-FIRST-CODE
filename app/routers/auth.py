
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.db import get_connection
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import os
import hashlib

router = APIRouter()
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "zoy-super-secret-key")
ALGORITHM = "HS256"

# Frontend se data lene ka structure
class UserSignup(BaseModel):
    email: str
    name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# Password chhupane ki machine
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed

# Token (ID Card) banane ki machine
def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Tera asil Security Guard
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(401, "Invalid token")
        return user_id
    except:
        raise HTTPException(401, "Invalid token")

# 🚀 1. THE SIGNUP API
@router.post("/api/auth/signup")
def signup_api(user: UserSignup):
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Table ensure karo
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            password TEXT,
            api_token TEXT,
            created_at TEXT
        )
        """)
        
        hashed = hash_password(user.password)
        api_token = hashlib.sha256(f"{user.email}{datetime.now()}".encode()).hexdigest()[:32]
        
        try:
            cursor.execute(
                "INSERT INTO users (email, name, password, api_token, created_at) VALUES (?, ?, ?, ?, ?)",
                (user.email, user.name, hashed, api_token, datetime.now().isoformat())
            )
            return {"message": "Account successfully ban gaya! Welcome Boss."}
        except:
            raise HTTPException(400, "Yeh email pehle se exist karta hai!")

# 🔐 2. THE LOGIN API (Updated to send Name)
@router.post("/api/auth/login")
def login_api(user: UserLogin):
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Change 1: Hum id, password ke saath 'name' bhi nikal rahe hain
        cursor.execute("SELECT id, password, name FROM users WHERE email = ?", (user.email,))
        db_user = cursor.fetchone()
        
        if not db_user or not verify_password(user.password, db_user[1]):
            raise HTTPException(401, "Galat email ya password!")
        
        token = create_token(db_user[0])
        
        # Change 2: Ab hum wapas reply mein 'name' bhi bhej rahe hain taaki purana UI crash na ho
        return {
            "access_token": token, 
            "user_id": db_user[0], 
            "user": {
                "name": db_user[2], 
                "email": user.email
            },
            "name": db_user[2],
            "message": "Login Successful!"
        }