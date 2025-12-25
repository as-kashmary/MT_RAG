from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timezone
from fastapi import status, APIRouter, HTTPException
from .entities import Product, decode_uuid, encode_uuid
from .db_connection_new import DBSession
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy import select


from src.logging.logging import get_logger
logger= get_logger("product_routes")

class ProductCreate(BaseModel):
    name: str
    description: str
    company_id: str

router= APIRouter(
    prefix="/products",
    tags=["products"],
)

async def _get_product_by_id_from_db(db:AsyncSession)->list[UUID]:
    try:
        result= await db.execute(select(Product.id))
        rows= result.scalars().all()
        logger.info(f"Retrieved product IDs: {rows}")
        return rows
    except Exception as e:
        logger.error(f"Error retrieving product IDs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def _get_product_by_company_id_from_db(db:AsyncSession, company_id: str)->list[UUID]:
    try:
        result= await db.execute(select(Product.id).filter_by(company_id=encode_uuid(company_id))) 
        rows= result.scalars().all()
        logger.info(f"Retrieved product IDs for company {company_id}: {rows}")
        return rows
    except Exception as e:
        logger.error(f"Error retrieving product IDs for company {company_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
async def _create_product_in_db(db:AsyncSession, product:ProductCreate)->None:
    try:
        new_product= Product(
            name=product.name,
            description=product.description,
            company_id=encode_uuid(product.company_id)
        )
        db.add(new_product)
        await db.commit()
        logger.info(f"Created product with name: {product.name} for company_id: {product.company_id}")
    except Exception as e:
        logger.error(f"Error creating product with name {product.name} for company_id {product.company_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    return None
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_product(db:DBSession, product:ProductCreate)->None:
    return await _create_product_in_db(db, product)

@router.get("/{company_id}", status_code=status.HTTP_200_OK)
async def get_products_by_company_id(db:DBSession, company_id:str)->list[str]:
    product_ids= await _get_product_by_company_id_from_db(db, company_id)
    if len(product_ids)==0:
        logger.warning(f"No products found for company_id: {company_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No products found for company_id: {company_id}")
    logger.info(f"Retrieved product IDs for company_id {company_id}: {product_ids}")
    return [str(decode_uuid(pid)) for pid in product_ids]

@router.get("/ids", status_code=status.HTTP_200_OK)
async def get_all_product_id(db:DBSession)->list[str]:
    product_ids= await _get_product_by_id_from_db(db)
    if len(product_ids)==0:
        logger.warning("No products found in the database.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found")
    logger.info(f"Retrieved product IDs: {product_ids}")
    return [str(decode_uuid(pid)) for pid in product_ids]


