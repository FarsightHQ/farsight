"""
Error handling utilities for standardized API responses
Provides consistent error formatting and HTTP exception handling
"""
import uuid
from typing import Dict, List, Any, Optional, Union
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from datetime import datetime

from ..schemas.responses import (
    APIErrorResponse, ValidationErrorResponse, ErrorDetailModel, 
    StatusEnum, ERROR_TYPES
)


class APIError(Exception):
    """Base API error class"""
    def __init__(
        self, 
        message: str, 
        code: str = "API_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class RuleNotFoundError(APIError):
    """Rule not found error"""
    def __init__(self, rule_id: int):
        super().__init__(
            message=f"Rule with ID {rule_id} not found",
            code="RULE_NOT_FOUND",
            status_code=404,
            details={"rule_id": rule_id}
        )


class RequestNotFoundError(APIError):
    """Request not found error"""
    def __init__(self, request_id: int):
        super().__init__(
            message=f"Request with ID {request_id} not found",
            code="REQUEST_NOT_FOUND", 
            status_code=404,
            details={"request_id": request_id}
        )


class InvalidParameterError(APIError):
    """Invalid parameter error"""
    def __init__(self, parameter: str, value: Any, reason: str):
        super().__init__(
            message=f"Invalid parameter '{parameter}': {reason}",
            code="INVALID_PARAMETER",
            status_code=400,
            details={"parameter": parameter, "value": str(value), "reason": reason}
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error"""
    def __init__(self, service: str, reason: str = "Service temporarily unavailable"):
        super().__init__(
            message=f"{service} service unavailable: {reason}",
            code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service, "reason": reason}
        )


def generate_request_id() -> str:
    """Generate unique request ID for correlation"""
    return str(uuid.uuid4())


def create_error_detail(
    code: str, 
    message: str, 
    field: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> ErrorDetailModel:
    """Create standardized error detail"""
    return ErrorDetailModel(
        code=code,
        message=message,
        field=field,
        context=context
    )


def format_validation_errors(
    validation_error: ValidationError,
    request_id: Optional[str] = None
) -> ValidationErrorResponse:
    """Format Pydantic validation errors"""
    errors = []
    
    for error in validation_error.errors():
        field_path = ".".join(str(loc) for loc in error["loc"]) if error["loc"] else None
        errors.append(create_error_detail(
            code="VALIDATION_ERROR",
            message=error["msg"],
            field=field_path,
            context={"type": error["type"], "input": error.get("input")}
        ))
    
    return ValidationErrorResponse(
        status=StatusEnum.ERROR,
        message="Validation failed",
        errors=errors,
        request_id=request_id
    )


def format_api_error(
    error: APIError,
    request: Optional[Request] = None,
    request_id: Optional[str] = None
) -> APIErrorResponse:
    """Format API error as standardized response"""
    error_detail = create_error_detail(
        code=error.code,
        message=error.message,
        context=error.details
    )
    
    return APIErrorResponse(
        status=StatusEnum.ERROR,
        message=f"{error.code}: {error.message}",
        errors=[error_detail],
        request_id=request_id,
        path=str(request.url.path) if request else None,
        method=request.method if request else None
    )


def format_http_exception(
    exc: HTTPException,
    request: Optional[Request] = None,
    request_id: Optional[str] = None
) -> APIErrorResponse:
    """Format FastAPI HTTPException as standardized response"""
    error_code = ERROR_TYPES.get(exc.status_code, "HTTP_ERROR")
    
    error_detail = create_error_detail(
        code=error_code,
        message=str(exc.detail),
        context={"status_code": exc.status_code}
    )
    
    return APIErrorResponse(
        status=StatusEnum.ERROR,
        message=f"HTTP {exc.status_code}: {exc.detail}",
        errors=[error_detail],
        request_id=request_id,
        path=str(request.url.path) if request else None,
        method=request.method if request else None
    )


def format_generic_error(
    error: Exception,
    message: str = "Internal server error",
    request: Optional[Request] = None,
    request_id: Optional[str] = None
) -> APIErrorResponse:
    """Format generic exception as standardized response"""
    error_detail = create_error_detail(
        code="INTERNAL_ERROR",
        message=str(error),
        context={"exception_type": type(error).__name__}
    )
    
    return APIErrorResponse(
        status=StatusEnum.ERROR,
        message=message,
        errors=[error_detail],
        request_id=request_id,
        path=str(request.url.path) if request else None,
        method=request.method if request else None
    )


class ResponseFormatter:
    """Utility class for creating standardized responses"""
    
    @staticmethod
    def success(
        data: Any, 
        message: str = "Request successful",
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create standardized success response"""
        from ..schemas.responses import StandardResponse, StatusEnum
        
        response = StandardResponse(
            status=StatusEnum.SUCCESS,
            message=message,
            data=data,
            errors=None,
            metadata=metadata,
            request_id=request_id
        )
        
        return response.dict(exclude_none=True)
    
    @staticmethod
    def paginated(
        data: List[Any],
        pagination: Dict[str, Any],
        message: str = "Request successful",
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create standardized paginated response"""
        from ..schemas.responses import PaginatedResponse, StatusEnum, PaginationModel
        
        pagination_model = PaginationModel(**pagination)
        
        response = PaginatedResponse(
            status=StatusEnum.SUCCESS,
            message=message,
            data=data,
            pagination=pagination_model,
            metadata=metadata,
            request_id=request_id
        )
        
        return response.dict(exclude_none=True)
    
    @staticmethod
    def error(
        error_response: Union[APIErrorResponse, ValidationErrorResponse]
    ) -> JSONResponse:
        """Create error JSON response with proper status code"""
        status_code = 500  # Default
        
        if hasattr(error_response, 'errors') and error_response.errors:
            first_error = error_response.errors[0]
            if first_error.code == "VALIDATION_ERROR":
                status_code = 422
            elif first_error.code in ["RULE_NOT_FOUND", "REQUEST_NOT_FOUND"]:
                status_code = 404
            elif first_error.code == "INVALID_PARAMETER":
                status_code = 400
            elif first_error.code == "SERVICE_UNAVAILABLE":
                status_code = 503
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict(exclude_none=True)
        )


# Helper functions for common response patterns
def success_response(
    data: Any, 
    message: str = "Request successful",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Quick success response creation"""
    return ResponseFormatter.success(data, message, metadata)


def paginated_response(
    data: List[Any],
    skip: int,
    limit: int,
    total: int,
    message: str = "Request successful"
) -> Dict[str, Any]:
    """Quick paginated response creation"""
    pagination = {
        "skip": skip,
        "limit": limit,
        "total": total,
        "returned": len(data),
        "has_next": skip + len(data) < total,
        "has_previous": skip > 0
    }
    
    return ResponseFormatter.paginated(data, pagination, message)


def error_response(
    message: str,
    code: str = "API_ERROR",
    field: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Quick error response creation"""
    error_detail = create_error_detail(code, message, field, context)
    error_response_obj = APIErrorResponse(
        status=StatusEnum.ERROR,
        message=message,
        errors=[error_detail],
        request_id=None,
        path=None,
        method=None
    )
    
    return ResponseFormatter.error(error_response_obj)
