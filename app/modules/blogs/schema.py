# app/modules/blogs/schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BlogBase(BaseModel):
    title: str
    content: str
    author_name: str
    domain_name: str  # Will be used for auto-add if domain not exists

class BlogCreate(BlogBase):
    pass

class BlogUpdate(BaseModel):
    title: Optional[str]
    content: Optional[str]
    domain_name: Optional[str]

class BlogOut(BaseModel):
    id: int
    title: str
    content: str
    author_name: str
    domain_name: str
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
