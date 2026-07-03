from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Frontend se aane wale email/password ka format
class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/api/auth/login")
def login(data: LoginRequest):
    # Abhi ke liye hum default admin ko direct entry de rahe hain
    if data.email == "admin@orbitcloud.local" and data.password == "ChangeMe123!":
        return {
            "token": "orbit-local-admin-token",
            "user": {"name": "Zoya Admin"}
        }
    
    raise HTTPException(status_code=401, detail="Galat email ya password!")