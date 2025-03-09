from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class MessageBase(BaseModel):
    content: str
    role: str
    timestamp: datetime

class MessageCreate(BaseModel):
    content: str

class Message(MessageBase):
    id: int
    conversation_id: UUID4

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: str

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationUpdate(BaseModel):
    title: str

class Conversation(ConversationBase):
    id: UUID4
    created_at: datetime
    messages: List[Message] = []

    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    email: EmailStr

class MessageResponse(BaseModel):
    content: str
    role: str
    timestamp: datetime 