"""
Stream Provisioning API Routes
OneStopRadio - Dedicated Shoutcast Stream Management Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import logging

from ..database import get_db
from ..auth.dependencies import get_current_user
from ..models import User
from .service import stream_provisioning_service
from .schemas import (
    StreamProvisionRequest,
    StreamProvisionResponse,
    StreamInfoResponse,
    StreamStatsResponse,
    StreamListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/streams",
    tags=["Stream Provisioning"],
    responses={404: {"description": "Not found"}}
)


@router.post("/provision", response_model=StreamProvisionResponse)
async def provision_dedicated_stream(
    request: StreamProvisionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Provision a new dedicated Shoutcast stream for the authenticated user
    
    This endpoint:
    1. Allocates a unique port from the available pool (8100-8200)
    2. Generates secure source and admin passwords
    3. Updates the Shoutcast server configuration
    4. Returns stream credentials for encoder setup
    """
    try:
        # Provision the stream
        stream = await stream_provisioning_service.provision_stream(
            db=db,
            user_id=str(current_user.id),
            stream_title=request.stream_title,
            stream_description=request.stream_description,
            max_listeners=request.max_listeners,
            bitrate=request.bitrate,
            station_id=request.station_id
        )
        
        if not stream:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to provision stream. No available ports or configuration error."
            )
        
        # Schedule background task to verify stream configuration
        background_tasks.add_task(verify_stream_configuration, stream.id)
        
        return StreamProvisionResponse(
            stream_id=stream.id,
            host_address="stream.yourdjapp.com",  # Your domain
            port=stream.port,
            source_password=stream.source_password,
            admin_password=stream.admin_password,
            stream_url=f"http://stream.yourdjapp.com:{stream.port}",
            max_listeners=stream.max_listeners,
            bitrate=stream.bitrate,
            status=stream.status.value,
            created_at=stream.created_at,
            message="Stream provisioned successfully! You can now configure your encoder software."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to provision stream for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during stream provisioning"
        )


@router.get("/my-stream", response_model=StreamInfoResponse)
async def get_my_stream_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the authenticated user's dedicated stream information and credentials
    """
    try:
        stream = await stream_provisioning_service.get_user_stream(
            db=db,
            user_id=str(current_user.id)
        )
        
        if not stream:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active stream found for this user"
            )
        
        return StreamInfoResponse(
            stream_id=stream.id,
            host_address="stream.yourdjapp.com",
            port=stream.port,
            source_password=stream.source_password,
            admin_password=stream.admin_password,
            stream_url=f"http://stream.yourdjapp.com:{stream.port}",
            stream_title=stream.stream_title,
            stream_description=stream.stream_description,
            max_listeners=stream.max_listeners,
            bitrate=stream.bitrate,
            sample_rate=stream.sample_rate,
            genre=stream.genre,
            status=stream.status.value,
            is_live=stream.is_live,
            current_listeners=stream.current_listeners,
            created_at=stream.created_at,
            activated_at=stream.activated_at,
            last_connection=stream.last_connection
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stream info for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve stream information"
        )


@router.get("/my-stream/stats", response_model=StreamStatsResponse)
async def get_my_stream_stats(
    days: Optional[int] = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive statistics for the user's stream
    """
    try:
        # First get the stream
        stream = await stream_provisioning_service.get_user_stream(
            db=db,
            user_id=str(current_user.id)
        )
        
        if not stream:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active stream found for this user"
            )
        
        # Get statistics
        stats = await stream_provisioning_service.get_stream_stats(
            db=db,
            stream_id=stream.id,
            days=days or 30
        )
        
        return StreamStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stream stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve stream statistics"
        )


@router.post("/my-stream/suspend")
async def suspend_my_stream(
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Temporarily suspend the user's stream
    """
    try:
        stream = await stream_provisioning_service.get_user_stream(
            db=db,
            user_id=str(current_user.id)
        )
        
        if not stream:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active stream found for this user"
            )
        
        success = await stream_provisioning_service.suspend_stream(
            db=db,
            stream_id=stream.id,
            reason=reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to suspend stream"
            )
        
        return {"message": "Stream suspended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suspend stream for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend stream"
        )


@router.post("/my-stream/terminate")
async def terminate_my_stream(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently terminate the user's stream and release resources
    """
    try:
        stream = await stream_provisioning_service.get_user_stream(
            db=db,
            user_id=str(current_user.id)
        )
        
        if not stream:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active stream found for this user"
            )
        
        success = await stream_provisioning_service.terminate_stream(
            db=db,
            stream_id=stream.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to terminate stream"
            )
        
        return {"message": "Stream terminated successfully. Port has been released back to the pool."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to terminate stream for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate stream"
        )


@router.post("/initialize-pool")
async def initialize_port_pool(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize the port pool (Admin only - for initial setup)
    """
    # TODO: Add admin role check
    try:
        success = await stream_provisioning_service.initialize_port_pool(db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize port pool"
            )
        
        return {"message": "Port pool initialized successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize port pool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize port pool"
        )


# Background tasks
async def verify_stream_configuration(stream_id: str):
    """Background task to verify stream configuration"""
    try:
        # Add verification logic here
        # - Test connection to Shoutcast server
        # - Verify port is accessible
        # - Update stream status if needed
        logger.info(f"Verifying configuration for stream {stream_id}")
        
        # Placeholder for verification logic
        
    except Exception as e:
        logger.error(f"Failed to verify stream configuration for {stream_id}: {e}")


# WebSocket endpoint for real-time stream monitoring
@router.websocket("/my-stream/monitor")
async def websocket_stream_monitor(
    websocket,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time stream monitoring
    Sends updates about listener count, stream status, etc.
    """
    await websocket.accept()
    
    try:
        stream = await stream_provisioning_service.get_user_stream(
            db=db,
            user_id=str(current_user.id)
        )
        
        if not stream:
            await websocket.send_json({"error": "No active stream found"})
            await websocket.close()
            return
        
        # Send initial stream status
        await websocket.send_json({
            "type": "status",
            "stream_id": stream.id,
            "is_live": stream.is_live,
            "current_listeners": stream.current_listeners,
            "status": stream.status.value
        })
        
        # Keep connection alive and send periodic updates
        while True:
            # In a real implementation, this would:
            # - Query the Shoutcast server for live data
            # - Send updates when listener count changes
            # - Notify of connection/disconnection events
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
            # Placeholder update
            await websocket.send_json({
                "type": "update",
                "timestamp": datetime.utcnow().isoformat(),
                "current_listeners": stream.current_listeners,
                "is_live": stream.is_live
            })
            
    except Exception as e:
        logger.error(f"WebSocket error for stream monitoring: {e}")
        await websocket.close()