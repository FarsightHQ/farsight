"""
Configuration settings for the application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Find project root (3 levels up from this file: app/core/config.py -> backend/app/core -> backend/app -> backend -> root)
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent.parent

# Load environment variables
# First try project root .env, then fall back to default behavior (current directory)
_env_path = _project_root / '.env'
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    # Fall back to default behavior (searches current directory and parents)
    load_dotenv()

class Settings:
    """Application settings from environment variables"""
    
    # Database
    # Construct DATABASE_URL from individual POSTGRES_* variables if DATABASE_URL not set
    _db_url = os.getenv("DATABASE_URL")
    if not _db_url:
        _db_user = os.getenv("POSTGRES_USER", "farsight_user")
        _db_password = os.getenv("POSTGRES_PASSWORD", "farsight_password")
        _db_host = os.getenv("POSTGRES_HOST", "localhost")
        _db_port = os.getenv("POSTGRES_PORT", "5432")
        _db_name = os.getenv("POSTGRES_DB", "farsight")
        _db_url = f"postgresql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
    DATABASE_URL: str = _db_url
    
    # File Upload Settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "50"))
    
    @property
    def max_upload_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.MAX_UPLOAD_MB * 1024 * 1024
    
    # File Validation Settings
    MIN_DISK_SPACE_MULTIPLIER: float = float(os.getenv("MIN_DISK_SPACE_MULTIPLIER", "2.0"))
    CSV_VALIDATION_SAMPLE_SIZE: int = int(os.getenv("CSV_VALIDATION_SAMPLE_SIZE", "8192"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Keycloak Authentication Settings
    KEYCLOAK_URL: str = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "farsight")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "farsight-backend")
    KEYCLOAK_CLIENT_SECRET: str = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
    KEYCLOAK_ALGORITHM: str = os.getenv("KEYCLOAK_ALGORITHM", "RS256")
    KEYCLOAK_PUBLIC_KEY: str = os.getenv("KEYCLOAK_PUBLIC_KEY", "")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS Settings
    CORS_ORIGINS: list[str] = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
        if origin.strip()
    ]
    
    @property
    def keycloak_well_known_url(self) -> str:
        """Get Keycloak well-known configuration endpoint"""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/.well-known/openid-configuration"
    
    @property
    def keycloak_jwks_url(self) -> str:
        """Get Keycloak JWKS endpoint for public keys"""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"
    
    @property
    def keycloak_issuer(self) -> str:
        """Get Keycloak issuer URL"""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"


# Global settings instance
settings = Settings()
