from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime

# Import our database components
from database import get_db
from models import Item, FarRequest
from schemas import FarRequestResponse
from services import FarIngestionService
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Farsight API", 
    version="1.0.0",
    description="A FastAPI application with PostgreSQL, Alembic migrations, and FAR CSV upload"
)

# Dependency to get DB session (removed since it's now in database.py)

@app.get("/")
def read_root():
    return {"message": "Welcome to Farsight API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}


# FAR Ingestion Endpoints

@app.post("/ingest/far", response_model=FarRequestResponse)
async def ingest_far_request(
    file: UploadFile = File(..., description="CSV file to upload"),
    title: Optional[str] = Form(None, description="Title for the FAR request"),
    external_id: Optional[str] = Form(None, description="External reference ID"),
    created_by: str = Form("system", description="User creating the request"),
    db: Session = Depends(get_db)
) -> FarRequestResponse:
    """
    Upload CSV file for FAR (File Analysis Request) processing
    
    - **file**: CSV file (required, max 50MB)
    - **title**: Optional title (derived from filename if not provided)
    - **external_id**: Optional external reference ID
    - **created_by**: User/system creating the request (defaults to "system")
    
    Returns details of the created FAR request including file information.
    """
    logger.info(f"FAR ingestion request: file={file.filename}, title={title}, external_id={external_id}")
    
    service = FarIngestionService(db)
    return await service.process_upload(
        file=file,
        title=title,
        external_id=external_id,
        created_by=created_by
    )

@app.get("/ingest/far/{request_id}")
def get_far_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """Get FAR request by ID"""
    service = FarIngestionService(db)
    far_request = service.get_far_request(request_id)
    
    if not far_request:
        raise HTTPException(status_code=404, detail="FAR request not found")
    
    return {
        "request_id": far_request.id,
        "status": far_request.status,
        "title": far_request.title,
        "external_id": far_request.external_id,
        "source_filename": far_request.source_filename,
        "source_sha256": far_request.source_sha256,
        "source_size_bytes": far_request.source_size_bytes,
        "storage_path": far_request.storage_path,
        "created_by": far_request.created_by,
        "created_at": far_request.created_at
    }

@app.get("/ingest/far")
def list_far_requests(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List FAR requests with pagination"""
    service = FarIngestionService(db)
    requests = service.list_far_requests(limit=limit, offset=offset)
    
    return {
        "requests": [
            {
                "request_id": req.id,
                "status": req.status,
                "title": req.title,
                "external_id": req.external_id,
                "source_filename": req.source_filename,
                "created_by": req.created_by,
                "created_at": req.created_at
            }
            for req in requests
        ],
        "limit": limit,
        "offset": offset
    }


# Legacy Item Endpoints (keeping for backward compatibility)

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items

@app.post("/items")
def create_item(name: str, description: str | None = None, db: Session = Depends(get_db)):
    db_item = Item(name=name, description=description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
