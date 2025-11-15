"""
Database initialization script for stream provisioning system
Run this after migration to set up default Shoutcast server and port pool
"""
import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine
from app.stream_provisioning.models import ShoutcastServer, PortPool
from datetime import datetime


async def init_stream_infrastructure():
    """Initialize default Shoutcast server and port pool"""
    
    # Create tables if they don't exist
    from app.stream_provisioning.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as db:
        try:
            # Check if default server already exists
            from sqlalchemy import select
            result = await db.execute(select(ShoutcastServer).where(ShoutcastServer.host == 'localhost'))
            existing_server = result.scalar_one_or_none()
            
            if not existing_server:
                # Create default Shoutcast server
                default_server = ShoutcastServer(
                    host='localhost',
                    admin_port=8000,
                    admin_username='admin',
                    admin_password='changeme123',  # Change this in production!
                    is_active=True,
                    max_ports=100,
                    port_range_start=8100,
                    port_range_end=8200,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(default_server)
                await db.commit()
                await db.refresh(default_server)
                
                print(f"✅ Created default Shoutcast server (ID: {default_server.id})")
                
                # Create port pool (ports 8100-8200)
                port_pool_entries = []
                for port in range(8100, 8201):  # 8100 to 8200 inclusive
                    port_entry = PortPool(
                        port_number=port,
                        server_id=default_server.id,
                        is_allocated=False,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    port_pool_entries.append(port_entry)
                
                db.add_all(port_pool_entries)
                await db.commit()
                
                print(f"✅ Created port pool with {len(port_pool_entries)} ports (8100-8200)")
                
            else:
                print(f"ℹ️ Default Shoutcast server already exists (ID: {existing_server.id})")
                
                # Check port pool
                result = await db.execute(select(PortPool).where(PortPool.server_id == existing_server.id))
                existing_ports = result.scalars().all()
                
                if len(existing_ports) == 0:
                    # Add missing ports
                    port_pool_entries = []
                    for port in range(8100, 8201):
                        port_entry = PortPool(
                            port_number=port,
                            server_id=existing_server.id,
                            is_allocated=False,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        port_pool_entries.append(port_entry)
                    
                    db.add_all(port_pool_entries)
                    await db.commit()
                    print(f"✅ Added {len(port_pool_entries)} ports to existing server")
                else:
                    print(f"ℹ️ Port pool already has {len(existing_ports)} ports")
            
            print("\n🎯 Stream provisioning infrastructure is ready!")
            print("📋 Configuration Summary:")
            print(f"   • Shoutcast Server: localhost:8000")
            print(f"   • Port Range: 8100-8200 ({101} ports)")
            print(f"   • Admin Username: admin")
            print(f"   • Admin Password: changeme123 (CHANGE THIS!)")
            print("\n⚠️  SECURITY NOTE: Change the admin password in production!")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error initializing stream infrastructure: {e}")
            raise


if __name__ == "__main__":
    print("🚀 Initializing OneStopRadio Stream Provisioning Infrastructure...")
    asyncio.run(init_stream_infrastructure())