"""
Executive routes for the Executive Portal.
Handles registration, login, profile management, and admin invitations.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..entities import Executive, Company, Admin, decode_uuid, encode_uuid, generate_uuid
from ..db_connection_new import DBSession
from ..auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    decode_access_token,
    get_executive_by_email,
    generate_secure_password,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..email_service import send_admin_invite_email

from src.logging.logging import get_logger
logger = get_logger("executive_routes")


# Pydantic models for request/response validation
class ExecutiveRegister(BaseModel):
    company_name: str
    name: str
    email: EmailStr
    password: str
    industry: str = None


class ExecutiveLogin(BaseModel):
    email: EmailStr
    password: str


class AdminInvite(BaseModel):
    admin_email: EmailStr
    admin_username: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    executive: dict
    company: dict = None


class ExecutiveProfile(BaseModel):
    id: str
    name: str
    email: str
    company_id: str
    company_name: str
    industry: str = None


class AdminInviteResponse(BaseModel):
    admin_id: str
    admin_username: str
    temp_password: str
    email_sent: bool
    message: str


class SendEmailRequest(BaseModel):
    """Request model for sending email to an admin."""
    to_email: EmailStr
    admin_username: str
    temp_password: str
    company_name: str


class SendEmailResponse(BaseModel):
    """Response model for email sending."""
    success: bool
    message: str


class AdminListItem(BaseModel):
    """Response model for an admin in the list."""
    admin_id: str
    username: str
    created_at: Optional[str] = None


class AdminListResponse(BaseModel):
    """Response model for listing admins."""
    admins: list[AdminListItem]
    total: int


class AdminDeleteResponse(BaseModel):
    """Response model for admin deletion."""
    success: bool
    message: str
    admin_id: str


# Router setup
router = APIRouter(
    prefix="/executive",
    tags=["executive"]
)

security = HTTPBearer()


# Helper function to get current executive from token
async def get_current_executive_from_token(
    db: AsyncSession,
    credentials: HTTPAuthorizationCredentials
) -> Executive:
    """Validate token and return current executive."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    executive = await get_executive_by_email(db, email)
    if executive is None:
        raise credentials_exception
    
    return executive


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def register_executive(db: DBSession, data: ExecutiveRegister):
    """
    Register a new executive and create their company.
    Returns JWT token for immediate authentication.
    """
    try:
        # Check if email already exists
        existing = await get_executive_by_email(db, data.email)
        if existing:
            logger.warning(f"Registration attempt with existing email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create the company first
        new_company = Company(name=data.company_name)
        db.add(new_company)
        await db.flush()  # Get the company ID
        
        # Create the executive
        password_hash = get_password_hash(data.password)
        new_executive = Executive(
            name=data.name,
            email=data.email,
            password_hash=password_hash,
            company_id=new_company.id,
            industry=data.industry
        )
        db.add(new_executive)
        await db.commit()
        
        # Generate access token
        access_token = create_access_token(
            data={"sub": data.email, "company_id": str(decode_uuid(new_company.id))},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        logger.info(f"Registered new executive: {data.email} for company: {data.company_name}")
        
        return TokenResponse(
            access_token=access_token,
            executive={
                "id": str(decode_uuid(new_executive.id)),
                "name": new_executive.name,
                "email": new_executive.email,
                "industry": new_executive.industry
            },
            company={
                "id": str(decode_uuid(new_company.id)),
                "name": new_company.name
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login_executive(db: DBSession, data: ExecutiveLogin):
    """
    Authenticate executive and return JWT token.
    """
    try:
        executive = await get_executive_by_email(db, data.email)
        
        if not executive:
            logger.warning(f"Login attempt for non-existent email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not verify_password(data.password, executive.password_hash):
            logger.warning(f"Invalid password for: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Get company info
        result = await db.execute(select(Company).filter_by(id=executive.company_id))
        company = result.scalar_one_or_none()
        
        # Generate access token
        access_token = create_access_token(
            data={"sub": data.email, "company_id": str(decode_uuid(executive.company_id))},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        logger.info(f"Executive logged in: {data.email}")
        
        return TokenResponse(
            access_token=access_token,
            executive={
                "id": str(decode_uuid(executive.id)),
                "name": executive.name,
                "email": executive.email,
                "industry": executive.industry
            },
            company={
                "id": str(decode_uuid(company.id)) if company else None,
                "name": company.name if company else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=ExecutiveProfile)
async def get_current_executive_profile(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get the current authenticated executive's profile.
    """
    try:
        executive = await get_current_executive_from_token(db, credentials)
        
        # Get company info
        result = await db.execute(select(Company).filter_by(id=executive.company_id))
        company = result.scalar_one_or_none()
        
        return ExecutiveProfile(
            id=str(decode_uuid(executive.id)),
            name=executive.name,
            email=executive.email,
            company_id=str(decode_uuid(executive.company_id)),
            company_name=company.name if company else "Unknown",
            industry=executive.industry
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )


@router.post("/invite-admin", response_model=AdminInviteResponse)
async def invite_admin(
    db: DBSession,
    data: AdminInvite,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Invite an admin to the executive's company.
    Generates a temporary password and creates the admin account.
    """
    try:
        executive = await get_current_executive_from_token(db, credentials)
        
        # Check if username already exists
        result = await db.execute(select(Admin).filter_by(username=data.admin_username))
        existing_admin = result.scalar_one_or_none()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin username already exists"
            )
        
        # Generate temporary password
        temp_password = generate_secure_password()
        password_hash = get_password_hash(temp_password)
        
        # Create the admin with hashed password
        new_admin = Admin(
            username=data.admin_username,
            password_hash=password_hash,
            company_id=executive.company_id
        )
        db.add(new_admin)
        await db.commit()
        
        # Get company name for email
        company_result = await db.execute(select(Company).filter_by(id=executive.company_id))
        company = company_result.scalar_one_or_none()
        company_name = company.name if company else "Your Company"
        
        # Send invitation email using executive's email as sender
        email_sent = send_admin_invite_email(
            to_email=data.admin_email,
            admin_username=data.admin_username,
            temp_password=temp_password,
            company_name=company_name,
            from_email=executive.email,
            from_name=executive.name
        )
        
        if email_sent:
            logger.info(f"Admin invited and email sent: {data.admin_username} to {data.admin_email}")
            message = "Admin account created and credentials sent via email."
        else:
            logger.warning(f"Admin invited but email failed: {data.admin_username} to {data.admin_email}")
            message = "Admin account created but email failed. Please send credentials manually."
        
        return AdminInviteResponse(
            admin_id=str(decode_uuid(new_admin.id)),
            admin_username=new_admin.username,
            temp_password=temp_password,
            email_sent=email_sent,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin invite failed: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite admin: {str(e)}"
        )


@router.post("/send-admin-email", response_model=SendEmailResponse)
async def send_admin_email(
    db: DBSession,
    data: SendEmailRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Send admin credentials via email using backend SMTP.
    This endpoint is called by the frontend when the user clicks "Send Email".
    """
    try:
        executive = await get_current_executive_from_token(db, credentials)
        
        # Send invitation email using executive's email as sender
        email_sent = send_admin_invite_email(
            to_email=data.to_email,
            admin_username=data.admin_username,
            temp_password=data.temp_password,
            company_name=data.company_name,
            from_email=executive.email,
            from_name=executive.name
        )
        
        if email_sent:
            logger.info(f"Email sent successfully to {data.to_email} from {executive.email}")
            return SendEmailResponse(
                success=True,
                message=f"Email sent successfully to {data.to_email}"
            )
        else:
            logger.warning(f"Email failed to {data.to_email} - SMTP not configured or error")
            return SendEmailResponse(
                success=False,
                message="Email sending failed. Please check SMTP configuration."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send email failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.get("/admins", response_model=AdminListResponse)
async def list_admins(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    List all admins for the executive's company.
    Returns admin details including ID, username, and creation date.
    """
    try:
        executive = await get_current_executive_from_token(db, credentials)
        
        # Get all admins for the executive's company
        result = await db.execute(
            select(Admin).filter_by(company_id=executive.company_id)
        )
        admins = result.scalars().all()
        
        admin_list = []
        for admin in admins:
            admin_list.append(
                AdminListItem(
                    admin_id=str(decode_uuid(admin.id)),
                    username=admin.username,
                    created_at=None  # Admin entity doesn't have created_at yet
                )
            )
        
        logger.info(f"Listed {len(admin_list)} admins for company {decode_uuid(executive.company_id)}")
        
        return AdminListResponse(
            admins=admin_list,
            total=len(admin_list)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list admins: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list admins: {str(e)}"
        )


@router.delete("/admins/{admin_id}", response_model=AdminDeleteResponse)
async def delete_admin(
    admin_id: str,
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete an admin by ID.
    Only allows deletion of admins belonging to the executive's company.
    """
    try:
        executive = await get_current_executive_from_token(db, credentials)
        
        # Convert string ID to binary UUID for query
        try:
            admin_uuid_bytes = encode_uuid(admin_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid admin ID format"
            )
        
        # Find the admin
        result = await db.execute(
            select(Admin).filter_by(id=admin_uuid_bytes)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        # Verify the admin belongs to the executive's company
        if admin.company_id != executive.company_id:
            logger.warning(f"Unauthorized delete attempt: executive {executive.email} tried to delete admin from different company")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete admins from your own company"
            )
        
        # Delete the admin
        admin_username = admin.username
        await db.delete(admin)
        await db.commit()
        
        logger.info(f"Admin '{admin_username}' (ID: {admin_id}) deleted by executive {executive.email}")
        
        return AdminDeleteResponse(
            success=True,
            message=f"Admin '{admin_username}' has been successfully deleted",
            admin_id=admin_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete admin: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete admin: {str(e)}"
        )
