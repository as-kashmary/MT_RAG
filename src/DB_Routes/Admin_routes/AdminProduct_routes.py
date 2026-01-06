"""
Admin Product Management Routes for the Admin Portal.
Handles product CRUD operations scoped to admin's company.
"""

from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..entities import Admin, Product, File, decode_uuid, encode_uuid, generate_uuid
from ..db_connection_new import DBSession
from ..auth import decode_access_token

from src.logging.logging import get_logger
logger = get_logger("admin_product_routes")


# Pydantic models
class ProductInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    document_count: int = 0


class ProductListResponse(BaseModel):
    products: List[ProductInfo]
    total: int


class ProductCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProductResponse(BaseModel):
    success: bool
    message: str
    product: Optional[ProductInfo] = None


class ProductDeleteResponse(BaseModel):
    success: bool
    message: str
    product_id: str


# Router setup
router = APIRouter(
    prefix="/admin/products",
    tags=["admin-products"]
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


@router.get("", response_model=ProductListResponse)
async def list_products(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    List all products for the admin's company.
    Returns products sorted by name with document counts.
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        result = await db.execute(
            select(Product)
            .filter_by(company_id=company_id)
            .order_by(Product.name)
        )
        products = result.scalars().all()
        
        # Build product list with document counts
        product_list = []
        for p in products:
            # Count documents for this product
            doc_count_result = await db.execute(
                select(func.count(File.id)).filter_by(product_id=p.id)
            )
            doc_count = doc_count_result.scalar() or 0
            
            product_list.append(ProductInfo(
                id=str(decode_uuid(p.id)),
                name=p.name,
                description=p.description,
                document_count=doc_count
            ))
        
        logger.info(f"Retrieved {len(product_list)} products for company: {str(decode_uuid(company_id))}")
        
        return ProductListResponse(
            products=product_list,
            total=len(product_list)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product list error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list products: {str(e)}"
        )


@router.get("/{product_id}", response_model=ProductInfo)
async def get_product(
    product_id: str,
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get details of a specific product.
    Only returns product if it belongs to admin's company.
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        result = await db.execute(
            select(Product)
            .filter_by(id=encode_uuid(product_id), company_id=company_id)
        )
        product = result.scalar_one_or_none()
        
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Count documents
        doc_count_result = await db.execute(
            select(func.count(File.id)).filter_by(product_id=product.id)
        )
        doc_count = doc_count_result.scalar() or 0
        
        return ProductInfo(
            id=str(decode_uuid(product.id)),
            name=product.name,
            description=product.description,
            document_count=doc_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product fetch error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product: {str(e)}"
        )


@router.post("", response_model=ProductResponse)
async def create_product(
    request: ProductCreateRequest,
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new product for the admin's company.
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        # Check if product with same name exists
        existing = await db.execute(
            select(Product).filter_by(company_id=company_id, name=request.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A product with this name already exists"
            )
        
        # Create new product
        new_product = Product(
            id=generate_uuid(),
            name=request.name,
            description=request.description,
            company_id=company_id
        )
        
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        
        logger.info(f"Product created: {request.name}")
        
        return ProductResponse(
            success=True,
            message="Product created successfully",
            product=ProductInfo(
                id=str(decode_uuid(new_product.id)),
                name=new_product.name,
                description=new_product.description,
                document_count=0
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product create error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    request: ProductUpdateRequest,
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update an existing product.
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        result = await db.execute(
            select(Product)
            .filter_by(id=encode_uuid(product_id), company_id=company_id)
        )
        product = result.scalar_one_or_none()
        
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Update fields
        if request.name:
            # Check for duplicate name
            existing = await db.execute(
                select(Product).filter_by(company_id=company_id, name=request.name)
            )
            existing_product = existing.scalar_one_or_none()
            if existing_product and existing_product.id != product.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A product with this name already exists"
                )
            product.name = request.name
        
        if request.description is not None:
            product.description = request.description
        
        await db.commit()
        await db.refresh(product)
        
        # Get document count
        doc_count_result = await db.execute(
            select(func.count(File.id)).filter_by(product_id=product.id)
        )
        doc_count = doc_count_result.scalar() or 0
        
        logger.info(f"Product updated: {product_id}")
        
        return ProductResponse(
            success=True,
            message="Product updated successfully",
            product=ProductInfo(
                id=str(decode_uuid(product.id)),
                name=product.name,
                description=product.description,
                document_count=doc_count
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )


@router.delete("/{product_id}", response_model=ProductDeleteResponse)
async def delete_product(
    product_id: str,
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a product. Associated documents will also be deleted (CASCADE).
    """
    try:
        company_id = await get_company_id_from_token(db, credentials)
        
        result = await db.execute(
            select(Product)
            .filter_by(id=encode_uuid(product_id), company_id=company_id)
        )
        product = result.scalar_one_or_none()
        
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        product_name = product.name
        await db.delete(product)
        await db.commit()
        
        logger.info(f"Product deleted: {product_name} (ID: {product_id})")
        
        return ProductDeleteResponse(
            success=True,
            message=f"Product '{product_name}' deleted successfully",
            product_id=product_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product delete error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}"
        )
