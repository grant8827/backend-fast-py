"""
Pydantic schemas for authentication endpoints
Request and response models
"""

from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dj_name: Optional[str] = None
    bio: Optional[str] = None
    email_notifications: bool = True


class UserCreate(UserBase):
    """User creation schema with password"""
    password: str
    confirm_password: str
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v.lower().strip()
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserUpdate(BaseModel):
    """User update schema"""
    username: Optional[str] = None
    email: str


class UserLogin(BaseModel):
    """User login schema"""
    email: str
    password: str


class UserUpdate(BaseModel):
    """User profile update schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dj_name: Optional[str] = None
    bio: Optional[str] = None
    email_notifications: Optional[bool] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dj_name: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    is_verified: bool
    email_notifications: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Authentication response schema"""
    success: bool
    message: str
    user: Optional[UserResponse] = None
    tokens: Optional[TokenResponse] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    detail: str
    errors: Optional[dict] = None