#!/usr/bin/env python3
"""
Debug client for testing MCP server functionality with FastMCP 2.7+ and Python 3.11+.

This script tests the MCP weather server functionality using modern async patterns
and provides detailed output for debugging issues.
"""
import asyncio
import json
import logging
import os
import sys
import traceback
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

# Now import modules that depend on config
from main.clients.mcp_client import MCPWeatherClient
from main import create_app
from fastmcp import Client

# Configure logging for better debugging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_mcp_connection():
    """Test MCP client functionality using Flask config."""
    # Create app to get proper config
    app = create_app('development')
    
    with app.app_context():
        mcp_url = app.config.get('MCP_WEATHER_URL')
        logger.info(f"🔗 Using MCP URL from config: {mcp_url}")
        
        client = MCPWeatherClient()  # Will use Flask config automatically
        
        try:
            logger.info("🧪 Testing health check...")
            result = await client.health_check()
            logger.info(f"✅ Health check: {result}")
            
            if "error" not in result:
                logger.info("🔍 Testing location lookup...")
                location_result = await client.lookup_location("Sydney", 1)
                logger.info(f"📍 Location result: {location_result}")
                
                if location_result.get("locations"):
                    location_id = location_result["locations"][0]["id"]
                    logger.info(f"🌤️  Testing weather data for location {location_id}...")
                    weather_result = await client.get_weather(location_id)
                    logger.info(f"Weather data keys: {list(weather_result.keys()) if isinstance(weather_result, dict) else 'error'}")
                    
                    logger.info("🌊 Testing swell data...")
                    swell_result = await client.get_swell(location_id)
                    logger.info(f"Swell data keys: {list(swell_result.keys()) if isinstance(swell_result, dict) else 'error'}")
                    
                    return True
                else:
                    logger.error("❌ No locations found")
            else:
                logger.error(f"❌ Health check failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"💥 Test failed: {str(e)}", exc_info=True)
            return False
        
        return False

async def test_weather_data():
    """Test weather data retrieval and display all available fields"""
    try:
        async with Client(base_url="http://localhost:8000/mcp") as client:
            # Use Newcastle (location ID 2172)
            location_id = 2172
            
            print(f"\n=== Testing Weather Data for Location {location_id} ===")
            
            # Test weather
            print("\n--- Current Weather ---")
            weather_result = await client.call_tool("get_weather", {"location_id": location_id})
            if weather_result and weather_result.content:
                for item in weather_result.content:
                    if hasattr(item, 'text'):
                        data = json.loads(item.text)
                        print("Temperature Information:")
                        print(f"  Current: {data.get('temperature_current', 'N/A')}°C")
                        print(f"  Min: {data.get('temperature_min', 'N/A')}°C")
                        print(f"  Max: {data.get('temperature_max', 'N/A')}°C")
                        print(f"  Apparent: {data.get('temperature_apparent', 'N/A')}°C")
                        print(f"  Dewpoint: {data.get('dewpoint', 'N/A')}°C")
                        
                        print("\nAtmospheric Conditions:")
                        print(f"  Conditions: {data.get('conditions', 'N/A')}")
                        print(f"  Humidity: {data.get('humidity', 'N/A')}%")
                        print(f"  Pressure: {data.get('pressure', 'N/A')} hPa")
                        print(f"  Pressure MSL: {data.get('pressure_msl', 'N/A')} hPa")
                        print(f"  Pressure Trend: {data.get('pressure_trend', 'N/A')}")
                        print(f"  Cloud Cover: {data.get('cloud', 'N/A')}%")
                        print(f"  Visibility: {data.get('visibility', 'N/A')} km")
                        print(f"  UV Index: {data.get('uv_index', 'N/A')}")
                        
                        print("\nWind Information:")
                        print(f"  Speed: {data.get('wind_speed', 'N/A')} km/h")
                        print(f"  Direction: {data.get('wind_direction', 'N/A')}°")
                        print(f"  Direction Text: {data.get('wind_direction_text', 'N/A')}")
                        print(f"  Gust Speed: {data.get('wind_gust_speed', 'N/A')} km/h")
                        print(f"  Strength: {data.get('wind_strength', 'N/A')}")
                        print(f"  Trend: {data.get('wind_trend', 'N/A')}")
                        
                        print("\nRainfall Information:")
                        print(f"  Amount: {data.get('rainfall_amount', 'N/A')} mm")
                        print(f"  Since 9am: {data.get('rainfall_since9am', 'N/A')} mm")
                        print(f"  Probability: {data.get('rainfall_probability', 'N/A')}%")
                        
                        print("\nMetadata:")
                        print(f"  Updated: {data.get('updated_at', 'N/A')}")
                        print(f"  Icon: {data.get('icon', 'N/A')}")
            
            # Test swell
            print("\n--- Swell Forecast ---")
            swell_result = await client.call_tool("get_swell", {"location_id": location_id, "days": 3})
            if swell_result and swell_result.content:
                for item in swell_result.content:
                    if hasattr(item, 'text'):
                        data = json.loads(item.text)
                        print(f"Height: {data.get('height', 'N/A')} m")
                        print(f"Direction: {data.get('direction', 'N/A')}°")
                        print(f"Direction Text: {data.get('direction_text', 'N/A')}")
                        print(f"Period: {data.get('period', 'N/A')} s")
                        print(f"Power: {data.get('power', 'N/A')}")
                        print(f"Energy: {data.get('energy', 'N/A')}")
                        
                        forecast = data.get('forecast', [])
                        if forecast:
                            print(f"\nNext few readings:")
                            for i, reading in enumerate(forecast[:5]):
                                print(f"  {i+1}: {reading.get('height', 'N/A')}m @ {reading.get('period', 'N/A')}s from {reading.get('directionText', 'N/A')}")
            
            # Test wind
            print("\n--- Wind Forecast ---")
            wind_result = await client.call_tool("get_wind", {"location_id": location_id})
            if wind_result and wind_result.content:
                for item in wind_result.content:
                    if hasattr(item, 'text'):
                        data = json.loads(item.text)
                        print(f"Speed: {data.get('speed', 'N/A')} km/h")
                        print(f"Direction: {data.get('direction', 'N/A')}°")
                        print(f"Direction Text: {data.get('direction_text', 'N/A')}")
                        print(f"Gusts: {data.get('gusts', 'N/A')} km/h")
                        print(f"Strength: {data.get('strength', 'N/A')}")
                        print(f"Trend: {data.get('trend', 'N/A')}")
                        
                        forecast = data.get('forecast', [])
                        if forecast:
                            print(f"\nNext few readings:")
                            for i, reading in enumerate(forecast[:5]):
                                print(f"  {i+1}: {reading.get('speed', 'N/A')} km/h from {reading.get('directionText', 'N/A')} (gusts: {reading.get('gustSpeed', 'N/A')} km/h)")
            
    except Exception as e:
        print(f"Error testing weather data: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        success = asyncio.run(test_mcp_connection())
        if success:
            print("\n🎉 All tests passed!")
            # Also run the detailed weather data test
            asyncio.run(test_weather_data())
        else:
            print("\n💥 Tests failed!")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    sys.exit(0 if success else 1) 