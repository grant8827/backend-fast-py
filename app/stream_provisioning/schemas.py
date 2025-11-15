"""
Stream Provisioning Pydantic Schemas
OneStopRadio - Request/Response models for stream provisioning
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class StreamStatusEnum(str, Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    MAINTENANCE = "maintenance"


class StreamProvisionRequest(BaseModel):
    """Request model for provisioning a new stream"""
    stream_title: str = Field(..., min_length=1, max_length=255, description="Title for the stream")
    stream_description: Optional[str] = Field(None, max_length=1000, description="Optional stream description")
    max_listeners: Optional[int] = Field(100, ge=1, le=1000, description="Maximum concurrent listeners")
    bitrate: Optional[int] = Field(128, ge=64, le=320, description="Audio bitrate in kbps")
    station_id: Optional[str] = Field(None, description="Optional station ID to associate with stream")
    
    @validator('stream_title')
    def validate_stream_title(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Stream title cannot be empty')
        return v.strip()
    
    @validator('bitrate')
    def validate_bitrate(cls, v):
        valid_bitrates = [64, 96, 128, 192, 256, 320]
        if v not in valid_bitrates:
            raise ValueError(f'Bitrate must be one of: {valid_bitrates}')
        return v


class StreamProvisionResponse(BaseModel):
    """Response model for successful stream provisioning"""
    stream_id: str = Field(..., description="Unique stream identifier")
    host_address: str = Field(..., description="Stream server hostname")
    port: int = Field(..., description="Allocated port number")
    source_password: str = Field(..., description="Source encoder password")
    admin_password: str = Field(..., description="Stream admin password")
    stream_url: str = Field(..., description="Complete stream URL for listeners")
    max_listeners: int = Field(..., description="Maximum concurrent listeners")
    bitrate: int = Field(..., description="Stream bitrate in kbps")
    status: str = Field(..., description="Current stream status")
    created_at: datetime = Field(..., description="Stream creation timestamp")
    message: str = Field(..., description="Success message with instructions")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StreamInfoResponse(BaseModel):
    """Response model for stream information"""
    stream_id: str
    host_address: str
    port: int
    source_password: str
    admin_password: str
    stream_url: str
    stream_title: str
    stream_description: Optional[str]
    max_listeners: int
    bitrate: int
    sample_rate: int
    genre: str
    status: str
    is_live: bool
    current_listeners: int
    created_at: datetime
    activated_at: Optional[datetime]
    last_connection: Optional[datetime]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class StreamSessionInfo(BaseModel):
    """Model for individual stream session information"""
    id: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[float]
    peak_listeners: int
    total_data_mb: float
    source_ip: Optional[str]
    encoder_type: Optional[str]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class StreamMonitoringData(BaseModel):
    """Model for stream monitoring data points"""
    recorded_at: datetime
    current_listeners: int
    is_live: bool
    current_bitrate: Optional[int]
    bandwidth_mbps: Optional[float]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StreamStatsResponse(BaseModel):
    """Response model for comprehensive stream statistics"""
    stream_info: Dict[str, Any] = Field(..., description="Basic stream information")
    session_stats: Dict[str, Any] = Field(..., description="Session statistics")
    recent_monitoring: List[StreamMonitoringData] = Field(..., description="Recent monitoring data")


class StreamListResponse(BaseModel):
    """Response model for listing multiple streams"""
    streams: List[StreamInfoResponse]
    total_count: int
    active_count: int
    suspended_count: int


class EncoderSetupGuide(BaseModel):
    """Response model providing encoder setup instructions"""
    stream_id: str
    server_details: Dict[str, str] = Field(..., description="Server connection details")
    encoder_configs: Dict[str, Dict[str, Any]] = Field(..., description="Pre-configured settings for popular encoders")
    troubleshooting: List[str] = Field(..., description="Common troubleshooting tips")


class StreamHealthCheck(BaseModel):
    """Response model for stream health check"""
    stream_id: str
    is_accessible: bool
    response_time_ms: float
    last_checked: datetime
    issues: List[str] = Field(default_factory=list, description="Any detected issues")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PortPoolStatus(BaseModel):
    """Response model for port pool status"""
    total_ports: int
    allocated_ports: int
    available_ports: int
    port_range: str
    allocation_rate: float = Field(..., description="Percentage of ports allocated")


class ShoutcastServerStatus(BaseModel):
    """Response model for Shoutcast server status"""
    server_id: str
    hostname: str
    is_active: bool
    current_streams: int
    max_streams: int
    uptime: str
    version: str
    last_health_check: Optional[datetime]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# WebSocket message models
class WebSocketMessage(BaseModel):
    """Base model for WebSocket messages"""
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StreamStatusUpdate(WebSocketMessage):
    """WebSocket message for stream status updates"""
    type: str = "status_update"
    stream_id: str
    is_live: bool
    current_listeners: int
    status: str


class ListenerUpdate(WebSocketMessage):
    """WebSocket message for listener count updates"""
    type: str = "listener_update"
    stream_id: str
    current_listeners: int
    peak_listeners: int
    change_delta: int = Field(..., description="Change in listener count since last update")


class StreamAlert(WebSocketMessage):
    """WebSocket message for stream alerts"""
    type: str = "alert"
    stream_id: str
    alert_type: str = Field(..., description="Type of alert: connection_lost, high_cpu, etc.")
    message: str
    severity: str = Field(..., description="Alert severity: info, warning, error, critical")


# Admin-only models
class AdminStreamList(BaseModel):
    """Admin response model for listing all streams"""
    streams: List[Dict[str, Any]]
    total_count: int
    active_count: int
    suspended_count: int
    terminated_count: int
    server_utilization: float = Field(..., description="Overall server utilization percentage")


class AdminPortManagement(BaseModel):
    """Admin model for port management operations"""
    action: str = Field(..., description="Action to perform: allocate, release, reserve")
    port: Optional[int] = Field(None, description="Specific port number")
    port_range: Optional[str] = Field(None, description="Port range for bulk operations")
    reason: Optional[str] = Field(None, description="Reason for the action")


class AdminStreamAction(BaseModel):
    """Admin model for stream management actions"""
    action: str = Field(..., description="Action: suspend, terminate, restart")
    stream_ids: List[str] = Field(..., description="List of stream IDs to act on")
    reason: str = Field(..., description="Reason for the action")
    notify_users: bool = Field(True, description="Whether to notify affected users")