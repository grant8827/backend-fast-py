"""
Pydantic schemas for Stream Management API
Request/Response models for dynamic stream provisioning
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ..stream_models import StreamStatus, StreamQuality


class StreamCreate(BaseModel):
    """Schema for creating a new stream"""
    
    stream_name: str = Field(..., min_length=3, max_length=100, description="Display name for the stream")
    server_name: str = Field(..., min_length=3, max_length=255, description="Server name for Icecast metadata")
    server_description: Optional[str] = Field(None, max_length=500, description="Stream description")
    genre: Optional[str] = Field(None, max_length=100, description="Music genre")
    server_url: Optional[str] = Field(None, max_length=500, description="Associated website URL")
    
    # Technical configuration
    bitrate: Optional[int] = Field(None, ge=32, le=320, description="Stream bitrate in kbps")
    max_listeners: Optional[int] = Field(None, ge=1, le=1000, description="Maximum concurrent listeners")
    quality: StreamQuality = Field(StreamQuality.STANDARD, description="Stream quality preset")
    format: Optional[str] = Field("mp3", pattern=r"^(mp3|aac|ogg)$", description="Audio format")
    
    # Access control
    public: bool = Field(True, description="Whether stream appears in public directory")
    requires_auth: Optional[bool] = Field(False, description="Whether listeners need authentication")
    
    # Template
    template_id: Optional[str] = Field(None, description="Stream configuration template ID")
    
    # Advanced configuration (optional)
    icecast_config: Optional[Dict[str, Any]] = Field(None, description="Custom Icecast configuration")
    
    @field_validator('stream_name')
    @classmethod
    def validate_stream_name(cls, v):
        # Remove special characters for mount point generation
        if not v.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            raise ValueError('Stream name must contain only alphanumeric characters, spaces, hyphens, and underscores')
        return v.strip()
    
    @field_validator('bitrate')
    @classmethod
    def validate_bitrate(cls, v):
        if v is not None:
            # Common bitrate values
            valid_bitrates = [32, 48, 64, 96, 128, 160, 192, 224, 256, 320]
            if v not in valid_bitrates:
                raise ValueError(f'Bitrate must be one of: {valid_bitrates}')
        return v


class StreamUpdate(BaseModel):
    """Schema for updating stream configuration"""
    
    stream_name: Optional[str] = Field(None, min_length=3, max_length=100)
    server_name: Optional[str] = Field(None, min_length=3, max_length=255)
    server_description: Optional[str] = Field(None, max_length=500)
    genre: Optional[str] = Field(None, max_length=100)
    server_url: Optional[str] = Field(None, max_length=500)
    
    # Technical configuration
    bitrate: Optional[int] = Field(None, ge=32, le=320)
    max_listeners: Optional[int] = Field(None, ge=1, le=1000)
    quality: Optional[StreamQuality] = None
    
    # Access control
    public: Optional[bool] = None
    requires_auth: Optional[bool] = None
    
    # Advanced configuration
    icecast_config: Optional[Dict[str, Any]] = None
    metadata_config: Optional[Dict[str, Any]] = None


class StreamResponse(BaseModel):
    """Schema for stream information response"""
    
    # Identifiers
    id: str
    stream_name: str
    mount_point: str
    
    # Configuration
    server_name: str
    server_description: Optional[str]
    genre: Optional[str]
    server_url: Optional[str]
    
    # Technical details
    bitrate: int
    max_listeners: int
    quality: StreamQuality
    format: str
    
    # Access control
    public: bool
    requires_auth: bool
    
    # Status
    status: StreamStatus
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime]
    last_connected_at: Optional[datetime]
    
    # Statistics
    total_connections: int
    total_bytes_sent: int
    total_uptime_seconds: int
    
    # Connection info (for DJ software)
    connection_info: Optional[Dict[str, str]] = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, stream_obj):
        """Create response with connection info"""
        data = super().from_orm(stream_obj)
        
        # Add connection information for DJ software
        if stream_obj.status in [StreamStatus.READY, StreamStatus.ACTIVE]:
            data.connection_info = {
                "server": "your-icecast-server.com",  # TODO: Make configurable
                "port": "8000",
                "mount_point": stream_obj.mount_point,
                "username": "source",
                "password": stream_obj.source_password,  # Only return if user owns stream
                "stream_url": f"http://your-icecast-server.com:8000{stream_obj.mount_point}",
                "admin_url": f"http://your-icecast-server.com:8000/admin/"
            }
        
        return data


class StreamStatusResponse(BaseModel):
    """Schema for stream status information"""
    
    stream_id: str
    status: StreamStatus
    message: str
    live_data: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class StreamTemplateResponse(BaseModel):
    """Schema for stream template information"""
    
    id: str
    name: str
    display_name: str
    description: Optional[str]
    default_bitrate: int
    default_max_listeners: int
    quality: StreamQuality
    format: str
    is_premium: bool
    
    # Template configuration preview
    config_preview: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, template_obj):
        """Create response with config preview"""
        data = super().from_orm(template_obj)
        
        # Add safe config preview (remove sensitive data)
        if template_obj.config_template:
            safe_config = template_obj.config_template.copy()
            # Remove any sensitive keys
            sensitive_keys = ['password', 'secret', 'key', 'token']
            for key in list(safe_config.keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    del safe_config[key]
            data.config_preview = safe_config
        
        return data


class MountPointResponse(BaseModel):
    """Schema for mount point information"""
    
    mount_point: str
    status: str
    stream_id: Optional[str]
    reserved_at: Optional[datetime]
    is_system_reserved: bool
    
    class Config:
        from_attributes = True


class StreamAnalyticsResponse(BaseModel):
    """Schema for stream analytics data"""
    
    stream_id: str
    timestamp: datetime
    current_listeners: int
    peak_listeners: int
    bytes_sent_delta: int
    total_bytes_sent: int
    bandwidth_kbps: Optional[float]
    uptime_seconds: int
    
    # Performance metrics
    cpu_usage_percent: Optional[float]
    memory_usage_mb: Optional[int]
    buffer_health: Optional[float]
    dropped_frames: int
    reconnection_count: int
    
    # Geographic data
    listener_countries: Optional[Dict[str, int]]
    
    class Config:
        from_attributes = True


class StreamEventResponse(BaseModel):
    """Schema for stream event information"""
    
    id: str
    event_type: str
    message: Optional[str]
    timestamp: datetime
    severity: str
    source_service: Optional[str]
    event_data: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class StreamConnectionResponse(BaseModel):
    """Schema for stream connection information"""
    
    id: str
    connected_at: datetime
    disconnected_at: Optional[datetime]
    duration_seconds: Optional[int]
    client_ip: Optional[str]
    user_agent: Optional[str]
    country: Optional[str]
    city: Optional[str]
    bytes_received: int
    connection_type: str
    disconnect_reason: Optional[str]
    
    class Config:
        from_attributes = True


# Analytics and reporting schemas
class StreamStatsRequest(BaseModel):
    """Schema for stream statistics request"""
    
    stream_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    granularity: str = Field("hour", pattern=r"^(minute|hour|day|month)$")
    metrics: List[str] = Field(default=["listeners", "bandwidth"], description="Metrics to include")


class StreamStatsResponse(BaseModel):
    """Schema for stream statistics response"""
    
    stream_id: str
    period_start: datetime
    period_end: datetime
    granularity: str
    
    # Aggregated metrics
    total_listeners: int
    peak_listeners: int
    average_listeners: float
    total_bandwidth_gb: float
    total_uptime_hours: float
    
    # Time series data
    data_points: List[Dict[str, Any]]
    
    # Geographic breakdown
    listener_countries: Dict[str, int]
    top_user_agents: Dict[str, int]


class BulkStreamOperation(BaseModel):
    """Schema for bulk operations on multiple streams"""
    
    stream_ids: List[str] = Field(..., min_items=1, max_items=50)
    operation: str = Field(..., pattern=r"^(activate|deactivate|delete|update)$")
    operation_data: Optional[Dict[str, Any]] = None


class BulkStreamOperationResponse(BaseModel):
    """Schema for bulk operation response"""
    
    operation: str
    total_streams: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, str]]


# Configuration validation schemas
class StreamConfigValidation(BaseModel):
    """Schema for stream configuration validation"""
    
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    estimated_cost: Optional[float] = None  # Monthly cost estimate
    estimated_bandwidth: Optional[float] = None  # GB/month estimate


class IcecastConfigTemplate(BaseModel):
    """Schema for Icecast configuration template"""
    
    # Basic settings
    burst_on_connect: bool = True
    burst_size: int = 65536
    queue_size: int = 524288
    
    # Authentication
    authentication: str = "source"
    
    # Fallback configuration
    fallback_mount: Optional[str] = None
    fallback_when_full: bool = False
    
    # Script hooks
    on_connect: Optional[str] = None
    on_disconnect: Optional[str] = None
    
    # Custom headers
    headers: Optional[Dict[str, str]] = None
    
    # Stream metadata
    charset: str = "UTF-8"
    mp3_metadata: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "burst_on_connect": True,
                "burst_size": 65536,
                "queue_size": 524288,
                "authentication": "source",
                "fallback_mount": "/fallback.mp3",
                "charset": "UTF-8",
                "mp3_metadata": True,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Origin, Accept, X-Requested-With, Content-Type"
                }
            }
        }