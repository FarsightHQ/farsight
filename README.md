# Farsight - Docker Compose Setup

A complete development environment with PostgreSQL database, Python FastAPI backend, frontend interface, database viewers, and low-code UI platform.

## Tech Stack

- **Database**: PostgreSQL (latest)
- **Backend**: Python 3.11 + FastAPI + Alembic migrations
- **Frontend**: Nginx-based web interface
- **Database Viewer**: pgAdmin 4 (web-based PostgreSQL admin)
- **API Documentation**: Swagger UI
- **Low-Code Platform**: Appsmith CE for building internal tools
- **Caching**: Redis (for Appsmith)

## Quick Start

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Check service status:**
   ```bash
   docker-compose ps
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f backend
   ```

## Service URLs

- **Backend API**: http://localhost:8000
  - API Documentation: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health

- **Frontend Interface**: http://localhost:3000
  - Web-based user interface for Farsight

- **pgAdmin**: http://localhost:5050
  - Email: admin@farsight.com
  - Password: admin123

- **Swagger UI**: http://localhost:8080
  - Interactive API documentation and testing

- **Appsmith**: http://localhost:8082
  - Low-code platform for building internal tools
  - First-time setup required on initial access

## Database Connection

- **Host**: localhost (from host machine) or postgres (from containers)
- **Port**: 5432
- **Database**: farsight
- **Username**: farsight_user
- **Password**: farsight_password

## Appsmith Configuration

When connecting Appsmith to the Farsight API, use these settings:

- **Base URL**: `http://backend:8000` (Docker service name)
- **Available API Endpoints**:
  - FAR (Firewall Access Rules): `http://backend:8000/api/v1/far/`
  - IP Rules: `http://backend:8000/api/v1/ip/`
  - Asset Registry: `http://backend:8000/api/v1/assets/`

**Note**: Use `backend:8000` instead of `localhost:8000` when configuring REST API datasources in Appsmith, as it runs inside Docker.

## Development

### Backend Development
The backend code is mounted as a volume, so changes are reflected immediately with hot reload.

### Database Migrations
```bash
# Create a new migration after modifying models
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply pending migrations
docker-compose exec backend alembic upgrade head

# Check migration status
docker-compose exec backend alembic current
```

**Note:** Migrations run automatically when the backend starts.

### Adding Dependencies
Add new packages to `backend/requirements.txt` and rebuild:
```bash
docker-compose build backend
docker-compose up -d backend
```

### Database Migrations
```bash
docker-compose exec backend alembic init alembic
docker-compose exec backend alembic revision --autogenerate -m "Initial migration"
docker-compose exec backend alembic upgrade head
```

## Useful Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (careful: deletes data!)
docker-compose down -v

# Rebuild specific service
docker-compose build backend

# Access backend shell
docker-compose exec backend bash

# Access PostgreSQL shell
docker-compose exec postgres psql -U farsight_user -d farsight

# Access Appsmith container
docker-compose exec appsmith bash

# View service logs
docker-compose logs -f backend
docker-compose logs -f appsmith
docker-compose logs -f frontend

# Database migrations
docker-compose exec backend alembic current
docker-compose exec backend alembic history

# Check service status
docker-compose ps

# Restart specific service
docker-compose restart backend
docker-compose restart appsmith
```

## Project Structure

```
farsight/
├── docker-compose.yml      # Docker services configuration
├── .env                    # Environment variables (if used)
├── backend/
│   ├── Dockerfile         # Backend container config
│   ├── requirements.txt   # Python dependencies
│   ├── app/
│   │   ├── main.py       # FastAPI application
│   │   ├── api/          # API routes
│   │   ├── core/         # Core configuration
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── utils/        # Utility functions
│   ├── migrate.py        # Migration helper script
│   ├── alembic.ini       # Alembic configuration
│   └── alembic/          # Migration files
├── frontend/
│   ├── Dockerfile        # Frontend container config
│   ├── index.html        # Main web interface
│   ├── nginx.conf        # Nginx configuration
│   └── js/               # JavaScript files
├── scripts/
│   └── create-multiple-databases.sh  # Database initialization
├── docs/                 # Documentation files
├── tests/                # Test files and sample data
├── API_TESTING_GUIDE.md  # API testing documentation
├── MIGRATION_GUIDE.md    # Database migration guide
└── README.md             # This file
```

## Architecture

The Farsight system consists of:

1. **PostgreSQL Database** - Stores FAR rules, IP rules, and asset registry data
2. **FastAPI Backend** - REST API with endpoints for managing firewall rules and assets
3. **Frontend Interface** - Web-based UI for interacting with the system
4. **pgAdmin** - Database administration tool
5. **Swagger UI** - Interactive API documentation
6. **Appsmith** - Low-code platform for building custom dashboards and tools
7. **Redis** - Caching layer for Appsmith

All services run in Docker containers and communicate over a dedicated network (`farsight_network`).