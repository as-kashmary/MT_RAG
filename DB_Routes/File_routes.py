from pydantic import BaseModel
from uuid import UUID
from .db_connection_new import DBSession
from fastapi import APIRouter, HTTPException, Request, Response, status, Depends, UploadFile, File, Body, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .entities import File as FileModel , decode_uuid, encode_uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import  AsyncSession
from hashlib import sha256



class FileCreateForm:
    def __init__(
        self,
        file_name: str = Form(...),
        company_id: str = Form(...),
        file: UploadFile = File(...),
    ):
        self.file_name = file_name
        self.company_id = company_id
        self.file= file

    

router= APIRouter(
    prefix='/file',
    tags=['file']
)



def _calculate_file_hash(file_data: bytes)->str:
    sha256_hash= sha256()
    sha256_hash.update(file_data)
    return sha256_hash.hexdigest()
    

async def _hash_exist_or_not(file_hash: str, db:AsyncSession)->bool:
    result= await db.execute(select(FileModel).filter_by(file_hash=file_hash))
    return result.scalar_one_or_none()




async def _get_all_files_id_from_db(db:AsyncSession, Company_id: UUID )-> list[UUID]:

    result= await db.execute(select(FileModel.id).filter_by(company_id=encode_uuid(Company_id)))
    rows= result.scalars().all()
    return rows


async def _get_all_files_by_company_pending(db:AsyncSession, Company_id: UUID )-> list[UUID]:
    """
    This is the old sync function
        file_ids_tuples = db.query(File.id).filter_by(company_id=Company_id, status="pending").all()

    """
    result = await db.execute(select(FileModel.id).filter_by(company_id=encode_uuid(Company_id), status="pending"))
    rows= result.scalars().all()
    return rows

async def _update_file_status_running(db:AsyncSession, file_id: UUID)->None:
    result= await db.execute(select(FileModel).filter_by(id=encode_uuid(file_id)))
    file_record= result.scalars().first()
    print(file_record)
    if file_record:
        file_record.status= "running"
        await db.commit()
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No file found with ID {file_id}")

async def _update_file_status_successful(db:AsyncSession, file_id: UUID)->None:


    result= await db.execute(select(FileModel).filter_by(id=encode_uuid(file_id)))
    file_record= result.scalars().first()
    print(file_record)
    if file_record:
        file_record.status = "successful"
        await db.commit()
        print(f"Updated successful status for file ID {file_id} to successful")
    else:
        print(f"No file found with ID {file_id}")

async def _update_file_status_failed(db:AsyncSession, file_id: UUID)->None:
    result= await db.execute(select(FileModel).filter_by(id=encode_uuid(file_id)))
    file_record= result.scalars().first()
    print(file_record)
    if file_record:
        file_record.status = "failed"
        await db.commit()
        print(f"Updated failed status for file ID {file_id} to failed")
    else:
        print(f"No file found with ID {file_id}")


"""


"""
@router.post("/create",status_code=status.HTTP_201_CREATED)
async def create_file(
                      db:DBSession,
                      file_name: str =Form(...) ,
                      company_id: str =Form(...),
                      file: UploadFile = File(...))->None:
    try:
        """
        FastAPI's UploadFile is async so we have to use await before it
        We are storing file_hash to compare the newly uploaded file's hash to the previous uploaded file's hash.
        In this way we can find which file is uploaded or not.

        .read() is also async so it also needs to be awaited.
        """
        file_bytes=await file.read()
        hashed= _calculate_file_hash(file_bytes)
        existing= await _hash_exist_or_not(hashed, db)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f" The file already exists")
        else:
            new_file= FileModel(
                file_name=file_name,
                company_id=encode_uuid(company_id),
                file_data=file_bytes,
                file_hash=hashed,
                file_format= file.content_type

            )
            db.add(new_file)
            await db.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failure in creating file {str(e)}")

@router.get("/ids", status_code=status.HTTP_200_OK, response_model=list[UUID])
async def get_all_file_id_by_company(db:DBSession, company_id: str)->list[UUID]:
    try:
        file_id= await  _get_all_files_id_from_db(db, company_id)
        if len(file_id)==0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
            
        return [decode_uuid(id) for id in file_id]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
    
@router.get("/{company_id}/pending", status_code=status.HTTP_200_OK, response_model=list[UUID])
async def get_all_file_id_by_company_pending(db:DBSession, company_id: str)->list[UUID]:
    try:
        file_id= await _get_all_files_by_company_pending(db, company_id)
        if len(file_id)==0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        return file_id
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")

@router.post("/{file_id}/running", status_code=status.HTTP_200_OK)
async def update_file_status_running(db:DBSession, file_id: str)->None:
    try:
        await _update_file_status_running(db, file_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
        

@router.post("/{file_id}/successful", status_code=status.HTTP_200_OK)
async def update_file_status_successful(db:DBSession, file_id: str)->None:
    try:
        await _update_file_status_successful(db, file_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
      
@router.post("/{file_id}/failed", status_code=status.HTTP_200_OK)
async def update_file_status_failed(db:DBSession, file_id: str)->None:
    try:
       await _update_file_status_failed(db, file_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
      