"""
Utility functions for file operations and validation
"""
import os
import hashlib
import uuid
import re
import csv
import io
import shutil
from datetime import datetime
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException
import aiofiles
from app.utils.csv_errors import InsufficientStorageError, CSVFileError
from app.core.config import settings


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
        InsufficientStorageError: If insufficient disk space
        FileSystemError: For filesystem errors
    """
    from app.utils.csv_errors import FileSystemError
    
    # Create directory if it doesn't exist
    try:
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    except (OSError, PermissionError) as e:
        raise FileSystemError(
            message=f"Cannot create upload directory: {str(e)}",
            details={"path": destination_path, "error": str(e)}
        )
    
    # Check disk space before writing (estimate based on max_size_bytes)
    try:
        check_disk_space(max_size_bytes, os.path.dirname(destination_path))
    except InsufficientStorageError:
        raise  # Re-raise as-is
    
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
                    if os.path.exists(destination_path):
                        os.unlink(destination_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {max_size_bytes / (1024*1024):.1f}MB"
                    )
                
                sha256_hash.update(chunk)
                await f.write(chunk)
    
    except (OSError, PermissionError) as e:
        # Clean up on filesystem error
        if os.path.exists(destination_path):
            try:
                os.unlink(destination_path)
            except:
                pass
        raise FileSystemError(
            message=f"Error saving file: {str(e)}",
            details={"path": destination_path, "error": str(e)}
        )
    except Exception as e:
        # Clean up on any other error
        if os.path.exists(destination_path):
            try:
                os.unlink(destination_path)
            except:
                pass
        raise e
    
    return sha256_hash.hexdigest(), total_size


def _validate_csv_content(file: UploadFile, sample_size: int = 8192) -> None:
    """
    Validate CSV file content structure
    
    Args:
        file: FastAPI UploadFile object
        sample_size: Number of bytes to read for validation
        
    Raises:
        HTTPException: If file content is not valid CSV
    """
    # Read sample of file content
    file.file.seek(0)
    sample = file.file.read(sample_size)
    file.file.seek(0)  # Reset file pointer
    
    if len(sample) == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )
    
    # Check if file is UTF-8 decodable (not binary)
    try:
        decoded_sample = sample.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File appears to be binary, not a valid CSV file. Please upload a text-based CSV file."
        )
    
    # Validate CSV structure using csv.Sniffer
    try:
        csv.Sniffer().sniff(decoded_sample)
    except csv.Error as e:
        raise HTTPException(
            status_code=400,
            detail=f"File does not appear to be a valid CSV: {str(e)}"
        )


def validate_csv_file(file: UploadFile) -> None:
    """
    Validate that uploaded file is a CSV (basic validation)
    
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


def validate_csv_file_enhanced(file: UploadFile, sample_size: int = None) -> None:
    """
    Enhanced CSV file validation with content checking
    
    Validates:
    - File extension
    - Content type (stricter, no octet-stream)
    - File is not empty
    - File is UTF-8 decodable (not binary)
    - File has valid CSV structure
    
    Args:
        file: FastAPI UploadFile object
        sample_size: Number of bytes to read for CSV structure validation
                    (defaults to CSV_VALIDATION_SAMPLE_SIZE from config)
        
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
    
    # Stricter content type validation (removed application/octet-stream for security)
    valid_content_types = [
        "text/csv",
        "application/csv",
        "text/plain; charset=utf-8",
        "text/plain"
    ]
    
    if file.content_type and file.content_type not in valid_content_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {file.content_type}. Expected CSV file."
        )
    
    # Use config value if sample_size not provided
    if sample_size is None:
        sample_size = getattr(settings, 'CSV_VALIDATION_SAMPLE_SIZE', 8192)
    
    # Validate file content structure
    _validate_csv_content(file, sample_size)


def check_disk_space(
    file_size: int,
    upload_dir: str,
    multiplier: float = None
) -> None:
    """
    Check if there's sufficient disk space for file upload
    
    Args:
        file_size: Size of file to upload in bytes
        upload_dir: Directory where file will be saved
        multiplier: Safety multiplier for required space (defaults to config)
        
    Raises:
        InsufficientStorageError: If insufficient disk space
    """
    if multiplier is None:
        multiplier = getattr(settings, 'MIN_DISK_SPACE_MULTIPLIER', 2.0)
    
    try:
        # Get disk usage for the upload directory
        stat = shutil.disk_usage(upload_dir)
        available_space = stat.free
        required_space = int(file_size * multiplier)
        
        if available_space < required_space:
            raise InsufficientStorageError(
                message=f"Insufficient disk space. Required: {required_space / (1024*1024):.1f}MB, Available: {available_space / (1024*1024):.1f}MB",
                available_space=available_space,
                required_space=required_space
            )
    except OSError as e:
        # If we can't check disk space, log warning but don't block upload
        # (might be permission issue or network mount)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not check disk space for {upload_dir}: {str(e)}")


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
