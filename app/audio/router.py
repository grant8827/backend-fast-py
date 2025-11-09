"""
Audio API Router
Handles microphone, talkover, and audio system endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Optional
import json
import asyncio
from datetime import datetime

from .schemas import (
    MicrophoneConfig, MicrophoneStatus, TalkoverConfig, TalkoverStatus,
    AudioLevels, AudioDevice, AudioSystemStatus, AudioCommand, AudioCommandResponse
)
from ..auth.dependencies import get_current_user_optional


router = APIRouter(prefix="/api/audio", tags=["audio"])

# Global state for audio system
audio_state = {
    "microphone": {
        "enabled": False,
        "gain": 70.0,
        "device_id": None,
        "device_name": None,
        "sample_rate": 48000,
        "channels": 1,
        "latency": 0.0
    },
    "talkover": {
        "enabled": False,
        "active": False,
        "duck_level": 25.0,
        "fade_time": 0.1,
        "auto_enable": True,
        "original_volume": None
    },
    "levels": {
        "microphone": 0.0,
        "master_left": 0.0,
        "master_right": 0.0,
        "channel_a_left": 0.0,
        "channel_a_right": 0.0,
        "channel_b_left": 0.0,
        "channel_b_right": 0.0,
        "timestamp": datetime.now()
    },
    "backend_connected": False,
    "backend_type": "web_audio"
}

# WebSocket connections for real-time updates
websocket_connections: List[WebSocket] = []


async def broadcast_audio_status():
    """Broadcast current audio status to all connected WebSocket clients"""
    if not websocket_connections:
        return
    
    status = AudioSystemStatus(
        microphone=MicrophoneStatus(**audio_state["microphone"]),
        talkover=TalkoverStatus(**audio_state["talkover"]),
        levels=AudioLevels(**audio_state["levels"]),
        backend_connected=audio_state["backend_connected"],
        backend_type=audio_state["backend_type"]
    )
    
    message = {
        "type": "audio_status_update",
        "data": status.dict()
    }
    
    # Send to all connected clients
    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except:
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected:
        websocket_connections.remove(ws)


# Microphone endpoints
@router.get("/microphone/status/", response_model=MicrophoneStatus)
async def get_microphone_status():
    """Get current microphone status"""
    return MicrophoneStatus(**audio_state["microphone"])


@router.post("/microphone/toggle/", response_model=AudioCommandResponse)
async def toggle_microphone(
    config: MicrophoneConfig,
    user = Depends(get_current_user_optional)
):
    """Toggle microphone on/off with optional configuration"""
    try:
        # Update microphone state
        audio_state["microphone"]["enabled"] = config.enabled
        audio_state["microphone"]["gain"] = config.gain
        
        if config.device_id:
            audio_state["microphone"]["device_id"] = config.device_id
        
        # Auto-enable talkover if configured
        if config.enabled and audio_state["talkover"]["auto_enable"]:
            audio_state["talkover"]["enabled"] = True
            audio_state["talkover"]["active"] = True
            print(f"🎤 Microphone enabled - Auto-activating talkover")
        elif not config.enabled:
            # Disable talkover when microphone is turned off
            audio_state["talkover"]["enabled"] = False
            audio_state["talkover"]["active"] = False
            audio_state["talkover"]["original_volume"] = None
            print(f"🎤 Microphone disabled - Deactivating talkover")
        
        # Broadcast status update
        await broadcast_audio_status()
        
        action = "enabled" if config.enabled else "disabled"
        message = f"Microphone {action} successfully"
        if config.enabled and audio_state["talkover"]["auto_enable"]:
            message += " with talkover auto-activated"
        
        return AudioCommandResponse(
            success=True,
            command="toggle_microphone",
            message=message,
            data={
                "microphone_enabled": config.enabled,
                "talkover_auto_enabled": config.enabled and audio_state["talkover"]["auto_enable"]
            }
        )
        
    except Exception as e:
        return AudioCommandResponse(
            success=False,
            command="toggle_microphone",
            message="Failed to toggle microphone",
            error=str(e)
        )


@router.post("/microphone/gain/", response_model=AudioCommandResponse)
async def set_microphone_gain(gain: float):
    """Set microphone gain level (0-100%)"""
    try:
        # Clamp gain to valid range
        gain = max(0.0, min(100.0, gain))
        audio_state["microphone"]["gain"] = gain
        
        # Broadcast status update
        await broadcast_audio_status()
        
        return AudioCommandResponse(
            success=True,
            command="set_microphone_gain",
            message=f"Microphone gain set to {gain}%",
            data={"gain": gain}
        )
        
    except Exception as e:
        return AudioCommandResponse(
            success=False,
            command="set_microphone_gain",
            message="Failed to set microphone gain",
            error=str(e)
        )


# Talkover endpoints
@router.get("/talkover/status/", response_model=TalkoverStatus)
async def get_talkover_status():
    """Get current talkover status"""
    return TalkoverStatus(**audio_state["talkover"])


@router.post("/talkover/toggle/", response_model=AudioCommandResponse)
async def toggle_talkover(
    config: TalkoverConfig,
    user = Depends(get_current_user_optional)
):
    """Toggle talkover on/off with configuration"""
    try:
        # Only allow talkover when microphone is enabled
        if config.enabled and not audio_state["microphone"]["enabled"]:
            return AudioCommandResponse(
                success=False,
                command="toggle_talkover",
                message="Cannot enable talkover - microphone is not enabled",
                error="Microphone must be enabled first"
            )
        
        # Update talkover state
        audio_state["talkover"]["enabled"] = config.enabled
        audio_state["talkover"]["duck_level"] = config.duck_level
        audio_state["talkover"]["fade_time"] = config.fade_time
        audio_state["talkover"]["auto_enable"] = config.auto_enable
        
        if config.enabled:
            audio_state["talkover"]["active"] = True
        else:
            audio_state["talkover"]["active"] = False
            audio_state["talkover"]["original_volume"] = None
        
        # Broadcast status update
        await broadcast_audio_status()
        
        action = "enabled" if config.enabled else "disabled"
        return AudioCommandResponse(
            success=True,
            command="toggle_talkover",
            message=f"Talkover {action} successfully",
            data={
                "talkover_enabled": config.enabled,
                "duck_level": config.duck_level
            }
        )
        
    except Exception as e:
        return AudioCommandResponse(
            success=False,
            command="toggle_talkover",
            message="Failed to toggle talkover",
            error=str(e)
        )


# Audio levels endpoint
@router.get("/levels/", response_model=AudioLevels)
async def get_audio_levels():
    """Get current audio levels"""
    audio_state["levels"]["timestamp"] = datetime.now()
    return AudioLevels(**audio_state["levels"])


@router.post("/levels/update/", response_model=AudioCommandResponse)
async def update_audio_levels(levels: AudioLevels):
    """Update audio levels (typically called by C++ backend or WebRTC)"""
    try:
        # Update levels
        audio_state["levels"].update(levels.dict(exclude={"timestamp"}))
        audio_state["levels"]["timestamp"] = datetime.now()
        
        # Broadcast to WebSocket clients for real-time monitoring
        await broadcast_audio_status()
        
        return AudioCommandResponse(
            success=True,
            command="update_audio_levels",
            message="Audio levels updated successfully"
        )
        
    except Exception as e:
        return AudioCommandResponse(
            success=False,
            command="update_audio_levels",
            message="Failed to update audio levels",
            error=str(e)
        )


# Audio system status
@router.get("/status/", response_model=AudioSystemStatus)
async def get_audio_system_status():
    """Get complete audio system status"""
    return AudioSystemStatus(
        microphone=MicrophoneStatus(**audio_state["microphone"]),
        talkover=TalkoverStatus(**audio_state["talkover"]),
        levels=AudioLevels(**audio_state["levels"]),
        backend_connected=audio_state["backend_connected"],
        backend_type=audio_state["backend_type"]
    )


# C++ Backend integration endpoints
@router.post("/backend/connect/", response_model=AudioCommandResponse)
async def connect_cpp_backend():
    """Mark C++ backend as connected"""
    audio_state["backend_connected"] = True
    audio_state["backend_type"] = "cpp_media_server"
    
    await broadcast_audio_status()
    
    return AudioCommandResponse(
        success=True,
        command="connect_cpp_backend",
        message="C++ Media Server backend connected"
    )


@router.post("/backend/disconnect/", response_model=AudioCommandResponse)
async def disconnect_cpp_backend():
    """Mark C++ backend as disconnected - fallback to Web Audio"""
    audio_state["backend_connected"] = False
    audio_state["backend_type"] = "web_audio"
    
    await broadcast_audio_status()
    
    return AudioCommandResponse(
        success=True,
        command="disconnect_cpp_backend",
        message="C++ Media Server backend disconnected - using Web Audio fallback"
    )


# WebSocket endpoint for real-time updates
@router.websocket("/ws/")
async def audio_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio status updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send initial status
        await broadcast_audio_status()
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (like ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "request_status":
                    await broadcast_audio_status()
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


# Generic audio command endpoint
@router.post("/command/", response_model=AudioCommandResponse)
async def execute_audio_command(command: AudioCommand):
    """Execute a generic audio command"""
    try:
        if command.command == "start_microphone":
            config = MicrophoneConfig(enabled=True, **command.parameters)
            return await toggle_microphone(config)
            
        elif command.command == "stop_microphone":
            config = MicrophoneConfig(enabled=False)
            return await toggle_microphone(config)
            
        elif command.command == "set_microphone_gain":
            gain = command.parameters.get("gain", 70.0)
            return await set_microphone_gain(gain)
            
        elif command.command == "enable_talkover":
            config = TalkoverConfig(enabled=True, **command.parameters)
            return await toggle_talkover(config)
            
        elif command.command == "disable_talkover":
            config = TalkoverConfig(enabled=False)
            return await toggle_talkover(config)
            
        else:
            return AudioCommandResponse(
                success=False,
                command=command.command,
                message=f"Unknown command: {command.command}",
                error="Command not recognized"
            )
            
    except Exception as e:
        return AudioCommandResponse(
            success=False,
            command=command.command,
            message=f"Failed to execute command: {command.command}",
            error=str(e)
        )