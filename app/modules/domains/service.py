# app/modules/domains/service.py
from fastapi import Depends, HTTPException
from db.connection import get_db
from core.logger import log_info, log_error


def list_domains(db=Depends(get_db)):
    try:
        db.execute("SELECT * FROM domains ORDER BY name;")
        domains = db.fetchall()
        log_info("Listed all domains")
        return domains
    except Exception as e:
        log_error(f"Error in list_domains: {e}")
        return []


def get_domain(domain_id: int, db=Depends(get_db)):
    try:
        db.execute("SELECT * FROM domains WHERE id=%s;", (domain_id,))
        domain = db.fetchone()
        log_info(f"Fetched domain ID {domain_id}")
        return domain
    except Exception as e:
        log_error(f"Error in get_domain: {e}")
        return None


def create_domain(domain_data, db=Depends(get_db)):
    try:
        db.execute(
            "INSERT INTO domains (name) VALUES (%s) RETURNING *;",
            (domain_data.name,)
        )
        domain = db.fetchone()
        log_info(f"Domain '{domain['name']}' created with ID {domain['id']}")
        return domain
    except Exception as e:
        log_error(f"Error creating domain: {e}")
        raise HTTPException(status_code=500, detail="Failed to create domain")


def update_domain(domain_id: int, domain_data, db=Depends(get_db)):
    try:
        db.execute(
            "UPDATE domains SET name=%s, updated_at=NOW() WHERE id=%s RETURNING *;",
            (domain_data.name, domain_id)
        )
        domain = db.fetchone()
        if domain:
            log_info(f"Domain ID {domain_id} updated to '{domain['name']}'")
        return domain
    except Exception as e:
        log_error(f"Error updating domain: {e}")
        raise HTTPException(status_code=500, detail="Failed to update domain")


def delete_domain(domain_id: int, db=Depends(get_db)):
    try:
        # Check if any blogs are associated with this domain
        db.execute("SELECT COUNT(*) as count FROM blogs WHERE domain_id = %s;", (domain_id,))
        row = db.fetchone()
        count = row['count'] if row else 0

        if count > 0:
            log_error(f"Attempted to delete domain ID {domain_id} but {count} blogs exist")
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete domain ID {domain_id} because {count} blog(s) are attached"
            )

        # Safe to delete
        db.execute("DELETE FROM domains WHERE id = %s RETURNING *;", (domain_id,))
        deleted_row = db.fetchone()

        if deleted_row is None:
            raise HTTPException(status_code=404, detail="Domain not found")

        deleted = dict(deleted_row)
        log_info(f"Domain ID {domain_id} deleted")
        return deleted
    except HTTPException as he:
        raise he
    except Exception as e:
        log_error(f"Error deleting domain: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete domain")
