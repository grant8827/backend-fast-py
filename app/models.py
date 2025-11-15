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
from .auth.models import User
from .stations.models import Station
from .music.models import Track, Playlist


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
    station: Mapped[Station] = relationship("Station")


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
    station: Mapped[Station] = relationship("Station")


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
    dj: Mapped[User] = relationship("User")


# Create indexes for better performance
from sqlalchemy import Index

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