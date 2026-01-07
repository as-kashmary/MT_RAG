"""
Admin Analytics Routes for the Admin Portal Dashboard.
Provides document statistics and usage metrics for admins.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..entities import Admin, File, QueryAndAnswer, decode_uuid, encode_uuid
from ..db_connection_new import DBSession
from ..auth import decode_access_token

from src.logging.logging import get_logger
logger = get_logger("admin_analytics_routes")


# Pydantic models for response validation
class DocumentStatusBreakdown(BaseModel):
    pending: int
    running: int
    successful: int
    failed: int


class AdminAnalyticsDashboard(BaseModel):
    total_documents: int
    document_status: DocumentStatusBreakdown
    recent_uploads: List[Dict]
    processing_rate: float  # Percentage of successfully processed documents


# Router setup
router = APIRouter(
    prefix="/admin/analytics",
    tags=["admin-analytics"]
)

security = HTTPBearer()


async def get_admin_by_id(db: AsyncSession, admin_id: bytes) -> Optional[Admin]:
    """Get an admin by their ID."""
    result = await db.execute(select(Admin).filter_by(id=admin_id))
    return result.scalar_one_or_none()


async def get_company_id_from_token(
    db: AsyncSession,
    credentials: HTTPAuthorizationCredentials
) -> bytes:
    """Extract company_id from admin's JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    admin_id: str = payload.get("sub")
    user_type: str = payload.get("type")
    
    if admin_id is None or user_type != "admin":
        raise credentials_exception
    
    admin = await get_admin_by_id(db, encode_uuid(admin_id))
    if admin is None:
        raise credentials_exception
    
    return admin.company_id


@router.get("/dashboard", response_model=AdminAnalyticsDashboard)
async def get_admin_dashboard_analytics(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get comprehensive analytics for the admin's dashboard.
    Returns document counts, status breakdown, and processing metrics.
    Note: With simplified status handling, documents are only 'successful' or 'failed'.
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        # Count total documents
        total_result = await db.execute(
            select(func.count(File.id)).filter_by(company_id=company_id)
        )
        total_documents = total_result.scalar() or 0
        
        # Count by status
        pending_result = await db.execute(
            select(func.count(File.id)).filter_by(company_id=company_id, status="pending")
        )
        pending_count = pending_result.scalar() or 0
        
        successful_result = await db.execute(
            select(func.count(File.id)).filter_by(company_id=company_id, status="successful")
        )
        successful_count = successful_result.scalar() or 0
        
        failed_result = await db.execute(
            select(func.count(File.id)).filter_by(company_id=company_id, status="failed")
        )
        failed_count = failed_result.scalar() or 0
        
        # Get recent uploads (last 5)
        recent_result = await db.execute(
            select(File)
            .filter_by(company_id=company_id)
            .order_by(File.uploaded_at.desc())
            .limit(5)
        )
        recent_files = recent_result.scalars().all()
        
        recent_uploads = [
            {
                "id": str(decode_uuid(f.id)),
                "file_name": f.file_name,
                "status": f.status,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else ""
            }
            for f in recent_files
        ]
        
        # Calculate processing rate (successful out of total processed)
        processed_count = successful_count + failed_count
        processing_rate = (successful_count / processed_count * 100) if processed_count > 0 else 100.0
        
        logger.info(f"Analytics retrieved for company: {str(decode_uuid(company_id))}")
        
        return AdminAnalyticsDashboard(
            total_documents=total_documents,
            document_status=DocumentStatusBreakdown(
                pending=pending_count,
                running=0,  # Not used in current workflow
                successful=successful_count,
                failed=failed_count
            ),
            recent_uploads=recent_uploads,
            processing_rate=round(processing_rate, 1)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )
