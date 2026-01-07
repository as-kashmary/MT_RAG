"""
Analytics routes for the Executive Portal Dashboard.
Provides system statistics and usage metrics for executives.
"""

from pydantic import BaseModel
from typing import Dict, List
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..entities import (
    Executive, Company, Admin, File, QueryAndAnswer, User,
    decode_uuid, encode_uuid
)
from ..db_connection_new import DBSession
from ..auth import decode_access_token, get_executive_by_email

from src.logging.logging import get_logger
logger = get_logger("analytics_routes")


# Pydantic models for response validation
class FileStatusBreakdown(BaseModel):
    pending: int
    running: int
    successful: int
    failed: int


class AnalyticsDashboard(BaseModel):
    total_queries: int
    total_files: int
    total_admins: int
    total_users: int
    file_status_breakdown: FileStatusBreakdown
    recent_activity: List[Dict] = []


# Router setup
router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

security = HTTPBearer()


async def get_company_id_from_token(
    db: AsyncSession,
    credentials: HTTPAuthorizationCredentials
) -> bytes:
    """Extract company_id from JWT token."""
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
    
    return executive.company_id


@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_dashboard_analytics(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get comprehensive analytics for the executive's company dashboard.
    Returns file counts, query counts, admin counts, and status breakdowns.
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        # Count files by status
        file_count_result = await db.execute(
            select(func.count(File.id)).filter_by(company_id=company_id)
        )
        total_files = file_count_result.scalar() or 0
        
        # File status breakdown
        pending_result = await db.execute(
            select(func.count(File.id)).filter_by(company_id=company_id, status="pending")
        )
        pending_count = pending_result.scalar() or 0
        
        running_result = await db.execute(
            select(func.count(File.id)).filter_by(company_id=company_id, status="running")
        )
        running_count = running_result.scalar() or 0
        
        successful_result = await db.execute(
            select(func.count(File.id)).filter_by(company_id=company_id, status="successful")
        )
        successful_count = successful_result.scalar() or 0
        
        failed_result = await db.execute(
            select(func.count(File.id)).filter_by(company_id=company_id, status="failed")
        )
        failed_count = failed_result.scalar() or 0
        
        # Count admins for this company
        admin_count_result = await db.execute(
            select(func.count(Admin.id)).filter_by(company_id=company_id)
        )
        total_admins = admin_count_result.scalar() or 0
        
        # Count total queries (system-wide for now, can be scoped later)
        query_count_result = await db.execute(
            select(func.count(QueryAndAnswer.id))
        )
        total_queries = query_count_result.scalar() or 0
        
        # Count total users (system-wide for now)
        user_count_result = await db.execute(
            select(func.count(User.id))
        )
        total_users = user_count_result.scalar() or 0
        
        logger.info(f"Analytics retrieved for company: {str(decode_uuid(company_id))}")
        
        return AnalyticsDashboard(
            total_queries=total_queries,
            total_files=total_files,
            total_admins=total_admins,
            total_users=total_users,
            file_status_breakdown=FileStatusBreakdown(
                pending=pending_count,
                running=running_count,
                successful=successful_count,
                failed=failed_count
            ),
            recent_activity=[]  # Can be expanded later
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )
