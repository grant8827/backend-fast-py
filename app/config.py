"""
FastAPI Configuration Settings
Railway-optimized configuration with environment variables
"""

import os
from typing import List


class Settings:
    def __init__(self):
        # Environment detection
        self.environment = os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")
        
        # FastAPI Configuration
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.secret_key = os.getenv("SECRET_KEY", "fastapi-secret-key-change-in-production-onestopradio-12345")
        self.allowed_hosts = ["localhost", "127.0.0.1", "0.0.0.0"]
        
        # Database Configuration
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./onestopradio.db")
        
        # Handle Railway PostgreSQL URL format conversion
        if database_url.startswith("postgres://"):
            # Railway provides postgres:// but SQLAlchemy 2.0+ requires postgresql://
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://"):
            # Convert to async driver
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        self.database_url = database_url
        
        # Database Pool Configuration (for PostgreSQL)
        self.db_pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.db_pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        
        # JWT Authentication
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        self.jwt_algorithm = "HS256"
        
        # CORS Configuration - Railway deployment friendly
        cors_origins_str = os.getenv("CORS_ORIGINS", "")
        if cors_origins_str:
            self.cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
        else:
            # Default origins for development
            self.cors_origins = [
                "http://localhost:3000",
                "http://localhost:5000", 
                "http://127.0.0.1:3000"
            ]
        
        # Add Railway deployment URLs if available
        if self.environment == "production":
            railway_static_url = os.getenv("RAILWAY_STATIC_URL")
            if railway_static_url:
                self.cors_origins.append(f"https://{railway_static_url}")
                self.cors_origins.append(f"http://{railway_static_url}")
            
            # Add common Railway patterns
            self.cors_origins.extend([
                "https://*.railway.app",
                "https://*.railway.dev"
            ])
        
        # File Upload Configuration
        self.max_upload_size = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB default
        self.upload_dir = os.getenv("UPLOAD_DIR", "static/uploads")
        
        # Service Configuration
        self.service_name = "OneStopRadio-FastAPI"
        self.service_version = "1.0.0"
        self.server_host = "0.0.0.0"
        self.server_port = int(os.getenv("PORT", "8000"))
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)


# Global settings instance
settings = Settings()