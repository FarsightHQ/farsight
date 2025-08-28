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
    
    # HTTP exceptions  
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers configured successfully")
