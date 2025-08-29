# app/modules/admin/routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from modules.admin import service, schema
from db.connection import get_db

router = APIRouter()

@router.get("/blogs/pending", response_model=List[schema.PendingBlogOut])
def get_pending_blogs(db=Depends(get_db)):
    return service.list_pending_blogs(db)

@router.put("/blogs/{blog_id}/approve")
def approve(blog_id: int, db=Depends(get_db)):
    approved_blog = service.approve_blog(blog_id, db)
    if not approved_blog:
        raise HTTPException(status_code=404, detail="Blog not found or already processed")
    return {"status": "success", "detail": f"Blog ID {blog_id} approved"}

@router.put("/blogs/{blog_id}/reject")
def reject(blog_id: int, data: schema.BlogApprovalUpdate, db=Depends(get_db)):
    if not data.rejection_reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required")
    rejected_blog = service.reject_blog(blog_id, data.rejection_reason, db)
    if not rejected_blog:
        raise HTTPException(status_code=404, detail="Blog not found or already processed")
    return {"status": "success", "detail": f"Blog ID {blog_id} rejected"}
