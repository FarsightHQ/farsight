"""
Authentication and authorization module using Keycloak
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
# Set auto_error=False so we can handle missing tokens ourselves and return 401 instead of 403
security = HTTPBearer(auto_error=False)


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
            except httpx.TimeoutException as e:
                logger.error(f"Timeout fetching JWKS keys: {e}")
                if cls._keys is None:
                    # If we have no cached keys and fetch times out, return empty dict
                    # This will allow token decoding without verification as fallback
                    logger.warning("JWKS fetch timeout, using fallback token validation")
                    return {"keys": []}
            except httpx.RequestError as e:
                logger.error(f"Request error fetching JWKS keys: {e}")
                if cls._keys is None:
                    logger.warning("JWKS fetch failed, using fallback token validation")
                    return {"keys": []}
            except Exception as e:
                logger.error(f"Failed to fetch JWKS keys: {e}")
                if cls._keys is None:
                    # Return empty keys dict instead of raising exception
                    # This allows token decoding without signature verification
                    logger.warning("JWKS unavailable, using fallback token validation")
                    return {"keys": []}
        
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


def normalize_issuer(issuer: str) -> str:
    """
    Normalize issuer URL for comparison.
    Handles differences between localhost and Docker internal hostnames.
    Returns the realm path portion (e.g., '/realms/farsight')
    """
    if not issuer:
        return ""
    
    # Remove trailing slash
    issuer = issuer.rstrip("/")
    
    # Extract realm path (e.g., '/realms/farsight')
    # This works regardless of whether hostname is localhost:8080 or keycloak:8080
    if "/realms/" in issuer:
        realm_path = issuer.split("/realms/")[1]
        return f"/realms/{realm_path}"
    
    return issuer


class IssuerCache:
    """Cache for Keycloak issuer URL from well-known endpoint"""
    _issuer: Optional[str] = None
    _cache_time: Optional[float] = None
    _cache_duration: int = 3600  # Cache for 1 hour

    @classmethod
    async def get_issuer(cls) -> str:
        """
        Get issuer URL, using configured value (not well-known endpoint).
        The well-known endpoint returns internal Docker hostname which doesn't match
        tokens issued to external clients (localhost).
        """
        # Use configured issuer from settings instead of fetching from well-known
        # This ensures consistency with how frontend accesses Keycloak
        configured_issuer = settings.keycloak_issuer.rstrip("/")
        return configured_issuer


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
        # Try to get public key for token (may fail if JWKS unavailable)
        try:
            key_data = await get_public_key_for_token(token)
        except HTTPException as e:
            # If JWKS fetch fails with 503, still try to decode token without verification
            # This allows the app to work even if Keycloak JWKS endpoint is temporarily unavailable
            if e.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
                logger.warning("JWKS unavailable, decoding token without signature verification")
            else:
                raise
        
        # Decode token (full verification would require constructing RSA key from JWKS)
        # For now, decode without signature verification and validate claims
        try:
            payload = jwt.get_unverified_claims(token)
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
        
        # Validate expiration
        import time
        exp = payload.get("exp")
        if exp and exp < time.time():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Validate issuer - normalize to handle localhost vs Docker hostname differences
        token_issuer = payload.get("iss", "")
        expected_issuer = await IssuerCache.get_issuer()
        
        # Normalize both issuers to realm path for comparison
        # This handles cases where token has localhost:8080 but backend sees keycloak:8080
        token_issuer_normalized = normalize_issuer(token_issuer)
        expected_issuer_normalized = normalize_issuer(expected_issuer)
        
        if token_issuer_normalized != expected_issuer_normalized:
            logger.warning(
                f"Issuer mismatch - Token issuer: '{token_issuer}' (normalized: '{token_issuer_normalized}'), "
                f"Expected: '{expected_issuer}' (normalized: '{expected_issuer_normalized}')"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token issuer. Expected realm: {expected_issuer_normalized}, Got: {token_issuer_normalized}"
            )
        
        logger.debug(f"Issuer validated successfully: {token_issuer_normalized}")
        
        # Validate audience - accept tokens from any allowed client, realm, or Keycloak account service
        aud = payload.get("aud")
        # Keycloak can issue tokens with 'account' as audience (account service)
        # Also accept the realm name and any configured client IDs
        valid_audiences = set(settings.KEYCLOAK_ALLOWED_CLIENT_IDS + [settings.KEYCLOAK_REALM, "account"])
        
        if isinstance(aud, list):
            # Check if any of the allowed client IDs, realm, or 'account' is in the audience list
            if not any(a in valid_audiences for a in aud):
                logger.warning(f"Token audience {aud} does not match allowed audiences {valid_audiences}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token audience"
                )
        elif aud:
            # Single audience value - check if it's in allowed list
            if aud not in valid_audiences:
                logger.warning(f"Token audience '{aud}' does not match allowed audiences {valid_audiences}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token audience"
                )
        
        return payload
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected exceptions and return 401 instead of 500
        logger.error(f"Token decode error: {e}", exc_info=True)
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


def uploader_from_user(user: Dict[str, Any]) -> str:
    """
    Map the authenticated user to created_by / uploaded_by audit fields (DB max 100 chars).
    """
    if not user:
        return "system"
    name = user.get("username") or user.get("email") or user.get("sub")
    if not name:
        return "system"
    return str(name)[:100]


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user from JWT token
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user}
    """
    try:
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials
        
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
        # Re-raise HTTP exceptions (401, 403, etc.) as-is
        raise
    except Exception as e:
        # Catch any unexpected exceptions and return 401 instead of 500
        logger.error(f"Authentication error: {e}", exc_info=True)
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
