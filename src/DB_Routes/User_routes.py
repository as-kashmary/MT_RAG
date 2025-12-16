from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timezone
from fastapi import status, APIRouter, HTTPException
from .entities import User, decode_uuid
from .db_connection_new import DBSession
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy import select


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
        print(rows)
        return rows
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))  

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(db:DBSession, user:UserCreate)->None:
    try:
        new_user=User(
            **user.model_dump()
        ) 
        db.add(new_user)
        await db.commit()
        return None
    except Exception as e:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail=f"Failure in creating user {str(e)}")
    
@router.get("/ids", status_code= status.HTTP_200_OK, response_model=list[str])
async def get_user_by_id(db:DBSession)->list[str]:
    try: 
        user_ids=await _get_user_by_id_from_db(db)
        if len(user_ids)==0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        print(type(user_ids[0]))
        
        return [str(decode_uuid(uid))for uid in user_ids]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))