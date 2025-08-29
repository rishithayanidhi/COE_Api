# app/modules/blogs/routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from modules.blogs import service, schema
from db.connection import get_db

router = APIRouter()
@router.post("/", response_model=schema.BlogOut)
def submit_blog(blog: schema.BlogCreate, db=Depends(get_db)):
    return service.create_blog(blog, db)

@router.get("/", response_model=List[schema.BlogOut])
def get_blogs(domain_name: Optional[str] = None, search: Optional[str] = None, db=Depends(get_db)):
    return service.list_blogs(db, domain_name, search)

@router.get("/{blog_id}", response_model=schema.BlogOut)
def read_blog(blog_id: int, db=Depends(get_db)):
    blog = service.get_blog(blog_id, db)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog

@router.put("/{blog_id}", response_model=schema.BlogOut)
def edit_blog(blog_id: int, blog: schema.BlogUpdate, db=Depends(get_db)):
    updated_blog = service.update_blog(blog_id, blog, db)
    if not updated_blog:
        raise HTTPException(status_code=400, detail="Cannot update blog (only pending blogs)")
    return updated_blog

@router.delete("/{blog_id}")
def remove_blog(blog_id: int, db=Depends(get_db)):
    deleted = service.delete_blog(blog_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Blog not found")
    return {"status": "success", "detail": "Blog deleted successfully"}
