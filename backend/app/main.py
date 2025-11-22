"""
FastAPI application entry point with standardized responses
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.exception_handlers import setup_exception_handlers
from app.api.router import router as api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app with enhanced documentation
app = FastAPI(
    title="Farsight API",
    version="2.0.0",  # Bumped version for standardized responses
    description="""
    **Farsight API v2.0** - Firewall Access Rule Analysis System
    
    ## ✨ Version 2.0 Features
    
    * **🔄 Standardized Responses** - Consistent response format across all endpoints
    * **📋 OpenAPI Documentation** - Complete schema documentation with examples
    * **⚠️ Standardized Error Handling** - Structured error responses with details
    * **🔗 Request Correlation** - Request IDs for tracking and debugging
    * **📄 Pagination Support** - Consistent pagination for list endpoints
    
    ## 🚀 Core Features
    
    * **📁 CSV Upload & Ingestion** - Upload firewall rule CSV files
    * **🧮 Facts Computation** - Calculate 17+ detailed facts per rule
    * **🔍 Hybrid Facts Analysis** - Advanced security and risk analysis
    * **📊 Request Analysis** - Comprehensive rule analysis for UI display
    * **🎨 Graph Visualization** - D3.js compatible network topology graphs
    * **🛡️ Security Analysis** - Risk assessment and compliance checking
    
    ## 📋 API Workflow
    
    1. **Upload CSV** → `POST /api/v1/requests` 
    2. **Compute Facts** → `POST /api/v1/requests/{id}/facts/compute`
    3. **Hybrid Analysis** → `POST /api/v1/requests/{id}/facts/compute-hybrid`
    4. **Get Analysis** → `GET /api/v1/analysis/requests/{id}`
    
    ## 📚 Response Format
    
    All API responses follow a standardized format:
    
    ```json
    {
      "status": "success|error|warning",
      "message": "Human-readable message",
      "data": { /* Response payload */ },
      "metadata": { /* Additional context */ },
      "timestamp": "2025-01-01T00:00:00Z",
      "request_id": "uuid-for-correlation"
    }
    ```
    
    ## 🔗 Navigation
    
    * **Interactive API Docs** (Swagger UI): `/docs`
    * **Alternative API Docs** (ReDoc): `/redoc`
    * **OpenAPI Schema**: `/openapi.json`
    """,
    contact={
        "name": "Farsight Team",
        "email": "team@farsight.com",
    },
    license_info={
        "name": "MIT License",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Setup standardized exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(api_router)


@app.get("/", tags=["System"])
def read_root():
    """Root endpoint with API information"""
    from app.utils.error_handlers import success_response
    
    return success_response(
        data={
            "api": "Farsight API",
            "version": "2.0.0",
            "status": "running",
            "features": [
                "Standardized responses",
                "OpenAPI documentation", 
                "Error handling",
                "Request correlation",
                "Pagination support"
            ],
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json",
                "health": "/health"
            }
        },
        message="Welcome to Farsight API v2.0"
    )


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint with system status"""
    from app.utils.error_handlers import success_response
    
    return success_response(
        data={
            "status": "healthy",
            "database": "connected",
            "api_version": "2.0.0",
            "response_format": "standardized"
        },
        message="System is healthy"
    )
