"""
File handling utilities for uploads
"""

import os
import shutil
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import uuid

from ..config import settings


ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'}
MAX_IMAGE_SIZE = (1920, 1080)  # Max dimensions for images
MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100MB for audio files


def validate_image_file(file: UploadFile) -> bool:
    """Validate if uploaded file is a valid image"""
    if not file.filename:
        return False
    
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def validate_audio_file(file: UploadFile) -> bool:
    """Validate if uploaded file is a valid audio file"""
    if not file.filename:
        return False
    
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    return ext in ALLOWED_AUDIO_EXTENSIONS


def validate_file_type(file: UploadFile, file_type: str = "image") -> bool:
    """Validate file based on type"""
    if file_type == "image":
        return validate_image_file(file)
    elif file_type == "audio":
        return validate_audio_file(file)
    else:
        return False


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving extension"""
    ext = os.path.splitext(original_filename)[1].lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{ext}"


async def save_upload_file(file: UploadFile, subfolder: str = "", file_type: str = "image") -> str:
    """
    Save uploaded file to disk and return the file path
    """
    if not validate_file_type(file, file_type):
        allowed = ALLOWED_IMAGE_EXTENSIONS if file_type == "image" else ALLOWED_AUDIO_EXTENSIONS
        raise HTTPException(status_code=400, detail=f"Invalid file type. Only {file_type} files are allowed: {allowed}")
    
    # Create filename and path
    filename = generate_unique_filename(file.filename)
    upload_path = os.path.join(settings.upload_dir, subfolder)
    os.makedirs(upload_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, filename)
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Optimize image if it's an image file
        if file_type == "image":
            await optimize_image(file_path)
        
        # Return full path for database storage
        return file_path
        
    except Exception as e:
        # Clean up file if something went wrong
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


async def optimize_image(file_path: str):
    """
    Optimize image size and quality
    """
    try:
        with Image.open(file_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Resize if too large
            if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
                img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(file_path, optimize=True, quality=85)
            
    except Exception as e:
        # If optimization fails, keep original file
        print(f"Warning: Failed to optimize image {file_path}: {str(e)}")


def delete_file(file_path: Optional[str]):
    """
    Delete file from disk
    """
    if not file_path:
        return
    
    full_path = os.path.join(settings.upload_dir, file_path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except Exception as e:
            print(f"Warning: Failed to delete file {full_path}: {str(e)}")


def get_file_url(file_path: Optional[str]) -> Optional[str]:
    """
    Generate public URL for file
    """
    if not file_path:
        return None
    
    # In production, this might be a CDN URL
    return f"/static/uploads/{file_path}"