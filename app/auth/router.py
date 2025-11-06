"""
Authentication Router
JWT-based authentication endpoints matching Django API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from ..database import get_db
from ..core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from ..core.exceptions import http_400_bad_request, http_401_unauthorized
from .models import User
from .schemas import (
    UserCreate, UserLogin, UserUpdate, UserResponse, 
    PasswordChange, AuthResponse, TokenResponse, ErrorResponse
)
from .dependencies import get_current_active_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register/", response_model=AuthResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise http_400_bad_request("Email already registered")
        else:
            raise http_400_bad_request("Username already taken")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        dj_name=user_data.dj_name,
        bio=user_data.bio,
        email_notifications=user_data.email_notifications
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": db_user.id})
    refresh_token = create_refresh_token(data={"sub": db_user.id})
    
    return AuthResponse(
        success=True,
        message="User registered successfully",
        user=UserResponse.from_orm(db_user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    )


@router.post("/login/", response_model=AuthResponse)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    User login with email and password
    """
    # Get user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise http_401_unauthorized("Incorrect email or password")
    
    if not user.is_active:
        raise http_401_unauthorized("User account is disabled")
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return AuthResponse(
        success=True,
        message="Login successful",
        user=UserResponse.from_orm(user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    )


@router.get("/me/", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile
    """
    return UserResponse.from_orm(current_user)


@router.put("/me/", response_model=AuthResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user profile
    """
    # Update user fields
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
    if user_update.dj_name is not None:
        current_user.dj_name = user_update.dj_name
    if user_update.bio is not None:
        current_user.bio = user_update.bio
    if user_update.email_notifications is not None:
        current_user.email_notifications = user_update.email_notifications
    
    await db.commit()
    await db.refresh(current_user)
    
    return AuthResponse(
        success=True,
        message="Profile updated successfully",
        user=UserResponse.from_orm(current_user)
    )


@router.post("/change-password/", response_model=AuthResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise http_400_bad_request("Current password is incorrect")
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    # Generate new tokens
    access_token = create_access_token(data={"sub": current_user.id})
    refresh_token = create_refresh_token(data={"sub": current_user.id})
    
    return AuthResponse(
        success=True,
        message="Password changed successfully",
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    )


@router.post("/logout/", response_model=dict)
async def logout_user():
    """
    User logout (client-side token removal)
    """
    return {
        "success": True,
        "message": "Logout successful"
    }