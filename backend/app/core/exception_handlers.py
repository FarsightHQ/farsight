"""
FastAPI exception handlers for standardized error responses
Automatically formats all exceptions into consistent API responses
"""
import logging
from typing import Union

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..utils.error_handlers import (
    APIError, format_api_error, format_http_exception,
    format_validation_errors, format_generic_error,
    generate_request_id, ResponseFormatter
)
from ..utils.csv_errors import (
    CSVProcessingError, CSVValidationError, CSVRowError,
    CSVColumnError, CSVEncodingError, CSVFileError,
    DatabaseConnectionError, FileSystemError, TimeoutError,
    InsufficientStorageError
)
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors"""
    request_id = generate_request_id()
    logger.error(f"API Error [{request_id}]: {exc.code} - {exc.message}", 
                extra={"request_id": request_id, "error_details": exc.details})
    
    error_response = format_api_error(exc, request, request_id)
    return ResponseFormatter.error(error_response)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    request_id = generate_request_id()
    logger.warning(f"HTTP Exception [{request_id}]: {exc.status_code} - {exc.detail}",
                  extra={"request_id": request_id, "status_code": exc.status_code})
    
    error_response = format_http_exception(exc, request, request_id)
    return ResponseFormatter.error(error_response)


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette HTTP exceptions"""
    # Convert Starlette exception to FastAPI format
    fastapi_exc = HTTPException(status_code=exc.status_code, detail=str(exc.detail))
    return await http_exception_handler(request, fastapi_exc)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors"""
    request_id = generate_request_id()
    logger.warning(f"Validation Error [{request_id}]: {len(exc.errors())} validation issues",
                  extra={"request_id": request_id, "validation_errors": exc.errors()})
    
    # Create error response manually from RequestValidationError
    from ..schemas.responses import ValidationErrorResponse, ErrorDetailModel, StatusEnum
    
    errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"]) if error["loc"] else None
        errors.append(ErrorDetailModel(
            code="VALIDATION_ERROR",
            message=error["msg"],
            field=field_path,
            context={"type": error["type"], "input": error.get("input")}
        ))
    
    error_response = ValidationErrorResponse(
        status=StatusEnum.ERROR,
        message="Validation failed",
        errors=errors,
        request_id=request_id
    )
    
    return ResponseFormatter.error(error_response)


async def csv_error_handler(request: Request, exc: CSVProcessingError) -> JSONResponse:
    """Handle CSV processing errors"""
    request_id = generate_request_id()
    logger.error(
        f"CSV Error [{request_id}]: {exc.code} - {exc.message}",
        extra={"request_id": request_id, "error_details": exc.details}
    )
    
    error_response = format_api_error(exc, request, request_id)
    return ResponseFormatter.error(error_response)


async def database_error_handler(request: Request, exc: DatabaseConnectionError) -> JSONResponse:
    """Handle database connection errors"""
    request_id = generate_request_id()
    logger.error(
        f"Database Error [{request_id}]: {exc.code} - {exc.message}",
        extra={"request_id": request_id, "error_details": exc.details}
    )
    
    error_response = format_api_error(exc, request, request_id)
    return ResponseFormatter.error(error_response)


async def filesystem_error_handler(request: Request, exc: FileSystemError) -> JSONResponse:
    """Handle filesystem errors"""
    request_id = generate_request_id()
    logger.error(
        f"Filesystem Error [{request_id}]: {exc.code} - {exc.message}",
        extra={"request_id": request_id, "error_details": exc.details}
    )
    
    error_response = format_api_error(exc, request, request_id)
    return ResponseFormatter.error(error_response)


async def timeout_error_handler(request: Request, exc: TimeoutError) -> JSONResponse:
    """Handle timeout errors"""
    request_id = generate_request_id()
    logger.warning(
        f"Timeout Error [{request_id}]: {exc.code} - {exc.message}",
        extra={"request_id": request_id, "error_details": exc.details}
    )
    
    error_response = format_api_error(exc, request, request_id)
    return ResponseFormatter.error(error_response)


async def storage_error_handler(request: Request, exc: InsufficientStorageError) -> JSONResponse:
    """Handle insufficient storage errors"""
    request_id = generate_request_id()
    logger.error(
        f"Storage Error [{request_id}]: {exc.code} - {exc.message}",
        extra={"request_id": request_id, "error_details": exc.details}
    )
    
    error_response = format_api_error(exc, request, request_id)
    return ResponseFormatter.error(error_response)


async def sqlalchemy_operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    """Handle SQLAlchemy operational errors (database connection issues)"""
    request_id = generate_request_id()
    logger.error(
        f"Database Operational Error [{request_id}]: {str(exc)}",
        extra={"request_id": request_id}, exc_info=True
    )
    
    # Convert to DatabaseConnectionError
    db_error = DatabaseConnectionError(
        message="Database connection failed",
        details={"error": str(exc)}
    )
    return await database_error_handler(request, db_error)


async def os_error_handler(request: Request, exc: OSError) -> JSONResponse:
    """Handle OS errors (filesystem, permissions, etc.)"""
    request_id = generate_request_id()
    logger.error(
        f"OS Error [{request_id}]: {str(exc)}",
        extra={"request_id": request_id}, exc_info=True
    )
    
    # Convert to FileSystemError
    fs_error = FileSystemError(
        message=f"File system error: {str(exc)}",
        details={"error": str(exc), "errno": getattr(exc, 'errno', None)}
    )
    return await filesystem_error_handler(request, fs_error)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    request_id = generate_request_id()
    logger.error(f"Unexpected Error [{request_id}]: {type(exc).__name__} - {str(exc)}",
                extra={"request_id": request_id}, exc_info=True)
    
    # In production, don't expose internal error details
    error_response = format_generic_error(
        exc, 
        "An unexpected error occurred. Please contact support.",
        request, 
        request_id
    )
    return ResponseFormatter.error(error_response)


def setup_exception_handlers(app):
    """Setup all exception handlers for the FastAPI app"""
    
    # Custom API errors
    app.add_exception_handler(APIError, api_error_handler)
    
    # CSV processing errors (register before generic APIError to catch specific types)
    app.add_exception_handler(CSVProcessingError, csv_error_handler)
    app.add_exception_handler(CSVValidationError, csv_error_handler)
    app.add_exception_handler(CSVRowError, csv_error_handler)
    app.add_exception_handler(CSVColumnError, csv_error_handler)
    app.add_exception_handler(CSVEncodingError, csv_error_handler)
    app.add_exception_handler(CSVFileError, csv_error_handler)
    
    # Database and filesystem errors
    app.add_exception_handler(DatabaseConnectionError, database_error_handler)
    app.add_exception_handler(FileSystemError, filesystem_error_handler)
    app.add_exception_handler(TimeoutError, timeout_error_handler)
    app.add_exception_handler(InsufficientStorageError, storage_error_handler)
    
    # SQLAlchemy and OS errors (catch before generic Exception)
    app.add_exception_handler(OperationalError, sqlalchemy_operational_error_handler)
    app.add_exception_handler(OSError, os_error_handler)
    app.add_exception_handler(PermissionError, os_error_handler)
    
    # HTTP exceptions  
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers configured successfully")
