from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timezone
from fastapi import status, APIRouter, HTTPException
from .entities import User, decode_uuid, encode_uuid
from .db_connection_new import DBSession
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy import select
import os


from src.logging.logging import get_logger 
logger= get_logger("user_routes")

# Set default company ID (from environment variable or hardcoded for single-company setup)
DEFAULT_COMPANY_ID = os.getenv("DEFAULT_COMPANY_ID", "1893ab51e6284c1b8ed64c88238b116b")


class UserCreate(BaseModel):
    name: str
    email: str
    password_hash: str
    




router= APIRouter(
    prefix="/users",
    tags=["users"],

)


async def _get_user_by_id_from_db(db:AsyncSession)->list[UUID]:
    try:
        result= await db.execute(select(User.id))
        rows= result.scalars().all()
        logger.info(f"Retrieved user IDs: {rows}")
        return rows
    except Exception as e:
        logger.error(f"Error retrieving user IDs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))  

async def _get_user_by_email_from_db(db:AsyncSession, email:str)->UUID|None:
    try:
        result= await db.execute(select(User.id).where(User.email==email))
        user_id= result.scalar_one_or_none()
        if user_id:
            logger.info(f"Found user ID for email {email}: {decode_uuid(user_id)}")
        else:
            logger.warning(f"No user found with email: {email}")
        return user_id
    except Exception as e:
        logger.error(f"Error retrieving user ID for email {email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def _user_email_password_hash_match(db:AsyncSession, email:str, password_hash:str)->bool:
    try:
        result= await db.execute(select(User).where(User.email==email, User.password_hash==password_hash))
        user= result.scalar_one_or_none()
        if user:
            logger.info(f"Email and password hash match for email: {email}")
            return True
        else:
            logger.warning(f"Email and password hash do not match for email: {email}")
            return False
    except Exception as e:
        logger.error(f"Error checking email and password hash match for email {email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))





@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(db:DBSession, user:UserCreate)->dict:
    try:
        new_user=User(
            **user.model_dump(),
            Company_id=encode_uuid(DEFAULT_COMPANY_ID)  # Automatically set default company_id
        ) 
        db.add(new_user)
        await db.commit()
        logger.info(f"Created new user with email: {user.email} and company_id: {DEFAULT_COMPANY_ID}")
        return {
            "success": True,
            "message": "User created successfully",
            "email": user.email
        }
    except Exception as e:
        logger.error(f"Error creating user with email {user.email}: {str(e)}")
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail=f"Failure in creating user {str(e)}")
    
@router.get("/ids", status_code= status.HTTP_200_OK, response_model=list[str])
async def get_user_by_id(db:DBSession)->list[str]:
    try: 
        user_ids=await _get_user_by_id_from_db(db)
        if len(user_ids)==0:
            logger.warning("User table is empty.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return [str(decode_uuid(uid))for uid in user_ids]
    except Exception as e:
        logger.error(f"Error retrieving user IDs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

@router.get("/login", status_code=status.HTTP_200_OK)
async def user_login(db:DBSession, email:str, password_hash:str)->str:
    try:
        is_match= await _user_email_password_hash_match(db, email, password_hash)
        if not is_match:
            logger.warning(f"Login failed for email: {email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password hash")
        
        user_id= await _get_user_by_email_from_db(db, email)
        logger.info(f"Login successful for email: {email}")
        return str(decode_uuid(user_id))
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error during login for email {email}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))