# app/modules/events/service.py
from fastapi import Depends, HTTPException
from db.connection import get_db
from core.logger import log_info, log_error


def list_events(db=Depends(get_db), domain_id: int = None, event_type: str = None):
    try:
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if domain_id:
            query += " AND domain_id = %s"
            params.append(domain_id)
        if event_type:
            query += " AND event_type = %s"
            params.append(event_type)

        query += " ORDER BY event_date DESC"
        db.execute(query, tuple(params))
        events = db.fetchall()
        log_info("Listed events")
        return events
    except Exception as e:
        log_error(f"Error in list_events: {e}")
        return []


def get_event(event_id: int, db=Depends(get_db)):
    try:
        db.execute("SELECT * FROM events WHERE id = %s;", (event_id,))
        event = db.fetchone()
        log_info(f"Fetched event ID {event_id}")
        return event
    except Exception as e:
        log_error(f"Error in get_event: {e}")
        return None


def create_event(event_data, db=Depends(get_db)):
    try:
        db.execute(
            """
            INSERT INTO events (title, description, domain_id, event_type, event_date)
            VALUES (%s, %s, %s, %s, %s) RETURNING *;
            """,
            (event_data.title, event_data.description, event_data.domain_id,
             event_data.event_type, event_data.event_date)
        )
        event = db.fetchone()
        log_info(f"Event '{event['title']}' created with ID {event['id']}")
        return event
    except Exception as e:
        log_error(f"Error in create_event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create event")


def update_event(event_id: int, event_data, db=Depends(get_db)):
    try:
        fields = []
        values = []

        if event_data.title:
            fields.append("title = %s")
            values.append(event_data.title)
        if event_data.description:
            fields.append("description = %s")
            values.append(event_data.description)
        if event_data.domain_id:
            fields.append("domain_id = %s")
            values.append(event_data.domain_id)
        if event_data.event_type:
            fields.append("event_type = %s")
            values.append(event_data.event_type)
        if event_data.event_date:
            fields.append("event_date = %s")
            values.append(event_data.event_date)

        if fields:
            query = f"UPDATE events SET {', '.join(fields)}, updated_at = NOW() WHERE id = %s RETURNING *;"
            values.append(event_id)
            db.execute(query, tuple(values))
            updated_event = db.fetchone()
            log_info(f"Event ID {event_id} updated")
            return updated_event
        return None
    except Exception as e:
        log_error(f"Error in update_event: {e}")
        raise HTTPException(status_code=500, detail="Failed to update event")


def delete_event(event_id: int, db=Depends(get_db)):
    try:
        db.execute("DELETE FROM events WHERE id=%s RETURNING *;", (event_id,))
        deleted = db.fetchone()
        if deleted:
            log_info(f"Event ID {event_id} deleted")
        return deleted
    except Exception as e:
        log_error(f"Error in delete_event: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete event")
