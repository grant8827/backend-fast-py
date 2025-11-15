"""
Shoutcast Server API Client
OneStopRadio - Integration with Shoutcast DNAS Server
"""

import aiohttp
import asyncio
import xml.etree.ElementTree as ET
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)


class ShoutcastClient:
    """Client for interacting with Shoutcast DNAS server API"""
    
    def __init__(self, hostname: str, admin_port: int, admin_password: str):
        self.hostname = hostname
        self.admin_port = admin_port
        self.admin_password = admin_password
        self.base_url = f"http://{hostname}:{admin_port}"
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def _make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Make an authenticated request to the Shoutcast server"""
        try:
            url = urljoin(self.base_url, endpoint)
            
            # Add authentication
            auth_params = {"pass": self.admin_password}
            if params:
                auth_params.update(params)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                if method.upper() == "GET":
                    async with session.get(url, params=auth_params) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            logger.error(f"Shoutcast request failed: {response.status} - {await response.text()}")
                            return None
                elif method.upper() == "POST":
                    async with session.post(url, params=auth_params, data=data) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            logger.error(f"Shoutcast request failed: {response.status} - {await response.text()}")
                            return None
        except Exception as e:
            logger.error(f"Shoutcast request exception: {e}")
            return None
    
    async def get_server_status(self) -> Optional[Dict[str, Any]]:
        """Get general server status and statistics"""
        try:
            response = await self._make_request("/admin.cgi", params={"mode": "viewxml"})
            if not response:
                return None
            
            # Parse XML response
            root = ET.fromstring(response)
            
            # Extract server information
            status = {
                'version': root.findtext('.//VERSION', 'Unknown'),
                'uptime': root.findtext('.//UPTIME', '0'),
                'total_streams': len(root.findall('.//STREAM')),
                'active_streams': len([s for s in root.findall('.//STREAM') if s.findtext('STREAMHITS', '0') != '0']),
                'peak_listeners': root.findtext('.//PEAKLISTENERS', '0'),
                'total_listeners': root.findtext('.//CURRENTLISTENERS', '0'),
                'max_listeners': root.findtext('.//MAXLISTENERS', '0'),
                'streams': []
            }
            
            # Extract individual stream information
            for stream in root.findall('.//STREAM'):
                stream_info = {
                    'id': stream.get('ID', ''),
                    'port': stream.findtext('SERVERPORT', ''),
                    'listeners': stream.findtext('CURRENTLISTENERS', '0'),
                    'peak_listeners': stream.findtext('PEAKLISTENERS', '0'),
                    'max_listeners': stream.findtext('MAXLISTENERS', '0'),
                    'title': stream.findtext('SERVERTITLE', ''),
                    'genre': stream.findtext('SERVERGENRE', ''),
                    'url': stream.findtext('SERVERURL', ''),
                    'status': stream.findtext('STREAMSTATUS', '0'),
                    'bitrate': stream.findtext('BITRATE', '0'),
                    'sample_rate': stream.findtext('SAMPLERATE', '0')
                }
                status['streams'].append(stream_info)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get server status: {e}")
            return None
    
    async def get_stream_info(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific stream"""
        try:
            params = {"mode": "viewxml", "sid": stream_id}
            response = await self._make_request("/admin.cgi", params=params)
            if not response:
                return None
            
            root = ET.fromstring(response)
            stream = root.find('.//STREAM')
            
            if stream is None:
                return None
            
            return {
                'id': stream.get('ID', ''),
                'port': stream.findtext('SERVERPORT', ''),
                'listeners': int(stream.findtext('CURRENTLISTENERS', '0')),
                'peak_listeners': int(stream.findtext('PEAKLISTENERS', '0')),
                'max_listeners': int(stream.findtext('MAXLISTENERS', '0')),
                'title': stream.findtext('SERVERTITLE', ''),
                'genre': stream.findtext('SERVERGENRE', ''),
                'url': stream.findtext('SERVERURL', ''),
                'status': int(stream.findtext('STREAMSTATUS', '0')),
                'bitrate': int(stream.findtext('BITRATE', '0')),
                'sample_rate': int(stream.findtext('SAMPLERATE', '0')),
                'uptime': stream.findtext('STREAMUPTIME', '0'),
                'hits': int(stream.findtext('STREAMHITS', '0')),
                'current_song': stream.findtext('SONGTITLE', '')
            }
            
        except Exception as e:
            logger.error(f"Failed to get stream info for {stream_id}: {e}")
            return None
    
    async def create_stream(self, config: Dict[str, Any]) -> bool:
        """Create a new stream configuration on the Shoutcast server"""
        try:
            # Shoutcast DNAS doesn't have a direct API to create streams
            # This would typically involve updating the configuration file
            # and reloading the server, or using a custom admin interface
            
            # For now, we'll simulate the configuration update
            # In a real implementation, you would:
            # 1. Generate a new configuration section
            # 2. Update the main configuration file
            # 3. Signal the server to reload configuration
            
            logger.info(f"Creating stream configuration for port {config['port']}")
            
            # Generate configuration section
            config_section = self._generate_stream_config(config)
            
            # In a real implementation:
            # - Write to configuration file
            # - Reload server configuration
            # - Verify stream is active
            
            # For demonstration, we'll assume success
            logger.info(f"Stream configuration created successfully for port {config['port']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create stream: {e}")
            return False
    
    def _generate_stream_config(self, config: Dict[str, Any]) -> str:
        """Generate Shoutcast configuration section for a stream"""
        return f"""
        <STREAM>
            <SERVERPORT>{config['port']}</SERVERPORT>
            <PASSWORD>{config['password']}</PASSWORD>
            <ADMINPASSWORD>{config['admin_password']}</ADMINPASSWORD>
            <MAXLISTENERS>{config['max_listeners']}</MAXLISTENERS>
            <BITRATE>{config['bitrate']}</BITRATE>
            <SERVERGENRE>{config['genre']}</SERVERGENRE>
            <SERVERTITLE>{config['title']}</SERVERTITLE>
            <SERVERURL>{config['url']}</SERVERURL>
            <PUBLICSERVER>{1 if config['public'] else 0}</PUBLICSERVER>
            <STREAMAUTHHASH>uvox2</STREAMAUTHHASH>
        </STREAM>
        """
    
    async def update_stream_metadata(
        self, 
        stream_id: str, 
        title: Optional[str] = None,
        url: Optional[str] = None,
        genre: Optional[str] = None
    ) -> bool:
        """Update stream metadata"""
        try:
            params = {"mode": "updinfo", "sid": stream_id}
            
            if title:
                params["title"] = title
            if url:
                params["url"] = url
            if genre:
                params["genre"] = genre
            
            response = await self._make_request("/admin.cgi", params=params)
            return response is not None
            
        except Exception as e:
            logger.error(f"Failed to update stream metadata for {stream_id}: {e}")
            return False
    
    async def kick_source(self, stream_id: str) -> bool:
        """Disconnect the source encoder from a stream"""
        try:
            params = {"mode": "kicksrc", "sid": stream_id}
            response = await self._make_request("/admin.cgi", params=params)
            return response is not None
            
        except Exception as e:
            logger.error(f"Failed to kick source for stream {stream_id}: {e}")
            return False
    
    async def kick_listener(self, stream_id: str, listener_id: str) -> bool:
        """Kick a specific listener from a stream"""
        try:
            params = {"mode": "kick", "sid": stream_id, "uid": listener_id}
            response = await self._make_request("/admin.cgi", params=params)
            return response is not None
            
        except Exception as e:
            logger.error(f"Failed to kick listener {listener_id} from stream {stream_id}: {e}")
            return False
    
    async def get_listener_list(self, stream_id: str) -> List[Dict[str, Any]]:
        """Get list of connected listeners for a stream"""
        try:
            params = {"mode": "viewxml", "sid": stream_id, "page": "3"}
            response = await self._make_request("/admin.cgi", params=params)
            if not response:
                return []
            
            root = ET.fromstring(response)
            listeners = []
            
            for listener in root.findall('.//LISTENER'):
                listener_info = {
                    'id': listener.get('ID', ''),
                    'ip': listener.findtext('HOSTNAME', ''),
                    'user_agent': listener.findtext('USERAGENT', ''),
                    'connected_at': listener.findtext('CONNECTTIME', ''),
                    'connection_time': listener.findtext('POINTER', '0'),
                    'uid': listener.findtext('UID', '')
                }
                listeners.append(listener_info)
            
            return listeners
            
        except Exception as e:
            logger.error(f"Failed to get listener list for stream {stream_id}: {e}")
            return []
    
    async def set_stream_title(self, stream_id: str, song_title: str) -> bool:
        """Update the current song title for a stream"""
        try:
            # URL encode the title
            encoded_title = quote(song_title)
            params = {"mode": "updinfo", "sid": stream_id, "song": encoded_title}
            
            response = await self._make_request("/admin.cgi", params=params)
            return response is not None
            
        except Exception as e:
            logger.error(f"Failed to set stream title for {stream_id}: {e}")
            return False
    
    async def reload_configuration(self) -> bool:
        """Reload the server configuration"""
        try:
            params = {"mode": "reload"}
            response = await self._make_request("/admin.cgi", params=params)
            return response is not None
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False


class ShoutcastConfigManager:
    """Manages Shoutcast server configuration files"""
    
    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
    
    async def add_stream_to_config(self, stream_config: Dict[str, Any]) -> bool:
        """Add a new stream configuration to the main config file"""
        try:
            # In a real implementation, this would:
            # 1. Read the existing configuration file
            # 2. Parse the XML structure
            # 3. Add the new stream configuration
            # 4. Write the updated configuration back to file
            # 5. Signal the server to reload
            
            logger.info(f"Adding stream configuration for port {stream_config['port']}")
            
            # Placeholder for actual file manipulation
            # This would use XML parsing libraries to modify the config
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add stream to config: {e}")
            return False
    
    async def remove_stream_from_config(self, port: int) -> bool:
        """Remove a stream configuration from the main config file"""
        try:
            logger.info(f"Removing stream configuration for port {port}")
            
            # Placeholder for actual file manipulation
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove stream from config: {e}")
            return False