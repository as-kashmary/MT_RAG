from pydantic import BaseModel
from uuid import UUID
from .db_connection_new import DBSession
from fastapi import APIRouter, HTTPException, Request, Response, status, Depends, UploadFile, File, Body, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .entities import QueryAndAnswer as QueryAndAnswerModel , decode_uuid, encode_uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import  AsyncSession
from hashlib import sha256

from src.logging.logging import get_logger
logger= get_logger("query_routes")


class query_answer_validation(BaseModel):
    query: str
    response: str
    user_id: str


router= APIRouter(
    prefix='/query_answer',
    tags=['query_answer']
)

async def _get_all_query_ids_from_db(db:AsyncSession)->list[UUID]:
    result= await db.execute(select(QueryAndAnswerModel.id))
    rows= result.scalars().all()
    logger.info(f"Retrieved query IDs: {rows}")
    return rows

async def _get_all_query_ids_by_user_from_db(db:AsyncSession, user_id:str)->list[UUID]:
    result= await db.execute(select(QueryAndAnswerModel.id).filter_by(user_id=encode_uuid(user_id)))
    rows= result.scalars().all()
    logger.info(f"Retrieved query IDs for user {user_id}: {rows}")
    return rows


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_query_answer(db:DBSession, query_answer:query_answer_validation)->None:
    try:
        user_id_bytes=encode_uuid(query_answer.user_id)
        new_query_answer= QueryAndAnswerModel(
            query=query_answer.query,
            response=query_answer.response,
            user_id=user_id_bytes
        )
        db.add(new_query_answer)
        await db.commit()
        logger.info(f"Created new query answer for user_id: {query_answer.user_id}")
        return None
    except Exception as e:
        logger.error(f"Error creating query answer for user_id: {query_answer.user_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failure in creating query answer {str(e)}")
    
@router.get("/ids", status_code=status.HTTP_200_OK, response_model=list[str])
async def get_all_query_id(db:DBSession)->list[str]:
    try: 
        query_ids= await _get_all_query_ids_from_db(db)
        if len(query_ids)==0:
            logger.warning("Query table is empty.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query table is empty")
        return [str(decode_uuid(qid)) for qid in query_ids]
    except Exception as e:
        logger.error(f"Error retrieving query IDs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=list[str])
async def get_all_ids_by_user(db:DBSession, user_id:str)->list[str]:
    try:
        query_ids= await _get_all_query_ids_by_user_from_db(db, user_id)
        if len(query_ids)==0:
            logger.warning(f"Query table is empty for user {user_id}.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Query table is empty for this specific user {user_id}")
        return [str(decode_uuid(qid)) for qid in query_ids]
    except Exception as e:
        logger.error(f"Error retrieving query IDs for user {user_id}: {str(e)}")
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))