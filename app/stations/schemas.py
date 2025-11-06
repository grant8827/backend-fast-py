"""
Pydantic schemas for station endpoints
Request and response models
"""

from pydantic import BaseModel, validator
from typing import Optional, Dict
from datetime import datetime


class StationBase(BaseModel):
    """Base station schema"""
    name: str
    description: Optional[str] = None
    genre: str = "mixed"
    is_public: bool = True
    allow_chat: bool = True
    auto_record: bool = False
    max_bitrate: int = 320


class StationCreate(StationBase):
    """Station creation schema"""
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Station name must be at least 2 characters long')
        return v.strip()
    
    @validator('genre')
    def validate_genre(cls, v):
        valid_genres = [
            'electronic', 'rock', 'pop', 'jazz', 'classical', 'hip_hop',
            'r_and_b', 'country', 'folk', 'reggae', 'latin', 'world',
            'talk', 'news', 'mixed', 'other'
        ]
        if v not in valid_genres:
            raise ValueError(f'Invalid genre. Must be one of: {", ".join(valid_genres)}')
        return v


class StationUpdate(BaseModel):
    """Station update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    is_public: Optional[bool] = None
    allow_chat: Optional[bool] = None
    auto_record: Optional[bool] = None
    max_bitrate: Optional[int] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Station name must be at least 2 characters long')
        return v.strip() if v else v


class SocialLinksUpdate(BaseModel):
    """Social media links update schema"""
    youtube_url: Optional[str] = None
    twitch_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None


class StationResponse(BaseModel):
    """Station response schema"""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    genre: str
    logo: Optional[str] = None
    cover_image: Optional[str] = None
    youtube_url: Optional[str] = None
    twitch_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    is_public: bool
    allow_chat: bool
    auto_record: bool
    max_bitrate: int
    total_listeners: int
    peak_listeners: int
    total_hours: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StationStatsUpdate(BaseModel):
    """Station statistics update schema"""
    listeners: Optional[int] = None
    duration_minutes: Optional[float] = None


class FileUploadResponse(BaseModel):
    """File upload response schema"""
    success: bool
    message: str
    file_url: Optional[str] = None


class StationApiResponse(BaseModel):
    """Station API response schema"""
    success: bool
    message: str
    station: Optional[StationResponse] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    detail: str
    errors: Optional[dict] = None