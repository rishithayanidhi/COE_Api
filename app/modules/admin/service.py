# app/modules/admin/service.py
from fastapi import Depends
from db.connection import get_db
from core.logger import log_info, log_error


def list_pending_blogs(db=Depends(get_db)):
    try:
        query = """
            SELECT b.*, d.name AS domain_name
            FROM blogs b
            JOIN domains d ON b.domain_id = d.id
            WHERE b.status = 'pending'
            ORDER BY b.created_at ASC;
        """
        db.execute(query)
        blogs = db.fetchall()
        log_info("Listed pending blogs")
        return blogs
    except Exception as e:
        log_error(f"Error in list_pending_blogs: {str(e)}")
        return []

def approve_blog(blog_id: int, db=Depends(get_db)):
    try:
        db.execute(
            "UPDATE blogs SET status='approved', updated_at=NOW() WHERE id=%s RETURNING id;",
            (blog_id,)
        )
        result = db.fetchone()
        if not result:
            return None

        db.execute(
            """
            SELECT b.*, d.name AS domain_name
            FROM blogs b
            JOIN domains d ON b.domain_id = d.id
            WHERE b.id = %s;
            """,
            (blog_id,)
        )
        approved_blog = db.fetchone()
        if approved_blog:
            log_info(f"Blog ID {blog_id} approved")
        return approved_blog
    except Exception as e:
        log_error(f"Error in approve_blog: {str(e)}")
        return None


def reject_blog(blog_id: int, rejection_reason: str, db=Depends(get_db)):
    try:
        db.execute(
            "UPDATE blogs SET status='rejected', rejection_reason=%s, updated_at=NOW() WHERE id=%s RETURNING id;",
            (rejection_reason, blog_id)
        )
        result = db.fetchone()
        if not result:
            return None

        db.execute(
            """
            SELECT b.*, d.name AS domain_name
            FROM blogs b
            JOIN domains d ON b.domain_id = d.id
            WHERE b.id = %s;
            """,
            (blog_id,)
        )
        rejected_blog = db.fetchone()
        if rejected_blog:
            log_info(f"Blog ID {blog_id} rejected with reason: {rejection_reason}")
        return rejected_blog
    except Exception as e:
        log_error(f"Error in reject_blog: {str(e)}")
        return None
