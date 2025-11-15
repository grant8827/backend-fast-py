"""
Stream Provisioning Service
OneStopRadio - Dedicated Shoutcast Stream Management
"""

import secrets
import string
import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, Station
from .stream_provisioning_models import (
    DedicatedStream, PortPool, StreamSession, StreamMonitoring, 
    ShoutcastServer, StreamStatus
)
from .shoutcast_client import ShoutcastClient

logger = logging.getLogger(__name__)


class StreamProvisioningService:
    """Core service for managing dedicated stream provisioning"""
    
    def __init__(self):
        self.port_range_start = 8100
        self.port_range_end = 8200
        self.default_max_listeners = 100
        self.default_bitrate = 128
        
    async def initialize_port_pool(self, db: AsyncSession) -> bool:
        """Initialize the port pool with available ports"""
        try:
            # Check if port pool is already initialized
            result = await db.execute(select(func.count(PortPool.port)))
            existing_count = result.scalar()
            
            if existing_count > 0:
                logger.info(f"Port pool already initialized with {existing_count} ports")
                return True
            
            # Create port pool entries
            ports_to_create = []
            for port in range(self.port_range_start, self.port_range_end + 1):
                ports_to_create.append(PortPool(
                    port=port,
                    is_allocated=False
                ))
            
            db.add_all(ports_to_create)
            await db.commit()
            
            logger.info(f"Initialized port pool with {len(ports_to_create)} ports ({self.port_range_start}-{self.port_range_end})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize port pool: {e}")
            await db.rollback()
            return False
    
    async def allocate_port(self, db: AsyncSession, user_id: str) -> Optional[int]:
        """Allocate an available port from the pool"""
        try:
            # Find an available port
            result = await db.execute(
                select(PortPool)
                .where(PortPool.is_allocated == False)
                .order_by(PortPool.port)
                .limit(1)
            )
            port_entry = result.scalar_one_or_none()
            
            if not port_entry:
                logger.error("No available ports in the pool")
                return None
            
            # Allocate the port
            port_entry.is_allocated = True
            port_entry.allocated_at = datetime.utcnow()
            port_entry.allocated_to_user_id = user_id
            
            await db.commit()
            
            logger.info(f"Allocated port {port_entry.port} to user {user_id}")
            return port_entry.port
            
        except Exception as e:
            logger.error(f"Failed to allocate port: {e}")
            await db.rollback()
            return None
    
    async def release_port(self, db: AsyncSession, port: int) -> bool:
        """Release a port back to the pool"""
        try:
            result = await db.execute(
                select(PortPool).where(PortPool.port == port)
            )
            port_entry = result.scalar_one_or_none()
            
            if not port_entry:
                logger.error(f"Port {port} not found in pool")
                return False
            
            # Release the port
            port_entry.is_allocated = False
            port_entry.allocated_at = None
            port_entry.allocated_to_user_id = None
            port_entry.allocated_to_stream_id = None
            
            await db.commit()
            
            logger.info(f"Released port {port} back to pool")
            return True
            
        except Exception as e:
            logger.error(f"Failed to release port {port}: {e}")
            await db.rollback()
            return False
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure password for stream access"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def provision_stream(
        self, 
        db: AsyncSession, 
        user_id: str, 
        stream_title: str,
        stream_description: Optional[str] = None,
        max_listeners: Optional[int] = None,
        bitrate: Optional[int] = None,
        station_id: Optional[str] = None
    ) -> Optional[DedicatedStream]:
        """Provision a new dedicated stream for a user"""
        try:
            # Check if user already has an active stream
            existing_result = await db.execute(
                select(DedicatedStream)
                .where(and_(
                    DedicatedStream.user_id == user_id,
                    DedicatedStream.status.in_([StreamStatus.PROVISIONING, StreamStatus.ACTIVE])
                ))
            )
            existing_stream = existing_result.scalar_one_or_none()
            
            if existing_stream:
                logger.warning(f"User {user_id} already has an active stream on port {existing_stream.port}")
                return existing_stream
            
            # Allocate a port
            port = await self.allocate_port(db, user_id)
            if not port:
                logger.error(f"Failed to allocate port for user {user_id}")
                return None
            
            # Generate secure passwords
            source_password = self.generate_secure_password()
            admin_password = self.generate_secure_password()
            
            # Create the dedicated stream record
            stream = DedicatedStream(
                user_id=user_id,
                station_id=station_id,
                port=port,
                source_password=source_password,
                admin_password=admin_password,
                stream_title=stream_title,
                stream_description=stream_description,
                max_listeners=max_listeners or self.default_max_listeners,
                bitrate=bitrate or self.default_bitrate,
                status=StreamStatus.PROVISIONING,
                created_at=datetime.utcnow()
            )
            
            db.add(stream)
            await db.flush()  # Get the stream ID
            
            # Update port pool with stream association
            await db.execute(
                update(PortPool)
                .where(PortPool.port == port)
                .values(allocated_to_stream_id=stream.id)
            )
            
            # Configure Shoutcast server
            shoutcast_configured = await self._configure_shoutcast_stream(db, stream)
            if not shoutcast_configured:
                logger.error(f"Failed to configure Shoutcast for stream {stream.id}")
                # Don't fail the provisioning, mark as needs configuration
                stream.status = StreamStatus.PROVISIONING
            else:
                stream.status = StreamStatus.ACTIVE
                stream.activated_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Successfully provisioned stream {stream.id} on port {port} for user {user_id}")
            return stream
            
        except Exception as e:
            logger.error(f"Failed to provision stream for user {user_id}: {e}")
            await db.rollback()
            
            # Try to release the port if it was allocated
            if 'port' in locals():
                await self.release_port(db, port)
            
            return None
    
    async def _configure_shoutcast_stream(
        self, 
        db: AsyncSession, 
        stream: DedicatedStream
    ) -> bool:
        """Configure the Shoutcast server with the new stream"""
        try:
            # Get the primary Shoutcast server
            result = await db.execute(
                select(ShoutcastServer)
                .where(and_(
                    ShoutcastServer.is_active == True,
                    ShoutcastServer.is_primary == True
                ))
            )
            server = result.scalar_one_or_none()
            
            if not server:
                logger.error("No active primary Shoutcast server found")
                return False
            
            # Create Shoutcast client
            client = ShoutcastClient(
                hostname=server.hostname,
                admin_port=server.admin_port,
                admin_password=server.admin_password
            )
            
            # Configure the stream on the server
            stream_config = {
                'port': stream.port,
                'password': stream.source_password,
                'admin_password': stream.admin_password,
                'max_listeners': stream.max_listeners,
                'bitrate': stream.bitrate,
                'genre': stream.genre,
                'title': stream.stream_title,
                'url': stream.stream_url or '',
                'public': stream.public_server
            }
            
            success = await client.create_stream(stream_config)
            if success:
                stream.last_config_update = datetime.utcnow()
                stream.config_version += 1
                logger.info(f"Successfully configured Shoutcast for stream {stream.id} on port {stream.port}")
                return True
            else:
                logger.error(f"Failed to configure Shoutcast for stream {stream.id}")
                return False
            
        except Exception as e:
            logger.error(f"Error configuring Shoutcast for stream {stream.id}: {e}")
            return False
    
    async def get_user_stream(
        self, 
        db: AsyncSession, 
        user_id: str
    ) -> Optional[DedicatedStream]:
        """Get the user's dedicated stream with all details"""
        try:
            result = await db.execute(
                select(DedicatedStream)
                .options(
                    selectinload(DedicatedStream.user),
                    selectinload(DedicatedStream.station),
                    selectinload(DedicatedStream.allocated_port)
                )
                .where(and_(
                    DedicatedStream.user_id == user_id,
                    DedicatedStream.status != StreamStatus.TERMINATED
                ))
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get stream for user {user_id}: {e}")
            return None
    
    async def suspend_stream(
        self, 
        db: AsyncSession, 
        stream_id: str, 
        reason: Optional[str] = None
    ) -> bool:
        """Suspend a stream temporarily"""
        try:
            result = await db.execute(
                select(DedicatedStream).where(DedicatedStream.id == stream_id)
            )
            stream = result.scalar_one_or_none()
            
            if not stream:
                logger.error(f"Stream {stream_id} not found")
                return False
            
            # Update stream status
            stream.status = StreamStatus.SUSPENDED
            stream.is_live = False
            
            # TODO: Disconnect active connections via Shoutcast API
            
            await db.commit()
            logger.info(f"Successfully suspended stream {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to suspend stream {stream_id}: {e}")
            await db.rollback()
            return False
    
    async def terminate_stream(
        self, 
        db: AsyncSession, 
        stream_id: str
    ) -> bool:
        """Permanently terminate a stream and release resources"""
        try:
            result = await db.execute(
                select(DedicatedStream).where(DedicatedStream.id == stream_id)
            )
            stream = result.scalar_one_or_none()
            
            if not stream:
                logger.error(f"Stream {stream_id} not found")
                return False
            
            # Update stream status
            stream.status = StreamStatus.TERMINATED
            stream.is_live = False
            
            # Release the port
            await self.release_port(db, stream.port)
            
            # TODO: Remove from Shoutcast configuration
            
            await db.commit()
            logger.info(f"Successfully terminated stream {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to terminate stream {stream_id}: {e}")
            await db.rollback()
            return False
    
    async def get_stream_stats(
        self, 
        db: AsyncSession, 
        stream_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive stream statistics"""
        try:
            # Get the stream
            result = await db.execute(
                select(DedicatedStream).where(DedicatedStream.id == stream_id)
            )
            stream = result.scalar_one_or_none()
            
            if not stream:
                return {}
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get session statistics
            session_stats = await db.execute(
                select(
                    func.count(StreamSession.id).label('total_sessions'),
                    func.sum(StreamSession.duration_seconds).label('total_duration'),
                    func.avg(StreamSession.duration_seconds).label('avg_duration'),
                    func.sum(StreamSession.total_data_mb).label('total_data_mb'),
                    func.max(StreamSession.peak_listeners).label('peak_listeners')
                )
                .where(and_(
                    StreamSession.stream_id == stream_id,
                    StreamSession.started_at >= start_date
                ))
            )
            session_data = session_stats.first()
            
            # Get recent monitoring data
            monitoring_stats = await db.execute(
                select(StreamMonitoring)
                .where(and_(
                    StreamMonitoring.stream_id == stream_id,
                    StreamMonitoring.recorded_at >= start_date
                ))
                .order_by(StreamMonitoring.recorded_at.desc())
                .limit(100)
            )
            monitoring_data = monitoring_stats.scalars().all()
            
            return {
                'stream_info': {
                    'id': stream.id,
                    'port': stream.port,
                    'status': stream.status.value,
                    'is_live': stream.is_live,
                    'current_listeners': stream.current_listeners,
                    'max_listeners': stream.max_listeners,
                    'bitrate': stream.bitrate,
                    'created_at': stream.created_at.isoformat(),
                    'activated_at': stream.activated_at.isoformat() if stream.activated_at else None
                },
                'session_stats': {
                    'total_sessions': session_data.total_sessions or 0,
                    'total_duration_hours': (session_data.total_duration or 0) / 3600,
                    'avg_duration_minutes': (session_data.avg_duration or 0) / 60,
                    'total_data_gb': (session_data.total_data_mb or 0) / 1024,
                    'peak_listeners': session_data.peak_listeners or 0
                },
                'recent_monitoring': [
                    {
                        'recorded_at': data.recorded_at.isoformat(),
                        'current_listeners': data.current_listeners,
                        'is_live': data.is_live,
                        'current_bitrate': data.current_bitrate,
                        'bandwidth_mbps': data.bandwidth_mbps
                    }
                    for data in monitoring_data
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for stream {stream_id}: {e}")
            return {}


# Singleton instance
stream_provisioning_service = StreamProvisioningService()