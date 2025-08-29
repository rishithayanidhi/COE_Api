# app/modules/event_registrations/service.py
from db.connection import get_db
from fastapi import Depends, HTTPException
from core.logger import log_info, log_error


def register_user(event_id: int, user_id: int, db=Depends(get_db), ip_address=None):
    try:
        query = """
            INSERT INTO event_registrations (event_id, user_id)
            VALUES (%s, %s)
            RETURNING id, event_id, user_id, registered_at, status;
        """
        db.execute(query, (event_id, user_id))
        registration = db.fetchone()
        log_info(f"User ID {user_id} registered for Event ID {event_id}")
        return registration
    except Exception as e:
        log_error(f"Error registering user ID {user_id} for Event ID {event_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register user for event")


def list_registrations(event_id: int, db=Depends(get_db)):
    try:
        query = """
            SELECT id, event_id, user_id, registered_at, status
            FROM event_registrations
            WHERE event_id = %s;
        """
        db.execute(query, (event_id,))
        registrations = db.fetchall()
        log_info(f"Listed registrations for Event ID {event_id}")
        return registrations
    except Exception as e:
        log_error(f"Error listing registrations for Event ID {event_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch registrations")
