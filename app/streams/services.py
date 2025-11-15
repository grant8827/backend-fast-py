"""
Stream Management Services
Business logic for dynamic stream provisioning and management
"""

import httpx
import secrets
import string
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import re
import logging

from ..stream_models import UserStream, MountPoint, StreamEvent, StreamStatus
from .schemas import StreamConfigValidation

logger = logging.getLogger(__name__)


class StreamService:
    """Core stream management business logic"""
    
    @staticmethod
    def validate_stream_limits(user_id: str, db: Session) -> bool:
        """Check if user can create additional streams"""
        
        active_streams = db.query(UserStream).filter(
            UserStream.user_id == user_id,
            UserStream.status.in_([StreamStatus.READY, StreamStatus.ACTIVE, StreamStatus.PENDING])
        ).count()
        
        # TODO: Make configurable per user plan/subscription
        MAX_STREAMS = 5
        return active_streams < MAX_STREAMS
    
    @staticmethod
    def calculate_estimated_costs(bitrate: int, max_listeners: int) -> Dict[str, float]:
        """Calculate estimated monthly costs for stream configuration"""
        
        # Base cost calculation (example pricing)
        # TODO: Make configurable based on actual hosting costs
        
        base_cost = 5.0  # Base monthly cost
        bitrate_multiplier = bitrate / 128.0  # Cost scales with quality
        listener_cost = max_listeners * 0.10  # Cost per potential listener
        
        monthly_cost = base_cost * bitrate_multiplier + listener_cost
        
        # Bandwidth estimation (very rough)
        # Assumes 50% average listener capacity, 12 hours/day streaming
        avg_listeners = max_listeners * 0.5
        hours_per_month = 12 * 30  # 12 hours/day * 30 days
        bandwidth_gb = (bitrate * 1000 / 8) * avg_listeners * hours_per_month * 3600 / (1024**3)
        
        return {
            "monthly_cost_usd": round(monthly_cost, 2),
            "estimated_bandwidth_gb": round(bandwidth_gb, 2),
            "cost_breakdown": {
                "base_cost": base_cost,
                "quality_multiplier": bitrate_multiplier,
                "listener_capacity_cost": listener_cost
            }
        }


class CppControllerService:
    """Interface to C++ Stream Controller microservice"""
    
    def __init__(self):
        # Updated to use new C++ Stream Controller API port
        self.base_url = "http://localhost:8083"  # C++ Stream Controller port
        self.timeout = 10.0
    
    async def create_mount_point(self, stream_config: Dict[str, Any]) -> bool:
        """Create mount point on Icecast server via C++ service"""
        
        try:
            # Convert FastAPI config to C++ format
            cpp_config = self._convert_to_cpp_config(stream_config)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/streams",
                    json=cpp_config
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("success", False)
                return False
            
        except Exception as e:
            logger.error(f"Failed to create mount point: {e}")
            return False
    
    async def activate_stream(self, stream_id: str) -> bool:
        """Activate stream on C++ service"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/streams/{stream_id}/activate"
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("success", False)
                return False
            
        except Exception as e:
            logger.error(f"Failed to activate stream {stream_id}: {e}")
            return False
    
    async def deactivate_stream(self, stream_id: str) -> bool:
        """Deactivate stream on C++ service"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/streams/{stream_id}/deactivate"
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("success", False)
                return False
            
        except Exception as e:
            logger.error(f"Failed to deactivate stream {stream_id}: {e}")
            return False
    
    async def update_stream_config(self, stream_id: str, config: Dict[str, Any]) -> bool:
        """Update stream configuration on C++ service"""
        
        try:
            cpp_config = self._convert_to_cpp_config(config)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    f"{self.base_url}/api/v1/streams/{stream_id}",
                    json=cpp_config
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("success", False)
                return False
            
        except Exception as e:
            logger.error(f"Failed to update stream config {stream_id}: {e}")
            return False
    
    async def get_stream_status(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get live stream status from C++ service"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/streams/{stream_id}/status"
                )
                
                if response.status_code == 200:
                    cpp_status = response.json()
                    return self._convert_from_cpp_status(cpp_status)
                return None
            
        except Exception as e:
            logger.error(f"Failed to get stream status {stream_id}: {e}")
            return None
    
    async def delete_mount_point(self, stream_id: str) -> bool:
        """Delete mount point from C++ service"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/v1/streams/{stream_id}"
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("success", False)
                return False
            
        except Exception as e:
            logger.error(f"Failed to delete mount point {stream_id}: {e}")
            return False
    
    async def reload_server_config(self) -> bool:
        """Trigger Icecast server configuration reload"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/reload"
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("success", False)
                return False
            
        except Exception as e:
            logger.error(f"Failed to reload server config: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if C++ Stream Controller is healthy"""
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    return health_data.get("healthy", False)
                return False
            
        except Exception as e:
            logger.error(f"C++ service health check failed: {e}")
            return False
    
    def _convert_to_cpp_config(self, fastapi_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert FastAPI stream config to C++ service format"""
        return {
            "stream_id": fastapi_config.get("stream_id", ""),
            "user_id": fastapi_config.get("user_id", ""),
            "mount_point": fastapi_config.get("mount_point", ""),
            "source_password": fastapi_config.get("source_password", ""),
            "station_name": fastapi_config.get("station_name", ""),
            "description": fastapi_config.get("description", ""),
            "genre": fastapi_config.get("genre", "Various"),
            "quality": int(fastapi_config.get("bitrate", 128)),
            "max_listeners": int(fastapi_config.get("max_listeners", 100)),
            "server_host": fastapi_config.get("server_host", "localhost"),
            "server_port": int(fastapi_config.get("server_port", 8000)),
            "protocol": fastapi_config.get("protocol", "icecast"),
            "format": fastapi_config.get("format", "MP3"),
            "public_stream": fastapi_config.get("public_stream", True)
        }
    
    def _convert_from_cpp_status(self, cpp_status: Dict[str, Any]) -> Dict[str, Any]:
        """Convert C++ service status to FastAPI format"""
        # Map C++ status codes to FastAPI status names
        status_map = {
            0: "PENDING",
            1: "READY", 
            2: "ACTIVE",
            3: "INACTIVE",
            4: "ERROR",
            5: "SUSPENDED",
            6: "DELETED"
        }
        
        status_code = cpp_status.get("status", 4)
        
        return {
            "stream_id": cpp_status.get("stream_id", ""),
            "status": status_map.get(status_code, "ERROR"),
            "is_connected": cpp_status.get("is_connected", False),
            "current_listeners": cpp_status.get("current_listeners", 0),
            "peak_listeners": cpp_status.get("peak_listeners", 0),
            "bytes_sent": cpp_status.get("bytes_sent", 0),
            "uptime_seconds": cpp_status.get("uptime_seconds", 0.0),
            "error_message": cpp_status.get("error_message", ""),
            "last_update": cpp_status.get("last_update")
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class NotificationService:
    """Service for sending stream-related notifications"""
    
    @staticmethod
    async def notify_stream_status_change(
        stream_id: str, 
        old_status: StreamStatus, 
        new_status: StreamStatus,
        user_id: str
    ):
        """Send notification about stream status change"""
        
        # TODO: Integrate with WebSocket service for real-time notifications
        # TODO: Send email/SMS notifications for critical events
        
        notifications = {
            StreamStatus.READY: "Stream is ready for connection",
            StreamStatus.ACTIVE: "Stream is now live!",
            StreamStatus.INACTIVE: "Stream has gone offline",
            StreamStatus.ERROR: "Stream encountered an error",
            StreamStatus.SUSPENDED: "Stream has been suspended"
        }
        
        message = notifications.get(new_status, f"Stream status changed to {new_status}")
        
        logger.info(f"Stream {stream_id} status changed: {old_status} -> {new_status}")
        
        # Here you would integrate with:
        # - WebSocket service for real-time dashboard updates
        # - Email service for important notifications
        # - SMS service for critical alerts
        # - Push notification service for mobile apps
    
    @staticmethod
    async def notify_stream_error(stream_id: str, error_message: str, user_id: str):
        """Send error notification"""
        
        logger.error(f"Stream {stream_id} error: {error_message}")
        
        # TODO: Send immediate error notifications
        # - Real-time dashboard alerts
        # - Email for persistent errors
        # - SMS for critical system failures


class AnalyticsService:
    """Service for stream analytics and reporting"""
    
    @staticmethod
    def calculate_listener_statistics(
        stream_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Calculate listener statistics for a date range"""
        
        # TODO: Implement analytics calculations
        # This would query StreamAnalytics and StreamConnection tables
        
        return {
            "total_unique_listeners": 0,
            "peak_concurrent_listeners": 0,
            "average_session_duration": 0,
            "total_bandwidth_gb": 0,
            "geographic_breakdown": {},
            "hourly_patterns": {}
        }
    
    @staticmethod
    def generate_billing_report(user_id: str, month: int, year: int, db: Session) -> Dict[str, Any]:
        """Generate billing report for user streams"""
        
        # TODO: Implement billing calculations
        # Based on actual usage from analytics data
        
        return {
            "user_id": user_id,
            "billing_period": f"{year}-{month:02d}",
            "total_cost": 0.0,
            "breakdown_by_stream": {},
            "bandwidth_usage_gb": 0.0,
            "total_streaming_hours": 0.0
        }