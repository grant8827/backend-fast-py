"""
Music API Router
Handles track and playlist operations
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from typing import List, Optional
import json
import uuid
import os
from datetime import datetime

from ..database import get_db
from ..auth.dependencies import get_current_user_optional
from .models import Track, Playlist, playlist_tracks
from .schemas import (
    TrackCreate, TrackUpdate, Track as TrackSchema,
    PlaylistCreate, PlaylistUpdate, Playlist as PlaylistSchema,
    PlaylistStats, TrackUpload
)
from ..utils.file_handler import save_upload_file
from ..config import settings


router = APIRouter(prefix="/api/music", tags=["music"])


# Track endpoints
@router.get("/tracks/", response_model=List[TrackSchema])
async def list_tracks(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    genre: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user_optional)
):
    """List all tracks with optional filtering"""
    query = select(Track)
    
    if user:
        query = query.where(Track.user_id == user.id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Track.title.ilike(search_term)) |
            (Track.artist.ilike(search_term)) |
            (Track.album.ilike(search_term))
        )
    
    if genre:
        query = query.where(Track.genre == genre)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/tracks/", response_model=TrackSchema)
async def create_track(
    track: TrackCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user_optional)
):
    """Create a new track"""
    db_track = Track(
        id=str(uuid.uuid4()),
        **track.dict(),
        user_id=user.id if user else None,
        play_count=0
    )
    
    db.add(db_track)
    await db.commit()
    await db.refresh(db_track)
    return db_track


@router.post("/tracks/upload/", response_model=TrackUpload)
async def upload_track(
    file: UploadFile = File(...),
    title: str = Form(...),
    artist: str = Form(...),
    album: Optional[str] = Form(None),
    genre: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user_optional)
):
    """Upload an audio file and create a track"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Save file
    file_path = await save_upload_file(file, "tracks", "audio")
    file_url = f"/static/tracks/{os.path.basename(file_path)}"
    
    # Create track record
    track_data = TrackCreate(
        title=title,
        artist=artist,
        album=album,
        genre=genre,
        duration=0,  # Would be extracted from audio file in production
        file_path=file_path,
        file_size=file.size if hasattr(file, 'size') else 0
    )
    
    db_track = Track(
        id=str(uuid.uuid4()),
        **track_data.dict(),
        user_id=user.id if user else None,
        play_count=0
    )
    
    db.add(db_track)
    await db.commit()
    await db.refresh(db_track)
    
    return TrackUpload(track=db_track, file_url=file_url)


@router.get("/tracks/{track_id}/", response_model=TrackSchema)
async def get_track(track_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific track"""
    result = await db.execute(select(Track).where(Track.id == track_id))
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    return track


@router.put("/tracks/{track_id}/", response_model=TrackSchema)
async def update_track(
    track_id: str,
    track_update: TrackUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a track"""
    result = await db.execute(select(Track).where(Track.id == track_id))
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    update_data = track_update.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Track).where(Track.id == track_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(track)
    
    return track


@router.delete("/tracks/{track_id}/")
async def delete_track(track_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a track"""
    result = await db.execute(select(Track).where(Track.id == track_id))
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Delete file if it exists
    if track.file_path and os.path.exists(track.file_path):
        os.remove(track.file_path)
    
    await db.execute(delete(Track).where(Track.id == track_id))
    await db.commit()
    
    return {"success": True, "message": "Track deleted"}


# Playlist endpoints
@router.get("/playlists/", response_model=List[PlaylistSchema])
async def list_playlists(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user_optional)
):
    """List all playlists"""
    query = select(Playlist)
    
    if user:
        query = query.where(Playlist.user_id == user.id)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/playlists/", response_model=PlaylistSchema)
async def create_playlist(
    playlist: PlaylistCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user_optional)
):
    """Create a new playlist"""
    db_playlist = Playlist(
        id=str(uuid.uuid4()),
        name=playlist.name,
        is_auto_mix=playlist.is_auto_mix,
        user_id=user.id if user else None
    )
    
    db.add(db_playlist)
    await db.commit()
    
    # Add tracks if provided
    if playlist.track_ids:
        for position, track_id in enumerate(playlist.track_ids):
            await db.execute(
                playlist_tracks.insert().values(
                    playlist_id=db_playlist.id,
                    track_id=track_id,
                    position=position
                )
            )
        await db.commit()
    
    await db.refresh(db_playlist)
    return db_playlist


@router.get("/playlists/{playlist_id}/", response_model=PlaylistSchema)
async def get_playlist(playlist_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific playlist with tracks"""
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    return playlist


@router.put("/playlists/{playlist_id}/", response_model=PlaylistSchema)
async def update_playlist(
    playlist_id: str,
    playlist_update: PlaylistUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a playlist"""
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    update_data = playlist_update.dict(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Playlist).where(Playlist.id == playlist_id).values(**update_data)
        )
        await db.commit()
        await db.refresh(playlist)
    
    return playlist


@router.delete("/playlists/{playlist_id}/")
async def delete_playlist(playlist_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a playlist"""
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    await db.execute(delete(Playlist).where(Playlist.id == playlist_id))
    await db.commit()
    
    return {"success": True, "message": "Playlist deleted"}


@router.post("/playlists/{playlist_id}/tracks/{track_id}/")
async def add_track_to_playlist(
    playlist_id: str,
    track_id: str,
    position: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Add a track to a playlist"""
    # Verify playlist and track exist
    playlist_result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    if not playlist_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    track_result = await db.execute(select(Track).where(Track.id == track_id))
    if not track_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Get current max position if position not provided
    if position is None:
        max_pos_result = await db.execute(
            select(func.max(playlist_tracks.c.position))
            .where(playlist_tracks.c.playlist_id == playlist_id)
        )
        max_position = max_pos_result.scalar() or -1
        position = max_position + 1
    
    # Add track to playlist
    await db.execute(
        playlist_tracks.insert().values(
            playlist_id=playlist_id,
            track_id=track_id,
            position=position
        )
    )
    await db.commit()
    
    return {"success": True, "message": "Track added to playlist"}


@router.delete("/playlists/{playlist_id}/tracks/{track_id}/")
async def remove_track_from_playlist(
    playlist_id: str,
    track_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a track from a playlist"""
    await db.execute(
        delete(playlist_tracks).where(
            (playlist_tracks.c.playlist_id == playlist_id) &
            (playlist_tracks.c.track_id == track_id)
        )
    )
    await db.commit()
    
    return {"success": True, "message": "Track removed from playlist"}


@router.get("/playlists/{playlist_id}/stats/", response_model=PlaylistStats)
async def get_playlist_stats(playlist_id: str, db: AsyncSession = Depends(get_db)):
    """Get playlist statistics"""
    # Get playlist with tracks
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Calculate stats
    stats = PlaylistStats(
        total_tracks=len(playlist.tracks),
        total_duration=sum(track.duration for track in playlist.tracks),
        genres={},
        average_bpm=0.0,
        key_distribution={}
    )
    
    if playlist.tracks:
        # Genre distribution
        for track in playlist.tracks:
            if track.genre:
                stats.genres[track.genre] = stats.genres.get(track.genre, 0) + 1
        
        # Key distribution
        for track in playlist.tracks:
            if track.key:
                stats.key_distribution[track.key] = stats.key_distribution.get(track.key, 0) + 1
        
        # Average BPM
        bpm_tracks = [track for track in playlist.tracks if track.bpm]
        if bpm_tracks:
            stats.average_bpm = sum(track.bpm for track in bpm_tracks) / len(bpm_tracks)
    
    return stats