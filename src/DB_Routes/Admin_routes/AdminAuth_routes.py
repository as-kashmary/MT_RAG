"""
Admin Authentication Routes for the Admin Portal.
Handles admin login, profile retrieval, and password management.
"""

from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..entities import Admin, Company, decode_uuid, encode_uuid
from ..db_connection_new import DBSession
from ..auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)

from src.logging.logging import get_logger
logger = get_logger("admin_auth_routes")


# Pydantic models for request/response validation
class AdminLogin(BaseModel):
    username: str
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: dict


class AdminProfile(BaseModel):
    id: str
    username: str
    company_id: str
    company_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangePasswordResponse(BaseModel):
    success: bool
    message: str


# Router setup
router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

security = HTTPBearer()


async def get_admin_by_username(db: AsyncSession, username: str) -> Optional[Admin]:
    """Get an admin by their username."""
    result = await db.execute(select(Admin).filter_by(username=username))
    return result.scalar_one_or_none()


async def get_admin_by_id(db: AsyncSession, admin_id: bytes) -> Optional[Admin]:
    """Get an admin by their ID."""
    result = await db.execute(select(Admin).filter_by(id=admin_id))
    return result.scalar_one_or_none()


async def get_company_by_id(db: AsyncSession, company_id: bytes) -> Optional[Company]:
    """Get a company by its ID."""
    result = await db.execute(select(Company).filter_by(id=company_id))
    return result.scalar_one_or_none()


async def get_current_admin_from_token(
    db: AsyncSession,
    credentials: HTTPAuthorizationCredentials
) -> Admin:
    """Validate token and return current admin."""
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
    
    admin_id: str = payload.get("sub")
    user_type: str = payload.get("type")
    
    if admin_id is None or user_type != "admin":
        logger.warning("Token missing admin subject or incorrect type")
        raise credentials_exception
    
    admin = await get_admin_by_id(db, encode_uuid(admin_id))
    if admin is None:
        logger.warning(f"Admin not found for ID: {admin_id}")
        raise credentials_exception
    
    return admin


@router.post("/login", response_model=AdminTokenResponse)
async def login_admin(db: DBSession, data: AdminLogin):
    """
    Authenticate admin and return JWT token.
    """
    try:
        logger.info(f"Login attempt for admin: {data.username}")
        
        # Find admin by username
        admin = await get_admin_by_username(db, data.username)
        
        if admin is None:
            logger.warning(f"Admin not found: {data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Check if admin has a password set
        if admin.password_hash is None:
            logger.warning(f"Admin {data.username} has no password set")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password not set. Please contact your administrator."
            )
        
        # Verify password
        if not verify_password(data.password, admin.password_hash):
            logger.warning(f"Invalid password for admin: {data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Get company info
        company = await get_company_by_id(db, admin.company_id)
        company_name = company.name if company else "Unknown"
        
        # Create JWT token with admin ID and type
        admin_id_str = str(decode_uuid(admin.id))
        access_token = create_access_token(
            data={"sub": admin_id_str, "type": "admin"}
        )
        
        logger.info(f"Admin logged in successfully: {data.username}")
        
        return AdminTokenResponse(
            access_token=access_token,
            admin={
                "id": admin_id_str,
                "username": admin.username,
                "company_id": str(decode_uuid(admin.company_id)),
                "company_name": company_name
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=AdminProfile)
async def get_current_admin_profile(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get the current authenticated admin's profile.
    """
    try:
        admin = await get_current_admin_from_token(db, credentials)
        
        # Get company info
        company = await get_company_by_id(db, admin.company_id)
        company_name = company.name if company else "Unknown"
        
        logger.info(f"Profile retrieved for admin: {admin.username}")
        
        return AdminProfile(
            id=str(decode_uuid(admin.id)),
            username=admin.username,
            company_id=str(decode_uuid(admin.company_id)),
            company_name=company_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_admin_password(
    db: DBSession,
    data: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Change the current admin's password.
    Requires current password verification.
    """
    try:
        admin = await get_current_admin_from_token(db, credentials)
        
        # Verify current password
        if admin.password_hash and not verify_password(data.current_password, admin.password_hash):
            logger.warning(f"Invalid current password for admin: {admin.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if len(data.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long"
            )
        
        # Update password
        admin.password_hash = get_password_hash(data.new_password)
        await db.commit()
        
        logger.info(f"Password changed successfully for admin: {admin.username}")
        
        return ChangePasswordResponse(
            success=True,
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )
