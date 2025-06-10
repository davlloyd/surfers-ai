import os
from fastmcp import Client
from typing import Dict, Any, Optional
import logging
from contextlib import asynccontextmanager
import asyncio
import json
import httpx

logger = logging.getLogger(__name__)

class MCPWeatherClient:
    """Client for communicating with the MCP weather server using fastmcp.Client."""
    
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

    @asynccontextmanager
    async def get_client(self):
        """Get a properly managed client connection using async context manager."""
        client = None
        try:
            # Use FastMCP 2.7+ Client with streamable-http transport
            client = Client(self.base_url)
            async with client as connected_client:
                yield connected_client
        except Exception as e:
            logger.error(f"Error with client connection: {e}", exc_info=True)
            raise
        finally:
            if client:
                logger.debug("Client connection closed automatically")

    async def _call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to call an MCP tool and handle response using modern FastMCP 2.7+ patterns."""
        try:
            async with self.get_client() as client:
                # Use modern FastMCP 2.7+ call_tool method
                response = await client.call_tool(tool_name, params)
                
                # Handle FastMCP 2.7+ response format with proper content parsing
                if response and hasattr(response, 'content') and response.content:
                    # Modern response format: response.content is a list of content items
                    content_items = response.content
                    if content_items and len(content_items) > 0:
                        content_item = content_items[0]
                        if hasattr(content_item, 'text'):
                            try:
                                return json.loads(content_item.text)
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON from tool '{tool_name}' response: {content_item.text}")
                                return {"error": f"Failed to parse response as JSON: {str(e)}"}
                        else:
                            logger.warning(f"Tool '{tool_name}' response content item has no text attribute")
                            return {"error": f"Tool '{tool_name}' response content is not text."}
                    else:
                        logger.warning(f"Tool '{tool_name}' response has empty content list")
                        return {"error": "Empty response content from MCP server."}
                elif response and isinstance(response, list) and len(response) > 0:
                    # Legacy response format handling for backward compatibility
                    content_item = response[0]
                    if hasattr(content_item, 'text'):
                        try:
                            return json.loads(content_item.text)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON from legacy response: {content_item.text}")
                            return {"error": f"Failed to parse response as JSON: {str(e)}"}
                    else:
                        logger.warning(f"Tool '{tool_name}' legacy response is not text content. Content: {content_item}")
                        return {"error": f"Tool '{tool_name}' response is not text content."}
                else:
                    # Handle empty or malformed responses
                    logger.warning(f"Malformed or empty response from MCP server for tool '{tool_name}'. Response: {response}")
                    return {"error": "Malformed or empty response from MCP server."}
                    
        except httpx.ConnectError as e:
            logger.error(f"Connection error calling tool '{tool_name}': {str(e)}")
            return {"error": "Failed to connect to MCP server. Please check if the server is running."}
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error calling tool '{tool_name}': {str(e)}")
            return {"error": "Request timed out. The MCP server may be overloaded."}
        except Exception as e:
            # Log the full error with traceback for debugging
            logger.error(f"Client-side error calling tool '{tool_name}': {str(e)}", exc_info=True)
            return {"error": f"Client error: {str(e)}"}

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
        return await self._call_mcp_tool("get_weather", {"location_id": location_id})
    
    async def get_swell(self, location_id: int, days: int = 3) -> Dict[str, Any]:
        """Get swell data for a specific location."""
        return await self._call_mcp_tool("get_swell", {"location_id": location_id, "days": days})
    
    async def get_wind(self, location_id: int) -> Dict[str, Any]:
        """Get wind data for a specific location."""
        return await self._call_mcp_tool("get_wind", {"location_id": location_id})
        
    async def get_location_data(self, location_id: int, days: int = 3) -> Dict[str, Any]:
        """Get all weather-related data for a location in a single request."""
        return await self._call_mcp_tool("get_location_data", {
            "location_id": location_id,
            "days": days
        })
        
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the MCP server."""
        return await self._call_mcp_tool("health", {})
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools from the MCP server."""
        try:
            async with self.get_client() as client:
                tools = await client.list_tools()
                return {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema.model_dump() if hasattr(tool, 'inputSchema') else None
                        }
                        for tool in tools
                    ]
                }
        except Exception as e:
            logger.error(f"Error listing tools: {e}", exc_info=True)
            return {"error": f"Error listing tools: {str(e)}"}
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources from the MCP server."""
        try:
            async with self.get_client() as client:
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
        """Read a specific resource from the MCP server."""
        try:
            async with self.get_client() as client:
                resource = await client.read_resource(uri)
                
                # Handle FastMCP 2.7+ resource response format
                if resource and hasattr(resource, 'content') and resource.content:
                    content_items = resource.content
                    if content_items and len(content_items) > 0:
                        content_item = content_items[0]
                        if hasattr(content_item, 'text'):
                            try:
                                return json.loads(content_item.text)
                            except json.JSONDecodeError:
                                # Return raw text if not JSON
                                return {"text": content_item.text}
                        else:
                            return {"error": "Resource content is not text"}
                    else:
                        return {"error": "Empty resource content"}
                else:
                    return {"error": "No resource content returned"}
                    
        except Exception as e:
            logger.error(f"Error reading resource '{uri}': {e}", exc_info=True)
            return {"error": f"Error reading resource: {str(e)}"}
    
    async def close(self):
        """Close method for compatibility - modern implementation uses context manager."""
        # Modern FastMCP 2.7+ client connections are managed via context managers
        # This method is kept for backward compatibility but doesn't need to do anything
        logger.debug("Close called - connections are managed via context managers in modern FastMCP")
        pass 