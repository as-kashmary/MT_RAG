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
import os

from src.logging.logging import get_logger 
logger= get_logger("file_routes")


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
    logger.info(f"Retrieved file IDs for company {Company_id}: {rows}")
    return rows


async def _get_all_files_by_company_pending(db:AsyncSession, Company_id: UUID )-> list[UUID]:
    """
    This is the old sync function
        file_ids_tuples = db.query(File.id).filter_by(company_id=Company_id, status="pending").all()

    """
    result = await db.execute(select(FileModel.id).filter_by(company_id=encode_uuid(Company_id), status="pending"))
    rows= result.scalars().all()
    logger.info(f"Retrieved pending file IDs for company {Company_id}: {rows}")
    return rows

async def _update_file_status_running(db:AsyncSession, file_id: UUID)->None:
    result= await db.execute(select(FileModel).filter_by(id=encode_uuid(file_id)))
    file_record= result.scalars().first()
    logger.info(f"File record before updating to running: {file_record}")
    if file_record:
        file_record.status= "running"
        await db.commit()
        logger.info(f"Updated status for file ID {file_id} to running")
    else:
        logger.warning(f"No file found with ID {file_id} to update to running")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No file found with ID {file_id}")

async def _update_file_status_successful(db:AsyncSession, file_id: UUID)->None:


    result= await db.execute(select(FileModel).filter_by(id=encode_uuid(file_id)))
    file_record= result.scalars().first()
    logger.info(f"File record before updating to successful: {file_record}")
    if file_record:
        file_record.status = "successful"
        await db.commit()
        logger.info(f"Updated status for file ID {file_id} to successful")
    else:
        logger.warning(f"No file found with ID {file_id} to update to successful")

async def _update_file_status_failed(db:AsyncSession, file_id: UUID)->None:
    try:    
        result= await db.execute(select(FileModel).filter_by(id=encode_uuid(file_id)))
        file_record= result.scalars().first()
        logger.info(f"File record before updating to failed: {file_record}")
        if file_record:
            file_record.status = "failed"
            await db.commit()
            logger.info(f"Updated status for file ID {file_id} to failed")
        else:
            logger.warning(f"No file found with ID {file_id} to update to failed")
    except Exception as e:
        logger.error(f"Error updating file status to failed for file ID {file_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")



async def _creating_file_object(file_name: str, company_id: str, file_bytes: bytes, hashed: str, file_type: str):
    new_file= FileModel(
        file_name=file_name,
        company_id=encode_uuid(company_id),
        file_data=file_bytes,
        file_hash=hashed,
        file_format= file_type

    )
    return new_file


"""


"""
@router.post("/create_By_Upload",status_code=status.HTTP_201_CREATED)
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
        file_type=file.content_type
        if existing:
            logger.warning(f"The file {file_name} already exists with hash {hashed}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f" The file already exists")
        else:
            new_file=await _creating_file_object(file_name, company_id, file_bytes, hashed, file_type)
            db.add(new_file)
            await db.commit()
            logger.info(f"Created new file with name: {file_name} for company_id: {company_id}")
        return None

    except Exception as e:
        logger.error(f"Failure in creating file {file_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failure in creating file {str(e)}")


@router.post("/create_By_directory",status_code=status.HTTP_201_CREATED)
async def create_file_by_directory(db:DBSession, directory_path: str, company_id: str)->None:
    """
    This endpoint will take input of a direectory and will keep uploading all the files in it.
    """
    try:
        for file_name in os.listdir(directory_path):
            file_path= os.path.join(directory_path, file_name)
            logger.info(f"Processing file: {file_path}")
            file_type= file_name.split(".")[-1]
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            
            logger.info(f"file_type: {file_type}")
            hashed= _calculate_file_hash(file_bytes)
            existing= await _hash_exist_or_not(hashed, db)  
            if existing:
                logger.warning(f"The file {file_name} already exists with hash {hashed}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f" The file already exists")
            else:
                new_file= await _creating_file_object(file_name, company_id, file_bytes, hashed, file_type)
                db.add(new_file)
                await db.commit()
                logger.info(f"Created new file with name: {file_name} for company_id: {company_id}")
        return None

    except Exception as e:
        logger.error(f"Failure in uploading file by directory: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failure in uploading file by directory: {str(e)}")

@router.get("/download/{company_id}", status_code=status.HTTP_200_OK)
async def download_files_by_company(company_id: str, db:DBSession)->None:
    try:
        result= await db.execute(select(FileModel).filter_by(company_id=encode_uuid(company_id)))
        files= result.scalars().all()
        if not files:
            logger.warning(f"No files found for company {company_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        # The files.file_data is in bytes format, so we need to convert it to bytes
        for file in files:
            # Save the file.file_data to download_dir
            file_path= os.path.join("download_dir", file.file_name)
            with open(file_path, "wb") as f:
                f.write(file.file_data)
            logger.info(f"File {file.file_name} downloaded to {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error downloading files for company {company_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")



@router.get("/ids", status_code=status.HTTP_200_OK, response_model=list[str])
async def get_all_file_id_by_company(db:DBSession, company_id: str)->list[str]:
    try:
        file_id= await  _get_all_files_id_from_db(db, company_id)
        if len(file_id)==0:
            logger.warning(f"No files found for company {company_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
            
        return [str(decode_uuid(id)) for id in file_id]
    except Exception as e:
        logger.error(f"Error retrieving file IDs for company {company_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
    
@router.get("/{company_id}/pending", status_code=status.HTTP_200_OK, response_model=list[UUID])
async def get_all_file_id_by_company_pending(db:DBSession, company_id: str)->list[UUID]:
    try:
        file_id= await _get_all_files_by_company_pending(db, company_id)
        if len(file_id)==0:
            logger.warning(f"No pending files found for company {company_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        return file_id
    except Exception as e:
        logger.error(f"Error retrieving pending file IDs for company {company_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")

@router.post("/{file_id}/running", status_code=status.HTTP_200_OK)
async def update_file_status_running(db:DBSession, file_id: str)->None:
    try:
        await _update_file_status_running(db, file_id)
    except Exception as e:
        logger.error(f"Error updating file status to running for file ID {file_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
        

@router.post("/{file_id}/successful", status_code=status.HTTP_200_OK)
async def update_file_status_successful(db:DBSession, file_id: str)->None:
    try:
        await _update_file_status_successful(db, file_id)
    except Exception as e:
        logger.error(f"Error updating file status to successful for file ID {file_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
      
@router.post("/{file_id}/failed", status_code=status.HTTP_200_OK)
async def update_file_status_failed(db:DBSession, file_id: str)->None:
    try:
       await _update_file_status_failed(db, file_id)
    except Exception as e:
        logger.error(f"Error updating file status to failed for file ID {file_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}")
      