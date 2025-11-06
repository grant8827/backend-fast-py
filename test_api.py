"""
Simple test script for FastAPI endpoints
Run this after starting the server to verify everything works
"""

import asyncio
import aiohttp
import json

API_BASE = "http://localhost:8000"

async def test_api_endpoints():
    """Test basic API functionality"""
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing OneStopRadio FastAPI Backend")
        print("=" * 50)
        
        # Test health check
        print("\n1. Testing Health Check...")
        try:
            async with session.get(f"{API_BASE}/api/health/") as resp:
                data = await resp.json()
                print(f"✅ Health Check: {data}")
        except Exception as e:
            print(f"❌ Health Check Failed: {e}")
            return
        
        # Test root endpoint
        print("\n2. Testing Root Endpoint...")
        try:
            async with session.get(f"{API_BASE}/") as resp:
                data = await resp.json()
                print(f"✅ Root: {data}")
        except Exception as e:
            print(f"❌ Root Endpoint Failed: {e}")
        
        # Test user registration
        print("\n3. Testing User Registration...")
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "dj_name": "Test DJ"
        }
        
        try:
            async with session.post(
                f"{API_BASE}/api/v1/auth/register/",
                json=user_data
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    print(f"✅ Registration Success: User created")
                    access_token = data.get("tokens", {}).get("access_token")
                    
                    if access_token:
                        print("\n4. Testing Authenticated Endpoints...")
                        headers = {"Authorization": f"Bearer {access_token}"}
                        
                        # Test user profile
                        async with session.get(
                            f"{API_BASE}/api/v1/auth/me/",
                            headers=headers
                        ) as profile_resp:
                            profile_data = await profile_resp.json()
                            print(f"✅ User Profile: {profile_data.get('username')}")
                        
                        # Test station creation/retrieval
                        async with session.get(
                            f"{API_BASE}/api/v1/stations/",
                            headers=headers
                        ) as station_resp:
                            station_data = await station_resp.json()
                            print(f"✅ Station Created: {station_data.get('name')}")
                            
                else:
                    error_data = await resp.json()
                    print(f"❌ Registration Failed: {error_data}")
                    
        except Exception as e:
            print(f"❌ Registration Test Failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 API Testing Complete!")
        print("\n📚 Full API Documentation: http://localhost:8000/api/docs")


if __name__ == "__main__":
    print("Starting API tests...")
    print("Make sure the FastAPI server is running on localhost:8000")
    print("Run: python run_server.py")
    print()
    
    try:
        asyncio.run(test_api_endpoints())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure the server is running: python run_server.py")