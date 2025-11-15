"""
Stream Provisioning Models
OneStopRadio - Dedicated Shoutcast Stream Management
"""

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import enum

from .database import Base


class StreamStatus(enum.Enum):
    """Stream status enumeration"""
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    MAINTENANCE = "maintenance"


class PortPool(Base):
    """Port allocation pool management"""
    __tablename__ = "port_pool"
    
    # Port identification
    port: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Status tracking
    is_allocated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allocated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Allocation details
    allocated_to_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    allocated_to_stream_id: Mapped[Optional[str]] = mapped_column(ForeignKey("dedicated_streams.id"))
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    allocated_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[allocated_to_user_id])
    stream: Mapped[Optional["DedicatedStream"]] = relationship("DedicatedStream", back_populates="allocated_port")


class DedicatedStream(Base):
    """Dedicated Shoutcast stream configuration for users"""
    __tablename__ = "dedicated_streams"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User association
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    station_id: Mapped[Optional[str]] = mapped_column(ForeignKey("stations.id"))
    
    # Stream configuration
    port: Mapped[int] = mapped_column(ForeignKey("port_pool.port"), unique=True, nullable=False)
    source_password: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Stream metadata
    stream_title: Mapped[str] = mapped_column(String(255), nullable=False)
    stream_description: Mapped[Optional[str]] = mapped_column(Text)
    stream_url: Mapped[Optional[str]] = mapped_column(String(500))
    genre: Mapped[str] = mapped_column(String(100), default="Various")
    
    # Technical settings
    max_listeners: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    bitrate: Mapped[int] = mapped_column(Integer, default=128, nullable=False)
    sample_rate: Mapped[int] = mapped_column(Integer, default=44100, nullable=False)
    public_server: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Stream status
    status: Mapped[StreamStatus] = mapped_column(Enum(StreamStatus), default=StreamStatus.PROVISIONING, nullable=False)
    is_live: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Configuration tracking
    shoutcast_config_path: Mapped[Optional[str]] = mapped_column(String(500))
    config_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_config_update: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Activity tracking
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_connection: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_disconnect: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Statistics
    total_connections: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_listener_hours: Mapped[float] = mapped_column(Integer, default=0.0, nullable=False)
    peak_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_transferred_mb: Mapped[float] = mapped_column(Integer, default=0.0, nullable=False)
    
    # Billing and limits
    monthly_listener_limit: Mapped[Optional[int]] = mapped_column(Integer)
    monthly_bandwidth_limit_gb: Mapped[Optional[float]] = mapped_column(Integer)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="dedicated_streams")
    station: Mapped[Optional["Station"]] = relationship("Station")
    allocated_port: Mapped["PortPool"] = relationship("PortPool", back_populates="stream")
    sessions: Mapped[List["StreamSession"]] = relationship("StreamSession", back_populates="stream", cascade="all, delete-orphan")
    monitoring_data: Mapped[List["StreamMonitoring"]] = relationship("StreamMonitoring", back_populates="stream", cascade="all, delete-orphan")


class StreamSession(Base):
    """Individual streaming session tracking"""
    __tablename__ = "stream_sessions"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Session tracking
    stream_id: Mapped[str] = mapped_column(ForeignKey("dedicated_streams.id"), nullable=False)
    session_key: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[float]] = mapped_column(Integer)
    
    # Session metadata
    source_ip: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    encoder_type: Mapped[Optional[str]] = mapped_column(String(100))  # SAM Broadcaster, OBS, etc.
    
    # Stream quality
    average_bitrate: Mapped[Optional[float]] = mapped_column(Integer)
    peak_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_data_mb: Mapped[float] = mapped_column(Integer, default=0.0, nullable=False)
    
    # Disconnect reason
    disconnect_reason: Mapped[Optional[str]] = mapped_column(String(255))
    was_planned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    stream: Mapped["DedicatedStream"] = relationship("DedicatedStream", back_populates="sessions")


class StreamMonitoring(Base):
    """Real-time stream monitoring data"""
    __tablename__ = "stream_monitoring"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Monitoring association
    stream_id: Mapped[str] = mapped_column(ForeignKey("dedicated_streams.id"), nullable=False)
    
    # Timestamp
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Listener metrics
    current_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    peak_listeners_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Stream health
    is_live: Mapped[bool] = mapped_column(Boolean, nullable=False)
    stream_uptime_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    current_bitrate: Mapped[Optional[int]] = mapped_column(Integer)
    audio_level_db: Mapped[Optional[float]] = mapped_column(Integer)
    
    # Performance metrics
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Integer)
    memory_usage_mb: Mapped[Optional[float]] = mapped_column(Integer)
    bandwidth_mbps: Mapped[Optional[float]] = mapped_column(Integer)
    
    # Stream metadata
    current_song: Mapped[Optional[str]] = mapped_column(String(500))
    stream_genre: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Error tracking
    connection_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    audio_dropouts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    stream: Mapped["DedicatedStream"] = relationship("DedicatedStream", back_populates="monitoring_data")


class ShoutcastServer(Base):
    """Shoutcast server configuration and management"""
    __tablename__ = "shoutcast_servers"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Server details
    server_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_port: Mapped[int] = mapped_column(Integer, default=8000, nullable=False)
    
    # Authentication
    admin_password: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Server configuration
    max_streams: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    config_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    executable_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_streams: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Capacity management
    cpu_limit_percent: Mapped[float] = mapped_column(Integer, default=80.0, nullable=False)
    memory_limit_gb: Mapped[float] = mapped_column(Integer, default=4.0, nullable=False)
    bandwidth_limit_mbps: Mapped[float] = mapped_column(Integer, default=100.0, nullable=False)
    
    # Monitoring
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    health_status: Mapped[str] = mapped_column(String(50), default="unknown")
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


# Add relationships to existing User model
from .models import User
User.dedicated_streams = relationship("DedicatedStream", back_populates="user", cascade="all, delete-orphan")


# Database indexes for performance
from sqlalchemy import Index

# Port pool indexes
Index("idx_port_pool_allocated", PortPool.is_allocated)
Index("idx_port_pool_user", PortPool.allocated_to_user_id)
Index("idx_port_pool_activity", PortPool.last_activity)

# Dedicated streams indexes
Index("idx_dedicated_streams_user", DedicatedStream.user_id)
Index("idx_dedicated_streams_status", DedicatedStream.status)
Index("idx_dedicated_streams_live", DedicatedStream.is_live)
Index("idx_dedicated_streams_port", DedicatedStream.port)

# Stream sessions indexes
Index("idx_stream_sessions_stream", StreamSession.stream_id)
Index("idx_stream_sessions_started", StreamSession.started_at)
Index("idx_stream_sessions_duration", StreamSession.duration_seconds)

# Stream monitoring indexes
Index("idx_stream_monitoring_stream", StreamMonitoring.stream_id)
Index("idx_stream_monitoring_recorded", StreamMonitoring.recorded_at)
Index("idx_stream_monitoring_live", StreamMonitoring.is_live)

# Shoutcast servers indexes
Index("idx_shoutcast_servers_active", ShoutcastServer.is_active)
Index("idx_shoutcast_servers_primary", ShoutcastServer.is_primary)
Index("idx_shoutcast_servers_hostname", ShoutcastServer.hostname)