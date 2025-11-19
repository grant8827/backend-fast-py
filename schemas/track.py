from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TrackBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Track title")
    artist: str = Field(..., min_length=1, max_length=255, description="Artist name")
    album: Optional[str] = Field(None, max_length=255, description="Album name")
    genre: Optional[str] = Field(None, max_length=100, description="Music genre")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Release year")
    duration: Optional[float] = Field(None, ge=0, description="Duration in seconds")
    bpm: Optional[float] = Field(None, ge=0, le=300, description="Beats per minute")
    key_signature: Optional[str] = Field(None, max_length=10, description="Musical key")
    energy_level: Optional[float] = Field(None, ge=0, le=1, description="Energy level (0-1)")
    file_format: Optional[str] = Field(None, max_length=20, description="Audio file format")
    intro_time: Optional[float] = Field(None, ge=0, description="Intro length in seconds")
    outro_time: Optional[float] = Field(None, ge=0, description="Outro length in seconds")
    cue_points: Optional[str] = Field(None, description="JSON array of cue points")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Track rating (1-5 stars)")

class TrackCreate(TrackBase):
    file_path: str = Field(..., min_length=1, max_length=500, description="Path to audio file")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")

class TrackUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    artist: Optional[str] = Field(None, min_length=1, max_length=255)
    album: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2030)
    duration: Optional[float] = Field(None, ge=0)
    bpm: Optional[float] = Field(None, ge=0, le=300)
    key_signature: Optional[str] = Field(None, max_length=10)
    energy_level: Optional[float] = Field(None, ge=0, le=1)
    intro_time: Optional[float] = Field(None, ge=0)
    outro_time: Optional[float] = Field(None, ge=0)
    cue_points: Optional[str] = Field(None)
    rating: Optional[int] = Field(None, ge=1, le=5)

class TrackResponse(TrackBase):
    id: int
    file_path: str
    file_size: Optional[int] = None
    waveform_path: Optional[str] = None
    analyzed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_played: Optional[datetime] = None
    play_count: int = 0

    class Config:
        from_attributes = True

class TrackSearchQuery(BaseModel):
    query: Optional[str] = Field(None, max_length=255, description="Search text")
    artist: Optional[str] = Field(None, max_length=255, description="Filter by artist")
    genre: Optional[str] = Field(None, max_length=100, description="Filter by genre")
    year_min: Optional[int] = Field(None, ge=1900, description="Minimum year")
    year_max: Optional[int] = Field(None, le=2030, description="Maximum year")
    bpm_min: Optional[float] = Field(None, ge=0, description="Minimum BPM")
    bpm_max: Optional[float] = Field(None, le=300, description="Maximum BPM")
    duration_min: Optional[float] = Field(None, ge=0, description="Minimum duration (seconds)")
    duration_max: Optional[float] = Field(None, description="Maximum duration (seconds)")
    rating_min: Optional[int] = Field(None, ge=1, le=5, description="Minimum rating")
    analyzed_only: Optional[bool] = Field(False, description="Only show analyzed tracks")
    sort_by: Optional[str] = Field("title", description="Sort field")
    sort_order: Optional[str] = Field("asc", regex="^(asc|desc)$", description="Sort order")
    limit: Optional[int] = Field(50, ge=1, le=500, description="Results per page")
    offset: Optional[int] = Field(0, ge=0, description="Results offset")

class TrackSearchResponse(BaseModel):
    tracks: List[TrackResponse]
    total: int
    limit: int
    offset: int
    has_more: bool

class DeckLoadCommand(BaseModel):
    command: str = Field(..., description="WebSocket command type")
    track_id: int = Field(..., ge=1, description="Track ID to load")
    deck_id: str = Field(..., regex="^(A|B)$", description="Deck identifier (A or B)")
    auto_play: Optional[bool] = Field(False, description="Start playing immediately")
    cue_point: Optional[float] = Field(None, ge=0, description="Start position in seconds")

class TrackCompatibility(BaseModel):
    track_id: int
    compatible: bool
    bpm_difference: Optional[float] = None
    harmonic_match: Optional[bool] = None
    key_compatibility: Optional[str] = None

class TrackAnalysisStatus(BaseModel):
    track_id: int
    analyzed: bool
    waveform_available: bool
    analysis_progress: Optional[float] = Field(None, ge=0, le=1)
    error_message: Optional[str] = None