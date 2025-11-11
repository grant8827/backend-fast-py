"""
Stream Management Package
Dynamic stream provisioning and lifecycle management for OneStopRadio
"""

from .routes import router as streams_router
from .schemas import (
    StreamCreate,
    StreamUpdate,
    StreamResponse,
    StreamStatusResponse,
    StreamTemplateResponse,
    MountPointResponse,
    StreamAnalyticsResponse,
    StreamEventResponse,
    StreamConnectionResponse,
    StreamStatsRequest,
    StreamStatsResponse,
    BulkStreamOperation,
    BulkStreamOperationResponse,
    StreamConfigValidation,
    IcecastConfigTemplate
)
from .services import (
    StreamService,
    CppControllerService,
    NotificationService,
    AnalyticsService
)
from .utils import (
    generate_mount_point,
    generate_source_password,
    validate_stream_config,
    sanitize_mount_point,
    generate_icecast_config,
    validate_mount_point_availability,
    get_recommended_bitrates,
    format_bandwidth_usage,
    calculate_stream_uptime
)

__all__ = [
    # Router
    "streams_router",
    
    # Schemas
    "StreamCreate",
    "StreamUpdate", 
    "StreamResponse",
    "StreamStatusResponse",
    "StreamTemplateResponse",
    "MountPointResponse",
    "StreamAnalyticsResponse",
    "StreamEventResponse",
    "StreamConnectionResponse",
    "StreamStatsRequest",
    "StreamStatsResponse",
    "BulkStreamOperation",
    "BulkStreamOperationResponse",
    "StreamConfigValidation",
    "IcecastConfigTemplate",
    
    # Services
    "StreamService",
    "CppControllerService",
    "NotificationService",
    "AnalyticsService",
    
    # Utilities
    "generate_mount_point",
    "generate_source_password",
    "validate_stream_config",
    "sanitize_mount_point",
    "generate_icecast_config",
    "validate_mount_point_availability",
    "get_recommended_bitrates",
    "format_bandwidth_usage",
    "calculate_stream_uptime"
]