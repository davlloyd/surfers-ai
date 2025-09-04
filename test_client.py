import asyncio, json
from fastmcp import Client
from typing import Dict

client = Client("https://mcp-weather-server.apps.tas.tanzu.rocks/mcp") # Assumes my_mcp_server.py exists

async def main():
    # Connection is established here
    async with client:
        print(f"Client connected: {client.is_connected()}")

        # Make MCP calls within the context
        tools = await client.list_tools()
        for tool in tools:
            print (f"/nTool: {tool.name} - {tool.description}")

        if any(tool.name == "health" for tool in tools):
            health_status = await client.call_tool("health")
            print(f"\nHealth status: {health_status}")

        if any(tool.name == "lookup_location" for tool in tools):
            location_status = await client.call_tool("lookup_location", {"name": "Townsville", "limit": 1})
            print(f"\nLocation status: {location_status}")
            data = json.loads(location_status[0].text)
            location_id = data["locations"][0]["id"]
            params = dict({"location_id": location_id})


        if any(tool.name == "get_weather" for tool in tools):
            location_weather = await client.call_tool("get_weather", params)
            print(f"\nLocation weather: {location_weather}")

        if any(tool.name == "get_swell" for tool in tools):
            location_swell = await client.call_tool("get_swell", params)
            print(f"\nLocation swell: {location_swell}")

        if any(tool.name == "get_location_data" for tool in tools):
            location_weather = await client.call_tool("get_location_data", params)
            print(f"\nLocation weather: {location_weather}")

        if any(tool.name == "get_wind" for tool in tools):
            location_wind = await client.call_tool("get_wind", params)
            print(f"\n\nLocation wind: {location_wind}")

    # Connection is closed automatically here
    print(f"Client connected: {client.is_connected()}")

if __name__ == "__main__":
    asyncio.run(main())