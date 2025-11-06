"""
Station Management Router
Station CRUD operations and file uploads matching Django API
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from ..database import get_db
from ..auth.dependencies import get_current_active_user
from ..auth.models import User
from ..core.exceptions import http_404_not_found, http_400_bad_request
from ..utils.file_handler import save_upload_file, delete_file, get_file_url
from .models import Station
from .schemas import (
    StationCreate, StationUpdate, StationResponse, SocialLinksUpdate,
    StationApiResponse, FileUploadResponse, StationStatsUpdate
)

router = APIRouter(prefix="/api/v1/stations", tags=["Stations"])


@router.get("/", response_model=StationResponse)
async def get_station(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's station (create if doesn't exist)
    """
    # Try to get existing station
    result = await db.execute(select(Station).where(Station.user_id == current_user.id))
    station = result.scalar_one_or_none()
    
    # Create station if doesn't exist
    if not station:
        station = Station(
            user_id=current_user.id,
            name=f"{current_user.display_name}'s Radio Station",
            description="My awesome radio station",
            genre="mixed"
        )
        db.add(station)
        await db.commit()
        await db.refresh(station)
    
    return StationResponse.from_orm(station)


@router.put("/", response_model=StationApiResponse)
async def update_station(
    station_update: StationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's station
    """
    # Get station
    result = await db.execute(select(Station).where(Station.user_id == current_user.id))
    station = result.scalar_one_or_none()
    
    if not station:
        raise http_404_not_found("Station not found")
    
    # Update fields
    if station_update.name is not None:
        station.name = station_update.name
    if station_update.description is not None:
        station.description = station_update.description
    if station_update.genre is not None:
        station.genre = station_update.genre
    if station_update.is_public is not None:
        station.is_public = station_update.is_public
    if station_update.allow_chat is not None:
        station.allow_chat = station_update.allow_chat
    if station_update.auto_record is not None:
        station.auto_record = station_update.auto_record
    if station_update.max_bitrate is not None:
        station.max_bitrate = station_update.max_bitrate
    
    await db.commit()
    await db.refresh(station)
    
    return StationApiResponse(
        success=True,
        message="Station updated successfully",
        station=StationResponse.from_orm(station)
    )


@router.put("/social-links/", response_model=dict)
async def update_social_links(
    social_links: SocialLinksUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update station social media links
    """
    # Get station
    result = await db.execute(select(Station).where(Station.user_id == current_user.id))
    station = result.scalar_one_or_none()
    
    if not station:
        raise http_404_not_found("Station not found")
    
    # Update social links
    if social_links.youtube_url is not None:
        station.youtube_url = social_links.youtube_url
    if social_links.twitch_url is not None:
        station.twitch_url = social_links.twitch_url
    if social_links.facebook_url is not None:
        station.facebook_url = social_links.facebook_url
    if social_links.instagram_url is not None:
        station.instagram_url = social_links.instagram_url
    if social_links.twitter_url is not None:
        station.twitter_url = social_links.twitter_url
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Social links updated successfully",
        "social_links": station.social_links
    }


@router.post("/upload-logo/", response_model=FileUploadResponse)
async def upload_logo(
    logo: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload station logo
    """
    # Get station
    result = await db.execute(select(Station).where(Station.user_id == current_user.id))
    station = result.scalar_one_or_none()
    
    if not station:
        raise http_404_not_found("Station not found")
    
    # Delete old logo if exists
    if station.logo:
        delete_file(station.logo)
    
    # Save new logo
    try:
        file_path = await save_upload_file(logo, "logos")
        station.logo = file_path
        await db.commit()
        
        return FileUploadResponse(
            success=True,
            message="Logo uploaded successfully",
            file_url=get_file_url(file_path)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise http_400_bad_request(f"Failed to upload logo: {str(e)}")


@router.post("/upload-cover/", response_model=FileUploadResponse)
async def upload_cover(
    cover: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload station cover image
    """
    # Get station
    result = await db.execute(select(Station).where(Station.user_id == current_user.id))
    station = result.scalar_one_or_none()
    
    if not station:
        raise http_404_not_found("Station not found")
    
    # Delete old cover if exists
    if station.cover_image:
        delete_file(station.cover_image)
    
    # Save new cover
    try:
        file_path = await save_upload_file(cover, "covers")
        station.cover_image = file_path
        await db.commit()
        
        return FileUploadResponse(
            success=True,
            message="Cover image uploaded successfully",
            file_url=get_file_url(file_path)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise http_400_bad_request(f"Failed to upload cover: {str(e)}")


@router.post("/update-stats/", response_model=dict)
async def update_station_stats(
    stats: StationStatsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update station statistics (for streaming integrations)
    """
    # Get station
    result = await db.execute(select(Station).where(Station.user_id == current_user.id))
    station = result.scalar_one_or_none()
    
    if not station:
        raise http_404_not_found("Station not found")
    
    # Update stats
    station.update_stream_stats(stats.listeners, stats.duration_minutes)
    await db.commit()
    
    return {
        "success": True,
        "message": "Station statistics updated successfully",
        "stats": {
            "total_listeners": station.total_listeners,
            "peak_listeners": station.peak_listeners,
            "total_hours": station.total_hours
        }
    }