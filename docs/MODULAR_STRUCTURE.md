# Farsight API - Modular Structure Documentation

## 📁 Project Structure

```
backend/
├── app/                          # Main application package
│   ├── __init__.py              
│   ├── main.py                  # Application entry point
│   ├── api/                     # API layer
│   │   ├── __init__.py
│   │   ├── router.py            # Main API router
│   │   └── v1/                  # API version 1
│   │       ├── __init__.py
│   │       ├── router.py        # V1 router
│   │       └── endpoints/       # API endpoints
│   │           ├── __init__.py
│   │           ├── far.py       # FAR endpoints
│   │           └── items.py     # Items endpoints
│   ├── core/                    # Core configuration and database
│   │   ├── __init__.py
│   │   ├── config.py            # Application settings
│   │   └── database.py          # Database configuration
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── far_request.py       # FAR request model
│   │   └── item.py              # Item model
│   ├── schemas/                 # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── far_request.py       # FAR request schemas
│   │   └── item.py              # Item schemas
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   └── far_service.py       # FAR ingestion service
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       └── file_utils.py        # File handling utilities
├── alembic/                     # Database migrations
├── Dockerfile                   # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
└── requirements.txt             # Python dependencies
```

## 🚀 API Endpoints

All endpoints are now under the `/api/v1` prefix:

### Core Endpoints
- `GET /` - Welcome message
- `GET /health` - Health check

### FAR (File Analysis Request) Endpoints
- `POST /api/v1/ingest/far` - Upload CSV file for processing
- `GET /api/v1/ingest/far` - List all FAR requests
- `GET /api/v1/ingest/far/{request_id}` - Get specific FAR request

### Items Endpoints
- `GET /api/v1/items` - List all items
- `POST /api/v1/items` - Create new item
- `GET /api/v1/items/{item_id}` - Get specific item

## 🏗️ Architecture Benefits

### Separation of Concerns
- **API Layer**: Route handling and request/response validation
- **Service Layer**: Business logic and data processing
- **Model Layer**: Database entities and relationships
- **Core Layer**: Configuration and infrastructure

### Modular Design
- Easy to add new API versions
- Clear boundaries between components
- Simplified testing and maintenance
- Better code organization

### Scalability
- Ready for microservices split
- Version-controlled API endpoints
- Independent module development
- Clean dependency management

## 🔧 Development

### Running the Application
```bash
docker-compose up -d
```

### API Documentation
Once running, visit:
- FastAPI Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testing Endpoints
```bash
# Health check
curl http://localhost:8000/health

# List FAR requests
curl http://localhost:8000/api/v1/ingest/far

# List items
curl http://localhost:8000/api/v1/items
```

## 📝 Migration Notes

- ✅ All legacy endpoints removed
- ✅ Everything moved to `/api/v1` structure
- ✅ Modular codebase with clear separation
- ✅ Backward compatibility removed for cleaner structure
- ✅ Database migrations updated for new structure
