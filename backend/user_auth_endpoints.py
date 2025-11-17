"""
User Authentication Endpoints

Handles user registration, login, and profile management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import bcrypt
import os
import re
import redis
import requests
from jose import jwt, JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_db
from database_models import User

# Redis client for account lockout tracking
REDIS_URL = os.getenv("REDIS_URL", "redis://fantasy_cricket_redis:6379")
redis_client = redis.from_url(REDIS_URL)

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Turnstile configuration
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    turnstile_token: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    turnstile_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash - supports both bcrypt and passlib formats"""
    try:
        # Try bcrypt verification first (new format)
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, AttributeError):
        # Fall back to passlib for legacy passwords
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.verify(plain_password, hashed_password)
        except:
            return False


def verify_turnstile_token(token: str, remote_ip: str = None) -> bool:
    """
    Verify Cloudflare Turnstile token with Cloudflare API
    Returns True if verification succeeds, False otherwise
    """
    if not TURNSTILE_SECRET_KEY:
        # If Turnstile is not configured, skip verification (development mode)
        print("Warning: TURNSTILE_SECRET_KEY not configured, skipping verification")
        return True

    try:
        # Call Cloudflare Turnstile verification endpoint
        verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            "secret": TURNSTILE_SECRET_KEY,
            "response": token
        }

        if remote_ip:
            payload["remoteip"] = remote_ip

        response = requests.post(verify_url, json=payload, timeout=5)
        result = response.json()

        # Log verification result for debugging
        print(f"Turnstile verification result: {result}")
        if not result.get("success", False):
            print(f"Turnstile verification failed. Error codes: {result.get('error-codes', [])}")

        return result.get("success", False)
    except Exception as e:
        print(f"Turnstile verification error: {e}")
        # Fail closed for security - if verification fails, deny access
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"

    return True, ""


def check_account_lockout(email: str) -> tuple[bool, int]:
    """
    Check if account is locked due to failed login attempts.
    Returns (is_locked, remaining_seconds)
    """
    lockout_key = f"lockout:{email}"
    attempts_key = f"login_attempts:{email}"

    try:
        # Check if account is currently locked
        lockout_ttl = redis_client.ttl(lockout_key)
        if lockout_ttl > 0:
            return True, lockout_ttl

        # Check failed attempts count
        attempts = redis_client.get(attempts_key)
        if attempts and int(attempts) >= 5:
            # Lock account for 30 minutes
            redis_client.setex(lockout_key, 1800, "locked")  # 30 minutes = 1800 seconds
            redis_client.delete(attempts_key)
            return True, 1800

        return False, 0
    except Exception as e:
        # If Redis fails, allow login (fail open for availability)
        print(f"Redis error in check_account_lockout: {e}")
        return False, 0


def record_failed_login(email: str):
    """Record a failed login attempt"""
    attempts_key = f"login_attempts:{email}"
    try:
        # Increment attempts counter, set expiry to 15 minutes if new
        current = redis_client.incr(attempts_key)
        if current == 1:
            redis_client.expire(attempts_key, 900)  # 15 minutes = 900 seconds
    except Exception as e:
        print(f"Redis error in record_failed_login: {e}")


def clear_failed_logins(email: str):
    """Clear failed login attempts after successful login"""
    attempts_key = f"login_attempts:{email}"
    lockout_key = f"lockout:{email}"
    try:
        redis_client.delete(attempts_key)
        redis_client.delete(lockout_key)
    except Exception as e:
        print(f"Redis error in clear_failed_logins: {e}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return user data"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def register(user_data: UserRegister, request: Request, db: Session = Depends(get_db)):
    """Register a new user account"""

    # Verify Turnstile token
    client_ip = request.client.host if request.client else None
    if not verify_turnstile_token(user_data.turnstile_token, client_ip):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security verification failed. Please try again."
        )

    # Check if email already exists
    existing_user = db.query(User).filter_by(email=user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Create new user
    hashed_pw = hash_password(user_data.password)
    new_user = User(
        email=user_data.email.lower(),
        password_hash=hashed_pw,
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False,  # Can add email verification later
        is_admin=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create access token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email, "is_admin": False}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "is_admin": new_user.is_admin
        }
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # Only 5 login attempts per minute per IP
async def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password"""

    # Verify Turnstile token
    client_ip = request.client.host if request.client else None
    if not verify_turnstile_token(credentials.turnstile_token, client_ip):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security verification failed. Please try again."
        )

    email_lower = credentials.email.lower()

    # Check if account is locked
    is_locked, remaining_seconds = check_account_lockout(email_lower)
    if is_locked:
        minutes_remaining = remaining_seconds // 60
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to multiple failed login attempts. Try again in {minutes_remaining} minutes."
        )

    # Find user by email
    user = db.query(User).filter_by(email=email_lower).first()
    if not user:
        record_failed_login(email_lower)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        record_failed_login(email_lower)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Clear failed login attempts on successful login
    clear_failed_logins(email_lower)

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "is_admin": user.is_admin}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin
        }
    }


@router.get("/me")
async def get_current_user(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get current user profile"""

    user_id = token_data.get("sub") or token_data.get("user_id")
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_admin": user.is_admin,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None
    }


@router.post("/toggle-mode")
async def toggle_admin_mode(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Toggle between admin and user mode for admin users"""
    
    user_id = token_data.get("sub") or token_data.get("user_id")
    user = db.query(User).filter_by(id=user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can toggle mode"
        )
    
    # Get current mode from token
    current_mode_is_admin = token_data.get("is_admin", False)
    
    # Toggle the mode
    new_mode_is_admin = not current_mode_is_admin
    
    # Create new token with toggled mode
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "is_admin": new_mode_is_admin}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "mode": "admin" if new_mode_is_admin else "user",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin  # Always true, but current mode varies
        }
    }
