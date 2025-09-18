# database.py
import os
import time
import logging
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, Gauge

# Load environment variables
load_dotenv()

# ---------------- Logger ----------------
logger = logging.getLogger("db")
logger.setLevel(logging.INFO)

# ---------------- Prometheus Metrics ----------------
db_query_total = Counter(
    'db_query_total',
    'Total number of database queries executed',
    ['query_type']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Duration of database queries in seconds',
    ['query_type']
)

db_active_connections = Gauge(
    'db_active_connections',
    'Number of active connections in the database pool'
)

# ---------------- Database Manager ----------------
class DatabaseManager:
    """Database manager using psycopg2 connection pooling"""

    def __init__(self):
        self.pool = None
        self._ensure_database_exists()
        self._init_pool()
        self._ensure_tables_exist()

    def _ensure_database_exists(self):
        """Create database if it doesn't exist"""
        try:
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = int(os.getenv("DB_PORT", 5432))
            db_name = os.getenv("DB_NAME", "blogpost_db")
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "rishi1023")
            
            # Connect to default postgres database to check if our database exists
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                database="postgres",  # Connect to default database
                user=db_user,
                password=db_password
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cursor.fetchone():
                logger.info(f"Database '{db_name}' not found. Creating...")
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                logger.info(f"Database '{db_name}' created successfully")
            else:
                logger.info(f"Database '{db_name}' already exists")
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error ensuring database exists: {e}", exc_info=True)
            # Don't raise here - let the connection pool initialization handle the error

    def _init_pool(self):
        """Initialize the connection pool"""
        try:
            min_conn = int(os.getenv("DB_POOL_MIN", 1))
            max_conn = int(os.getenv("DB_POOL_MAX", 20))

            self.pool = psycopg2.pool.SimpleConnectionPool(
                min_conn, max_conn,
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 5432)),
                database=os.getenv("DB_NAME", "blogpost_db"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "rishi1023"),
                cursor_factory=RealDictCursor
            )
            logger.info(f"Database pool initialized (min={min_conn}, max={max_conn})")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}", exc_info=True)
            raise e

    def _ensure_tables_exist(self):
        """Create tables if they don't exist"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create domains table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS domains (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(255) UNIQUE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # Create blogs table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS blogs (
                            id SERIAL PRIMARY KEY,
                            title VARCHAR(500) NOT NULL,
                            content TEXT NOT NULL,
                            author_name VARCHAR(255) NOT NULL,
                            domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
                            status VARCHAR(50) DEFAULT 'pending',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # Create events table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS events (
                            id SERIAL PRIMARY KEY,
                            title VARCHAR(500) NOT NULL,
                            description TEXT,
                            event_date TIMESTAMP NOT NULL,
                            event_type VARCHAR(100) NOT NULL,
                            domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # Create event_registrations table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS event_registrations (
                            id SERIAL PRIMARY KEY,
                            event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                            user_name VARCHAR(255) NOT NULL,
                            email VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(event_id, email)
                        );
                    """)
                    
                    # Insert default domains if none exist
                    cursor.execute("SELECT COUNT(*) as domain_count FROM domains")
                    result = cursor.fetchone()
                    domain_count = result['domain_count'] if result else 0
                    
                    if domain_count == 0:
                        default_domains = [
                            'Computer Science',
                            'Information Technology',
                            'Electronics',
                            'Mechanical Engineering',
                            'Civil Engineering'
                        ]
                        
                        for domain in default_domains:
                            cursor.execute(
                                "INSERT INTO domains (name) VALUES (%s)",
                                (domain,)
                            )
                        
                        logger.info(f"Inserted {len(default_domains)} default domains")
                    
                    conn.commit()
                    logger.info("All required tables ensured to exist")
                    
        except Exception as e:
            logger.error(f"Error ensuring tables exist: {e}", exc_info=True)
            raise e

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.pool.getconn()
            # Update Prometheus active connections
            db_active_connections.set(len(self.pool._used))
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation error: {e}", exc_info=True)
            raise e
        finally:
            if conn:
                self.pool.putconn(conn)
                db_active_connections.set(len(self.pool._used))

    def _track_query(self, query: str, func, params=None):
        query_type = query.strip().split()[0].upper()
        db_query_total.labels(query_type=query_type).inc()
        start_time = time.time()
        result = func(query, params)
        db_query_duration_seconds.labels(query_type=query_type).observe(time.time() - start_time)
        return result

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        return self._track_query(query, lambda q, p: self._execute(q, p, fetch="all"), params)

    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute a SELECT query and return single result"""
        return self._track_query(query, lambda q, p: self._execute(q, p, fetch="one"), params)

    def execute_insert(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute an INSERT query and return the inserted record"""
        return self._track_query(query, lambda q, p: self._execute(q, p, fetch="one"), params)

    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an UPDATE/DELETE query and return affected rows"""
        return self._track_query(query, lambda q, p: self._execute(q, p, fetch="rowcount"), params)

    def _execute(self, query: str, params: tuple = None, fetch="all"):
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch == "all":
                    return cursor.fetchall()
                elif fetch == "one":
                    return cursor.fetchone()
                elif fetch == "rowcount":
                    return cursor.rowcount
                return None

    def get_active_connections_count(self) -> int:
        """Get the number of active connections in the pool"""
        try:
            return len(self.pool._used) if self.pool else 0
        except Exception as e:
            logger.error(f"Error getting active connections count: {e}")
            return 0

    def check_database_health(self) -> Dict[str, Any]:
        """Check database health and return status"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if all required tables exist
                    required_tables = ['domains', 'blogs', 'events', 'event_registrations']
                    existing_tables = []
                    
                    for table in required_tables:
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = %s
                            );
                        """, (table,))
                        if cursor.fetchone()[0]:
                            existing_tables.append(table)
                    
                    # Check row counts
                    table_counts = {}
                    for table in existing_tables:
                        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                        result = cursor.fetchone()
                        table_counts[table] = result['count'] if result else 0
                    
                    return {
                        "status": "healthy" if len(existing_tables) == len(required_tables) else "missing_tables",
                        "required_tables": required_tables,
                        "existing_tables": existing_tables,
                        "table_counts": table_counts,
                        "active_connections": self.get_active_connections_count()
                    }
        except Exception as e:
            logger.error(f"Error checking database health: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def repair_database(self) -> bool:
        """Repair database by recreating missing tables"""
        try:
            logger.info("Starting database repair...")
            self._ensure_tables_exist()
            logger.info("Database repair completed successfully")
            return True
        except Exception as e:
            logger.error(f"Database repair failed: {e}")
            return False

    def close_pool(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


# ---------------- Global Database Manager ----------------
db_manager = DatabaseManager()

# ---------------- BlogsDB ----------------
class BlogsDB:
    """Database operations for blogs"""

    @staticmethod
    def get_or_create_domain(domain_name: str) -> Optional[int]:
        try:
            domain = db_manager.execute_single(
                "SELECT id FROM domains WHERE name = %s;",
                (domain_name,)
            )
            if domain:
                return domain["id"]
            new_domain = db_manager.execute_insert(
                "INSERT INTO domains (name) VALUES (%s) RETURNING id;",
                (domain_name,)
            )
            logger.info(f"Domain '{domain_name}' auto-created with ID {new_domain['id']}")
            return new_domain["id"]
        except Exception as e:
            logger.error(f"Error in get_or_create_domain: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def create_blog(title: str, content: str, author_name: str, domain_name: str) -> Optional[Dict[str, Any]]:
        try:
            domain_id = BlogsDB.get_or_create_domain(domain_name)
            if domain_id is None:
                raise Exception("Domain creation failed")
            blog_result = db_manager.execute_insert(
                """
                INSERT INTO blogs (title, content, author_name, domain_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (title, content, author_name, domain_id)
            )
            blog = db_manager.execute_single(
                """
                SELECT b.*, d.name AS domain_name
                FROM blogs b
                JOIN domains d ON b.domain_id = d.id
                WHERE b.id = %s;
                """,
                (blog_result["id"],)
            )
            logger.info(f"Blog '{blog['title']}' submitted by {blog['author_name']}")
            return blog
        except Exception as e:
            logger.error(f"Error creating blog: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def get_blogs(domain_name: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
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
            logger.error(f"Error getting blogs: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def get_blog_by_id(blog_id: int) -> Optional[Dict[str, Any]]:
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
            logger.error(f"Error getting blog by ID: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def update_blog(blog_id: int, title: str, content: str, author_name: str, domain_name: str) -> Optional[Dict[str, Any]]:
        try:
            domain_id = BlogsDB.get_or_create_domain(domain_name)
            if domain_id is None:
                raise Exception("Domain creation failed")
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
            return BlogsDB.get_blog_by_id(blog_id)
        except Exception as e:
            logger.error(f"Error updating blog: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def delete_blog(blog_id: int) -> bool:
        try:
            affected_rows = db_manager.execute_update(
                "DELETE FROM blogs WHERE id = %s;",
                (blog_id,)
            )
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error deleting blog: {str(e)}", exc_info=True)
            return False


# ---------------- DomainsDB ----------------
class DomainsDB:
    @staticmethod
    def get_all_domains() -> List[Dict[str, Any]]:
        try:
            return db_manager.execute_query("SELECT * FROM domains ORDER BY name;")
        except Exception as e:
            logger.error(f"Error getting domains: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def create_domain(name: str, description: str = None) -> Optional[Dict[str, Any]]:
        try:
            return db_manager.execute_insert(
                "INSERT INTO domains (name) VALUES (%s) RETURNING *;",
                (name,)
            )
        except Exception as e:
            logger.error(f"Error creating domain: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def get_domain_by_id(domain_id: int) -> Optional[Dict[str, Any]]:
        try:
            return db_manager.execute_single(
                "SELECT * FROM domains WHERE id = %s;",
                (domain_id,)
            )
        except Exception as e:
            logger.error(f"Error getting domain by ID: {str(e)}", exc_info=True)
            return None


# ---------------- EventsDB ----------------
class EventsDB:
    @staticmethod
    def create_event(title: str, description: str, event_date: str, event_type: str, domain_id: int) -> Optional[Dict[str, Any]]:
        try:
            return db_manager.execute_insert(
                """
                INSERT INTO events (title, description, event_date, event_type, domain_id)
                VALUES (%s, %s, %s, %s, %s) RETURNING *;
                """,
                (title, description, event_date, event_type, domain_id)
            )
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def get_events(domain_name: Optional[str] = None) -> List[Dict[str, Any]]:
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
            logger.error(f"Error getting events: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def get_event_by_id(event_id: int) -> Optional[Dict[str, Any]]:
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
            logger.error(f"Error getting event by ID: {str(e)}", exc_info=True)
            return None


# ---------------- EventRegistrationsDB ----------------
class EventRegistrationsDB:
    @staticmethod
    def create_registration(event_id: int, user_name: str, email: str) -> Optional[Dict[str, Any]]:
        try:
            return db_manager.execute_insert(
                """
                INSERT INTO event_registrations (event_id, user_name, email)
                VALUES (%s, %s, %s) RETURNING *;
                """,
                (event_id, user_name, email)
            )
        except Exception as e:
            logger.error(f"Error creating registration: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def get_registrations_by_event(event_id: int) -> List[Dict[str, Any]]:
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
            logger.error(f"Error getting registrations: {str(e)}", exc_info=True)
            return []


# ---------------- AdminDB ----------------
class AdminDB:
    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        try:
            stats = {}
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
            logger.error(f"Error getting dashboard stats: {str(e)}", exc_info=True)
            return {}

    @staticmethod
    def get_active_db_connections() -> int:
        """Get the number of active database connections"""
        try:
            return db_manager.get_active_connections_count()
        except Exception as e:
            logger.error(f"Error getting active DB connections: {str(e)}", exc_info=True)
            return 0

    @staticmethod
    def get_database_health() -> Dict[str, Any]:
        """Get comprehensive database health information"""
        try:
            return db_manager.check_database_health()
        except Exception as e:
            logger.error(f"Error getting database health: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    @staticmethod
    def repair_database() -> bool:
        """Repair database if there are issues"""
        try:
            return db_manager.repair_database()
        except Exception as e:
            logger.error(f"Error repairing database: {str(e)}", exc_info=True)
            return False
