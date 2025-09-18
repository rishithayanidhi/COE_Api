# # main.py
# import logging
# import os
# import sys
# import traceback
# import time
# import asyncio
# from datetime import datetime, date
# from fastapi import FastAPI, HTTPException, Request
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# from typing import Optional

# # Import database
# from database import (
#     BlogsDB,
#     DomainsDB,
#     EventsDB,
#     EventRegistrationsDB,
#     AdminDB,
#     db_active_connections,       # Gauge
#     db_query_total,              # Counter
#     db_query_duration_seconds    # Histogram
# )

# # Prometheus
# from prometheus_fastapi_instrumentator import Instrumentator
# from prometheus_client import Counter, Histogram, Gauge

# # ----------------- Logging Setup -----------------
# def setup_logging():
#     os.makedirs("logs", exist_ok=True)
#     log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#     date_format = "%Y-%m-%d %H:%M:%S"
#     formatter = logging.Formatter(log_format, date_format)
#     logger = logging.getLogger()
#     logger.setLevel(logging.INFO)
#     logger.handlers.clear()

#     console_handler = logging.StreamHandler(sys.stdout)
#     console_handler.setLevel(logging.INFO)
#     console_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)

#     file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
#     file_handler.setLevel(logging.INFO)
#     file_handler.setFormatter(formatter)
#     logger.addHandler(file_handler)

#     error_handler = logging.FileHandler("logs/error.log", encoding="utf-8")
#     error_handler.setLevel(logging.ERROR)
#     error_handler.setFormatter(formatter)
#     logger.addHandler(error_handler)

#     return logger

# logger = setup_logging()
# START_TIME = time.time()

# # ----------------- System Info -----------------
# def log_system_info():
#     import platform, psutil

#     logger.info("=" * 50)
#     logger.info("COE API STARTUP - SYSTEM INFORMATION")
#     logger.info("=" * 50)
#     logger.info(f"Application Version: 1.0.0")
#     logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#     logger.info(f"Python Version: {sys.version}")
#     logger.info(f"Platform: {platform.platform()}")
#     logger.info(f"Architecture: {platform.architecture()}")
#     logger.info(f"Processor: {platform.processor()}")
#     logger.info(f"CPU Cores: {psutil.cpu_count()}")
#     logger.info(f"Memory: {psutil.virtual_memory().total / (1024**3):.2f} GB")
#     logger.info(f"Working Directory: {os.getcwd()}")

#     safe_env_vars = [
#         "DB_HOST",
#         "DB_PORT",
#         "DB_NAME",
#         "APP_HOST",
#         "APP_PORT",
#         "DEBUG",
#         "LOG_LEVEL",
#     ]
#     logger.info("Environment Variables:")
#     for var in safe_env_vars:
#         value = os.getenv(var, "Not Set")
#         logger.info(f"  {var}: {value}")
#     logger.info("=" * 50)

# # ----------------- FastAPI App -----------------
# app = FastAPI(
#     title="COE Resource Themes API",
#     description="API for managing blogs, events, domains and registrations with Prometheus metrics",
#     version="1.0.0",
# )

# # ----------------- Prometheus Metrics -----------------
# http_requests_total = Counter(
#     "http_requests_total",
#     "Total HTTP requests",
#     ["method", "endpoint", "status"],
# )
# http_request_duration_seconds = Histogram(
#     "http_request_duration_seconds",
#     "Request duration in seconds",
#     ["method", "endpoint"],
# )
# process_uptime_seconds = Gauge(
#     "process_uptime_seconds",
#     "API uptime in seconds"
# )

# # ----------------- Database Metrics -----------------
# # db_active_connections = Gauge("db_active_connections", "Active DB connections")
# # db_query_total = Counter("db_query_total", "Total DB queries executed", ["query_type"])
# # db_query_duration_seconds = Histogram("db_query_duration_seconds", "DB query duration", ["query_type"])

# # ----------------- Middleware for metrics -----------------
# @app.middleware("http")
# async def metrics_middleware(request: Request, call_next):
#     start_time = time.time()
#     method = request.method
#     endpoint = request.url.path
#     try:
#         response = await call_next(request)
#         status = str(response.status_code)
#     except Exception:
#         status = "500"
#         raise
#     finally:
#         duration = time.time() - start_time
#         http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
#         http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
#         process_uptime_seconds.set(time.time() - START_TIME)
#     return response

# # ----------------- Prometheus Instrumentator -----------------
# instrumentator = Instrumentator(
#     should_group_status_codes=False,
#     should_ignore_untemplated=False,
#     excluded_handlers=["/metrics"],
# )
# instrumentator.instrument(app).expose(app)

# # ----------------- DB Metrics Task -----------------
# async def update_db_metrics_task():
#     while True:
#         try:
#             active_conns = AdminDB.get_active_db_connections()
#             db_active_connections.set(active_conns)
#         except Exception as e:
#             logger.error(f"Error updating DB metrics: {e}")
#         await asyncio.sleep(5)

# # ----------------- Pydantic Models -----------------
# class BlogCreate(BaseModel):
#     title: str
#     content: str
#     author_name: str
#     domain_name: str

# class BlogUpdate(BaseModel):
#     title: Optional[str] = None
#     content: Optional[str] = None
#     author_name: Optional[str] = None
#     domain_name: Optional[str] = None

# class DomainCreate(BaseModel):
#     name: str
#     description: Optional[str] = None

# class EventCreate(BaseModel):
#     title: str
#     description: str
#     event_date: date
#     event_type: str
#     domain_id: int

# class EventRegistrationCreate(BaseModel):
#     event_id: int
#     user_name: str
#     email: str

# # ----------------- Exception Handlers -----------------
# @app.exception_handler(Exception)
# async def global_exception_handler(request: Request, exc: Exception):
#     error_id = datetime.now().strftime("%Y%m%d_%H%M%S")
#     logger.error(f"Unhandled Exception [ID: {error_id}] {type(exc).__name__}: {exc}")
#     logger.error(traceback.format_exc())
#     return JSONResponse(
#         status_code=500,
#         content={
#             "error": "Internal Server Error",
#             "error_id": error_id,
#             "timestamp": datetime.now().isoformat(),
#         },
#     )

# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     logger.warning(f"HTTP Exception {exc.status_code}: {exc.detail}")
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "error": "Request Error",
#             "message": exc.detail,
#             "timestamp": datetime.now().isoformat(),
#         },
#     )

# # ----------------- Startup / Shutdown -----------------
# @app.on_event("startup")
# async def startup_event():
#     log_system_info()
#     logger.info("🚀 COE API started")
#     logger.info("📊 API Docs: /docs")
#     logger.info("📊 Metrics: /metrics")
#     asyncio.create_task(update_db_metrics_task())

# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("🛑 COE API shutting down")

# # ----------------- Root -----------------
# @app.get("/")
# def read_root():
#     return {
#         "message": "Welcome to COE Resource Themes API",
#         "version": "1.0.0",
#         "documentation": "/docs",
#         "metrics": "/metrics",
#     }

# # ----------------- Blog Endpoints -----------------
# @app.post("/blogs/", tags=["Blogs"])
# def create_blog(blog: BlogCreate):
#     result = BlogsDB.create_blog(blog.title, blog.content, blog.author_name, blog.domain_name)
#     if not result:
#         raise HTTPException(status_code=400, detail="Failed to create blog")
#     return result

# @app.get("/blogs/", tags=["Blogs"])
# def get_blogs(domain_name: Optional[str] = None, search: Optional[str] = None):
#     return BlogsDB.get_blogs(domain_name=domain_name, search=search)

# @app.get("/blogs/{blog_id}", tags=["Blogs"])
# def get_blog(blog_id: int):
#     blog = BlogsDB.get_blog_by_id(blog_id)
#     if not blog:
#         raise HTTPException(status_code=404, detail="Blog not found")
#     return blog

# @app.put("/blogs/{blog_id}", tags=["Blogs"])
# def update_blog(blog_id: int, blog: BlogUpdate):
#     current_blog = BlogsDB.get_blog_by_id(blog_id)
#     if not current_blog:
#         raise HTTPException(status_code=404, detail="Blog not found")
#     updated_blog = BlogsDB.update_blog(
#         blog_id,
#         blog.title or current_blog["title"],
#         blog.content or current_blog["content"],
#         blog.author_name or current_blog["author_name"],
#         blog.domain_name or current_blog["domain_name"]
#     )
#     if not updated_blog:
#         raise HTTPException(status_code=400, detail="Cannot update blog")
#     return updated_blog

# @app.delete("/blogs/{blog_id}", tags=["Blogs"])
# def delete_blog(blog_id: int):
#     success = BlogsDB.delete_blog(blog_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Blog not found")
#     return {"status": "success", "detail": "Blog deleted successfully"}

# # ----------------- Domain Endpoints -----------------
# @app.get("/domains/", tags=["Domains"])
# def get_domains(): return DomainsDB.get_all_domains()

# @app.post("/domains/", tags=["Domains"])
# def create_domain(domain: DomainCreate):
#     result = DomainsDB.create_domain(domain.name, domain.description)
#     if not result:
#         raise HTTPException(status_code=400, detail="Failed to create domain")
#     return result

# @app.get("/domains/{domain_id}", tags=["Domains"])
# def get_domain(domain_id: int):
#     domain = DomainsDB.get_domain_by_id(domain_id)
#     if not domain:
#         raise HTTPException(status_code=404, detail="Domain not found")
#     return domain

# # ----------------- Event Endpoints -----------------
# @app.post("/events/", tags=["Events"])
# def create_event(event: EventCreate):
#     result = EventsDB.create_event(
#         event.title, event.description, str(event.event_date), event.event_type, event.domain_id
#     )
#     if not result:
#         raise HTTPException(status_code=400, detail="Failed to create event")
#     return result

# @app.get("/events/", tags=["Events"])
# def get_events(domain_name: Optional[str] = None):
#     return EventsDB.get_events(domain_name=domain_name)

# @app.get("/events/{event_id}", tags=["Events"])
# def get_event(event_id: int):
#     event = EventsDB.get_event_by_id(event_id)
#     if not event:
#         raise HTTPException(status_code=404, detail="Event not found")
#     return event

# # ----------------- Event Registrations -----------------
# @app.post("/event-registrations/", tags=["Event Registrations"])
# def create_registration(registration: EventRegistrationCreate):
#     result = EventRegistrationsDB.create_registration(
#         registration.event_id, registration.user_name, registration.email
#     )
#     if not result:
#         raise HTTPException(status_code=400, detail="Failed to create registration")
#     return result

# @app.get("/event-registrations/event/{event_id}", tags=["Event Registrations"])
# def get_event_registrations(event_id: int):
#     return EventRegistrationsDB.get_registrations_by_event(event_id)

# # ----------------- Admin Endpoints -----------------
# @app.get("/admin/dashboard", tags=["Admin"])
# def get_dashboard_stats(): return AdminDB.get_dashboard_stats()

# @app.get("/admin/health", tags=["Admin"])
# def health_check():
#     try:
#         AdminDB.get_dashboard_stats()
#         db_status = "healthy"
#     except Exception as e:
#         logger.error(str(e))
#         db_status = "unhealthy"
#     return {
#         "status": "healthy" if db_status == "healthy" else "degraded",
#         "database": db_status,
#         "timestamp": datetime.now().isoformat(),
#     }

# # ----------------- Run Server -----------------
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
