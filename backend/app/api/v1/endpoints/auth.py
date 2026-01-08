"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.auth import get_current_user
from app.utils.error_handlers import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me")
async def get_current_user_info(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current authenticated user information
    
    Returns user details extracted from JWT token:
    - User ID (sub)
    - Username
    - Email
    - Name
    - Roles
    """
    return success_response(
        data=user,
        message="User information retrieved successfully"
    )
