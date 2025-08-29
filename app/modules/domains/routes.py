# app/modules/domains/routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from modules.domains import service, schema
from db.connection import get_db

router = APIRouter()

@router.get("/", response_model=List[schema.DomainOut])
def get_domains(db=Depends(get_db)):
    return service.list_domains(db)

@router.get("/{domain_id}", response_model=schema.DomainOut)
def read_domain(domain_id: int, db=Depends(get_db)):
    domain = service.get_domain(domain_id, db)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain

@router.post("/", response_model=schema.DomainOut)
def add_domain(domain: schema.DomainCreate, db=Depends(get_db)):
    return service.create_domain(domain, db)

@router.put("/{domain_id}", response_model=schema.DomainOut)
def edit_domain(domain_id: int, domain: schema.DomainUpdate, db=Depends(get_db)):
    updated = service.update_domain(domain_id, domain, db)
    if not updated:
        raise HTTPException(status_code=404, detail="Domain not found")
    return updated

@router.delete("/{domain_id}")
def remove_domain(domain_id: int, db=Depends(get_db)):
    deleted = service.delete_domain(domain_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Domain not found")
    return {"status": "success", "detail": "Domain deleted"}
