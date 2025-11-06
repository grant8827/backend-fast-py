"""
Station SQLAlchemy Models
Matching Django Station functionality
"""

from sqlalchemy import String, Text, Boolean, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import uuid

from ..database import Base


class Station(Base):
    """Radio station model for DJ broadcasting"""
    
    __tablename__ = "stations"
    
    # Genre choices
    GENRE_CHOICES = [
        'electronic', 'rock', 'pop', 'jazz', 'classical', 'hip_hop', 
        'r_and_b', 'country', 'folk', 'reggae', 'latin', 'world', 
        'talk', 'news', 'mixed', 'other'
    ]
    
    # Primary fields
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    
    # Basic information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    genre: Mapped[str] = mapped_column(String(20), default='mixed', nullable=False)
    
    # Media assets
    logo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # File path
    cover_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # File path
    
    # Social media links
    youtube_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    twitch_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    facebook_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    instagram_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    twitter_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Station settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_chat: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_record: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_bitrate: Mapped[int] = mapped_column(Integer, default=320, nullable=False)
    
    # Statistics
    total_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    peak_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="station")
    
    @property
    def social_links(self) -> dict:
        """Return dictionary of social media links"""
        return {
            'youtube': self.youtube_url,
            'twitch': self.twitch_url,
            'facebook': self.facebook_url,
            'instagram': self.instagram_url,
            'twitter': self.twitter_url,
        }
    
    def update_stream_stats(self, listeners: Optional[int] = None, duration_minutes: Optional[float] = None):
        """Update station statistics from streaming session"""
        if listeners is not None:
            self.total_listeners = listeners
            if listeners > self.peak_listeners:
                self.peak_listeners = listeners
        
        if duration_minutes is not None:
            self.total_hours += duration_minutes / 60.0
    
    def __repr__(self):
        return f"<Station(id={self.id}, name={self.name}, user_id={self.user_id})>"


class StationSettings(Base):
    """Extended station settings and preferences"""
    
    __tablename__ = "station_settings"
    
    # Primary key
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    station_id: Mapped[str] = mapped_column(String, ForeignKey("stations.id"), nullable=False)
    
    # Advanced audio settings
    audio_quality: Mapped[str] = mapped_column(String(20), default='high', nullable=False)  # standard, high, premium
    enable_auto_dj: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    crossfade_duration: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # seconds
    
    # Recording settings
    recording_format: Mapped[str] = mapped_column(String(10), default='mp3', nullable=False)  # mp3, aac, flac
    auto_archive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    archive_duration_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    
    # Notification settings
    notify_on_listeners: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    listener_threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    notify_on_errors: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # API keys and integrations (would be encrypted in production)
    last_fm_api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    spotify_client_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    station: Mapped["Station"] = relationship("Station", back_populates="settings_extended")
    
    def __repr__(self):
        return f"<StationSettings(id={self.id}, station_id={self.station_id})>"


# Update User model to include station relationship
from ..auth.models import User
User.station = relationship("Station", back_populates="user", uselist=False)
Station.settings_extended = relationship("StationSettings", back_populates="station", uselist=False)