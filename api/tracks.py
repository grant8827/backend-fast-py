from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional
import os
import json
from datetime import datetime

from ..database import get_db
from ..models.track import Track
from ..schemas.track import (
    TrackResponse, 
    TrackCreate, 
    TrackUpdate, 
    TrackSearchQuery, 
    TrackSearchResponse,
    DeckLoadCommand,
    TrackCompatibility,
    TrackAnalysisStatus
)

router = APIRouter(prefix="/api/tracks", tags=["tracks"])

@router.get("/", response_model=TrackSearchResponse)
async def get_tracks(
    query: Optional[str] = Query(None, description="Search text"),
    artist: Optional[str] = Query(None, description="Filter by artist"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    year_min: Optional[int] = Query(None, description="Minimum year"),
    year_max: Optional[int] = Query(None, description="Maximum year"),
    bpm_min: Optional[float] = Query(None, description="Minimum BPM"),
    bpm_max: Optional[float] = Query(None, description="Maximum BPM"),
    duration_min: Optional[float] = Query(None, description="Minimum duration"),
    duration_max: Optional[float] = Query(None, description="Maximum duration"),
    rating_min: Optional[int] = Query(None, description="Minimum rating"),
    analyzed_only: Optional[bool] = Query(False, description="Only analyzed tracks"),
    sort_by: Optional[str] = Query("title", description="Sort field"),
    sort_order: Optional[str] = Query("asc", description="Sort order"),
    limit: int = Query(50, ge=1, le=500, description="Results per page"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: Session = Depends(get_db)
):
    """
    Get tracks with search, filtering, and pagination.
    
    Supports full-text search across title, artist, and album.
    Provides filtering by various metadata fields.
    """
    
    # Start with base query
    base_query = db.query(Track)
    
    # Apply filters
    filters = []
    
    # Text search across multiple fields
    if query:
        search_filter = or_(
            Track.title.ilike(f"%{query}%"),
            Track.artist.ilike(f"%{query}%"),
            Track.album.ilike(f"%{query}%")
        )
        filters.append(search_filter)
    
    # Specific field filters
    if artist:
        filters.append(Track.artist.ilike(f"%{artist}%"))
    
    if genre:
        filters.append(Track.genre.ilike(f"%{genre}%"))
    
    if year_min:
        filters.append(Track.year >= year_min)
    
    if year_max:
        filters.append(Track.year <= year_max)
    
    if bpm_min:
        filters.append(Track.bpm >= bpm_min)
    
    if bpm_max:
        filters.append(Track.bpm <= bpm_max)
    
    if duration_min:
        filters.append(Track.duration >= duration_min)
    
    if duration_max:
        filters.append(Track.duration <= duration_max)
    
    if rating_min:
        filters.append(Track.rating >= rating_min)
    
    if analyzed_only:
        filters.append(Track.analyzed == True)
    
    # Apply all filters
    if filters:
        base_query = base_query.filter(and_(*filters))
    
    # Get total count before pagination
    total = base_query.count()
    
    # Apply sorting
    sort_column = getattr(Track, sort_by, Track.title)
    if sort_order == "desc":
        base_query = base_query.order_by(desc(sort_column))
    else:
        base_query = base_query.order_by(asc(sort_column))
    
    # Apply pagination
    tracks = base_query.offset(offset).limit(limit).all()
    
    # Convert to response format
    track_responses = [TrackResponse.from_orm(track) for track in tracks]
    
    return TrackSearchResponse(
        tracks=track_responses,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total
    )

@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(track_id: int, db: Session = Depends(get_db)):
    """Get a specific track by ID."""
    
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    return TrackResponse.from_orm(track)

@router.post("/", response_model=TrackResponse)
async def create_track(track_data: TrackCreate, db: Session = Depends(get_db)):
    """Create a new track entry."""
    
    # Check if file path already exists
    existing_track = db.query(Track).filter(Track.file_path == track_data.file_path).first()
    if existing_track:
        raise HTTPException(status_code=400, detail="Track with this file path already exists")
    
    # Check if file actually exists
    if not os.path.exists(track_data.file_path):
        raise HTTPException(status_code=400, detail="Audio file not found at specified path")
    
    # Create new track
    track = Track(**track_data.dict())
    db.add(track)
    db.commit()
    db.refresh(track)
    
    return TrackResponse.from_orm(track)

@router.put("/{track_id}", response_model=TrackResponse)
async def update_track(
    track_id: int, 
    track_data: TrackUpdate, 
    db: Session = Depends(get_db)
):
    """Update track metadata."""
    
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Update only provided fields
    update_data = track_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(track, field, value)
    
    track.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(track)
    
    return TrackResponse.from_orm(track)

@router.delete("/{track_id}")
async def delete_track(track_id: int, db: Session = Depends(get_db)):
    """Delete a track entry."""
    
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    db.delete(track)
    db.commit()
    
    return {"message": "Track deleted successfully"}

@router.post("/{track_id}/play")
async def mark_track_played(track_id: int, db: Session = Depends(get_db)):
    """Mark track as played and update statistics."""
    
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    track.last_played = datetime.utcnow()
    track.play_count += 1
    db.commit()
    
    return {"message": "Play count updated", "play_count": track.play_count}

@router.get("/{track_id}/compatibility/{reference_bpm}")
async def check_track_compatibility(
    track_id: int, 
    reference_bpm: float, 
    db: Session = Depends(get_db)
):
    """Check if track is compatible for mixing with reference BPM."""
    
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if not track.bpm:
        return TrackCompatibility(
            track_id=track_id,
            compatible=False,
            bpm_difference=None,
            harmonic_match=None
        )
    
    compatible = track.is_compatible_bpm(reference_bpm)
    bpm_difference = abs(track.bpm - reference_bpm) if track.bpm else None
    
    # Check for harmonic mixing (double/half time)
    harmonic_match = False
    if track.bpm:
        if abs(track.bpm - reference_bpm * 2) <= 5.0 or abs(track.bpm * 2 - reference_bpm) <= 5.0:
            harmonic_match = True
    
    return TrackCompatibility(
        track_id=track_id,
        compatible=compatible,
        bpm_difference=bpm_difference,
        harmonic_match=harmonic_match
    )

@router.get("/{track_id}/analysis-status")
async def get_track_analysis_status(track_id: int, db: Session = Depends(get_db)):
    """Get track analysis status and waveform availability."""
    
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    waveform_available = False
    if track.waveform_path and os.path.exists(track.waveform_path):
        waveform_available = True
    
    return TrackAnalysisStatus(
        track_id=track_id,
        analyzed=track.analyzed,
        waveform_available=waveform_available
    )

@router.get("/{track_id}/waveform")
async def get_track_waveform(track_id: int, db: Session = Depends(get_db)):
    """Get track waveform data for visualization."""
    
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if not track.waveform_path or not os.path.exists(track.waveform_path):
        raise HTTPException(status_code=404, detail="Waveform data not available")
    
    try:
        with open(track.waveform_path, 'r') as f:
            waveform_data = json.load(f)
        return waveform_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load waveform data: {str(e)}")

@router.post("/scan-directory")
async def scan_music_directory(
    directory_path: str,
    background_tasks: BackgroundTasks,
    recursive: bool = Query(True, description="Scan subdirectories recursively"),
    db: Session = Depends(get_db)
):
    """Scan a directory for audio files and add them to the library."""
    
    if not os.path.exists(directory_path):
        raise HTTPException(status_code=400, detail="Directory not found")
    
    if not os.path.isdir(directory_path):
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    # Queue background task for scanning
    background_tasks.add_task(scan_directory_for_tracks, directory_path, recursive, db)
    
    return {"message": "Directory scan started", "directory": directory_path}

async def scan_directory_for_tracks(directory_path: str, recursive: bool, db: Session):
    """Background task to scan directory for audio files."""
    
    audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.aiff', '.au'}
    
    def scan_path(path):
        tracks_added = 0
        
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                
                if os.path.isfile(item_path):
                    # Check if it's an audio file
                    _, ext = os.path.splitext(item_path.lower())
                    if ext in audio_extensions:
                        # Check if already in database
                        existing = db.query(Track).filter(Track.file_path == item_path).first()
                        if not existing:
                            # Extract basic metadata from filename
                            filename = os.path.splitext(os.path.basename(item_path))[0]
                            
                            # Try to parse "Artist - Title" format
                            if ' - ' in filename:
                                artist, title = filename.split(' - ', 1)
                            else:
                                artist = "Unknown Artist"
                                title = filename
                            
                            # Get file stats
                            file_stats = os.stat(item_path)
                            file_size = file_stats.st_size
                            
                            # Create track entry
                            track = Track(
                                title=title.strip(),
                                artist=artist.strip(),
                                file_path=item_path,
                                file_size=file_size,
                                file_format=ext.lstrip('.'),
                                imported_at=datetime.utcnow()
                            )
                            
                            db.add(track)
                            tracks_added += 1
                
                elif os.path.isdir(item_path) and recursive:
                    tracks_added += scan_path(item_path)
                    
        except Exception as e:
            print(f"Error scanning {path}: {e}")
        
        return tracks_added
    
    total_added = scan_path(directory_path)
    db.commit()
    
    print(f"Scan complete. Added {total_added} tracks from {directory_path}")
    return total_added