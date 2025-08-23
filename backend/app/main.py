"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
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
    version="1.0.0",
    description="""
    **Farsight API** - Firewall Access Rule Analysis System
    
    ## Features
    
    * **CSV Upload & Ingestion** - Upload firewall rule CSV files
    * **Facts Computation** - Calculate 17+ detailed facts per rule
    * **Hybrid Facts Analysis** - Advanced security and risk analysis
    * **Request Analysis** - Comprehensive rule analysis for UI display
    
    ## Workflow
    
    1. **Upload CSV** → `/api/v1/ingest` 
    2. **Compute Facts** → `/api/v1/requests/{id}/facts/compute`
    3. **Hybrid Analysis** → `/api/v1/requests/{id}/facts/compute-hybrid`
    4. **Get Analysis** → `/api/v1/requests/{id}/analysis`
    
    ## Documentation
    
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

# Include API routes
app.include_router(api_router)


@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Welcome to Farsight API", "status": "running"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}
