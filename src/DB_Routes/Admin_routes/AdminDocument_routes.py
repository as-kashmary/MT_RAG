"""
Admin Document Management Routes for the Admin Portal.
Handles document listing, upload, and deletion scoped to admin's company.
Documents are associated with products via product_id.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from hashlib import sha256

from ..entities import Admin, File as FileModel, Product, decode_uuid, encode_uuid
from ..db_connection_new import DBSession
from ..auth import decode_access_token

from src.logging.logging import get_logger
logger = get_logger("admin_document_routes")


# Pydantic models for response validation
class DocumentInfo(BaseModel):
    id: str
    file_name: str
    file_format: str
    status: str
    uploaded_at: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int


class DocumentDeleteResponse(BaseModel):
    success: bool
    message: str
    document_id: str


class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[str] = None
    status: str = "pending"


class StatusUpdateRequest(BaseModel):
    status: str  # 'pending', 'successful', 'failed'


class StatusUpdateResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    status: str


# Router setup
router = APIRouter(
    prefix="/admin/documents",
    tags=["admin-documents"]
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


def _calculate_file_hash(file_data: bytes) -> str:
    """Calculate SHA256 hash of file data."""
    sha256_hash = sha256()
    sha256_hash.update(file_data)
    return sha256_hash.hexdigest()


async def _hash_exists(file_hash: str, db: AsyncSession) -> bool:
    """Check if a file with this hash already exists."""
    result = await db.execute(select(FileModel).filter_by(file_hash=file_hash))
    return result.scalar_one_or_none() is not None


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    List all documents for the admin's company.
    Returns document metadata sorted by upload date (newest first).
    Includes product information for each document.
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        # Get all documents for the company
        result = await db.execute(
            select(FileModel)
            .filter_by(company_id=company_id)
            .order_by(FileModel.uploaded_at.desc())
        )
        files = result.scalars().all()
        
        # Build document list with product names
        documents = []
        for f in files:
            product_name = None
            if f.product_id:
                product_result = await db.execute(
                    select(Product).filter_by(id=f.product_id)
                )
                product = product_result.scalar_one_or_none()
                if product:
                    product_name = product.name
            
            documents.append(DocumentInfo(
                id=str(decode_uuid(f.id)),
                file_name=f.file_name,
                file_format=f.file_format,
                status=f.status,
                uploaded_at=f.uploaded_at.isoformat() if f.uploaded_at else "",
                product_id=str(decode_uuid(f.product_id)) if f.product_id else None,
                product_name=product_name
            ))
        
        logger.info(f"Retrieved {len(documents)} documents for company: {str(decode_uuid(company_id))}")
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document list error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get details of a specific document.
    Only returns document if it belongs to admin's company.
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        result = await db.execute(
            select(FileModel)
            .filter_by(id=encode_uuid(document_id), company_id=company_id)
        )
        file = result.scalar_one_or_none()
        
        if file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get product name if available
        product_name = None
        if file.product_id:
            product_result = await db.execute(
                select(Product).filter_by(id=file.product_id)
            )
            product = product_result.scalar_one_or_none()
            if product:
                product_name = product.name
        
        return DocumentInfo(
            id=str(decode_uuid(file.id)),
            file_name=file.file_name,
            file_format=file.file_format,
            status=file.status,
            uploaded_at=file.uploaded_at.isoformat() if file.uploaded_at else "",
            product_id=str(decode_uuid(file.product_id)) if file.product_id else None,
            product_name=product_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document fetch error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch document: {str(e)}"
        )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a document by ID.
    Only allows deletion of documents belonging to admin's company.
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        # First verify the document exists and belongs to the admin's company
        result = await db.execute(
            select(FileModel)
            .filter_by(id=encode_uuid(document_id), company_id=company_id)
        )
        file = result.scalar_one_or_none()
        
        if file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
        
        # Delete the document
        await db.delete(file)
        await db.commit()
        
        logger.info(f"Document deleted: {document_id}")
        
        return DocumentDeleteResponse(
            success=True,
            message="Document deleted successfully",
            document_id=document_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document delete error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    db: DBSession,
    file_name: str = Form(...),
    product_id: str = Form(...),
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Upload a new document for the admin's company.
    Requires product_id to associate document with a product.
    Documents are marked as successful immediately upon upload.
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        # Verify product exists and belongs to admin's company
        product_result = await db.execute(
            select(Product).filter_by(id=encode_uuid(product_id), company_id=company_id)
        )
        product = product_result.scalar_one_or_none()
        
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product selected"
            )
        
        # Read file data
        file_bytes = await file.read()
        file_hash = _calculate_file_hash(file_bytes)
        file_type = file.content_type or "application/octet-stream"
        
        # Check for duplicate
        if await _hash_exists(file_hash, db):
            logger.warning(f"Duplicate file upload attempted: {file_name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This file already exists in the system"
            )
        
        # Create new file record with product association - status starts as pending
        new_file = FileModel(
            file_name=file_name,
            company_id=company_id,
            product_id=encode_uuid(product_id),
            file_data=file_bytes,
            file_hash=file_hash,
            file_format=file_type,
            status="pending"  # Pending until chunking process completes
        )
        
        db.add(new_file)
        await db.commit()
        await db.refresh(new_file)
        
        document_id = str(decode_uuid(new_file.id))
        logger.info(f"Document uploaded: {file_name} for product: {product.name} with ID: {document_id}")
        
        return DocumentUploadResponse(
            success=True,
            message="Document uploaded - pending processing",
            document_id=document_id,
            status="pending"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.patch("/{document_id}/status", response_model=StatusUpdateResponse)
async def update_document_status(
    document_id: str,
    request: StatusUpdateRequest,
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update the processing status of a document.
    Used by the chunking process to mark documents as 'successful' after processing.
    Valid statuses: 'pending', 'successful', 'failed'
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        # Validate status value
        valid_statuses = ['pending', 'successful', 'failed']
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Find the document
        result = await db.execute(
            select(FileModel)
            .filter_by(id=encode_uuid(document_id), company_id=company_id)
        )
        file = result.scalar_one_or_none()
        
        if file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Update status
        old_status = file.status
        file.status = request.status
        await db.commit()
        
        logger.info(f"Document {document_id} status changed: {old_status} -> {request.status}")
        
        return StatusUpdateResponse(
            success=True,
            message=f"Document status updated to '{request.status}'",
            document_id=document_id,
            status=request.status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document status: {str(e)}"
        )

