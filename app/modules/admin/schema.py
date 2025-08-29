# app/modules/admin/schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PendingBlogOut(BaseModel):
    id: int
    title: str
    content: str
    author_name: str
    domain_name: str
    status: str
    created_at: datetime
    updated_at: datetime

class BlogApprovalUpdate(BaseModel):
    rejection_reason: Optional[str] = None
