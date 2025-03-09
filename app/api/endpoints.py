from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
from datetime import datetime, timedelta
import uuid

from app.database.database import get_db
from app.models.models import User, Conversation, Message
from app.schemas.schemas import (
    UserCreate, UserLogin, Token, User as UserSchema,
    Conversation as ConversationSchema, Message as MessageSchema,
    ConversationCreate, ConversationUpdate, MessageCreate, MessageResponse
)
from app.utils.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.utils.llm import llm

router = APIRouter()

@router.post("/register", response_model=UserSchema)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email == user.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/token", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/conversations", response_model=ConversationSchema)
async def create_conversation(
    conv: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    db_conversation = Conversation(
        title=conv.title,
        user_id=current_user.id
    )
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)
    return db_conversation

@router.get("/conversations", response_model=List[ConversationSchema])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Conversation).where(Conversation.user_id == current_user.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/conversations/{conversation_id}/title", response_model=ConversationSchema)
async def update_conversation_title(
    conversation_id: uuid.UUID,
    conv_update: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation.title = conv_update.title
    await db.commit()
    await db.refresh(conversation)
    return conversation

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageSchema])
async def get_messages(
    conversation_id: uuid.UUID,
    before_timestamp: datetime = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    query = select(Message).where(Message.conversation_id == conversation_id)
    if before_timestamp:
        query = query.where(Message.timestamp < before_timestamp)
    query = query.order_by(Message.timestamp.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/conversations/{conversation_id}/converse", response_model=MessageResponse)
async def converse(
    conversation_id: uuid.UUID,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify conversation exists and belongs to user
    query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Store user message
    user_message = Message(
        content=message.content,
        role="user",
        conversation_id=conversation_id
    )
    db.add(user_message)
    await db.commit()
    
    # Get conversation history for context
    query = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp)
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # Convert to format expected by LLM
    llm_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    
    # Get LLM response
    llm_response = await llm.infer(llm_messages)
    
    # Store assistant message
    assistant_message = Message(
        content=llm_response,
        role="assistant",
        conversation_id=conversation_id
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)
    
    return MessageResponse(
        content=assistant_message.content,
        role=assistant_message.role,
        timestamp=assistant_message.timestamp
    ) 