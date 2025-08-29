# app/modules/blogs/service.py
from fastapi import Depends
from db.connection import get_db
from core.logger import log_info, log_error

def get_or_create_domain(domain_name: str, db, user_id=None):
    """Check if domain exists, create if not, return domain_id"""
    try:
        db.execute("SELECT id FROM domains WHERE name = %s;", (domain_name,))
        domain = db.fetchone()
        if domain:
            return domain["id"]
        
        db.execute("INSERT INTO domains (name) VALUES (%s) RETURNING id;", (domain_name,))
        new_domain = db.fetchone()
        log_info(f"Domain '{domain_name}' auto-created with ID {new_domain['id']}")
        return new_domain["id"]
    except Exception as e:
        log_error(f"Error in get_or_create_domain: {str(e)}")
        return None


def create_blog(blog_data, db=Depends(get_db), user_id=None):
    try:
        domain_id = get_or_create_domain(blog_data.domain_name, db)
        if domain_id is None:
            raise Exception("Domain creation failed")

        db.execute(
            """
            INSERT INTO blogs (title, content, author_name, domain_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (blog_data.title, blog_data.content, blog_data.author_name, domain_id)
        )
        blog_id = db.fetchone()["id"]

        db.execute(
            """
            SELECT b.*, d.name AS domain_name
            FROM blogs b
            JOIN domains d ON b.domain_id = d.id
            WHERE b.id = %s;
            """,
            (blog_id,)
        )
        blog = db.fetchone()
        log_info(f"Blog '{blog['title']}' submitted by {blog['author_name']}")
        return blog
    except Exception as e:
        log_error(f"Error in create_blog: {str(e)}")
        return None


def get_blog(blog_id: int, db=Depends(get_db)):
    try:
        db.execute(
            """
            SELECT b.*, d.name AS domain_name
            FROM blogs b
            JOIN domains d ON b.domain_id = d.id
            WHERE b.id = %s;
            """,
            (blog_id,)
        )
        blog = db.fetchone()
        log_info(f"Fetched blog ID {blog_id}")
        return blog
    except Exception as e:
        log_error(f"Error in get_blog: {str(e)}")
        return None


def list_blogs(db=Depends(get_db), domain_name: str = None, search: str = None):
    try:
        query = """
            SELECT b.*, d.name AS domain_name
            FROM blogs b
            JOIN domains d ON b.domain_id = d.id
            WHERE b.status = 'approved'
        """
        params = []
        if domain_name:
            query += " AND d.name = %s"
            params.append(domain_name)
        if search:
            query += " AND b.title ILIKE %s"
            params.append(f"%{search}%")
        
        query += " ORDER BY b.created_at DESC"
        db.execute(query, tuple(params))
        blogs = db.fetchall()
        log_info("Listed approved blogs")
        return blogs
    except Exception as e:
        log_error(f"Error in list_blogs: {str(e)}")
        return []


def update_blog(blog_id: int, blog_data, db=Depends(get_db)):
    try:
        db.execute("SELECT * FROM blogs WHERE id = %s AND status = 'pending';", (blog_id,))
        existing = db.fetchone()
        if not existing:
            return None

        fields = []
        values = []

        if blog_data.title:
            fields.append("title = %s")
            values.append(blog_data.title)
        if blog_data.content:
            fields.append("content = %s")
            values.append(blog_data.content)
        if blog_data.domain_name:
            domain_id = get_or_create_domain(blog_data.domain_name, db)
            fields.append("domain_id = %s")
            values.append(domain_id)
        
        if fields:
            query = f"UPDATE blogs SET {', '.join(fields)}, updated_at = NOW() WHERE id = %s RETURNING id;"
            values.append(blog_id)
            db.execute(query, tuple(values))
            blog_id = db.fetchone()["id"]

            db.execute(
                """
                SELECT b.*, d.name AS domain_name
                FROM blogs b
                JOIN domains d ON b.domain_id = d.id
                WHERE b.id = %s;
                """,
                (blog_id,)
            )
            updated_blog = db.fetchone()
            log_info(f"Blog ID {blog_id} updated")
            return updated_blog
        return existing
    except Exception as e:
        log_error(f"Error in update_blog: {str(e)}")
        return None


def delete_blog(blog_id: int, db=Depends(get_db)):
    try:
        db.execute("DELETE FROM blogs WHERE id = %s RETURNING *;", (blog_id,))
        deleted = db.fetchone()
        if deleted:
            log_info(f"Blog ID {blog_id} deleted")
        return deleted
    except Exception as e:
        log_error(f"Error in delete_blog: {str(e)}")
        return None
