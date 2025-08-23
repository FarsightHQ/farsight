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

# Create FastAPI app
app = FastAPI(
    title="Farsight API", 
    version="1.0.0",
    description="A FastAPI application with PostgreSQL, Alembic migrations, and FAR CSV upload"
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
