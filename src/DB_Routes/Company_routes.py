from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Response, status
from .entities import Company, decode_uuid, Admin, encode_uuid
from .db_connection_new import DBSession
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy import select
from .Admin_routes import create_admin_in_db, AdminCreate

from src.logging.logging import get_logger
logger= get_logger("company_routes")


class CompanyCreate(BaseModel):
    name: str
    login_id: str
    passkey: str


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

async def _get_company_id_by_login_id_from_db(db: AsyncSession, login_id: str)->UUID|None:
    result = await db.execute(select(Company.id).where(Company.login_id == login_id))
    company_id = result.scalar_one_or_none()
    if company_id:
        logger.info(f"Found company ID for login_id {login_id}: {decode_uuid(company_id)}")
    else:
        logger.warning(f"No company found with login_id: {login_id}")
    return company_id

async def _company_login_id_passkey_match(db: AsyncSession, login_id: str, passkey: str)->bool:
    result = await db.execute(select(Company).where(Company.login_id == login_id, Company.passkey == passkey))
    company = result.scalar_one_or_none()
    if company:
        logger.info(f"Login ID and passkey match for login_id: {login_id}")
        return True
    else:
        logger.warning(f"Login ID and passkey do not match for login_id: {login_id}")
        return False

async def _create_admin_id_password_hash_for_company(db: AsyncSession, company_id: UUID, username: str)->dict:
    # Generate unique password hash for admin
    password_hash = f"admin_{str(decode_uuid(company_id))}_passhash"
    await create_admin_in_db(db, AdminCreate(username=username, password_hash=password_hash, company_id=str(decode_uuid(company_id))))
    logger.info(f"Created admin for company_id: {str(decode_uuid(company_id))} with username: {username}")
    return {"username": username, "password_hash": password_hash}

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
    


@router.post("/login", status_code=status.HTTP_200_OK)
async def company_login(db:DBSession, login_id:str, passkey:str)->dict:
    try:
        is_match= await _company_login_id_passkey_match(db, login_id, passkey)
        if not is_match:
            logger.warning(f"Login failed for login_id: {login_id}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login ID or passkey")
        
        company_id= await _get_company_id_by_login_id_from_db(db, login_id)
        if not company_id:
            logger.error(f"Company ID not found for login_id: {login_id} after successful match")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
        
        logger.info(f"Login successful for login_id: {login_id}")
        return {
            "company_id": str(decode_uuid(company_id)),
            "message": "Login successful"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error during company login for login_id {login_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")


@router.post("/create_admin_for_company", status_code=status.HTTP_201_CREATED)
async def create_admin_for_company(db:DBSession, company_login_id:str, admin_username:str)->dict:
    try:
        company_id= await _get_company_id_by_login_id_from_db(db, company_login_id)
        if not company_id:
            logger.warning(f"Company not found for login_id: {company_login_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        
        admin_credentials= await _create_admin_id_password_hash_for_company(db, company_id, admin_username)
        logger.info(f"Admin created for company with login_id: {company_login_id}")
        return admin_credentials
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating admin for company with login_id {company_login_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")