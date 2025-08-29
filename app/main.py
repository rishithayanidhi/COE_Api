from fastapi import FastAPI
from modules.blogs.routes import router as blogs_router
from modules.admin.routes import router as admin_router
from modules.domains.routes import router as domains_router
from modules.events.routes import router as events_router
from modules.event_registrations.routes import router as registrations_router


app = FastAPI(title="Resource Themes API")

app.include_router(blogs_router, prefix="/blogs", tags=["Blogs"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(domains_router, prefix="/domains", tags=["Domains"])
app.include_router(events_router, prefix="/events", tags=["Events"])
app.include_router(registrations_router, prefix="/event-registrations", tags=["Event Registrations"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Resource Themes API"}
