# Farsight - Docker Compose Setup

A complete development environment with PostgreSQL database, Python FastAPI backend, and database viewers.

## Tech Stack

- **Database**: PostgreSQL (latest)
- **Backend**: Python 3.11 + FastAPI
- **Database Viewers**: 
  - pgAdmin 4 (web-based PostgreSQL admin)
  - Adminer (lightweight alternative)

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

- **pgAdmin**: http://localhost:5050
  - Email: admin@farsight.com
  - Password: admin123

- **Adminer**: http://localhost:8080
  - Server: postgres
  - Username: farsight_user
  - Password: farsight_password
  - Database: farsight

## Database Connection

- **Host**: localhost (from host machine) or postgres (from containers)
- **Port**: 5432
- **Database**: farsight
- **Username**: farsight_user
- **Password**: farsight_password

## Development

### Backend Development
The backend code is mounted as a volume, so changes are reflected immediately with hot reload.

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

# View backend logs
docker-compose logs -f backend
```

## Project Structure

```
farsight/
├── docker-compose.yml      # Docker services configuration
├── .env                    # Environment variables
├── backend/
│   ├── Dockerfile         # Backend container config
│   ├── requirements.txt   # Python dependencies
│   └── main.py           # FastAPI application
└── README.md             # This file
```