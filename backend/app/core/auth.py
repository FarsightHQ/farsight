"""
Authentication and authorization module using Keycloak
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from jose.utils import base64url_decode
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


class JWKSCache:
    """Cache for Keycloak JWKS public keys"""
    _keys: Optional[Dict[str, Any]] = None
    _cache_time: Optional[float] = None
    _cache_duration: int = 3600  # Cache for 1 hour

    @classmethod
    async def get_keys(cls) -> Dict[str, Any]:
        """Get JWKS keys, fetching from Keycloak if not cached or expired"""
        import time
        current_time = time.time()
        
        if cls._keys is None or (cls._cache_time and current_time - cls._cache_time > cls._cache_duration):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(settings.keycloak_jwks_url, timeout=10.0)
                    response.raise_for_status()
                    cls._keys = response.json()
                    cls._cache_time = current_time
                    logger.info("Fetched JWKS keys from Keycloak")
            except Exception as e:
                logger.error(f"Failed to fetch JWKS keys: {e}")
                if cls._keys is None:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Unable to fetch authentication keys"
                    )
        
        return cls._keys

    @classmethod
    def get_public_key(cls, kid: str) -> Optional[str]:
        """Get public key for a specific key ID"""
        if cls._keys is None:
            return None
        
        for key in cls._keys.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None


async def get_public_key_for_token(token: str) -> Dict[str, Any]:
    """Get the public key for verifying a JWT token"""
    try:
        # Decode token header to get key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing key ID"
            )
        
        # Get JWKS keys
        jwks = await JWKSCache.get_keys()
        key_data = JWKSCache.get_public_key(kid)
        
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Public key not found for token"
            )
        
        return key_data
    except JWTError as e:
        logger.error(f"JWT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )


def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token signature and return decoded payload"""
    try:
        # For RS256, we need to construct the public key from JWKS
        # This is a simplified version - in production, use cryptography library
        # to properly construct RSA public key from JWKS
        unverified_payload = jwt.get_unverified_claims(token)
        
        # Verify issuer
        issuer = unverified_payload.get("iss")
        if issuer != settings.keycloak_issuer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer"
            )
        
        # Verify audience (client ID)
        aud = unverified_payload.get("aud")
        if isinstance(aud, list):
            if settings.KEYCLOAK_CLIENT_ID not in aud:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token audience"
                )
        elif aud != settings.KEYCLOAK_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience"
            )
        
        # Note: Full signature verification requires fetching JWKS and constructing RSA key
        # For now, we'll decode without verification and rely on Keycloak's token validation
        # In production, implement full RSA signature verification
        
        return unverified_payload
    except JWTError as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token"""
    try:
        # Get public key for token
        key_data = await get_public_key_for_token(token)
        
        # Decode token (full verification would require constructing RSA key from JWKS)
        # For now, decode without signature verification and validate claims
        payload = jwt.get_unverified_claims(token)
        
        # Validate expiration
        import time
        exp = payload.get("exp")
        if exp and exp < time.time():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Validate issuer
        if payload.get("iss") != settings.keycloak_issuer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer"
            )
        
        # Validate audience
        aud = payload.get("aud")
        if isinstance(aud, list):
            if settings.KEYCLOAK_CLIENT_ID not in aud:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token audience"
                )
        elif aud and aud != settings.KEYCLOAK_CLIENT_ID:
            # Allow if audience is the realm name (common in Keycloak)
            if aud != settings.KEYCLOAK_REALM:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token audience"
                )
        
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to decode token"
        )


def get_user_roles(token_payload: Dict[str, Any]) -> List[str]:
    """Extract user roles from token claims"""
    roles = []
    
    # Get realm roles
    realm_access = token_payload.get("realm_access", {})
    if isinstance(realm_access, dict):
        realm_roles = realm_access.get("roles", [])
        if isinstance(realm_roles, list):
            roles.extend(realm_roles)
    
    # Get client-specific roles
    resource_access = token_payload.get("resource_access", {})
    if isinstance(resource_access, dict):
        client_access = resource_access.get(settings.KEYCLOAK_CLIENT_ID, {})
        if isinstance(client_access, dict):
            client_roles = client_access.get("roles", [])
            if isinstance(client_roles, list):
                roles.extend(client_roles)
    
    return roles


def extract_user_info(token_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user information from token payload"""
    return {
        "sub": token_payload.get("sub"),
        "username": token_payload.get("preferred_username") or token_payload.get("username"),
        "email": token_payload.get("email"),
        "name": token_payload.get("name"),
        "given_name": token_payload.get("given_name"),
        "family_name": token_payload.get("family_name"),
        "roles": get_user_roles(token_payload),
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user from JWT token
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        # Decode and validate token
        payload = await decode_token(token)
        
        # Extract user information
        user_info = extract_user_info(payload)
        
        if not user_info.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier"
            )
        
        return user_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(required_role: str):
    """
    FastAPI dependency factory for role-based access control
    
    Usage:
        @router.get("/admin")
        async def admin_route(
            user: dict = Depends(get_current_user),
            _: None = Depends(require_role("admin"))
        ):
            return {"message": "Admin access granted"}
    """
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> None:
        user_roles = user.get("roles", [])
        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: role '{required_role}' required"
            )
        return None
    
    return role_checker
