"""
OneStopRadio Dynamic Stream Models
Extended models for dynamic stream provisioning and management
"""

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, Float, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import enum

from .database import Base


class StreamStatus(str, enum.Enum):
    """Stream lifecycle status"""
    PENDING = "pending"           # Configuration created, not yet provisioned
    READY = "ready"              # Provisioned and ready to accept connections
    ACTIVE = "active"            # Currently streaming
    INACTIVE = "inactive"        # Temporarily stopped
    ERROR = "error"              # Error state
    SUSPENDED = "suspended"      # Administratively suspended  
    DELETED = "deleted"          # Marked for deletion


class StreamQuality(str, enum.Enum):
    """Stream quality presets"""
    LOW = "low"          # 64 kbps
    STANDARD = "standard" # 128 kbps  
    HIGH = "high"        # 192 kbps
    PREMIUM = "premium"   # 320 kbps


class UserStream(Base):
    """Dynamic user stream configuration"""
    __tablename__ = "user_streams"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stream_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Mount point configuration (must be unique)
    mount_point: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    source_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Stream metadata
    server_name: Mapped[str] = mapped_column(String(255), nullable=False)
    server_description: Mapped[Optional[str]] = mapped_column(Text)
    genre: Mapped[Optional[str]] = mapped_column(String(100))
    server_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Technical configuration
    bitrate: Mapped[int] = mapped_column(Integer, default=128, nullable=False)
    max_listeners: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    quality: Mapped[StreamQuality] = mapped_column(Enum(StreamQuality), default=StreamQuality.STANDARD)
    format: Mapped[str] = mapped_column(String(10), default="mp3", nullable=False)
    
    # Visibility & access control
    public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Stream lifecycle
    status: Mapped[StreamStatus] = mapped_column(Enum(StreamStatus), default=StreamStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Advanced configuration (JSON for flexibility)
    icecast_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    metadata_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Usage statistics
    total_connections: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bytes_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_uptime_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Foreign keys
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    template_id: Mapped[Optional[str]] = mapped_column(ForeignKey("stream_templates.id"))
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    template: Mapped[Optional["StreamTemplate"]] = relationship("StreamTemplate")
    analytics: Mapped[List["StreamAnalytics"]] = relationship("StreamAnalytics", back_populates="stream", cascade="all, delete-orphan")
    connections: Mapped[List["StreamConnection"]] = relationship("StreamConnection", back_populates="stream", cascade="all, delete-orphan")


class StreamTemplate(Base):
    """Predefined stream configuration templates"""
    __tablename__ = "stream_templates"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Template configuration
    default_bitrate: Mapped[int] = mapped_column(Integer, nullable=False)
    default_max_listeners: Mapped[int] = mapped_column(Integer, nullable=False)
    quality: Mapped[StreamQuality] = mapped_column(Enum(StreamQuality), nullable=False)
    format: Mapped[str] = mapped_column(String(10), default="mp3", nullable=False)
    
    # Icecast configuration template
    config_template: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Template metadata
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class MountPoint(Base):
    """Mount point registry to prevent conflicts"""
    __tablename__ = "mount_points"
    
    # Primary identification (the mount point itself)
    mount_point: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # Reservation details
    stream_id: Mapped[Optional[str]] = mapped_column(ForeignKey("user_streams.id"))
    status: Mapped[str] = mapped_column(String(20), default="available", nullable=False)  # available, reserved, active
    reserved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reserved_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    
    # Metadata
    is_system_reserved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    stream: Mapped[Optional["UserStream"]] = relationship("UserStream")
    reserved_by_user: Mapped[Optional["User"]] = relationship("User")


class StreamAnalytics(Base):
    """Real-time and historical stream analytics"""
    __tablename__ = "stream_analytics"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time-series data
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    # Listener metrics
    current_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    peak_listeners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Bandwidth metrics
    bytes_sent_delta: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Since last measurement
    total_bytes_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bandwidth_kbps: Mapped[Optional[float]] = mapped_column(Float)
    
    # Performance metrics
    uptime_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Float)
    memory_usage_mb: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Quality metrics
    buffer_health: Mapped[Optional[float]] = mapped_column(Float)  # 0.0 to 1.0
    dropped_frames: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reconnection_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Geographic data (aggregated)
    listener_countries: Mapped[Optional[Dict[str, int]]] = mapped_column(JSON)
    
    # Foreign keys
    stream_id: Mapped[str] = mapped_column(ForeignKey("user_streams.id"), nullable=False)
    
    # Relationships
    stream: Mapped["UserStream"] = relationship("UserStream", back_populates="analytics")


class StreamConnection(Base):
    """Individual stream connection tracking"""
    __tablename__ = "stream_connections"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Connection details
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    disconnected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Client information
    client_ip: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    client_id: Mapped[Optional[str]] = mapped_column(String(255))  # For tracking return listeners
    
    # Geographic data
    country: Mapped[Optional[str]] = mapped_column(String(2))  # ISO country code
    city: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Technical details
    bytes_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    connection_type: Mapped[str] = mapped_column(String(20), default="listener", nullable=False)  # listener, source, relay
    
    # Disconnect reason
    disconnect_reason: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Foreign keys
    stream_id: Mapped[str] = mapped_column(ForeignKey("user_streams.id"), nullable=False)
    
    # Relationships
    stream: Mapped["UserStream"] = relationship("UserStream", back_populates="connections")


class StreamEvent(Base):
    """Stream lifecycle and operational events"""
    __tablename__ = "stream_events"
    
    # Primary identification
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timing
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    # Severity (for filtering/alerting)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)  # debug, info, warning, error, critical
    
    # Source information
    source_service: Mapped[Optional[str]] = mapped_column(String(50))  # fastapi, cpp-controller, icecast
    source_ip: Mapped[Optional[str]] = mapped_column(String(45))
    
    # Foreign keys
    stream_id: Mapped[Optional[str]] = mapped_column(ForeignKey("user_streams.id"))
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    stream: Mapped[Optional["UserStream"]] = relationship("UserStream")
    user: Mapped[Optional["User"]] = relationship("User")


# Performance indexes
from sqlalchemy import Index

# UserStream indexes
Index("idx_user_streams_mount_point", UserStream.mount_point, unique=True)
Index("idx_user_streams_user_status", UserStream.user_id, UserStream.status)
Index("idx_user_streams_status", UserStream.status)
Index("idx_user_streams_created", UserStream.created_at)
Index("idx_user_streams_quality", UserStream.quality)

# StreamTemplate indexes  
Index("idx_stream_templates_active", StreamTemplate.is_active, StreamTemplate.sort_order)
Index("idx_stream_templates_premium", StreamTemplate.is_premium)

# MountPoint indexes
Index("idx_mount_points_status", MountPoint.status)
Index("idx_mount_points_reserved_by", MountPoint.reserved_by)

# StreamAnalytics indexes (for time-series queries)
Index("idx_stream_analytics_stream_time", StreamAnalytics.stream_id, StreamAnalytics.timestamp)
Index("idx_stream_analytics_timestamp", StreamAnalytics.timestamp)

# StreamConnection indexes
Index("idx_stream_connections_stream_connected", StreamConnection.stream_id, StreamConnection.connected_at)
Index("idx_stream_connections_client_ip", StreamConnection.client_ip)
Index("idx_stream_connections_country", StreamConnection.country)

# StreamEvent indexes
Index("idx_stream_events_stream_type_time", StreamEvent.stream_id, StreamEvent.event_type, StreamEvent.timestamp)
Index("idx_stream_events_user_time", StreamEvent.user_id, StreamEvent.timestamp)
Index("idx_stream_events_severity_time", StreamEvent.severity, StreamEvent.timestamp)
Index("idx_stream_events_type", StreamEvent.event_type)