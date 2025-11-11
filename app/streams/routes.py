"""
Stream Management API Routes
Dynamic provisioning and lifecycle management for user streams
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from datetime import datetime
import secrets
import string
import httpx

from ..database import get_db
from ..auth.dependencies import get_current_user
from ..auth.models import User
from ..stream_models import UserStream, StreamTemplate, MountPoint, StreamEvent, StreamStatus
from .schemas import (
    StreamCreate,
    StreamUpdate, 
    StreamResponse,
    StreamStatusResponse,
    StreamTemplateResponse,
    MountPointResponse,
    StreamAnalyticsResponse
)
from .services import StreamService, CppControllerService
from .utils import generate_mount_point, generate_source_password, validate_stream_config

router = APIRouter(prefix="/api/v1/streams", tags=["streams"])


@router.post("/", response_model=StreamResponse, status_code=status.HTTP_201_CREATED)
async def create_stream(
    stream_data: StreamCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new dynamic stream for the authenticated user.
    
    This endpoint:
    1. Validates the stream configuration
    2. Reserves a unique mount point
    3. Generates secure credentials
    4. Stores configuration in database
    5. Triggers background provisioning to C++ service
    """
    
    # Check user's stream limit (business logic)
    user_stream_count = db.query(UserStream).filter(
        UserStream.user_id == current_user.id,
        UserStream.status != StreamStatus.DELETED
    ).count()
    
    # TODO: Make this configurable per user plan
    MAX_STREAMS_PER_USER = 5
    if user_stream_count >= MAX_STREAMS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum streams limit reached ({MAX_STREAMS_PER_USER})"
        )
    
    # Validate stream configuration
    validation_result = validate_stream_config(stream_data)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation_result.errors
        )
    
    # Generate unique mount point
    mount_point = generate_mount_point(stream_data.stream_name, db)
    if not mount_point:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to generate unique mount point. Please try a different stream name."
        )
    
    # Generate secure source password
    source_password = generate_source_password()
    
    # Get template if specified
    template = None
    if stream_data.template_id:
        template = db.query(StreamTemplate).filter(
            StreamTemplate.id == stream_data.template_id,
            StreamTemplate.is_active == True
        ).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stream template not found"
            )
    
    # Create stream record
    new_stream = UserStream(
        user_id=current_user.id,
        stream_name=stream_data.stream_name,
        mount_point=mount_point,
        source_password=source_password,
        server_name=stream_data.server_name,
        server_description=stream_data.server_description,
        genre=stream_data.genre,
        server_url=stream_data.server_url,
        bitrate=stream_data.bitrate or (template.default_bitrate if template else 128),
        max_listeners=stream_data.max_listeners or (template.default_max_listeners if template else 100),
        quality=stream_data.quality,
        format=stream_data.format or "mp3",
        public=stream_data.public,
        requires_auth=stream_data.requires_auth or False,
        template_id=stream_data.template_id,
        icecast_config=template.config_template if template else None,
        status=StreamStatus.PENDING
    )
    
    try:
        db.add(new_stream)
        db.commit()
        db.refresh(new_stream)
        
        # Reserve mount point
        mount_point_record = MountPoint(
            mount_point=mount_point,
            stream_id=new_stream.id,
            status="reserved",
            reserved_at=datetime.utcnow(),
            reserved_by=current_user.id
        )
        db.add(mount_point_record)
        db.commit()
        
        # Log stream creation event
        event = StreamEvent(
            stream_id=new_stream.id,
            user_id=current_user.id,
            event_type="stream_created",
            message=f"Stream '{stream_data.stream_name}' created with mount point {mount_point}",
            severity="info",
            source_service="fastapi"
        )
        db.add(event)
        db.commit()
        
        # Trigger background provisioning
        background_tasks.add_task(
            provision_stream_to_cpp_service,
            new_stream.id,
            db
        )
        
        return StreamResponse.from_orm(new_stream)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create stream: {str(e)}"
        )


@router.get("/", response_model=List[StreamResponse])
async def list_user_streams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[StreamStatus] = None,
    include_deleted: bool = False
):
    """
    List all streams for the authenticated user.
    """
    
    query = db.query(UserStream).filter(UserStream.user_id == current_user.id)
    
    if not include_deleted:
        query = query.filter(UserStream.status != StreamStatus.DELETED)
    
    if status_filter:
        query = query.filter(UserStream.status == status_filter)
    
    streams = query.order_by(UserStream.created_at.desc()).all()
    return [StreamResponse.from_orm(stream) for stream in streams]


@router.get("/{stream_id}", response_model=StreamResponse)
async def get_stream(
    stream_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific stream.
    """
    
    stream = db.query(UserStream).filter(
        UserStream.id == stream_id,
        UserStream.user_id == current_user.id,
        UserStream.status != StreamStatus.DELETED
    ).first()
    
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    return StreamResponse.from_orm(stream)


@router.put("/{stream_id}", response_model=StreamResponse)
async def update_stream(
    stream_id: str,
    stream_update: StreamUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update stream configuration.
    
    Note: Some changes may require stream restart to take effect.
    """
    
    stream = db.query(UserStream).filter(
        UserStream.id == stream_id,
        UserStream.user_id == current_user.id,
        UserStream.status != StreamStatus.DELETED
    ).first()
    
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    # Check if stream is in a state that allows updates
    if stream.status in [StreamStatus.ERROR, StreamStatus.SUSPENDED]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot update stream in {stream.status} status"
        )
    
    # Update fields that were provided
    update_data = stream_update.dict(exclude_unset=True)
    requires_restart = False
    
    # Check if critical settings changed (require restart)
    critical_fields = ['bitrate', 'max_listeners', 'format', 'icecast_config']
    for field in critical_fields:
        if field in update_data and getattr(stream, field) != update_data[field]:
            requires_restart = True
            break
    
    # Apply updates
    for field, value in update_data.items():
        setattr(stream, field, value)
    
    stream.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(stream)
        
        # Log update event
        event = StreamEvent(
            stream_id=stream.id,
            user_id=current_user.id,
            event_type="stream_updated",
            event_data={"updated_fields": list(update_data.keys()), "requires_restart": requires_restart},
            message=f"Stream configuration updated. Restart required: {requires_restart}",
            severity="info",
            source_service="fastapi"
        )
        db.add(event)
        db.commit()
        
        # Trigger background configuration update
        if requires_restart and stream.status == StreamStatus.ACTIVE:
            background_tasks.add_task(
                restart_stream_on_cpp_service,
                stream.id,
                db
            )
        elif stream.status in [StreamStatus.READY, StreamStatus.ACTIVE]:
            background_tasks.add_task(
                update_stream_config_on_cpp_service,
                stream.id,
                db
            )
        
        return StreamResponse.from_orm(stream)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stream: {str(e)}"
        )


@router.post("/{stream_id}/activate", response_model=StreamStatusResponse)
async def activate_stream(
    stream_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Activate a stream (make it available for connection).
    """
    
    stream = db.query(UserStream).filter(
        UserStream.id == stream_id,
        UserStream.user_id == current_user.id,
        UserStream.status != StreamStatus.DELETED
    ).first()
    
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    if stream.status not in [StreamStatus.READY, StreamStatus.INACTIVE]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot activate stream in {stream.status} status"
        )
    
    # Trigger background activation
    background_tasks.add_task(
        activate_stream_on_cpp_service,
        stream.id,
        db
    )
    
    return StreamStatusResponse(
        stream_id=stream.id,
        status=stream.status,
        message="Stream activation initiated"
    )


@router.post("/{stream_id}/deactivate", response_model=StreamStatusResponse)
async def deactivate_stream(
    stream_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deactivate a stream (stop accepting connections).
    """
    
    stream = db.query(UserStream).filter(
        UserStream.id == stream_id,
        UserStream.user_id == current_user.id,
        UserStream.status != StreamStatus.DELETED
    ).first()
    
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    if stream.status not in [StreamStatus.ACTIVE, StreamStatus.READY]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot deactivate stream in {stream.status} status"
        )
    
    # Trigger background deactivation
    background_tasks.add_task(
        deactivate_stream_on_cpp_service,
        stream.id,
        db
    )
    
    return StreamStatusResponse(
        stream_id=stream.id,
        status=stream.status,
        message="Stream deactivation initiated"
    )


@router.delete("/{stream_id}")
async def delete_stream(
    stream_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a stream permanently.
    """
    
    stream = db.query(UserStream).filter(
        UserStream.id == stream_id,
        UserStream.user_id == current_user.id,
        UserStream.status != StreamStatus.DELETED
    ).first()
    
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    # Cannot delete active streams
    if stream.status == StreamStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete active stream. Deactivate first."
        )
    
    # Mark as deleted (soft delete for audit trail)
    stream.status = StreamStatus.DELETED
    stream.updated_at = datetime.utcnow()
    
    # Release mount point
    mount_point = db.query(MountPoint).filter(MountPoint.stream_id == stream.id).first()
    if mount_point:
        mount_point.status = "available"
        mount_point.stream_id = None
    
    try:
        db.commit()
        
        # Log deletion event
        event = StreamEvent(
            stream_id=stream.id,
            user_id=current_user.id,
            event_type="stream_deleted",
            message=f"Stream '{stream.stream_name}' deleted",
            severity="info",
            source_service="fastapi"
        )
        db.add(event)
        db.commit()
        
        # Trigger background cleanup
        background_tasks.add_task(
            cleanup_stream_on_cpp_service,
            stream.id,
            db
        )
        
        return {"message": "Stream deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete stream: {str(e)}"
        )


@router.get("/{stream_id}/status", response_model=StreamStatusResponse)
async def get_stream_status(
    stream_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time stream status from C++ service.
    """
    
    stream = db.query(UserStream).filter(
        UserStream.id == stream_id,
        UserStream.user_id == current_user.id,
        UserStream.status != StreamStatus.DELETED
    ).first()
    
    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    # Query C++ service for live status
    try:
        cpp_service = CppControllerService()
        live_status = await cpp_service.get_stream_status(stream.id)
        
        return StreamStatusResponse(
            stream_id=stream.id,
            status=stream.status,
            message="Status retrieved successfully",
            live_data=live_status
        )
        
    except Exception as e:
        return StreamStatusResponse(
            stream_id=stream.id,
            status=stream.status,
            message=f"Status retrieved from database (C++ service unavailable: {str(e)})"
        )


@router.get("/templates/", response_model=List[StreamTemplateResponse])
async def list_stream_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available stream configuration templates.
    """
    
    templates = db.query(StreamTemplate).filter(
        StreamTemplate.is_active == True
    ).order_by(StreamTemplate.sort_order, StreamTemplate.display_name).all()
    
    return [StreamTemplateResponse.from_orm(template) for template in templates]


@router.get("/available-mounts/", response_model=List[str])
async def get_available_mount_points(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available mount points for new streams.
    """
    
    # Get reserved/active mount points
    taken_mounts = db.query(MountPoint.mount_point).filter(
        MountPoint.status.in_(["reserved", "active"])
    ).all()
    taken_mount_set = {mount[0] for mount in taken_mounts}
    
    # Generate suggestions based on user's stream name patterns
    suggestions = []
    base_suggestions = ["/live", "/radio", "/stream", "/music", "/dj"]
    
    for base in base_suggestions:
        if base not in taken_mount_set:
            suggestions.append(base)
        
        # Add numbered variations
        for i in range(1, 10):
            variant = f"{base}{i}"
            if variant not in taken_mount_set and len(suggestions) < 20:
                suggestions.append(variant)
    
    return suggestions[:10]  # Return top 10 suggestions


# Background task functions
async def provision_stream_to_cpp_service(stream_id: str, db: Session):
    """Background task to provision stream on C++ service"""
    # Implementation for C++ service integration
    pass


async def activate_stream_on_cpp_service(stream_id: str, db: Session):
    """Background task to activate stream on C++ service"""
    # Implementation for C++ service integration
    pass


async def deactivate_stream_on_cpp_service(stream_id: str, db: Session):
    """Background task to deactivate stream on C++ service"""
    # Implementation for C++ service integration
    pass


async def restart_stream_on_cpp_service(stream_id: str, db: Session):
    """Background task to restart stream on C++ service"""
    # Implementation for C++ service integration
    pass


async def update_stream_config_on_cpp_service(stream_id: str, db: Session):
    """Background task to update stream config on C++ service"""
    # Implementation for C++ service integration
    pass


async def cleanup_stream_on_cpp_service(stream_id: str, db: Session):
    """Background task to cleanup stream on C++ service"""
    # Implementation for C++ service integration
    pass