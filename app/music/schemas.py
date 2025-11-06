"""
Music API Schemas
Pydantic models for Track and Playlist serialization
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TrackBase(BaseModel):
    """Base track schema"""
    title: str
    artist: str
    album: Optional[str] = None
    duration: int = Field(..., description="Duration in seconds")
    bpm: Optional[int] = None
    key: Optional[str] = None
    genre: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    waveform: Optional[List[float]] = None
    cover_art: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class TrackCreate(TrackBase):
    """Schema for creating a new track"""
    pass


class TrackUpdate(BaseModel):
    """Schema for updating a track"""
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    duration: Optional[int] = None
    bpm: Optional[int] = None
    key: Optional[str] = None
    genre: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    waveform: Optional[List[float]] = None
    cover_art: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    play_count: Optional[int] = None


class Track(TrackBase):
    """Complete track schema with all fields"""
    id: str
    play_count: int
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class PlaylistBase(BaseModel):
    """Base playlist schema"""
    name: str
    is_auto_mix: bool = False


class PlaylistCreate(PlaylistBase):
    """Schema for creating a new playlist"""
    track_ids: Optional[List[str]] = []


class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist"""
    name: Optional[str] = None
    is_auto_mix: Optional[bool] = None


class Playlist(PlaylistBase):
    """Complete playlist schema with tracks"""
    id: str
    tracks: List[Track] = []
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class PlaylistStats(BaseModel):
    """Playlist statistics schema"""
    total_tracks: int
    total_duration: int
    genres: dict[str, int]
    average_bpm: float
    key_distribution: dict[str, int]


class TrackUpload(BaseModel):
    """Schema for track file upload response"""
    track: Track
    file_url: str