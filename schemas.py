from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
  username: str
  email: EmailStr
  full_name: Optional[str] = None
  password: str
  role: Optional[str] = "user"

class UserUpdate(BaseModel):
  email: Optional[EmailStr] = None
  full_name: Optional[str] = None
  password: Optional[str] = None

class UserResponse(BaseModel):
  username: str
  email: str
  full_name: Optional[str] = None
  disabled: bool
  role: str
  class Config:
    from_attributes = True

class Token(BaseModel):
  access_token: str
  token_type: str

class TokenData(BaseModel):
  username: Optional[str] = None

class NoteCreate(BaseModel):
  title: str
  content: str
  is_public: Optional[bool] = False
  tags: Optional[List[str]] = []

class NoteUpdate(BaseModel): 
  title: Optional[str] = None
  content: Optional[str] = None
  is_public: Optional[bool] = None
  tags: Optional[List[str]] = None

class NoteResponse(BaseModel):
  id: int
  title: str
  content: str
  owner: str
  is_public: bool
  created_at: datetime
  tags: List[str]
class Config:
  from_attributes = True