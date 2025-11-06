"""
OneStopRadio Database Models
DJ Platform - Users, Stations, Tracks, Playlists
"""

from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from .database import Base


class User(Base):
    """User account model for DJ authentication"""
    __tablename__ = "users"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    # Authentication
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Profile information
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    dj_name: Mapped[Optional[str]] = mapped_column(String(100))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamps
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    stations: Mapped[List["Station"]] = relationship("Station", back_populates="owner", cascade="all, delete-orphan")
    playlists: Mapped[List["Playlist"]] = relationship("Playlist", back_populates="user", cascade="all, delete-orphan")
    uploaded_tracks: Mapped[List["Track"]] = relationship("Track", back_populates="uploader")


class Station(Base):
    """Radio station/channel model"""
    __tablename__ = "stations"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Station details
    description: Mapped[Optional[str]] = mapped_column(Text)
    genre: Mapped[Optional[str]] = mapped_column(String(50))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    website_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Streaming configuration
    stream_url: Mapped[Optional[str]] = mapped_column(String(500))
    bitrate: Mapped[int] = mapped_column(Integer, default=320, nullable=False)
    is_live: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Social media links
    social_links: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Statistics
    total_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    peak_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_plays: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Foreign keys
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="stations")
    streaming_sessions: Mapped[List["StreamingSession"]] = relationship("StreamingSession", back_populates="station")


class Track(Base):
    """Music track model"""
    __tablename__ = "tracks"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    artist: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Track metadata
    album: Mapped[Optional[str]] = mapped_column(String(255))
    genre: Mapped[Optional[str]] = mapped_column(String(100))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    duration: Mapped[Optional[float]] = mapped_column(Float)  # seconds
    
    # DJ-specific metadata
    bpm: Mapped[Optional[float]] = mapped_column(Float)
    key: Mapped[Optional[str]] = mapped_column(String(10))  # Musical key (C, Am, etc.)
    energy: Mapped[Optional[float]] = mapped_column(Float)  # 0.0 to 1.0
    danceability: Mapped[Optional[float]] = mapped_column(Float)  # 0.0 to 1.0
    
    # File information
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)  # bytes
    file_format: Mapped[Optional[str]] = mapped_column(String(10))  # mp3, wav, etc.
    
    # Audio analysis data
    waveform_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    spectral_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Statistics
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[Optional[float]] = mapped_column(Float)  # User rating 1-5
    
    # Foreign keys
    uploader_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationships
    uploader: Mapped["User"] = relationship("User", back_populates="uploaded_tracks")
    playlist_entries: Mapped[List["PlaylistTrack"]] = relationship("PlaylistTrack", back_populates="track")


class Playlist(Base):
    """User playlists for organizing tracks"""
    __tablename__ = "playlists"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Playlist metadata
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Statistics
    total_duration: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # seconds
    track_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Foreign keys
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="playlists")
    tracks: Mapped[List["PlaylistTrack"]] = relationship("PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan")


class PlaylistTrack(Base):
    """Many-to-many relationship between playlists and tracks with ordering"""
    __tablename__ = "playlist_tracks"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Ordering
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Foreign keys
    playlist_id: Mapped[str] = mapped_column(ForeignKey("playlists.id"), nullable=False)
    track_id: Mapped[str] = mapped_column(ForeignKey("tracks.id"), nullable=False)
    
    # Relationships
    playlist: Mapped["Playlist"] = relationship("Playlist", back_populates="tracks")
    track: Mapped["Track"] = relationship("Track", back_populates="playlist_entries")


class StreamingSession(Base):
    """Live streaming session tracking"""
    __tablename__ = "streaming_sessions"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Session details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Statistics
    peak_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_duration: Mapped[Optional[float]] = mapped_column(Float)  # seconds
    data_transferred: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # bytes
    
    # Technical details
    bitrate: Mapped[int] = mapped_column(Integer, nullable=False)
    stream_key: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Foreign keys
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id"), nullable=False)
    
    # Relationships
    station: Mapped["Station"] = relationship("Station", back_populates="streaming_sessions")


class DJSet(Base):
    """DJ mix/set recordings and metadata"""
    __tablename__ = "dj_sets"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Set metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    genre: Mapped[Optional[str]] = mapped_column(String(100))
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Recording details
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration: Mapped[Optional[float]] = mapped_column(Float)  # seconds
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Mix data (for visualization)
    tracklist: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    transitions: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    
    # Statistics
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[Optional[float]] = mapped_column(Float)
    
    # Foreign keys
    dj_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationships
    dj: Mapped["User"] = relationship("User")


# Create indexes for better performance
from sqlalchemy import Index

# User indexes
Index("idx_users_username", User.username)
Index("idx_users_email", User.email)
Index("idx_users_active", User.is_active)

# Station indexes
Index("idx_stations_slug", Station.slug)
Index("idx_stations_owner", Station.owner_id)
Index("idx_stations_genre", Station.genre)
Index("idx_stations_live", Station.is_live)

# Track indexes
Index("idx_tracks_title", Track.title)
Index("idx_tracks_artist", Track.artist)
Index("idx_tracks_genre", Track.genre)
Index("idx_tracks_bpm", Track.bpm)
Index("idx_tracks_key", Track.key)
Index("idx_tracks_uploader", Track.uploader_id)

# Playlist indexes
Index("idx_playlists_user", Playlist.user_id)
Index("idx_playlists_public", Playlist.is_public)

# PlaylistTrack indexes
Index("idx_playlist_tracks_playlist", PlaylistTrack.playlist_id)
Index("idx_playlist_tracks_position", PlaylistTrack.playlist_id, PlaylistTrack.position)

# StreamingSession indexes
Index("idx_streaming_sessions_station", StreamingSession.station_id)
Index("idx_streaming_sessions_started", StreamingSession.started_at)

# DJSet indexes
Index("idx_dj_sets_dj", DJSet.dj_id)
Index("idx_dj_sets_recorded", DJSet.recorded_at)
Index("idx_dj_sets_genre", DJSet.genre)