# main.py
import logging
import os
import sys
import traceback
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from database import BlogsDB, DomainsDB, EventsDB, EventRegistrationsDB, AdminDB

# Configure logging
def setup_logging():
    """Setup comprehensive logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Create formatters
    formatter = logging.Formatter(log_format, date_format)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.FileHandler("logs/app.log", encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler("logs/error.log", encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

# Initialize logging
logger = setup_logging()

def log_system_info():
    """Log system information at startup"""
    import platform
    import psutil
    
    logger.info("=" * 50)
    logger.info("COE API STARTUP - SYSTEM INFORMATION")
    logger.info("=" * 50)
    logger.info(f"Application Version: 1.0.0")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Architecture: {platform.architecture()}")
    logger.info(f"Processor: {platform.processor()}")
    logger.info(f"CPU Cores: {psutil.cpu_count()}")
    logger.info(f"Memory: {psutil.virtual_memory().total / (1024**3):.2f} GB")
    logger.info(f"Working Directory: {os.getcwd()}")
    
    # Environment variables (exclude sensitive ones)
    logger.info("Environment Variables:")
    safe_env_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'APP_HOST', 'APP_PORT', 'DEBUG', 'LOG_LEVEL']
    for var in safe_env_vars:
        value = os.getenv(var, 'Not Set')
        logger.info(f"  {var}: {value}")
    
    logger.info("=" * 50)

# Pydantic models for request/response schemas
class BlogCreate(BaseModel):
    title: str
    content: str
    author_name: str
    domain_name: str

class BlogUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author_name: Optional[str] = None
    domain_name: Optional[str] = None

class DomainCreate(BaseModel):
    name: str
    description: Optional[str] = None

class EventCreate(BaseModel):
    title: str
    description: str
    event_date: date
    event_type: str
    domain_id: int

class EventRegistrationCreate(BaseModel):
    event_id: int
    user_name: str
    email: str

# Initialize FastAPI app
app = FastAPI(
    title="COE Resource Themes API",
    description="API for managing blogs, events, domains and registrations",
    version="1.0.0"
)

# Global exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    error_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.error(f"Unhandled Exception [ID: {error_id}]")
    logger.error(f"Request: {request.method} {request.url}")
    logger.error(f"Exception Type: {type(exc).__name__}")
    logger.error(f"Exception Message: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "error_id": error_id,
            "timestamp": datetime.now().isoformat()
        }
    )

# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with logging"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    logger.warning(f"Request: {request.method} {request.url}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Request Error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    log_system_info()
    logger.info("🚀 COE API application started successfully")
    logger.info("📊 API Documentation available at: /docs")
    logger.info("📋 ReDoc Documentation available at: /redoc")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information"""
    logger.info("🛑 COE API application shutting down")
    logger.info(f"📅 Shutdown Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = datetime.now()
    
    # Log request
    logger.info(f"📥 Request: {request.method} {request.url}")
    logger.info(f"📱 Client: {request.client.host if request.client else 'Unknown'}")
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        process_time = (datetime.now() - start_time).total_seconds()
        
        # Log response
        logger.info(f"📤 Response: {response.status_code} - {process_time:.3f}s")
        
        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Request failed: {str(e)} - {process_time:.3f}s")
        raise

# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint with system info"""
    logger.info("🏠 Root endpoint accessed")
    return {
        "message": "Welcome to the COE Resource Themes API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "documentation": "/docs"
    }

# Blog endpoints
@app.post("/blogs/", tags=["Blogs"])
def create_blog(blog: BlogCreate):
    """Create a new blog post"""
    try:
        logger.info(f"📝 Creating blog: '{blog.title}' by {blog.author_name}")
        logger.info(f"📝 Blog domain: {blog.domain_name}")
        
        result = BlogsDB.create_blog(
            title=blog.title,
            content=blog.content,
            author_name=blog.author_name,
            domain_name=blog.domain_name
        )
        
        if not result:
            logger.error(f"❌ Failed to create blog: '{blog.title}'")
            raise HTTPException(status_code=400, detail="Failed to create blog")
        
        logger.info(f"✅ Blog created successfully with ID: {result.get('id', 'Unknown')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error creating blog: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while creating blog")

@app.get("/blogs/", tags=["Blogs"])
def get_blogs(domain_name: Optional[str] = None, search: Optional[str] = None):
    """Get all blogs with optional filtering"""
    try:
        logger.info(f"📚 Fetching blogs - Domain: {domain_name or 'All'}, Search: {search or 'None'}")
        
        blogs = BlogsDB.get_blogs(domain_name=domain_name, search=search)
        
        logger.info(f"✅ Retrieved {len(blogs)} blogs")
        return blogs
        
    except Exception as e:
        logger.error(f"❌ Error fetching blogs: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching blogs")

@app.get("/blogs/{blog_id}", tags=["Blogs"])
def get_blog(blog_id: int):
    """Get a specific blog by ID"""
    try:
        logger.info(f"📖 Fetching blog with ID: {blog_id}")
        
        blog = BlogsDB.get_blog_by_id(blog_id)
        
        if not blog:
            logger.warning(f"⚠️ Blog not found with ID: {blog_id}")
            raise HTTPException(status_code=404, detail="Blog not found")
        
        logger.info(f"✅ Blog retrieved: '{blog.get('title', 'Unknown')}'")
        return blog
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching blog {blog_id}: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching blog")

@app.put("/blogs/{blog_id}", tags=["Blogs"])
def update_blog(blog_id: int, blog: BlogUpdate):
    """Update a blog (only pending blogs can be updated)"""
    try:
        logger.info(f"✏️ Updating blog with ID: {blog_id}")
        
        # Get current blog to merge with updates
        current_blog = BlogsDB.get_blog_by_id(blog_id)
        if not current_blog:
            logger.warning(f"⚠️ Blog not found for update with ID: {blog_id}")
            raise HTTPException(status_code=404, detail="Blog not found")
        
        # Use existing values if not provided in update
        title = blog.title if blog.title is not None else current_blog["title"]
        content = blog.content if blog.content is not None else current_blog["content"]
        author_name = blog.author_name if blog.author_name is not None else current_blog["author_name"]
        domain_name = blog.domain_name if blog.domain_name is not None else current_blog["domain_name"]
        
        logger.info(f"✏️ Updating blog: '{title}' by {author_name}")
        
        updated_blog = BlogsDB.update_blog(
            blog_id=blog_id,
            title=title,
            content=content,
            author_name=author_name,
            domain_name=domain_name
        )
        
        if not updated_blog:
            logger.warning(f"⚠️ Cannot update blog {blog_id} - may not be in pending status")
            raise HTTPException(status_code=400, detail="Cannot update blog (only pending blogs can be updated)")
        
        logger.info(f"✅ Blog {blog_id} updated successfully")
        return updated_blog
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating blog {blog_id}: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while updating blog")

@app.delete("/blogs/{blog_id}", tags=["Blogs"])
def delete_blog(blog_id: int):
    """Delete a blog"""
    try:
        logger.info(f"🗑️ Deleting blog with ID: {blog_id}")
        
        success = BlogsDB.delete_blog(blog_id)
        
        if not success:
            logger.warning(f"⚠️ Blog not found for deletion with ID: {blog_id}")
            raise HTTPException(status_code=404, detail="Blog not found")
        
        logger.info(f"✅ Blog {blog_id} deleted successfully")
        return {"status": "success", "detail": "Blog deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting blog {blog_id}: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting blog")

# Domain endpoints
@app.get("/domains/", tags=["Domains"])
def get_domains():
    """Get all domains"""
    try:
        logger.info("🏷️ Fetching all domains")
        
        domains = DomainsDB.get_all_domains()
        
        logger.info(f"✅ Retrieved {len(domains)} domains")
        return domains
        
    except Exception as e:
        logger.error(f"❌ Error fetching domains: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching domains")

@app.post("/domains/", tags=["Domains"])
def create_domain(domain: DomainCreate):
    """Create a new domain"""
    try:
        logger.info(f"🏷️ Creating domain: '{domain.name}'")
        logger.info(f"🏷️ Domain description: {domain.description or 'None'}")
        
        result = DomainsDB.create_domain(name=domain.name, description=domain.description)
        
        if not result:
            logger.error(f"❌ Failed to create domain: '{domain.name}'")
            raise HTTPException(status_code=400, detail="Failed to create domain")
        
        logger.info(f"✅ Domain created successfully with ID: {result.get('id', 'Unknown')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error creating domain: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while creating domain")

@app.get("/domains/{domain_id}", tags=["Domains"])
def get_domain(domain_id: int):
    """Get a specific domain by ID"""
    try:
        logger.info(f"🏷️ Fetching domain with ID: {domain_id}")
        
        domain = DomainsDB.get_domain_by_id(domain_id)
        
        if not domain:
            logger.warning(f"⚠️ Domain not found with ID: {domain_id}")
            raise HTTPException(status_code=404, detail="Domain not found")
        
        logger.info(f"✅ Domain retrieved: '{domain.get('name', 'Unknown')}'")
        return domain
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching domain {domain_id}: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching domain")

# Event endpoints
@app.post("/events/", tags=["Events"])
def create_event(event: EventCreate):
    """Create a new event"""
    try:
        logger.info(f"📅 Creating event: '{event.title}'")
        logger.info(f"📅 Event date: {event.event_date}, Type: {event.event_type}")
        logger.info(f"📅 Domain ID: {event.domain_id}")
        
        result = EventsDB.create_event(
            title=event.title,
            description=event.description,
            event_date=str(event.event_date),
            event_type=event.event_type,
            domain_id=event.domain_id
        )
        
        if not result:
            logger.error(f"❌ Failed to create event: '{event.title}'")
            raise HTTPException(status_code=400, detail="Failed to create event")
        
        logger.info(f"✅ Event created successfully with ID: {result.get('id', 'Unknown')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error creating event: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while creating event")

@app.get("/events/", tags=["Events"])
def get_events(domain_name: Optional[str] = None):
    """Get all events with optional domain filtering"""
    try:
        logger.info(f"📅 Fetching events - Domain: {domain_name or 'All'}")
        
        events = EventsDB.get_events(domain_name=domain_name)
        
        logger.info(f"✅ Retrieved {len(events)} events")
        return events
        
    except Exception as e:
        logger.error(f"❌ Error fetching events: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching events")

@app.get("/events/{event_id}", tags=["Events"])
def get_event(event_id: int):
    """Get a specific event by ID"""
    try:
        logger.info(f"📅 Fetching event with ID: {event_id}")
        
        event = EventsDB.get_event_by_id(event_id)
        
        if not event:
            logger.warning(f"⚠️ Event not found with ID: {event_id}")
            raise HTTPException(status_code=404, detail="Event not found")
        
        logger.info(f"✅ Event retrieved: '{event.get('title', 'Unknown')}'")
        return event
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching event {event_id}: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching event")

# Event Registration endpoints
@app.post("/event-registrations/", tags=["Event Registrations"])
def create_registration(registration: EventRegistrationCreate):
    """Register for an event"""
    try:
        logger.info(f"📝 Creating registration for event {registration.event_id}")
        logger.info(f"📝 User: {registration.user_name} ({registration.email})")
        
        result = EventRegistrationsDB.create_registration(
            event_id=registration.event_id,
            user_name=registration.user_name,
            email=registration.email
        )
        
        if not result:
            logger.error(f"❌ Failed to create registration for event {registration.event_id}")
            raise HTTPException(status_code=400, detail="Failed to create registration")
        
        logger.info(f"✅ Registration created successfully with ID: {result.get('id', 'Unknown')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error creating registration: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while creating registration")

@app.get("/event-registrations/event/{event_id}", tags=["Event Registrations"])
def get_event_registrations(event_id: int):
    """Get all registrations for a specific event"""
    try:
        logger.info(f"📝 Fetching registrations for event {event_id}")
        
        registrations = EventRegistrationsDB.get_registrations_by_event(event_id)
        
        logger.info(f"✅ Retrieved {len(registrations)} registrations for event {event_id}")
        return registrations
        
    except Exception as e:
        logger.error(f"❌ Error fetching registrations for event {event_id}: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching registrations")

# Admin endpoints
@app.get("/admin/dashboard", tags=["Admin"])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        logger.info("📊 Fetching dashboard statistics")
        
        stats = AdminDB.get_dashboard_stats()
        
        logger.info("✅ Dashboard stats retrieved successfully")
        logger.info(f"📊 Stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error fetching dashboard stats: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching dashboard stats")

@app.get("/admin/health", tags=["Admin"])
def health_check():
    """Health check endpoint"""
    try:
        logger.info("🏥 Health check requested")
        
        # Check database connectivity
        try:
            AdminDB.get_dashboard_stats()
            db_status = "healthy"
        except Exception as e:
            logger.error(f"❌ Database health check failed: {str(e)}")
            db_status = "unhealthy"
        
        health_data = {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "message": "API is running",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "version": "1.0.0"
        }
        
        if db_status == "healthy":
            logger.info("✅ Health check passed - All systems operational")
        else:
            logger.warning("⚠️ Health check warning - Database issues detected")
        
        return health_data
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return {
            "status": "unhealthy",
            "message": "Health check failed",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting COE API server...")
        logger.info("🌐 Server will be available at: http://0.0.0.0:8000")
        logger.info("📖 API Documentation: http://0.0.0.0:8000/docs")
        
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        sys.exit(1)
