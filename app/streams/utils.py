"""
Utility functions for stream management
Helper functions for mount point generation, validation, etc.
"""

import re
import secrets
import string
from typing import Optional, List
from sqlalchemy.orm import Session

from ..stream_models import MountPoint, UserStream
from .schemas import StreamCreate, StreamConfigValidation


def generate_mount_point(stream_name: str, db: Session, max_attempts: int = 10) -> Optional[str]:
    """
    Generate a unique mount point based on stream name.
    
    Args:
        stream_name: The display name of the stream
        db: Database session
        max_attempts: Maximum attempts to generate unique mount point
        
    Returns:
        Unique mount point string or None if failed
    """
    
    # Clean stream name for mount point
    base_name = stream_name.lower()
    base_name = re.sub(r'[^a-z0-9\s-_]', '', base_name)  # Remove special chars
    base_name = re.sub(r'\s+', '_', base_name.strip())   # Replace spaces with underscores
    base_name = re.sub(r'[-_]+', '_', base_name)         # Collapse multiple separators
    
    # Ensure it starts with letter or underscore
    if base_name and not base_name[0].isalpha() and base_name[0] != '_':
        base_name = f"stream_{base_name}"
    
    # Default fallback if name cleaning failed
    if not base_name or len(base_name) < 2:
        base_name = "stream"
    
    # Limit length
    if len(base_name) > 20:
        base_name = base_name[:20]
    
    # Try to find unique mount point
    for attempt in range(max_attempts):
        if attempt == 0:
            # First try with clean name
            mount_point = f"/{base_name}"
        else:
            # Add number suffix for subsequent attempts
            mount_point = f"/{base_name}_{attempt}"
        
        # Check if mount point is available
        existing = db.query(MountPoint).filter(
            MountPoint.mount_point == mount_point
        ).first()
        
        if not existing:
            return mount_point
    
    # If all attempts failed, generate random suffix
    for _ in range(5):
        random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
        mount_point = f"/{base_name}_{random_suffix}"
        
        existing = db.query(MountPoint).filter(
            MountPoint.mount_point == mount_point
        ).first()
        
        if not existing:
            return mount_point
    
    return None


def generate_source_password(length: int = 16) -> str:
    """
    Generate a secure source password for stream authentication.
    
    Args:
        length: Password length (minimum 12)
        
    Returns:
        Secure random password
    """
    
    if length < 12:
        length = 12
    
    # Use a mix of letters, numbers, and safe special characters
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Ensure password has at least one of each character type
    if not any(c.islower() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_lowercase)
    if not any(c.isupper() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_uppercase)
    if not any(c.isdigit() for c in password):
        password = password[:-1] + secrets.choice(string.digits)
    
    return password


def validate_stream_config(stream_data: StreamCreate) -> StreamConfigValidation:
    """
    Validate stream configuration for business rules and technical constraints.
    
    Args:
        stream_data: Stream configuration to validate
        
    Returns:
        Validation result with errors and warnings
    """
    
    errors = []
    warnings = []
    
    # Stream name validation
    if len(stream_data.stream_name.strip()) < 3:
        errors.append("Stream name must be at least 3 characters long")
    
    if len(stream_data.stream_name) > 100:
        errors.append("Stream name cannot exceed 100 characters")
    
    # Check for reserved words in stream name
    reserved_words = ['admin', 'api', 'system', 'server', 'test', 'www', 'ftp', 'mail']
    if any(word in stream_data.stream_name.lower() for word in reserved_words):
        warnings.append("Stream name contains reserved word that may cause conflicts")
    
    # Server name validation
    if len(stream_data.server_name.strip()) < 3:
        errors.append("Server name must be at least 3 characters long")
    
    # Bitrate validation
    if stream_data.bitrate:
        valid_bitrates = [32, 48, 64, 96, 128, 160, 192, 224, 256, 320]
        if stream_data.bitrate not in valid_bitrates:
            errors.append(f"Bitrate must be one of: {valid_bitrates}")
        
        if stream_data.bitrate > 192:
            warnings.append("High bitrate streams (>192kbps) consume more bandwidth and may cost extra")
    
    # Max listeners validation
    if stream_data.max_listeners:
        if stream_data.max_listeners > 500:
            warnings.append("High listener capacity may require additional server resources")
        
        if stream_data.max_listeners < 10:
            warnings.append("Very low listener capacity may limit your stream's reach")
    
    # URL validation
    if stream_data.server_url:
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(stream_data.server_url):
            errors.append("Invalid server URL format")
    
    # Genre validation
    if stream_data.genre:
        valid_genres = [
            'rock', 'pop', 'jazz', 'classical', 'electronic', 'hip-hop', 'country',
            'folk', 'blues', 'reggae', 'funk', 'soul', 'punk', 'metal', 'indie',
            'alternative', 'dance', 'house', 'techno', 'ambient', 'world',
            'latin', 'gospel', 'r&b', 'ska', 'dub', 'experimental', 'talk',
            'news', 'sports', 'comedy', 'variety'
        ]
        
        if stream_data.genre.lower() not in valid_genres:
            warnings.append(f"Genre '{stream_data.genre}' is not in the standard list. This may affect discoverability.")
    
    # Format validation
    if stream_data.format:
        supported_formats = ['mp3', 'aac', 'ogg']
        if stream_data.format.lower() not in supported_formats:
            errors.append(f"Audio format must be one of: {supported_formats}")
    
    # Icecast config validation
    if stream_data.icecast_config:
        # Basic validation of Icecast configuration
        if not isinstance(stream_data.icecast_config, dict):
            errors.append("Icecast configuration must be a valid JSON object")
        else:
            # Check for potentially dangerous configurations
            dangerous_keys = ['password', 'admin_password', 'relay_password']
            for key in dangerous_keys:
                if key in stream_data.icecast_config:
                    errors.append(f"Cannot specify '{key}' in custom configuration")
    
    # Calculate estimated costs and add to validation
    estimated_cost = None
    estimated_bandwidth = None
    
    if stream_data.bitrate and stream_data.max_listeners:
        from .services import StreamService
        cost_info = StreamService.calculate_estimated_costs(
            stream_data.bitrate, 
            stream_data.max_listeners
        )
        estimated_cost = cost_info["monthly_cost_usd"]
        estimated_bandwidth = cost_info["estimated_bandwidth_gb"]
        
        # Add cost warnings
        if estimated_cost > 50:
            warnings.append(f"Estimated monthly cost (${estimated_cost:.2f}) is high. Consider lower bitrate or listener capacity.")
        
        if estimated_bandwidth > 100:
            warnings.append(f"Estimated bandwidth usage ({estimated_bandwidth:.1f} GB/month) is high.")
    
    return StreamConfigValidation(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        estimated_cost=estimated_cost,
        estimated_bandwidth=estimated_bandwidth
    )


def sanitize_mount_point(mount_point: str) -> str:
    """
    Sanitize and validate mount point format.
    
    Args:
        mount_point: Raw mount point string
        
    Returns:
        Sanitized mount point
    """
    
    # Ensure it starts with /
    if not mount_point.startswith('/'):
        mount_point = f"/{mount_point}"
    
    # Remove invalid characters
    mount_point = re.sub(r'[^a-zA-Z0-9/_-]', '', mount_point)
    
    # Remove double slashes
    mount_point = re.sub(r'/+', '/', mount_point)
    
    # Limit length
    if len(mount_point) > 50:
        mount_point = mount_point[:50]
    
    # Ensure it doesn't end with / unless it's root
    if len(mount_point) > 1 and mount_point.endswith('/'):
        mount_point = mount_point[:-1]
    
    return mount_point


def generate_icecast_config(stream_data: Dict) -> Dict[str, any]:
    """
    Generate Icecast mount point configuration.
    
    Args:
        stream_data: Stream configuration dictionary
        
    Returns:
        Icecast configuration dictionary
    """
    
    config = {
        "mount-name": stream_data["mount_point"],
        "password": stream_data["source_password"],
        "bitrate": stream_data["bitrate"],
        "max-listeners": stream_data["max_listeners"],
        "public": "1" if stream_data.get("public", True) else "0",
        
        # Metadata
        "server-name": stream_data["server_name"],
        "server-description": stream_data.get("server_description", ""),
        "genre": stream_data.get("genre", "Various"),
        "server-url": stream_data.get("server_url", ""),
        
        # Technical settings
        "charset": "UTF-8",
        "stream-name": stream_data["stream_name"],
        "stream-description": stream_data.get("server_description", ""),
        
        # Default settings for reliability
        "burst-on-connect": "1",
        "burst-size": "65536",
        "queue-size": str(stream_data["bitrate"] * 1024 * 2),  # 2 seconds of audio
        
        # Authentication
        "authentication": {
            "type": "source"
        }
    }
    
    # Add custom configuration if provided
    if "icecast_config" in stream_data and stream_data["icecast_config"]:
        config.update(stream_data["icecast_config"])
    
    # Format-specific settings
    if stream_data.get("format") == "mp3":
        config["mp3-metadata"] = "1"
    elif stream_data.get("format") == "ogg":
        config["ogg-passthrough"] = "1"
    
    return config


def validate_mount_point_availability(mount_point: str, db: Session, exclude_stream_id: Optional[str] = None) -> bool:
    """
    Check if a mount point is available for use.
    
    Args:
        mount_point: Mount point to check
        db: Database session
        exclude_stream_id: Stream ID to exclude from check (for updates)
        
    Returns:
        True if available, False if taken
    """
    
    query = db.query(MountPoint).filter(MountPoint.mount_point == mount_point)
    
    if exclude_stream_id:
        query = query.filter(MountPoint.stream_id != exclude_stream_id)
    
    existing = query.first()
    return existing is None


def get_recommended_bitrates() -> List[Dict[str, any]]:
    """
    Get list of recommended bitrate configurations.
    
    Returns:
        List of bitrate recommendations with descriptions
    """
    
    return [
        {
            "bitrate": 64,
            "quality": "low",
            "description": "Voice/Talk radio, low bandwidth",
            "use_case": "Talk shows, podcasts, voice-only content",
            "estimated_file_size_mb_per_hour": 29
        },
        {
            "bitrate": 128,
            "quality": "standard",
            "description": "Standard quality music streaming",
            "use_case": "General music streaming, good balance of quality and bandwidth",
            "estimated_file_size_mb_per_hour": 58
        },
        {
            "bitrate": 192,
            "quality": "high",
            "description": "High quality music streaming",
            "use_case": "Professional music streaming, DJ mixes",
            "estimated_file_size_mb_per_hour": 86
        },
        {
            "bitrate": 320,
            "quality": "premium",
            "description": "Premium quality, near-CD quality",
            "use_case": "Audiophile content, high-end music streaming",
            "estimated_file_size_mb_per_hour": 144
        }
    ]


def format_bandwidth_usage(bytes_count: int) -> str:
    """
    Format bandwidth usage in human-readable format.
    
    Args:
        bytes_count: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 GB", "250 MB")
    """
    
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 ** 2:
        return f"{bytes_count / 1024:.1f} KB"
    elif bytes_count < 1024 ** 3:
        return f"{bytes_count / (1024 ** 2):.1f} MB"
    else:
        return f"{bytes_count / (1024 ** 3):.2f} GB"


def calculate_stream_uptime(created_at, last_connected_at, current_status) -> Dict[str, any]:
    """
    Calculate stream uptime statistics.
    
    Returns:
        Dictionary with uptime information
    """
    
    from datetime import datetime
    
    now = datetime.utcnow()
    total_age = (now - created_at).total_seconds()
    
    # This is a simplified calculation
    # In production, you'd track actual connection/disconnection events
    
    if last_connected_at:
        last_activity_age = (now - last_connected_at).total_seconds()
    else:
        last_activity_age = total_age
    
    uptime_percentage = 0.0
    if current_status in ['active', 'ready']:
        # Assume good uptime for active streams
        uptime_percentage = max(0.0, min(95.0, 90.0 - (last_activity_age / 3600)))
    
    return {
        "total_age_hours": total_age / 3600,
        "uptime_percentage": uptime_percentage,
        "last_activity_hours_ago": last_activity_age / 3600,
        "estimated_total_uptime_hours": (total_age * uptime_percentage / 100) / 3600
    }