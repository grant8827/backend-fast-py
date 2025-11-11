"""
Integration client for C++ Stream Controller Service
Provides Python interface for FastAPI to communicate with C++ microservice
"""

import httpx
import json
import asyncio
from typing import Dict, List, Optional, Any
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)

class StreamStatus(IntEnum):
    """Stream status enum matching C++ service"""
    PENDING = 0
    READY = 1
    ACTIVE = 2
    INACTIVE = 3
    ERROR = 4
    SUSPENDED = 5
    DELETED = 6

class StreamControllerClient:
    """Async HTTP client for C++ Stream Controller Service"""
    
    def __init__(self, base_url: str = "http://localhost:8083", timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if C++ service is healthy and responsive"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def create_stream(self, stream_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new stream mount point"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/streams",
                json=stream_config
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create stream: {e}")
            raise
    
    async def activate_stream(self, stream_id: str) -> Dict[str, Any]:
        """Activate a stream for broadcasting"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/streams/{stream_id}/activate"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to activate stream {stream_id}: {e}")
            raise
    
    async def deactivate_stream(self, stream_id: str) -> Dict[str, Any]:
        """Deactivate a stream"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/streams/{stream_id}/deactivate"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to deactivate stream {stream_id}: {e}")
            raise
    
    async def delete_stream(self, stream_id: str) -> Dict[str, Any]:
        """Delete a stream mount point"""
        try:
            response = await self.client.delete(
                f"{self.base_url}/api/v1/streams/{stream_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to delete stream {stream_id}: {e}")
            raise
    
    async def update_stream(self, stream_id: str, stream_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update stream configuration"""
        try:
            response = await self.client.put(
                f"{self.base_url}/api/v1/streams/{stream_id}",
                json=stream_config
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update stream {stream_id}: {e}")
            raise
    
    async def get_stream_status(self, stream_id: str) -> Dict[str, Any]:
        """Get detailed stream status"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/streams/{stream_id}/status"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get stream status {stream_id}: {e}")
            raise
    
    async def get_all_streams(self) -> Dict[str, Any]:
        """Get status of all streams"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/streams")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get all streams: {e}")
            raise
    
    async def update_metadata(self, stream_id: str, title: str, artist: str = "") -> Dict[str, Any]:
        """Update stream metadata (now playing info)"""
        try:
            metadata = {"title": title}
            if artist:
                metadata["artist"] = artist
                
            response = await self.client.post(
                f"{self.base_url}/api/v1/streams/{stream_id}/metadata",
                json=metadata
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update metadata for stream {stream_id}: {e}")
            raise
    
    async def reload_config(self) -> Dict[str, Any]:
        """Reload Icecast server configuration"""
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/reload")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")
            raise


class StreamControllerError(Exception):
    """Custom exception for Stream Controller errors"""
    pass


def convert_fastapi_to_cpp_config(fastapi_stream: Dict[str, Any]) -> Dict[str, Any]:
    """Convert FastAPI stream configuration to C++ service format"""
    return {
        "stream_id": fastapi_stream["stream_id"],
        "user_id": fastapi_stream["user_id"],
        "mount_point": fastapi_stream["mount_point"],
        "source_password": fastapi_stream["source_password"],
        "station_name": fastapi_stream["station_name"],
        "description": fastapi_stream.get("description", ""),
        "genre": fastapi_stream.get("genre", "Various"),
        "quality": int(fastapi_stream.get("quality", 128)),
        "max_listeners": int(fastapi_stream.get("max_listeners", 100)),
        "server_host": fastapi_stream.get("server_host", "localhost"),
        "server_port": int(fastapi_stream.get("server_port", 8000)),
        "protocol": fastapi_stream.get("protocol", "icecast"),
        "format": fastapi_stream.get("format", "MP3"),
        "public_stream": fastapi_stream.get("public_stream", True)
    }


def convert_cpp_to_fastapi_status(cpp_status: Dict[str, Any]) -> Dict[str, Any]:
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
        "stream_id": cpp_status["stream_id"],
        "status": status_map.get(status_code, "ERROR"),
        "is_connected": cpp_status.get("is_connected", False),
        "current_listeners": cpp_status.get("current_listeners", 0),
        "peak_listeners": cpp_status.get("peak_listeners", 0),
        "bytes_sent": cpp_status.get("bytes_sent", 0),
        "uptime_seconds": cpp_status.get("uptime_seconds", 0.0),
        "error_message": cpp_status.get("error_message", ""),
        "last_update": cpp_status.get("last_update")
    }


# Singleton instance for reuse across FastAPI
_stream_controller_client = None

def get_stream_controller_client(base_url: str = "http://localhost:8083") -> StreamControllerClient:
    """Get singleton StreamControllerClient instance"""
    global _stream_controller_client
    if _stream_controller_client is None:
        _stream_controller_client = StreamControllerClient(base_url)
    return _stream_controller_client


# Example usage and testing functions
async def test_stream_controller_integration():
    """Test integration with C++ Stream Controller Service"""
    async with StreamControllerClient() as client:
        # Health check
        health = await client.health_check()
        print(f"Health check: {health}")
        
        # Create test stream
        test_config = {
            "stream_id": "integration-test-001",
            "user_id": "test-user",
            "mount_point": "/integration-test",
            "source_password": "test123",
            "station_name": "Integration Test Stream",
            "description": "Testing FastAPI <-> C++ integration",
            "genre": "Test",
            "quality": 128,
            "max_listeners": 25,
            "server_host": "localhost",
            "server_port": 8000,
            "protocol": "icecast",
            "format": "MP3",
            "public_stream": true
        }
        
        try:
            # Create
            result = await client.create_stream(test_config)
            print(f"Create result: {result}")
            
            # Activate
            result = await client.activate_stream("integration-test-001")
            print(f"Activate result: {result}")
            
            # Get status
            status = await client.get_stream_status("integration-test-001")
            print(f"Status: {status}")
            
            # Update metadata
            result = await client.update_metadata(
                "integration-test-001", 
                "Test Song", 
                "Test Artist"
            )
            print(f"Metadata update: {result}")
            
            # Deactivate
            result = await client.deactivate_stream("integration-test-001")
            print(f"Deactivate result: {result}")
            
            # Delete
            result = await client.delete_stream("integration-test-001")
            print(f"Delete result: {result}")
            
        except Exception as e:
            print(f"Integration test error: {e}")


if __name__ == "__main__":
    # Run integration test
    asyncio.run(test_stream_controller_integration())