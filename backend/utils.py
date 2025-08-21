"""
Utility functions for file operations and validation
"""
import os
import hashlib
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException
import aiofiles


def safe_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing unsafe characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace spaces and unsafe characters with underscores
    filename = re.sub(r'[^\w\.-]', '_', filename)
    
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores and dots
    filename = filename.strip('_.')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def get_upload_path(filename: str, upload_dir: str = "./uploads") -> Tuple[str, str]:
    """
    Generate upload path with date-based directory structure
    
    Args:
        filename: Original filename
        upload_dir: Base upload directory
        
    Returns:
        Tuple of (full_path, relative_path)
    """
    now = datetime.now()
    date_path = f"{now.year:04d}/{now.month:02d}/{now.day:02d}"
    
    safe_name = safe_filename(filename)
    unique_filename = f"{uuid.uuid4()}__{safe_name}"
    
    relative_path = f"{date_path}/{unique_filename}"
    full_path = os.path.join(upload_dir, relative_path)
    
    return full_path, relative_path


async def save_upload_file(
    upload_file: UploadFile, 
    destination_path: str,
    max_size_bytes: int = 50 * 1024 * 1024  # 50MB default
) -> Tuple[str, int]:
    """
    Save uploaded file to disk and compute SHA-256 hash
    
    Args:
        upload_file: FastAPI UploadFile object
        destination_path: Where to save the file
        max_size_bytes: Maximum allowed file size
        
    Returns:
        Tuple of (sha256_hash, file_size_bytes)
        
    Raises:
        HTTPException: If file is too large or other errors
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    
    sha256_hash = hashlib.sha256()
    total_size = 0
    
    try:
        async with aiofiles.open(destination_path, 'wb') as f:
            while chunk := await upload_file.read(8192):  # Read in 8KB chunks
                total_size += len(chunk)
                
                # Check file size limit
                if total_size > max_size_bytes:
                    # Clean up partial file
                    await f.close()
                    os.unlink(destination_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {max_size_bytes / (1024*1024):.1f}MB"
                    )
                
                sha256_hash.update(chunk)
                await f.write(chunk)
    
    except Exception as e:
        # Clean up on any error
        if os.path.exists(destination_path):
            os.unlink(destination_path)
        raise e
    
    return sha256_hash.hexdigest(), total_size


def validate_csv_file(file: UploadFile) -> None:
    """
    Validate that uploaded file is a CSV
    
    Args:
        file: FastAPI UploadFile object
        
    Raises:
        HTTPException: If file is not a valid CSV
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Check file extension
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=400, 
            detail="Only CSV files are allowed"
        )
    
    # Check content type (optional, browsers might not set this correctly)
    valid_content_types = [
        "text/csv",
        "application/csv", 
        "text/plain",
        "application/octet-stream"  # Some browsers use this for CSV
    ]
    
    if file.content_type and file.content_type not in valid_content_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {file.content_type}. Expected CSV file."
        )


def derive_title_from_filename(filename: str) -> str:
    """
    Derive title from filename by removing extension
    
    Args:
        filename: Original filename
        
    Returns:
        Title derived from filename
    """
    if not filename:
        return "Untitled"
    
    # Remove extension
    name_without_ext = os.path.splitext(filename)[0]
    
    # Replace underscores and hyphens with spaces
    title = re.sub(r'[_-]', ' ', name_without_ext)
    
    # Clean up multiple spaces
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title or "Untitled"
