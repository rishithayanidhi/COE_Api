# database.py
import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseManager:
    """Database manager using psycopg2 connection pooling"""
    
    def __init__(self):
        self.pool = None
        self._init_pool()
    
    def _init_pool(self):
        """Initialize the connection pool"""
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,  # min and max connections
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 5432)),
                database=os.getenv("DB_NAME", "blogpost_db"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "rishi1023"),
                cursor_factory=RealDictCursor
            )
            print("Database connection pool initialized successfully")
        except Exception as e:
            print(f"Failed to create database pool: {e}")
            raise e
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Database operation error: {e}")
            raise e
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute a SELECT query and return single result"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
    
    def execute_insert(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute an INSERT query and return the inserted record"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
    
    def close_pool(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()

# Global database manager instance
db_manager = DatabaseManager()

# Database operations for different modules

class BlogsDB:
    """Database operations for blogs"""
    
    @staticmethod
    def get_or_create_domain(domain_name: str) -> Optional[int]:
        """Check if domain exists, create if not, return domain_id"""
        try:
            # Check if domain exists
            domain = db_manager.execute_single(
                "SELECT id FROM domains WHERE name = %s;", 
                (domain_name,)
            )
            if domain:
                return domain["id"]
            
            # Create new domain
            new_domain = db_manager.execute_insert(
                "INSERT INTO domains (name) VALUES (%s) RETURNING id;", 
                (domain_name,)
            )
            print(f"Domain '{domain_name}' auto-created with ID {new_domain['id']}")
            return new_domain["id"]
        except Exception as e:
            print(f"Error in get_or_create_domain: {str(e)}")
            return None
    
    @staticmethod
    def create_blog(title: str, content: str, author_name: str, domain_name: str) -> Optional[Dict[str, Any]]:
        """Create a new blog"""
        try:
            domain_id = BlogsDB.get_or_create_domain(domain_name)
            if domain_id is None:
                raise Exception("Domain creation failed")
            
            # Insert blog
            blog_result = db_manager.execute_insert(
                """
                INSERT INTO blogs (title, content, author_name, domain_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (title, content, author_name, domain_id)
            )
            
            # Get complete blog data
            blog = db_manager.execute_single(
                """
                SELECT b.*, d.name AS domain_name
                FROM blogs b
                JOIN domains d ON b.domain_id = d.id
                WHERE b.id = %s;
                """,
                (blog_result["id"],)
            )
            print(f"Blog '{blog['title']}' submitted by {blog['author_name']}")
            return blog
        except Exception as e:
            print(f"Error creating blog: {str(e)}")
            return None
    
    @staticmethod
    def get_blogs(domain_name: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all blogs with optional filtering"""
        try:
            query = """
                SELECT b.*, d.name AS domain_name
                FROM blogs b
                JOIN domains d ON b.domain_id = d.id
                WHERE 1=1
            """
            params = []
            
            if domain_name:
                query += " AND d.name = %s"
                params.append(domain_name)
            
            if search:
                query += " AND (b.title ILIKE %s OR b.content ILIKE %s)"
                params.extend([f"%{search}%", f"%{search}%"])
            
            query += " ORDER BY b.created_at DESC;"
            
            return db_manager.execute_query(query, tuple(params))
        except Exception as e:
            print(f"Error getting blogs: {str(e)}")
            return []
    
    @staticmethod
    def get_blog_by_id(blog_id: int) -> Optional[Dict[str, Any]]:
        """Get a single blog by ID"""
        try:
            return db_manager.execute_single(
                """
                SELECT b.*, d.name AS domain_name
                FROM blogs b
                JOIN domains d ON b.domain_id = d.id
                WHERE b.id = %s;
                """,
                (blog_id,)
            )
        except Exception as e:
            print(f"Error getting blog by ID: {str(e)}")
            return None
    
    @staticmethod
    def update_blog(blog_id: int, title: str, content: str, author_name: str, domain_name: str) -> Optional[Dict[str, Any]]:
        """Update a blog"""
        try:
            domain_id = BlogsDB.get_or_create_domain(domain_name)
            if domain_id is None:
                raise Exception("Domain creation failed")
            
            # Update blog
            affected_rows = db_manager.execute_update(
                """
                UPDATE blogs 
                SET title = %s, content = %s, author_name = %s, domain_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND status = 'pending';
                """,
                (title, content, author_name, domain_id, blog_id)
            )
            
            if affected_rows == 0:
                return None
            
            # Return updated blog
            return BlogsDB.get_blog_by_id(blog_id)
        except Exception as e:
            print(f"Error updating blog: {str(e)}")
            return None
    
    @staticmethod
    def delete_blog(blog_id: int) -> bool:
        """Delete a blog"""
        try:
            affected_rows = db_manager.execute_update(
                "DELETE FROM blogs WHERE id = %s;",
                (blog_id,)
            )
            return affected_rows > 0
        except Exception as e:
            print(f"Error deleting blog: {str(e)}")
            return False

class DomainsDB:
    """Database operations for domains"""
    
    @staticmethod
    def get_all_domains() -> List[Dict[str, Any]]:
        """Get all domains"""
        try:
            return db_manager.execute_query("SELECT * FROM domains ORDER BY name;")
        except Exception as e:
            print(f"Error getting domains: {str(e)}")
            return []
    
    @staticmethod
    def create_domain(name: str, description: str = None) -> Optional[Dict[str, Any]]:
        """Create a new domain"""
        try:
            return db_manager.execute_insert(
                "INSERT INTO domains (name) VALUES (%s) RETURNING *;",
                (name,)
            )
        except Exception as e:
            print(f"Error creating domain: {str(e)}")
            return None
    
    @staticmethod
    def get_domain_by_id(domain_id: int) -> Optional[Dict[str, Any]]:
        """Get domain by ID"""
        try:
            return db_manager.execute_single(
                "SELECT * FROM domains WHERE id = %s;",
                (domain_id,)
            )
        except Exception as e:
            print(f"Error getting domain by ID: {str(e)}")
            return None

class EventsDB:
    """Database operations for events"""
    
    @staticmethod
    def create_event(title: str, description: str, event_date: str, event_type: str, domain_id: int) -> Optional[Dict[str, Any]]:
        """Create a new event"""
        try:
            return db_manager.execute_insert(
                """
                INSERT INTO events (title, description, event_date, event_type, domain_id)
                VALUES (%s, %s, %s, %s, %s) RETURNING *;
                """,
                (title, description, event_date, event_type, domain_id)
            )
        except Exception as e:
            print(f"Error creating event: {str(e)}")
            return None
    
    @staticmethod
    def get_events(domain_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all events with optional domain filtering"""
        try:
            if domain_name:
                return db_manager.execute_query(
                    """
                    SELECT e.*, d.name AS domain_name
                    FROM events e
                    JOIN domains d ON e.domain_id = d.id
                    WHERE d.name = %s
                    ORDER BY e.event_date DESC;
                    """,
                    (domain_name,)
                )
            else:
                return db_manager.execute_query(
                    """
                    SELECT e.*, d.name AS domain_name
                    FROM events e
                    JOIN domains d ON e.domain_id = d.id
                    ORDER BY e.event_date DESC;
                    """
                )
        except Exception as e:
            print(f"Error getting events: {str(e)}")
            return []
    
    @staticmethod
    def get_event_by_id(event_id: int) -> Optional[Dict[str, Any]]:
        """Get event by ID"""
        try:
            return db_manager.execute_single(
                """
                SELECT e.*, d.name AS domain_name
                FROM events e
                JOIN domains d ON e.domain_id = d.id
                WHERE e.id = %s;
                """,
                (event_id,)
            )
        except Exception as e:
            print(f"Error getting event by ID: {str(e)}")
            return None

class EventRegistrationsDB:
    """Database operations for event registrations"""
    
    @staticmethod
    def create_registration(event_id: int, user_name: str, email: str) -> Optional[Dict[str, Any]]:
        """Create a new event registration"""
        try:
            return db_manager.execute_insert(
                """
                INSERT INTO event_registrations (event_id, user_name, email)
                VALUES (%s, %s, %s) RETURNING *;
                """,
                (event_id, user_name, email)
            )
        except Exception as e:
            print(f"Error creating registration: {str(e)}")
            return None
    
    @staticmethod
    def get_registrations_by_event(event_id: int) -> List[Dict[str, Any]]:
        """Get all registrations for an event"""
        try:
            return db_manager.execute_query(
                """
                SELECT er.*, e.title AS event_title
                FROM event_registrations er
                JOIN events e ON er.event_id = e.id
                WHERE er.event_id = %s
                ORDER BY er.created_at;
                """,
                (event_id,)
            )
        except Exception as e:
            print(f"Error getting registrations: {str(e)}")
            return []

class AdminDB:
    """Database operations for admin functions"""
    
    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            stats = {}
            
            # Get total counts
            total_blogs = db_manager.execute_single("SELECT COUNT(*) as count FROM blogs;")
            total_events = db_manager.execute_single("SELECT COUNT(*) as count FROM events;")
            total_domains = db_manager.execute_single("SELECT COUNT(*) as count FROM domains;")
            total_registrations = db_manager.execute_single("SELECT COUNT(*) as count FROM event_registrations;")
            
            stats.update({
                "total_blogs": total_blogs["count"] if total_blogs else 0,
                "total_events": total_events["count"] if total_events else 0,
                "total_domains": total_domains["count"] if total_domains else 0,
                "total_registrations": total_registrations["count"] if total_registrations else 0
            })
            
            return stats
        except Exception as e:
            print(f"Error getting dashboard stats: {str(e)}")
            return {}
