from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timezone
from fastapi import status, APIRouter, HTTPException
from .entities import Admin, decode_uuid, encode_uuid
from .db_connection_new import DBSession
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy import select


from src.logging.logging import get_logger
logger= get_logger("admin_routes")


class AdminCreate(BaseModel):
    username: str
    password_hash: str
    company_id: str



router= APIRouter(
    prefix="/admins",
    tags=["admins"],

)


async def _get_admin_by_id_from_db(db:AsyncSession)->list[UUID]:
    try:
        result= await db.execute(select(Admin.id))
        rows= result.scalars().all()
        logger.info(f"Retrieved admin IDs: {rows}")
        return rows
    except Exception as e:
        logger.error(f"Error retrieving admin IDs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))  

async def _admin_username_password_hash_match(db:AsyncSession, username:str, password_hash:str, company_id: str)->bool:
    try:
        result= await db.execute(select(Admin).where(Admin.username==username, Admin.password_hash==password_hash, Admin.company_id==encode_uuid(company_id)))
        admin= result.scalar_one_or_none()
        if admin:
            logger.info(f"Username and password hash match for username: {username}")
            return True
        else:
            logger.warning(f"Username and password hash do not match for username: {username}")
            return False
    except Exception as e:
        logger.error(f"Error checking username and password hash for username {username}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def _get_admin_by_company_id_from_db(db:AsyncSession, company_id: str)->list[UUID]:
    try:
        result= await db.execute(select(Admin.id).filter_by(company_id=encode_uuid(company_id))) 
        rows= result.scalars().all()
        logger.info(f"Retrieved admin IDs for company {company_id}: {rows}")
        return rows
    except Exception as e:
        logger.error(f"Error retrieving admin IDs for company {company_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))  


async def create_admin_in_db(db:AsyncSession, admin:AdminCreate)->None:
    try:
        new_admin=Admin(
            username=admin.username,
            password_hash=admin.password_hash,
            company_id=encode_uuid(admin.company_id)
        ) 
        db.add(new_admin)
        await db.commit()
        logger.info(f"Created new admin with username: {admin.username} for company_id: {admin.company_id}")
        return None
    except Exception as e:
        logger.error(f"Error creating admin with username: {admin.username} for company_id: {admin.company_id}: {str(e)}")
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail=f"Failure in creating admin {str(e)}")


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_admin(db:DBSession, admin:AdminCreate)->None:
    try:
       await create_admin_in_db(db, admin)
       return None
    except Exception as e:
        logger.error(f"Error creating admin with username: {admin.username} for company_id: {admin.company_id}: {str(e)}")
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail=f"Failure in creating admin {str(e)}")
    
@router.get("/ids", status_code= status.HTTP_200_OK, response_model=list[str])
async def get_admin_by_id(db:DBSession)->list[str]:
    try: 
        admin_ids=await _get_admin_by_id_from_db(db)
        if len(admin_ids)==0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
        logger.info(f"Retrieved admin IDs: {admin_ids}")
        
        return [str(decode_uuid(uid))for uid in admin_ids]
    except Exception as e:
        logger.error(f"Error retrieving admin IDs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/{company_id}/ids", status_code= status.HTTP_200_OK, response_model=list[str])
async def get_admin_by_company_id(db:DBSession, company_id: str)->list[str]:
    try: 
        admin_ids=await _get_admin_by_company_id_from_db(db,company_id)
        if len(admin_ids)==0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Admin not found in company {company_id}")
        logger.info(f"Retrieved admin IDs for company {company_id}: {admin_ids}")
        
        return [str(decode_uuid(uid))for uid in admin_ids]
    except Exception as e:
        logger.error(f"Error retrieving admin IDs for company {company_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    


@router.post("/login", status_code=status.HTTP_200_OK)
async def admin_login(db:DBSession, username, password_hash, company_id)->dict:
    try:
        is_valid= await _admin_username_password_hash_match(db, username, password_hash, company_id)
        if not is_valid:
            logger.warning(f"Invalid login attempt for admin username: {username}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        logger.info(f"Admin username: {username} logged in successfully")
        return {"message": "Login successful"}
    except Exception as e:
        logger.error(f"Error during login for admin username: {username}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))