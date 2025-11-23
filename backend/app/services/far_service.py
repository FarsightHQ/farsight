"""
Service layer for FAR request processing
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from fastapi import UploadFile, HTTPException

from app.models import FarRequest
from app.schemas import FarRequestCreate, FarRequestResponse
from app.utils import (
    validate_csv_file_enhanced, 
    get_upload_path, 
    save_upload_file, 
    derive_title_from_filename
)
from app.utils.csv_errors import (
    DatabaseConnectionError, FileSystemError, InsufficientStorageError
)
from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)


class FarIngestionService:
    """Service for handling FAR request ingestion"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_upload(
        self,
        file: UploadFile,
        title: Optional[str] = None,
        external_id: Optional[str] = None,
        created_by: str = "system"
    ) -> FarRequestResponse:
        """
        Process CSV file upload for FAR request
        
        Args:
            file: Uploaded CSV file
            title: Optional title (derived from filename if not provided)
            external_id: Optional external reference ID
            created_by: User/system creating the request
            
        Returns:
            FarRequestResponse with created request details
            
        Raises:
            HTTPException: For validation errors or processing failures
        """
        logger.info(f"Processing FAR upload: {file.filename}")
        
        # Enhanced file validation with content checking
        try:
            validate_csv_file_enhanced(file)
        except HTTPException:
            # Re-raise validation errors as-is
            raise
        
        # Generate title if not provided
        if not title:
            title = derive_title_from_filename(file.filename or "unknown")
        
        # Get storage path
        full_path, relative_path = get_upload_path(
            file.filename or "unknown.csv", 
            settings.UPLOAD_DIR
        )
        
        far_request = None
        try:
            # Save file and compute hash/size
            try:
                sha256_hash, file_size = await save_upload_file(
                    file, 
                    full_path, 
                    settings.max_upload_bytes
                )
            except (InsufficientStorageError, FileSystemError):
                # Re-raise storage/filesystem errors as-is
                raise
            except Exception as e:
                logger.error(f"Error saving file: {str(e)}", exc_info=True)
                raise FileSystemError(
                    message=f"Failed to save uploaded file: {str(e)}",
                    details={"filename": file.filename, "path": relative_path}
                )
            
            logger.info(
                f"File saved successfully: {relative_path}, "
                f"SHA256: {sha256_hash}, Size: {file_size} bytes"
            )
            
            # Create database record
            try:
                far_request_data = FarRequestCreate(
                    title=title,
                    external_id=external_id,
                    source_filename=file.filename or "unknown.csv",
                    source_sha256=sha256_hash,
                    source_size_bytes=file_size,
                    storage_path=relative_path,
                    created_by=created_by
                )
                
                far_request = FarRequest(**far_request_data.model_dump())
                self.db.add(far_request)
                self.db.commit()
                self.db.refresh(far_request)
            except OperationalError as e:
                # Database connection error
                self.db.rollback()
                logger.error(f"Database connection error: {str(e)}", exc_info=True)
                raise DatabaseConnectionError(
                    message="Database connection failed while creating request",
                    details={"error": str(e)}
                )
            except Exception as e:
                # Other database errors
                self.db.rollback()
                logger.error(f"Database error: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create database record: {str(e)}"
                )
            
            logger.info(
                f"FAR request created successfully: ID={far_request.id}, "
                f"File={file.filename}, SHA256={sha256_hash}"
            )
            
            # Build response directly from the database object
            return FarRequestResponse.from_orm(far_request)
            
        except (HTTPException, DatabaseConnectionError, FileSystemError, InsufficientStorageError):
            # Re-raise known exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing FAR upload: {str(e)}", exc_info=True)
            # Clean up database if created
            if far_request:
                try:
                    self.db.rollback()
                except:
                    pass
            # Clean up file if saved
            try:
                import os
                if os.path.exists(full_path):
                    os.unlink(full_path)
            except:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process upload: {str(e)}"
            )
    
    def get_far_request(self, request_id: int) -> Optional[FarRequest]:
        """
        Get FAR request by ID
        
        Args:
            request_id: The request ID to lookup
            
        Returns:
            FarRequest if found, None otherwise
        """
        return self.db.query(FarRequest).filter(FarRequest.id == request_id).first()
    
    def list_far_requests(self, limit: int = 100, offset: int = 0) -> list[FarRequest]:
        """
        List FAR requests with pagination
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of FarRequest objects
        """
        return (
            self.db.query(FarRequest)
            .order_by(FarRequest.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
