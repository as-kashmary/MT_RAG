from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from .db_connection_new import DBSession
from .entities import ChatSession, ChatMessage, encode_uuid, decode_uuid
from datetime import datetime

router = APIRouter(prefix="/history", tags=["history"])

# --- Models ---
class SessionResponse(BaseModel):
    id: str
    title: str
    product_name: str
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
    """Creates a new empty chat thread"""
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
    """Fetches all chat threads for the sidebar (Recent first)"""
    try:
        # We join with Product table to get the Product Name for the UI
        # Note: You need to import Product entity at top if you want to join. 
        # For simplicity, we assume product_id lookup or basic fetch here.
        stmt = select(ChatSession).where(
            ChatSession.user_id == encode_uuid(user_id)
        ).order_by(desc(ChatSession.updated_at))
        
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        return [
            SessionResponse(
                id=str(decode_uuid(s.id)),
                title=s.title or "New Chat",
                product_name="Assistant", # You can enhance this with a JOIN later
                updated_at=s.updated_at
            ) for s in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{session_id}", response_model=List[MessageResponse])
async def get_messages(
    db: DBSession, 
    session_id: str, 
    limit: int = 20, 
    skip: int = 0
):
    """Lazy Loads messages. Default: Last 20 messages."""
    try:
        stmt = select(ChatMessage).where(
            ChatMessage.session_id == encode_uuid(session_id)
        ).order_by(desc(ChatMessage.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        # Reverse them because UI expects oldest-to-newest, but we fetched newest-first
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