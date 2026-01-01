"""
Authentication utilities for Executive Portal.
Provides JWT token generation/validation and password hashing using bcrypt.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .db_connection_new import DBSession
from .entities import Executive, decode_uuid

from src.logging.logging import get_logger
logger = get_logger("auth")

# JWT Configuration
SECRET_KEY = "mt-rag-executive-portal-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing context - using argon2 (no password length limit, more secure than bcrypt)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# HTTP Bearer security scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using argon2."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created access token for: {data.get('sub', 'unknown')}")
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        return None


async def get_executive_by_email(db: AsyncSession, email: str) -> Optional[Executive]:
    """Get an executive by their email address."""
    result = await db.execute(select(Executive).filter_by(email=email))
    return result.scalar_one_or_none()


async def get_executive_by_id(db: AsyncSession, executive_id: bytes) -> Optional[Executive]:
    """Get an executive by their ID."""
    result = await db.execute(select(Executive).filter_by(id=executive_id))
    return result.scalar_one_or_none()


async def get_current_executive(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(lambda: None)  # Will be overridden in routes
) -> Executive:
    """
    Dependency to get the current authenticated executive from JWT token.
    Returns the Executive object if valid, raises HTTPException otherwise.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        logger.warning("Invalid or expired token")
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        logger.warning("Token missing subject claim")
        raise credentials_exception
    
    return {"email": email, "payload": payload}


def generate_secure_password(length: int = 12) -> str:
    """Generate a secure random password for admin invites."""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password
