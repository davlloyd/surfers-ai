import asyncio
from fastmcp import Client
from main.clients.mcp_client import MCPWeatherClient
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_direct_client():
    """Test direct FastMCP 2.7+ Client usage."""
    print("\n=== Testing Direct FastMCP 2.7+ Client ===")
    
    client = Client("http://localhost:8000/mcp")

    async with client:
        print(f"Client connected: {client.is_connected()}")

        # Test listing tools using modern patterns
        try:
            tools = await client.list_tools()
            print(f"Available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
        except Exception as e:
            print(f"Error listing tools: {e}")

        # Test listing resources using modern patterns  
        try:
            resources = await client.list_resources()
            print(f"Available resources: {len(resources)}")
            for resource in resources:
                print(f"  - {resource.uri}: {resource.name}")
        except Exception as e:
            print(f"Error listing resources: {e}")

        # Test health check tool
        try:
            health_response = await client.call_tool("health", {})
            
            # Handle FastMCP 2.7+ response format
            if health_response and hasattr(health_response, 'content') and health_response.content:
                health_text = health_response.content[0].text
                health_data = json.loads(health_text)
                print(f"Health status: {health_data}")
            else:
                print("Invalid health response format")
        except Exception as e:
            print(f"Error checking health: {e}")

        # Test location lookup tool
        try:
            location_response = await client.call_tool("lookup_location", {"name": "Townsville", "limit": 1})
            
            # Handle FastMCP 2.7+ response format
            if location_response and hasattr(location_response, 'content') and location_response.content:
                location_text = location_response.content[0].text
                location_data = json.loads(location_text)
                print(f"Location lookup: {location_data}")
            else:
                print("Invalid location response format")
        except Exception as e:
            print(f"Error looking up location: {e}")

    print(f"Client connected after context: {client.is_connected()}")

async def test_enhanced_client():
    """Test the enhanced MCPWeatherClient with FastMCP 2.7+ patterns."""
    print("\n=== Testing Enhanced MCPWeatherClient ===")
    
    client = MCPWeatherClient("http://localhost:8000")
    
    # Test health check
    print("Testing health check...")
    health_result = await client.health_check()
    print(f"Health result: {health_result}")
    
    # Test listing tools
    print("\nTesting list tools...")
    tools_result = await client.list_tools()
    if "error" not in tools_result:
        print(f"Found {len(tools_result['tools'])} tools:")
        for tool in tools_result['tools']:
            print(f"  - {tool['name']}: {tool['description']}")
            if tool.get('input_schema'):
                print(f"    Schema: {tool['input_schema']}")
    else:
        print(f"Error listing tools: {tools_result['error']}")
    
    # Test listing resources
    print("\nTesting list resources...")
    resources_result = await client.list_resources()
    if "error" not in resources_result:
        print(f"Found {len(resources_result['resources'])} resources:")
        for resource in resources_result['resources']:
            print(f"  - {resource['uri']}: {resource['name']}")
            print(f"    Type: {resource['mime_type']}")
    else:
        print(f"Error listing resources: {resources_result['error']}")
    
    # Test reading a resource
    print("\nTesting read resource...")
    info_result = await client.read_resource("config://server/info")
    if "error" not in info_result:
        print(f"Server info: {info_result}")
    else:
        print(f"Error reading resource: {info_result['error']}")
    
    # Test location lookup with caching
    print("\nTesting location lookup...")
    location_result = await client.lookup_location("Townsville", limit=1)
    if "error" not in location_result:
        print(f"Location result: {location_result}")
        
        # Test getting location data if we found a location
        if location_result.get("locations"):
            location_id = location_result["locations"][0]["id"]
            print(f"\nTesting get location data for ID {location_id}...")
            data_result = await client.get_location_data(location_id)
            if "error" not in data_result:
                print(f"Location data keys: {list(data_result.keys())}")
            else:
                print(f"Error getting location data: {data_result['error']}")
    else:
        print(f"Error looking up location: {location_result['error']}")
    
    # Test cache retrieval
    print("\nTesting cache retrieval...")
    cached_location = await client.get_location_by_id(1)  # Assuming ID 1 exists
    if cached_location:
        print(f"Cached location: {cached_location}")
    else:
        print("No cached location found for ID 1")

async def main():
    """Main test function."""
    print("FastMCP 2.7+ Client Testing")
    print("=" * 40)
    
    try:
        await test_direct_client()
        await test_enhanced_client()
        print("\n=== All tests completed ===")
    except Exception as e:
        logger.error(f"Test error: {e}", exc_info=True)
        print(f"\nTest failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())