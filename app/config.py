"""
FastAPI Configuration Settings
Simple configuration with hardcoded values for quick setup
"""

import os
from typing import List


class Settings:
    def __init__(self):
        # FastAPI Configuration
        self.debug = True
        self.secret_key = "fastapi-secret-key-change-in-production-onestopradio-12345"
        self.allowed_hosts = ["localhost", "127.0.0.1", "0.0.0.0"]
        
        # Database Configuration
        self.database_url = "sqlite+aiosqlite:///./onestopradio.db"
        
        # JWT Authentication
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 7
        self.jwt_algorithm = "HS256"
        
        # CORS Configuration
        self.cors_origins = [
            "http://localhost:3000",
            "http://localhost:5000", 
            "http://127.0.0.1:3000"
        ]
        
        # File Upload Configuration
        self.max_upload_size = 10485760  # 10MB
        self.upload_dir = "static/uploads"
        
        # Service Configuration
        self.service_name = "OneStopRadio-FastAPI"
        self.service_version = "1.0.0"
        self.server_host = "0.0.0.0"
        self.server_port = 8000
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)


# Global settings instance
settings = Settings()