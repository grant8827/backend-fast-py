"""
Audio API Schemas
Pydantic models for audio-related API endpoints
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class MicrophoneConfig(BaseModel):
    """Microphone configuration schema"""
    device_id: Optional[str] = None
    gain: float = 70.0  # 0-100%
    enabled: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MicrophoneStatus(BaseModel):
    """Microphone status response schema"""
    enabled: bool
    gain: float
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    latency: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TalkoverConfig(BaseModel):
    """Talkover configuration schema"""
    enabled: bool = False
    duck_level: float = 25.0  # Percentage to duck to (0-100%)
    fade_time: float = 0.1  # Fade time in seconds
    auto_enable: bool = True  # Auto-enable when mic turns on
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TalkoverStatus(BaseModel):
    """Talkover status response schema"""
    enabled: bool
    active: bool  # Whether currently ducking
    duck_level: float
    fade_time: float
    auto_enable: bool
    original_volume: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AudioLevels(BaseModel):
    """Audio level monitoring schema"""
    microphone: Optional[float] = None  # 0-100%
    master_left: Optional[float] = None  # 0-100%
    master_right: Optional[float] = None  # 0-100%
    channel_a_left: Optional[float] = None  # 0-100%
    channel_a_right: Optional[float] = None  # 0-100%
    channel_b_left: Optional[float] = None  # 0-100%
    channel_b_right: Optional[float] = None  # 0-100%
    timestamp: datetime = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AudioDevice(BaseModel):
    """Audio device information schema"""
    device_id: str
    name: str
    type: str  # "input" or "output"
    channels: int
    sample_rate: int
    is_default: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AudioSystemStatus(BaseModel):
    """Overall audio system status"""
    microphone: MicrophoneStatus
    talkover: TalkoverStatus
    levels: AudioLevels
    devices: Dict[str, AudioDevice] = {}
    backend_connected: bool = False
    backend_type: str = "web_audio"  # "cpp_media_server" or "web_audio"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AudioCommand(BaseModel):
    """Generic audio command schema"""
    command: str
    parameters: Dict[str, Any] = {}
    channel_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AudioCommandResponse(BaseModel):
    """Audio command response schema"""
    success: bool
    command: str
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }