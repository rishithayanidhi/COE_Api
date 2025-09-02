# Docker Setup for COE API

This guide will help you set up and run the COE API using Docker containers.

## 📋 Prerequisites

- Docker Desktop installed
- Docker Compose available
- At least 2GB of free RAM
- Ports 8000, 5432, and 8080 available

## 🚀 Quick Start

### Option 1: Using Helper Scripts

**For Windows PowerShell:**

```powershell
# Build and start services
.\docker-commands.ps1 build
.\docker-commands.ps1 up

# View logs
.\docker-commands.ps1 logs

# Stop services
.\docker-commands.ps1 down
```

**For Windows Command Prompt:**

```cmd
# Build and start services
docker-commands.bat build
docker-commands.bat up

# View logs
docker-commands.bat logs

# Stop services
docker-commands.bat down
```

### Option 2: Direct Docker Commands

```bash
# Build the application
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 📊 Services

After running `docker-compose up -d`, you'll have:

| Service        | URL                         | Description                   |
| -------------- | --------------------------- | ----------------------------- |
| **COE API**    | http://localhost:8000       | Main FastAPI application      |
| **API Docs**   | http://localhost:8000/docs  | Interactive API documentation |
| **ReDoc**      | http://localhost:8000/redoc | Alternative API documentation |
| **PostgreSQL** | localhost:5432              | Database server               |

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │
│   (Port 8000)   │────│   (Port 5432)   │
│                 │    │                 │
│ • main.py       │    │ • blogpost_db   │
│ • database.py   │    │ • Auto-init     │
└─────────────────┘    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables

The application uses these environment variables (defined in docker-compose.yml):

```yaml
environment:
  - DB_HOST=db
  - DB_PORT=5432
  - DB_NAME=blogpost_db
  - DB_USER=postgres
  - DB_PASSWORD=rishi1023
  - APP_HOST=0.0.0.0
  - APP_PORT=8000
  - DEBUG=True
  - LOG_LEVEL=INFO
```

### Database Initialization

The database is automatically initialized with the schema from `app/db/init_db.sql` when the container starts for the first time.

## 🛠️ Development

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f db
```

### Rebuilding After Changes

```bash
# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Accessing Database

**Via Command Line:**

```bash
# Connect to database container
docker-compose exec db psql -U postgres -d blogpost_db

# Run SQL commands
\dt  # List tables
\q   # Quit
```

## 🧪 Testing

### Test the API

```bash
# Health check
curl http://localhost:8000/admin/health

# Get domains
curl http://localhost:8000/domains/

# Create a domain
curl -X POST http://localhost:8000/domains/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Technology", "description": "Tech content"}'

# Create a blog
curl -X POST http://localhost:8000/blogs/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Blog",
    "content": "This is a test blog post",
    "author_name": "Test Author",
    "domain_name": "Technology"
  }'
```

### Using the Test Script

If you have Python and requests installed locally:

```bash
python test_api.py
```

## 🔄 Data Persistence

- **Database data** is persisted in Docker volume `postgres_data`
- **Application logs** are mounted to `./logs` directory

## 🧹 Cleanup

### Stop Services

```bash
docker-compose down
```

### Remove Everything (including data)

```bash
docker-compose down -v --rmi all --remove-orphans
docker system prune -f
```

## 🚨 Troubleshooting

### Common Issues

**Port Already in Use:**

```bash
# Check what's using the port
netstat -an | findstr :8000
netstat -an | findstr :5432

# Stop the process or change ports in docker-compose.yml
```

**Database Connection Failed:**

- Wait for database to fully start (check logs)
- Ensure environment variables are correct
- Try restarting services

**Permission Denied:**

```bash
# On Linux/Mac, you may need to fix permissions
sudo chown -R $USER:$USER logs/
```

### Checking Service Health

```bash
# Check service status
docker-compose ps

# Check specific service health
docker-compose exec backend curl http://localhost:8000/admin/health

# Check database connection
docker-compose exec db pg_isready -U postgres
```

## 📝 API Documentation

Once running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide interactive documentation where you can test all endpoints directly from your browser.

## 🔐 Security Notes

**For Production:**

1. Change default passwords in docker-compose.yml
2. Use secrets management
3. Set DEBUG=False
4. Use proper SSL certificates
5. Implement authentication/authorization
6. Use environment-specific configurations
