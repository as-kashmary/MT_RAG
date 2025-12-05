from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Response, status
from .entities import Company, decode_uuid
from .db_connection_new import DBSession
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy import select



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
    return rows

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_company(db:DBSession, company:CompanyCreate)->None:
    try:
        new_company= Company(**company.model_dump())
        print("Creating company:", company.name)
        db.add(new_company)
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failure in creating company {str(e)}")

@router.get("/ids", status_code=status.HTTP_200_OK)
async def get_all_company_id(db:DBSession)->list[UUID]:
    try: 
        company_ids= await _get_all_company_ids_from_db(db)
        if len(company_ids)==0:   
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No company found")
        return [decode_uuid(cid) for cid in company_ids]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")