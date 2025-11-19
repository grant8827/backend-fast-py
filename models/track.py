from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from .base import Base

class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    artist = Column(String(255), nullable=False, index=True)
    album = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=True, index=True)
    year = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds
    bpm = Column(Float, nullable=True, index=True)  # Beats per minute
    key_signature = Column(String(10), nullable=True)  # Musical key (e.g., "C major", "Am")
    energy_level = Column(Float, nullable=True)  # 0.0 to 1.0 energy rating
    
    # File information
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(Integer, nullable=True)  # File size in bytes
    file_format = Column(String(20), nullable=True)  # mp3, wav, flac, etc.
    
    # Waveform analysis data
    waveform_path = Column(String(500), nullable=True)  # Path to waveform JSON
    waveform_peaks = Column(Text, nullable=True)  # Serialized peak data for quick preview
    analyzed = Column(Boolean, default=False)  # Has C++ analyzer processed this file
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    imported_at = Column(DateTime(timezone=True), nullable=True)
    last_played = Column(DateTime(timezone=True), nullable=True)
    play_count = Column(Integer, default=0)
    
    # DJ-specific metadata
    intro_time = Column(Float, nullable=True)  # Intro length in seconds
    outro_time = Column(Float, nullable=True)  # Outro length in seconds
    cue_points = Column(Text, nullable=True)  # JSON array of cue point timestamps
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    
    def to_dict(self):
        """Convert track model to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'genre': self.genre,
            'year': self.year,
            'duration': self.duration,
            'bpm': self.bpm,
            'key_signature': self.key_signature,
            'energy_level': self.energy_level,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'waveform_path': self.waveform_path,
            'analyzed': self.analyzed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_played': self.last_played.isoformat() if self.last_played else None,
            'play_count': self.play_count,
            'intro_time': self.intro_time,
            'outro_time': self.outro_time,
            'cue_points': self.cue_points,
            'rating': self.rating
        }
    
    def get_display_name(self):
        """Get formatted display name for UI"""
        return f"{self.artist} - {self.title}"
    
    def get_duration_formatted(self):
        """Get human-readable duration"""
        if not self.duration:
            return "Unknown"
        
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes}:{seconds:02d}"
    
    def get_bpm_formatted(self):
        """Get formatted BPM display"""
        if not self.bpm:
            return "Unknown"
        return f"{self.bpm:.1f} BPM"
    
    def is_compatible_bpm(self, other_bpm, tolerance=5.0):
        """Check if this track's BPM is compatible with another for mixing"""
        if not self.bpm or not other_bpm:
            return False
        
        # Check direct compatibility
        if abs(self.bpm - other_bpm) <= tolerance:
            return True
        
        # Check harmonic mixing (double/half time)
        if abs(self.bpm - other_bpm * 2) <= tolerance:
            return True
        if abs(self.bpm * 2 - other_bpm) <= tolerance:
            return True
            
        return False