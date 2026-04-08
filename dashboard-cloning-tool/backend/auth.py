import jwt
import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, Header
from config import config
from database import get_user_by_email

def create_token(email: str, role: str) -> str:
    payload = {
        "sub": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=config.JWT_EXPIRE_HOURS)
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    user = get_user_by_email(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_admin(user: dict = None):
    if user["role"] not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def require_superadmin(user: dict = None):
    if user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user

def generate_invite_token() -> str:
    return secrets.token_urlsafe(32)

def invite_expires_at() -> str:
    return (datetime.utcnow() + timedelta(hours=config.INVITE_EXPIRE_HOURS)).isoformat()
