"""
Custom exceptions for CSV processing with detailed error context
"""
from typing import Optional, Dict, Any, List
from app.utils.error_handlers import APIError


class CSVProcessingError(APIError):
    """Base class for CSV processing errors"""
    def __init__(
        self,
        message: str,
        code: str = "CSV_PROCESSING_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, status_code, details)


class CSVValidationError(CSVProcessingError):
    """CSV file structure validation errors"""
    def __init__(
        self,
        message: str,
        row_number: Optional[int] = None,
        column_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = {
            "row_number": row_number,
            "column_name": column_name,
            **(details or {})
        }
        super().__init__(
            message=message,
            code="CSV_VALIDATION_ERROR",
            status_code=400,
            details=error_details
        )


class CSVRowError(CSVProcessingError):
    """Errors specific to individual CSV rows"""
    def __init__(
        self,
        message: str,
        row_number: int,
        row_data: Optional[Dict[str, str]] = None,
        field_errors: Optional[Dict[str, str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = {
            "row_number": row_number,
            "row_data": row_data,
            "field_errors": field_errors or {},
            **(details or {})
        }
        super().__init__(
            message=message,
            code="CSV_ROW_ERROR",
            status_code=422,
            details=error_details
        )


class CSVColumnError(CSVProcessingError):
    """Missing or invalid column errors"""
    def __init__(
        self,
        message: str,
        missing_columns: Optional[List[str]] = None,
        found_columns: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = {
            "missing_columns": missing_columns or [],
            "found_columns": found_columns or [],
            **(details or {})
        }
        super().__init__(
            message=message,
            code="CSV_COLUMN_ERROR",
            status_code=400,
            details=error_details
        )


class CSVEncodingError(CSVProcessingError):
    """File encoding issues"""
    def __init__(
        self,
        message: str,
        detected_encoding: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = {
            "detected_encoding": detected_encoding,
            **(details or {})
        }
        super().__init__(
            message=message,
            code="CSV_ENCODING_ERROR",
            status_code=400,
            details=error_details
        )


class CSVFileError(CSVProcessingError):
    """File-level errors (size, format, etc.)"""
    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = {
            "filename": filename,
            "file_size": file_size,
            **(details or {})
        }
        super().__init__(
            message=message,
            code="CSV_FILE_ERROR",
            status_code=400,
            details=error_details
        )


class DatabaseConnectionError(APIError):
    """Database connection errors"""
    def __init__(
        self,
        message: str = "Database connection failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="DATABASE_CONNECTION_ERROR",
            status_code=503,
            details=details or {}
        )


class FileSystemError(APIError):
    """File system errors (disk space, permissions, etc.)"""
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="FILESYSTEM_ERROR",
            status_code=500,
            details=details or {}
        )


class TimeoutError(APIError):
    """Operation timeout errors"""
    def __init__(
        self,
        message: str = "Operation timed out",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="TIMEOUT_ERROR",
            status_code=504,
            details=details or {}
        )


class InsufficientStorageError(APIError):
    """Insufficient disk space errors"""
    def __init__(
        self,
        message: str = "Insufficient disk space",
        available_space: Optional[int] = None,
        required_space: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = {
            "available_space": available_space,
            "required_space": required_space,
            **(details or {})
        }
        super().__init__(
            message=message,
            code="INSUFFICIENT_STORAGE",
            status_code=507,
            details=error_details
        )

