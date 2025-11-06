#!/usr/bin/env python3
"""
PostgreSQL Database Verification Script
Tests database connection, models, and basic CRUD operations
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any

# Set the DATABASE_URL environment variable
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:JLiWeljtTNmpmimgYJVzLhgBRBQZsqcJ@metro.proxy.rlwy.net:14967/railway'

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.database import engine, AsyncSessionLocal
    from app.models import User, Station, Track, Playlist, PlaylistTrack, StreamingSession, DJSet
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession
    import uuid
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're in the backend-fast-py directory and have installed dependencies")
    sys.exit(1)


async def test_database_connection():
    """Test basic database connection and table existence"""
    print("🔍 Testing PostgreSQL Connection...")
    
    try:
        async with engine.connect() as conn:
            # Test connection
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to: {version}")
            
            # Check tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            expected_tables = {
                'users', 'stations', 'tracks', 'playlists', 
                'playlist_tracks', 'streaming_sessions', 'dj_sets', 
                'alembic_version'
            }
            actual_tables = {table[0] for table in tables}
            
            print(f"✅ Tables found: {len(actual_tables)}")
            for table in sorted(actual_tables):
                print(f"   - {table}")
            
            missing_tables = expected_tables - actual_tables
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            
            print("✅ All expected tables present")
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_model_operations():
    """Test basic CRUD operations on all models"""
    print("\n🔍 Testing Model Operations...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Test User creation
            test_user = User(
                username="test_dj",
                email="test@example.com",
                hashed_password="hashed_test_password",
                full_name="Test DJ",
                dj_name="DJ Test",
                bio="Test DJ bio"
            )
            session.add(test_user)
            await session.flush()  # Get the user ID
            print(f"✅ User created: {test_user.id}")
            
            # Test Station creation
            test_station = Station(
                name="Test Radio Station",
                description="A test radio station",
                owner_id=test_user.id,
                slug="test-radio-station",
                genre="Electronic",
                stream_url="https://stream.example.com/test"
            )
            session.add(test_station)
            await session.flush()
            print(f"✅ Station created: {test_station.id}")
            
            # Test Track creation
            test_track = Track(
                title="Test Track",
                artist="Test Artist",
                uploader_id=test_user.id,
                file_path="/uploads/test-track.mp3",
                duration=180,  # 3 minutes
                bpm=128,
                key="Am",
                genre="House"
            )
            session.add(test_track)
            await session.flush()
            print(f"✅ Track created: {test_track.id}")
            
            # Test Playlist creation
            test_playlist = Playlist(
                name="Test Playlist",
                description="A test playlist",
                user_id=test_user.id,
                is_public=True
            )
            session.add(test_playlist)
            await session.flush()
            print(f"✅ Playlist created: {test_playlist.id}")
            
            # Test PlaylistTrack creation
            playlist_track = PlaylistTrack(
                playlist_id=test_playlist.id,
                track_id=test_track.id,
                position=1
            )
            session.add(playlist_track)
            await session.flush()
            print(f"✅ PlaylistTrack created: {playlist_track.id}")
            
            # Test StreamingSession creation  
            streaming_session = StreamingSession(
                title="Test Stream Session",
                description="A test streaming session",
                station_id=test_station.id,
                started_at=datetime.now(timezone.utc),
                peak_listeners=10,
                bitrate=128000,  # 128 kbps
                stream_key="test_stream_key_12345"
            )
            session.add(streaming_session)
            await session.flush()
            print(f"✅ StreamingSession created: {streaming_session.id}")
            
            # Test DJSet creation
            dj_set = DJSet(
                title="Test DJ Set",
                description="A test DJ set",
                dj_id=test_user.id,
                genre="Electronic",
                recorded_at=datetime.now(timezone.utc),
                duration=3600.0,  # 1 hour in seconds (float)
                file_path="/uploads/test-dj-set.mp3",
                file_size=104857600  # 100MB
            )
            session.add(dj_set)
            await session.flush()
            print(f"✅ DJSet created: {dj_set.id}")
            
            # Commit all changes
            await session.commit()
            print("✅ All test records committed successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Model operation failed: {e}")
            await session.rollback()
            return False


async def test_relationships():
    """Test model relationships and queries"""
    print("\n🔍 Testing Model Relationships...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Query with relationships
            result = await session.execute(text("""
                SELECT u.username, s.name as station_name, COUNT(t.id) as track_count
                FROM users u
                LEFT JOIN stations s ON u.id = s.owner_id  
                LEFT JOIN tracks t ON u.id = t.uploader_id
                WHERE u.username = 'test_dj'
                GROUP BY u.id, u.username, s.name
            """))
            
            row = result.fetchone()
            if row:
                print(f"✅ User: {row[0]}, Station: {row[1]}, Tracks: {row[2]}")
            
            # Test playlist tracks
            result = await session.execute(text("""
                SELECT p.name, COUNT(pt.id) as track_count
                FROM playlists p
                LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
                WHERE p.name = 'Test Playlist'
                GROUP BY p.id, p.name
            """))
            
            row = result.fetchone()
            if row:
                print(f"✅ Playlist: {row[0]}, Track Count: {row[1]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Relationship test failed: {e}")
            return False


async def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Delete in proper order to handle foreign keys
            await session.execute(text("DELETE FROM playlist_tracks WHERE position = 1"))
            await session.execute(text("DELETE FROM streaming_sessions WHERE title = 'Test Stream Session'"))
            await session.execute(text("DELETE FROM dj_sets WHERE title = 'Test DJ Set'"))
            await session.execute(text("DELETE FROM playlists WHERE name = 'Test Playlist'"))
            await session.execute(text("DELETE FROM tracks WHERE title = 'Test Track'"))
            await session.execute(text("DELETE FROM stations WHERE name = 'Test Radio Station'"))
            await session.execute(text("DELETE FROM users WHERE username = 'test_dj'"))
            
            await session.commit()
            print("✅ Test data cleaned up")
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            await session.rollback()


async def main():
    """Run all database verification tests"""
    print("🚀 OneStopRadio PostgreSQL Database Verification")
    print("=" * 50)
    
    # Test connection
    connection_ok = await test_database_connection()
    if not connection_ok:
        print("\n❌ Database connection failed. Exiting.")
        return
    
    # Test model operations
    models_ok = await test_model_operations()
    if not models_ok:
        print("\n❌ Model operations failed.")
        return
    
    # Test relationships
    relationships_ok = await test_relationships()
    if not relationships_ok:
        print("\n❌ Relationship tests failed.")
        
    # Cleanup
    await cleanup_test_data()
    
    # Final status
    print("\n" + "=" * 50)
    if connection_ok and models_ok and relationships_ok:
        print("🎉 All database tests passed!")
        print("✅ PostgreSQL migration verification complete")
        print("✅ Ready for Railway deployment")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    # Close engine
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())