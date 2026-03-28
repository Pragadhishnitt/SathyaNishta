from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_session
from app.models.chat import ChatThread, ChatMessage
from app.models.user import User
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

router = APIRouter(prefix="/api/chat", tags=["chat-persistence"])

class ChatThreadCreate(BaseModel):
    title: str
    mode: str = "standard"
    investigation_id: Optional[str] = None

class ChatThreadResponse(BaseModel):
    id: str
    title: str
    mode: str
    investigation_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessage] = []

class ChatMessageCreate(BaseModel):
    content: str
    role: str
    extra_data: Optional[str] = None

@router.get("/threads/{user_id}")
async def get_user_threads(user_id: int, session: Session = Depends(get_session)):
    """Get all chat threads for a specific user"""
    threads = session.query(ChatThread).filter(ChatThread.user_id == user_id).order_by(ChatThread.updated_at.desc()).all()
    return threads

@router.post("/threads/{user_id}")
async def create_thread(user_id: int, thread_data: ChatThreadCreate, session: Session = Depends(get_session)):
    """Create a new chat thread for a user"""
    # Verify user exists
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    thread = ChatThread(
        title=thread_data.title,
        mode=thread_data.mode,
        investigation_id=thread_data.investigation_id,
        user_id=user_id
    )
    session.add(thread)
    session.commit()
    session.refresh(thread)
    return thread

@router.get("/threads/{user_id}/{thread_id}")
async def get_thread_with_messages(user_id: int, thread_id: str, session: Session = Depends(get_session)):
    """Get a specific thread with all its messages"""
    thread = session.query(ChatThread).filter(
        ChatThread.user_id == user_id,
        ChatThread.id == thread_id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Get messages for this thread
    messages = session.query(ChatMessage).filter(ChatMessage.thread_id == thread_id).order_by(ChatMessage.created_at.asc()).all()
    
    return ChatThreadResponse(
        id=thread.id,
        title=thread.title,
        mode=thread.mode,
        investigation_id=thread.investigation_id,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        messages=messages
    )

@router.post("/threads/{user_id}/{thread_id}/messages")
async def add_message_to_thread(user_id: int, thread_id: str, message_data: ChatMessageCreate, session: Session = Depends(get_session)):
    """Add a new message to a thread"""
    # Verify thread exists and belongs to user
    thread = session.query(ChatThread).filter(
        ChatThread.user_id == user_id,
        ChatThread.id == thread_id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    message = ChatMessage(
        content=message_data.content,
        role=message_data.role,
        extra_data=message_data.extra_data,
        thread_id=thread_id,
        user_id=user_id
    )
    session.add(message)
    
    # Update thread's updated_at
    thread.updated_at = datetime.utcnow()
    session.commit()
    
    return message

@router.put("/threads/{user_id}/{thread_id}")
async def update_thread(user_id: int, thread_id: str, thread_data: ChatThreadCreate, session: Session = Depends(get_session)):
    """Update a thread's title or other properties"""
    thread = session.query(ChatThread).filter(
        ChatThread.user_id == user_id,
        ChatThread.id == thread_id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread_data.title is not None:
        thread.title = thread_data.title
    if thread_data.mode is not None:
        thread.mode = thread_data.mode
    if thread_data.investigation_id is not None:
        thread.investigation_id = thread_data.investigation_id
    
    thread.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(thread)
    return thread

@router.delete("/threads/{user_id}/{thread_id}")
async def delete_thread(user_id: int, thread_id: str, session: Session = Depends(get_session)):
    """Delete a thread and all its messages"""
    thread = session.query(ChatThread).filter(
        ChatThread.user_id == user_id,
        ChatThread.id == thread_id
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Delete all messages in the thread first
    session.query(ChatMessage).filter(ChatMessage.thread_id == thread_id).delete()
    
    # Delete the thread
    session.delete(thread)
    session.commit()
    
    return {"message": "Thread deleted successfully"}
