"""
Default Stream Templates
Predefined configurations for common streaming scenarios
"""

from datetime import datetime
from ..stream_models import StreamTemplate, StreamQuality

# Default stream templates to be inserted into database
DEFAULT_TEMPLATES = [
    {
        "name": "talk_radio",
        "display_name": "Talk Radio / Podcast",
        "description": "Optimized for voice content with minimal bandwidth usage. Perfect for talk shows, podcasts, and news broadcasts.",
        "default_bitrate": 64,
        "default_max_listeners": 200,
        "quality": StreamQuality.LOW,
        "format": "mp3",
        "is_premium": False,
        "sort_order": 1,
        "config_template": {
            "burst_on_connect": True,
            "burst_size": 32768,
            "queue_size": 262144,
            "authentication": "source",
            "charset": "UTF-8",
            "mp3_metadata": True,
            "fallback_when_full": False,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Origin, Accept, X-Requested-With, Content-Type"
            }
        }
    },
    {
        "name": "standard_music",
        "display_name": "Standard Music Stream",
        "description": "Balanced quality and bandwidth for general music streaming. Great for most radio stations and DJ sets.",
        "default_bitrate": 128,
        "default_max_listeners": 100,
        "quality": StreamQuality.STANDARD,
        "format": "mp3",
        "is_premium": False,
        "sort_order": 2,
        "config_template": {
            "burst_on_connect": True,
            "burst_size": 65536,
            "queue_size": 524288,
            "authentication": "source",
            "charset": "UTF-8",
            "mp3_metadata": True,
            "fallback_when_full": False,
            "on_connect": "/scripts/stream_connect.sh",
            "on_disconnect": "/scripts/stream_disconnect.sh",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Origin, Accept, X-Requested-With, Content-Type",
                "Cache-Control": "no-cache"
            }
        }
    },
    {
        "name": "hq_music",
        "display_name": "High Quality Music",
        "description": "High-quality audio streaming for professional DJs and music enthusiasts. Higher bandwidth usage.",
        "default_bitrate": 192,
        "default_max_listeners": 75,
        "quality": StreamQuality.HIGH,
        "format": "mp3",
        "is_premium": False,
        "sort_order": 3,
        "config_template": {
            "burst_on_connect": True,
            "burst_size": 98304,
            "queue_size": 786432,
            "authentication": "source",
            "charset": "UTF-8",
            "mp3_metadata": True,
            "fallback_when_full": False,
            "on_connect": "/scripts/hq_stream_connect.sh",
            "on_disconnect": "/scripts/hq_stream_disconnect.sh",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Origin, Accept, X-Requested-With, Content-Type",
                "Cache-Control": "no-cache",
                "X-Audio-Quality": "high"
            }
        }
    },
    {
        "name": "premium_audiophile",
        "display_name": "Premium Audiophile",
        "description": "Near CD-quality streaming for audiophiles and high-end content. Maximum quality with high bandwidth requirements.",
        "default_bitrate": 320,
        "default_max_listeners": 50,
        "quality": StreamQuality.PREMIUM,
        "format": "mp3",
        "is_premium": True,
        "sort_order": 4,
        "config_template": {
            "burst_on_connect": True,
            "burst_size": 131072,
            "queue_size": 1048576,
            "authentication": "source",
            "charset": "UTF-8",
            "mp3_metadata": True,
            "fallback_when_full": False,
            "on_connect": "/scripts/premium_stream_connect.sh",
            "on_disconnect": "/scripts/premium_stream_disconnect.sh",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Origin, Accept, X-Requested-With, Content-Type",
                "Cache-Control": "no-cache",
                "X-Audio-Quality": "premium",
                "X-Bitrate": "320"
            }
        }
    },
    {
        "name": "live_event",
        "display_name": "Live Event Broadcasting",
        "description": "Optimized for live events with high listener capacity. Balanced for large audiences and event broadcasting.",
        "default_bitrate": 128,
        "default_max_listeners": 500,
        "quality": StreamQuality.STANDARD,
        "format": "mp3",
        "is_premium": False,
        "sort_order": 5,
        "config_template": {
            "burst_on_connect": True,
            "burst_size": 65536,
            "queue_size": 524288,
            "authentication": "source",
            "charset": "UTF-8",
            "mp3_metadata": True,
            "fallback_mount": "/event_fallback.mp3",
            "fallback_when_full": True,
            "public": True,
            "on_connect": "/scripts/event_stream_connect.sh",
            "on_disconnect": "/scripts/event_stream_disconnect.sh",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Origin, Accept, X-Requested-With, Content-Type",
                "Cache-Control": "no-cache",
                "X-Stream-Type": "live-event"
            }
        }
    },
    {
        "name": "mobile_optimized",
        "display_name": "Mobile Optimized",
        "description": "Optimized for mobile listeners with data usage concerns. Lower bitrate with good quality compression.",
        "default_bitrate": 96,
        "default_max_listeners": 150,
        "quality": StreamQuality.STANDARD,
        "format": "aac",
        "is_premium": False,
        "sort_order": 6,
        "config_template": {
            "burst_on_connect": True,
            "burst_size": 49152,
            "queue_size": 393216,
            "authentication": "source",
            "charset": "UTF-8",
            "fallback_when_full": False,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Origin, Accept, X-Requested-With, Content-Type",
                "Cache-Control": "no-cache",
                "X-Mobile-Optimized": "true"
            }
        }
    },
    {
        "name": "24_7_automation",
        "display_name": "24/7 Automated Radio",
        "description": "Designed for automated 24/7 radio stations with playlist automation and reliable fallback systems.",
        "default_bitrate": 128,
        "default_max_listeners": 200,
        "quality": StreamQuality.STANDARD,
        "format": "mp3",
        "is_premium": False,
        "sort_order": 7,
        "config_template": {
            "burst_on_connect": True,
            "burst_size": 65536,
            "queue_size": 524288,
            "authentication": "source",
            "charset": "UTF-8",
            "mp3_metadata": True,
            "fallback_mount": "/automation_fallback.mp3",
            "fallback_when_full": False,
            "fallback_override": True,
            "on_connect": "/scripts/automation_connect.sh",
            "on_disconnect": "/scripts/automation_disconnect.sh",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Origin, Accept, X-Requested-With, Content-Type",
                "Cache-Control": "no-cache",
                "X-Stream-Type": "automated"
            }
        }
    },
    {
        "name": "dj_mix_session",
        "display_name": "DJ Mix Session",
        "description": "Optimized for live DJ performances with low latency and high interactivity. Perfect for club streaming and live mixes.",
        "default_bitrate": 192,
        "default_max_listeners": 100,
        "quality": StreamQuality.HIGH,
        "format": "mp3",
        "is_premium": False,
        "sort_order": 8,
        "config_template": {
            "burst_on_connect": True,
            "burst_size": 98304,
            "queue_size": 786432,
            "authentication": "source",
            "charset": "UTF-8",
            "mp3_metadata": True,
            "fallback_when_full": False,
            "on_connect": "/scripts/dj_session_connect.sh",
            "on_disconnect": "/scripts/dj_session_disconnect.sh",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Origin, Accept, X-Requested-With, Content-Type",
                "Cache-Control": "no-cache",
                "X-Stream-Type": "dj-mix",
                "X-Low-Latency": "true"
            }
        }
    }
]

# Reserved system mount points
SYSTEM_RESERVED_MOUNTS = [
    "/admin",
    "/status",
    "/stats",
    "/api",
    "/health",
    "/system",
    "/server",
    "/icecast",
    "/mount",
    "/stream",
    "/listen",
    "/fallback",
    "/backup",
    "/test",
    "/demo",
    "/example"
]

def create_default_templates(db_session):
    """
    Create default stream templates in the database.
    
    Args:
        db_session: SQLAlchemy database session
    """
    
    from ..stream_models import StreamTemplate, MountPoint
    
    # Create templates
    for template_data in DEFAULT_TEMPLATES:
        existing = db_session.query(StreamTemplate).filter(
            StreamTemplate.name == template_data["name"]
        ).first()
        
        if not existing:
            template = StreamTemplate(**template_data)
            db_session.add(template)
    
    # Reserve system mount points
    for mount in SYSTEM_RESERVED_MOUNTS:
        existing = db_session.query(MountPoint).filter(
            MountPoint.mount_point == mount
        ).first()
        
        if not existing:
            mount_point = MountPoint(
                mount_point=mount,
                status="system_reserved",
                is_system_reserved=True,
                notes="System reserved mount point"
            )
            db_session.add(mount_point)
    
    try:
        db_session.commit()
        print("✅ Default stream templates and system mounts created successfully")
    except Exception as e:
        db_session.rollback()
        print(f"❌ Error creating default templates: {e}")


def get_template_by_use_case(use_case: str) -> dict:
    """
    Get recommended template based on use case.
    
    Args:
        use_case: Type of streaming use case
        
    Returns:
        Template configuration dictionary
    """
    
    use_case_mapping = {
        "talk": "talk_radio",
        "podcast": "talk_radio", 
        "music": "standard_music",
        "dj": "dj_mix_session",
        "live": "live_event",
        "event": "live_event",
        "mobile": "mobile_optimized",
        "hq": "hq_music",
        "high_quality": "hq_music",
        "premium": "premium_audiophile",
        "automated": "24_7_automation",
        "radio": "24_7_automation"
    }
    
    template_name = use_case_mapping.get(use_case.lower(), "standard_music")
    
    for template in DEFAULT_TEMPLATES:
        if template["name"] == template_name:
            return template
    
    # Return standard music as fallback
    return DEFAULT_TEMPLATES[1]  # standard_music template