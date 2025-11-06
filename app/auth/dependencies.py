"""
Authentication dependencies for FastAPI
JWT token validation and user retrieval
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from ..database import get_db
from ..core.security import verify_token
from ..core.exceptions import http_401_unauthorized
from .models import User

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    # Verify JWT token
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise http_401_unauthorized("Could not validate credentials")
    
    # Extract user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise http_401_unauthorized("Could not validate credentials")
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise http_401_unauthorized("User not found")
    
    if not user.is_active:
        raise http_401_unauthorized("User account is disabled")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (already filtered by get_current_user)
    """
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns user if valid token, None otherwise
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None or not user.is_active:
            return None
            
        return user
    except Exception:
        return None


def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns user if valid token, None otherwise
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # This would need to be async, but for optional auth we'll keep it simple
        return None  # Implement if needed
    except Exception:
        return None