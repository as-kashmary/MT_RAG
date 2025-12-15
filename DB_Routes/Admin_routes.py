from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timezone
from fastapi import status, APIRouter, HTTPException
from .entities import Admin, decode_uuid, encode_uuid
from .db_connection_new import DBSession
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy import select


class AdminCreate(BaseModel):
    username: str
    company_id: str



router= APIRouter(
    prefix="/admins",
    tags=["admins"],

)


async def _get_admin_by_id_from_db(db:AsyncSession)->list[UUID]:
    try:
        result= await db.execute(select(Admin.id))
        rows= result.scalars().all()
        print(rows)
        return rows
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))  


async def _get_admin_by_company_id_from_db(db:AsyncSession, company_id: str)->list[UUID]:
    try:
        result= await db.execute(select(Admin.id).filter_by(company_id=encode_uuid(company_id))) 
        rows= result.scalars().all()
        return rows
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))  


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_admin(db:DBSession, admin:AdminCreate)->None:
    try:
        new_admin=Admin(
            username=admin.username,
            company_id=encode_uuid(admin.company_id)
        ) 
        db.add(new_admin)
        await db.commit()
        return None
    except Exception as e:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail=f"Failure in creating admin {str(e)}")
    
@router.get("/ids", status_code= status.HTTP_200_OK, response_model=list[str])
async def get_admin_by_id(db:DBSession)->list[str]:
    try: 
        admin_ids=await _get_admin_by_id_from_db(db)
        if len(admin_ids)==0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
        print(type(admin_ids[0]))
        
        return [str(decode_uuid(uid))for uid in admin_ids]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/{company_id}/ids", status_code= status.HTTP_200_OK, response_model=list[str])
async def get_admin_by_company_id(db:DBSession, company_id: str)->list[str]:
    try: 
        admin_ids=await _get_admin_by_company_id_from_db(db,company_id)
        if len(admin_ids)==0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Admin not found in company {company_id}")
        print(type(admin_ids[0]))
        
        return [str(decode_uuid(uid))for uid in admin_ids]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))