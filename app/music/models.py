"""
Music Database Models
Track and Playlist models for the DJ platform
"""

from sqlalchemy import String, Integer, Float, Boolean, Text, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime

from ..database import Base


# Association table for playlist-track many-to-many relationship
playlist_tracks = Table(
    'playlist_tracks',
    Base.metadata,
    Column('playlist_id', String, ForeignKey('playlists.id'), primary_key=True),
    Column('track_id', String, ForeignKey('tracks.id'), primary_key=True),
    Column('position', Integer, default=0)  # Track position in playlist
)


class Track(Base):
    """Track model for music files"""
    __tablename__ = "tracks"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    artist: Mapped[str] = mapped_column(String, nullable=False)
    album: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)  # in seconds
    bpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    waveform: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    cover_art: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 stars
    
    # User association
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    playlists: Mapped[List["Playlist"]] = relationship(
        secondary=playlist_tracks, 
        back_populates="tracks"
    )


class Playlist(Base):
    """Playlist model for organizing tracks"""
    __tablename__ = "playlists"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_auto_mix: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # User association
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    tracks: Mapped[List[Track]] = relationship(
        secondary=playlist_tracks,
        back_populates="playlists",
        order_by="playlist_tracks.c.position"
    )