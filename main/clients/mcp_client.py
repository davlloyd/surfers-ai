import os
import json
import logging
from typing import Dict, Any, Optional
import asyncio
import httpx
from fastmcp import Client

logger = logging.getLogger(__name__)

class MCPWeatherClient:
    """Client for communicating with the MCP weather server using FastMCP 2.7+."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize the MCP weather client.
        
        Args:
            base_url: Optional base URL for the MCP server. Defaults to environment variable.
        """
        # Use provided base_url or get from environment with default
        url = base_url or os.getenv("MCP_WEATHER_URL", "http://localhost:8000")
        
        # Ensure URL ends with /mcp for streamable-http transport
        if not url.endswith('/mcp'):
            url = f"{url.rstrip('/')}/mcp"
            
        self.base_url = url
        logger.info(f"Initialized MCPWeatherClient with URL: {self.base_url}")
        self._location_cache = {}  # Cache for location data

    async def _handle_response(self, response: Any, context: str) -> Dict[str, Any]:
        """Helper method to handle FastMCP 2.7+ responses consistently."""
        if response:
            try:
                # FastMCP 2.7+ returns the response directly
                if isinstance(response, dict):
                    return response
                # If it's a string, try to parse as JSON
                elif isinstance(response, str):
                    return json.loads(response)
                # If it's a response object (FastMCP 2.7+), it has a `content` list
                else:
                    # Prefer new FastMCP Response contract: object with `.content`
                    if hasattr(response, 'content'):
                        content_items = getattr(response, 'content', None)
                        if content_items and isinstance(content_items, list):
                            first_item = content_items[0]
                            if hasattr(first_item, 'text'):
                                try:
                                    data = json.loads(first_item.text)
                                    logger.debug(f"Response data from {context}: {json.dumps(data, indent=2)}")
                                    return data
                                except json.JSONDecodeError:
                                    return {"text": first_item.text}
                            logger.warning(f"First response item missing text attribute from {context}: {first_item}")
                            return {"error": f"First response item missing text attribute from {context}"}
                        logger.warning(f"Empty response content from {context}: {response}")
                        return {"error": f"Empty response content from {context}"}

                    # Backward compatibility: sometimes raw list is returned
                    if isinstance(response, list) and len(response) > 0:
                        first_item = response[0]
                        if hasattr(first_item, 'text'):
                            try:
                                data = json.loads(first_item.text)
                                logger.debug(f"Response data from {context}: {json.dumps(data, indent=2)}")
                                return data
                            except json.JSONDecodeError:
                                return {"text": first_item.text}
                        logger.warning(f"First response item missing text attribute from {context}: {first_item}")
                        return {"error": f"First response item missing text attribute from {context}"}

                    logger.warning(f"Empty or invalid response from {context}: {response}")
                    return {"error": f"Empty or invalid response from {context}"}
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from {context}: {response}")
                return {"error": f"Failed to parse response as JSON: {str(e)}"}
        else:
            logger.warning(f"Empty response from MCP server for {context}")
            return {"error": f"Empty response from MCP server for {context}"}

    async def _call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to call an MCP tool using FastMCP 2.7+ patterns."""
        try:
            async with Client(self.base_url) as client:
                response = await client.call_tool(tool_name, params)
                return await self._handle_response(response, f"tool '{tool_name}'")
                    
        except httpx.ConnectError as e:
            logger.error(f"Connection error calling tool '{tool_name}': {str(e)}")
            return {"error": "Failed to connect to MCP server. Please check if the server is running."}
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error calling tool '{tool_name}': {str(e)}")
            return {"error": "Request timed out. The MCP server may be overloaded."}
        except Exception as e:
            error_msg = str(e)
            if "TaskGroup" in error_msg or "ExceptionGroup" in error_msg:
                logger.error(f"Async error calling tool '{tool_name}': {error_msg}", exc_info=True)
                return {"error": "Internal async error. Please try again."}
            else:
                logger.error(f"Client error calling tool '{tool_name}': {error_msg}", exc_info=True)
                return {"error": f"Client error: {error_msg}"}

    async def lookup_location(self, name: str, limit: int = 5) -> Dict[str, Any]:
        """Look up a location by name, using cache if available."""
        try:
            # Check cache first
            cache_key = f"{name}:{limit}"
            if cache_key in self._location_cache:
                logger.debug(f"Cache hit for location lookup: {cache_key}")
                return self._location_cache[cache_key]
            
            # If not in cache, make the API call
            result = await self._call_mcp_tool("lookup_location", {"name": name, "limit": limit})
            
            # Cache the result if it's valid
            if "error" not in result and result.get("locations"):
                self._location_cache[cache_key] = result
                logger.debug(f"Cached location lookup result for: {cache_key}")
                
                # Also cache by location ID for reverse lookups
                for location in result["locations"]:
                    if "id" in location:
                        self._location_cache[f"id:{location['id']}"] = location
            
            return result
        except Exception as e:
            logger.error("Error in lookup_location", exc_info=True)
            return {"error": f"Error looking up location: {str(e)}"}
    
    async def get_location_by_id(self, location_id: int) -> Optional[Dict[str, Any]]:
        """Get location data by ID from cache."""
        cache_key = f"id:{location_id}"
        return self._location_cache.get(cache_key)
    
    async def get_weather(self, location_id: int) -> Dict[str, Any]:
        """Get weather data for a specific location."""
        result = await self._call_mcp_tool("get_weather", {"location_id": location_id})
        if "error" in result:
            return result
        
        # Extract entries from the response
        if "entries" in result:
            return {
                "entries": result["entries"],
                "units": result.get("units"),
                "issueDateTime": result.get("issueDateTime")
            }
        return result
    
    async def get_swell(self, location_id: int, days: int = 3) -> Dict[str, Any]:
        """Get swell data for a specific location."""
        result = await self._call_mcp_tool("get_swell", {"location_id": location_id, "days": days})
        if "error" in result:
            return result
        
        # Extract entries from the response
        if "entries" in result:
            return {
                "entries": result["entries"],
                "units": result.get("units"),
                "issueDateTime": result.get("issueDateTime"),
                "message": result.get("message")  # Include message for when swell data is not available
            }
        return result
    
    async def get_wind(self, location_id: int) -> Dict[str, Any]:
        """Get wind data for a specific location."""
        result = await self._call_mcp_tool("get_wind", {"location_id": location_id})
        if "error" in result:
            return result
        
        # Extract entries from the response
        if "entries" in result:
            return {
                "entries": result["entries"],
                "units": result.get("units"),
                "issueDateTime": result.get("issueDateTime")
            }
        return result
        
    async def get_location_data(self, location_id: int, days: int = 3) -> Dict[str, Any]:
        """Get all weather-related data for a location in a single request."""
        result = await self._call_mcp_tool("get_location_data", {
            "location_id": location_id,
            "days": days
        })
        if "error" in result:
            return result
        
        # Process each section of the response
        processed_result = {}
        
        # Process weather data
        if "weather" in result:
            weather = result["weather"]
            if "entries" in weather:
                processed_result["weather"] = {
                    "entries": weather["entries"],
                    "units": weather.get("units"),
                    "issueDateTime": weather.get("issueDateTime")
                }
            else:
                processed_result["weather"] = weather
        
        # Process swell data
        if "swell" in result:
            swell = result["swell"]
            if "entries" in swell:
                processed_result["swell"] = {
                    "entries": swell["entries"],
                    "units": swell.get("units"),
                    "issueDateTime": swell.get("issueDateTime"),
                    "message": swell.get("message")
                }
            else:
                processed_result["swell"] = swell
        
        # Process wind data (from weather response)
        if "wind" in result:
            wind = result["wind"]
            if "entries" in wind:
                processed_result["wind"] = {
                    "entries": wind["entries"],
                    "units": wind.get("units"),
                    "issueDateTime": wind.get("issueDateTime")
                }
            else:
                processed_result["wind"] = wind
        
        return processed_result
        
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the MCP server."""
        return await self._call_mcp_tool("health", {})
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools from the MCP server using FastMCP 2.7+."""
        try:
            async with Client(self.base_url) as client:
                tools = await client.list_tools()
                return {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description
                        }
                        for tool in tools
                    ]
                }
        except Exception as e:
            logger.error(f"Error listing tools: {e}", exc_info=True)
            return {"error": f"Error listing tools: {str(e)}"}
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources from the MCP server using FastMCP 2.7+."""
        try:
            async with Client(self.base_url) as client:
                resources = await client.list_resources()
                return {
                    "resources": [
                        {
                            "uri": resource.uri,
                            "name": resource.name,
                            "description": resource.description,
                            "mime_type": resource.mimeType
                        }
                        for resource in resources
                    ]
                }
        except Exception as e:
            logger.error(f"Error listing resources: {e}", exc_info=True)
            return {"error": f"Error listing resources: {str(e)}"}
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource from the MCP server using FastMCP 2.7+."""
        try:
            async with Client(self.base_url) as client:
                response = await client.read_resource(uri)
                return await self._handle_response(response, f"resource '{uri}'")
                    
        except Exception as e:
            logger.error(f"Error reading resource '{uri}': {e}", exc_info=True)
            return {"error": f"Error reading resource: {str(e)}"}
    
    async def close(self):
        """Close method for compatibility - FastMCP 2.7+ handles connections via context managers."""
        logger.debug("Close called - connections are managed via context managers in FastMCP 2.7+")
        pass 