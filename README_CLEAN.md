# COE API - Clean Architecture

This is a clean, simplified version of the COE API that separates database operations from the main API logic using psycopg2 directly without ORM.

## Files Structure

- `main.py` - FastAPI application with all API endpoints
- `database.py` - Database connection management and query operations using psycopg2
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

## Setup Instructions

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Environment setup:**

   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Database setup:**
   Make sure PostgreSQL is running and create the required database and tables.

4. **Run the application:**

   ```bash
   python main.py
   ```

   Or using uvicorn directly:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### Blogs

- `POST /blogs/` - Create a new blog
- `GET /blogs/` - Get all blogs (with optional filtering)
- `GET /blogs/{blog_id}` - Get specific blog
- `PUT /blogs/{blog_id}` - Update blog
- `DELETE /blogs/{blog_id}` - Delete blog

### Domains

- `GET /domains/` - Get all domains
- `POST /domains/` - Create new domain
- `GET /domains/{domain_id}` - Get specific domain

### Events

- `POST /events/` - Create new event
- `GET /events/` - Get all events (with optional filtering)
- `GET /events/{event_id}` - Get specific event

### Event Registrations

- `POST /event-registrations/` - Register for event
- `GET /event-registrations/event/{event_id}` - Get registrations for event

### Admin

- `GET /admin/dashboard` - Get dashboard statistics
- `GET /admin/health` - Health check

## Database Operations

The `database.py` file contains:

1. **DatabaseManager class** - Handles connection pooling and basic query operations
2. **Specialized DB classes:**
   - `BlogsDB` - Blog-related database operations
   - `DomainsDB` - Domain-related operations
   - `EventsDB` - Event management
   - `EventRegistrationsDB` - Registration handling
   - `AdminDB` - Administrative functions

## Key Features

- **Connection Pooling:** Efficient database connection management
- **Error Handling:** Proper exception handling with rollback
- **Context Management:** Safe database operations with automatic cleanup
- **Modular Design:** Separated concerns between API and database layers
- **Type Hints:** Full type annotations for better code clarity
- **No ORM:** Direct SQL queries using psycopg2 for better performance

## Development

Access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
