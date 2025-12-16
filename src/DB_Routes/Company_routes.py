from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Response, status
from .entities import Company, decode_uuid
from .db_connection_new import DBSession
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy import select

from src.logging.logging import get_logger
logger= get_logger("company_routes")


class CompanyCreate(BaseModel):
    name: str


router= APIRouter(
    prefix='/company',
    tags=['company']
)

async def _get_all_company_ids_from_db(db: AsyncSession):
    """
    The old sync query function was result_tuples= db.query(Company.id).all()
    """
    result = await db.execute(select(Company.id))
    rows = result.scalars().all()
    logger.info(f"Retrieved company IDs: {rows}")
    return rows

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_company(db:DBSession, company:CompanyCreate)->None:
    try:
        new_company= Company(**company.model_dump())
        db.add(new_company)
        await db.commit()
        logger.info(f"Created new company with name: {company.name}")
        return None
    except Exception as e:
        logger.error(f"Error creating company with name: {company.name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failure in creating company {str(e)}")

@router.get("/ids", status_code=status.HTTP_200_OK)
async def get_all_company_id(db:DBSession)->list[str]:
    try: 
        company_ids= await _get_all_company_ids_from_db(db)
        if len(company_ids)==0:   
            logger.warning("No company found in the database.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No company found")
        logger.info(f"Retrieved company IDs: {company_ids}")
        return [str(decode_uuid(cid)) for cid in company_ids]
    except Exception as e:
        logger.error(f"Error retrieving company IDs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")