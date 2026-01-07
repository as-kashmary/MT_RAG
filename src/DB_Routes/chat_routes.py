from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import select, desc
from .db_connection_new import DBSession
from .entities import ChatSession, ChatMessage, Product, encode_uuid, decode_uuid
from datetime import datetime

router = APIRouter(prefix="/history", tags=["history"])

# --- Models ---
class SessionResponse(BaseModel):
    id: str
    title: str
    product_name: str
    product_id: str
    updated_at: datetime

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

class CreateSessionRequest(BaseModel):
    user_id: str
    product_id: str

# --- Routes ---

@router.post("/session/create")
async def create_session(db: DBSession, req: CreateSessionRequest):
    try:
        new_session = ChatSession(
            user_id=encode_uuid(req.user_id),
            product_id=encode_uuid(req.product_id),
            title="New Conversation"
        )
        db.add(new_session)
        await db.commit()
        return {"session_id": str(decode_uuid(new_session.id))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{user_id}", response_model=List[SessionResponse])
async def get_user_sessions(db: DBSession, user_id: str):
    """Fetches chat threads for sidebar (Joined with Product Name)"""
    try:
        stmt = select(ChatSession, Product.name).join(
            Product, ChatSession.product_id == Product.id
        ).where(
            ChatSession.user_id == encode_uuid(user_id)
        ).order_by(desc(ChatSession.updated_at))
        
        result = await db.execute(stmt)
        rows = result.all()
        
        return [
            SessionResponse(
                id=str(decode_uuid(row[0].id)),
                title=row[0].title or "New Chat",
                product_id=str(decode_uuid(row[0].product_id)),
                product_name=row[1], 
                updated_at=row[0].updated_at
            ) for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{session_id}", response_model=List[MessageResponse])
async def get_messages(db: DBSession, session_id: str, limit: int = 20, skip: int = 0):
    """Lazy Loads messages (Infinite Scroll)"""
    try:
        stmt = select(ChatMessage).where(
            ChatMessage.session_id == encode_uuid(session_id)
        ).order_by(desc(ChatMessage.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        # Reverse to show oldest first in UI
        messages.reverse() 
        
        return [
            MessageResponse(
                id=str(decode_uuid(m.id)),
                role=m.role,
                content=m.content,
                created_at=m.created_at
            ) for m in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))