#!/usr/bin/env python3
"""
Test script to verify FastMCP 2.7+ and Python 3.11+ compatibility.

This script tests basic MCP functionality to ensure TaskGroup and other
async issues are resolved with the updated FastMCP patterns.
"""
import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from main.clients.mcp_client import MCPWeatherClient
from main import create_app

# Configure logging with detailed formatting for debugging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_simple_call() -> bool:
    """Test simple MCP calls using FastMCP 2.7+ to verify TaskGroup issues are resolved."""
    try:
        client = MCPWeatherClient("http://localhost:8000")
        logger.info("🧪 Testing FastMCP 2.7+ client connectivity...")
        
        # Test 1: Health check
        logger.info("1️⃣ Testing health check...")
        result = await client.health_check()
        logger.info(f"Health check result: {result}")
        
        if "error" not in result:
            logger.info("✅ Health check successful")
            
            # Test 2: Location lookup
            logger.info("2️⃣ Testing location lookup...")
            location_result = await client.lookup_location("Sydney", 1)
            logger.info(f"Location result: {location_result}")
            
            if "error" not in location_result and location_result.get("locations"):
                location_id = location_result["locations"][0]["id"]
                logger.info(f"📍 Found location ID: {location_id}")
                
                # Test 3: Enhanced weather data
                logger.info("3️⃣ Testing enhanced weather data...")
                weather_result = await client.get_weather(location_id)
                
                if "error" not in weather_result:
                    logger.info("✅ Enhanced weather data successful")
                    logger.info(f"📊 Weather fields available: {list(weather_result.keys())}")
                    
                    # Test 4: Swell data
                    logger.info("4️⃣ Testing swell data...")
                    swell_result = await client.get_swell(location_id)
                    
                    if "error" not in swell_result:
                        logger.info("✅ Swell data successful")
                        return True
                    else:
                        logger.error(f"❌ Swell data failed: {swell_result['error']}")
                else:
                    logger.error(f"❌ Weather data failed: {weather_result['error']}")
            else:
                logger.error("❌ Location lookup failed")
        else:
            logger.error(f"❌ Health check failed: {result['error']}")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {str(e)}", exc_info=True)
        return False

async def test_fallback_individual_calls() -> bool:
    """Test individual weather calls to verify fallback functionality."""
    try:
        client = MCPWeatherClient("http://localhost:8000")
        logger.info("🔄 Testing fallback individual calls...")
        
        # Get location first
        location_result = await client.lookup_location("Newcastle", 1)
        if "error" in location_result or not location_result.get("locations"):
            logger.error("❌ Could not get location for fallback test")
            return False
        
        location_id = location_result["locations"][0]["id"]
        
        # Test individual calls
        weather_data = await client.get_weather(location_id)
        swell_data = await client.get_swell(location_id)
        
        if "error" not in weather_data and "error" not in swell_data:
            logger.info("✅ Individual calls successful")
            return True
        else:
            logger.error("❌ Individual calls failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fallback test failed: {str(e)}", exc_info=True)
        return False

def test_environment_loading() -> bool:
    """Test that environment variables are loaded correctly."""
    try:
        # Create app to test config loading
        app = create_app('development')
        
        with app.app_context():
            logger.info("🔧 Testing environment variable loading...")
            
            # Test that config values are accessible
            app_name = app.config.get('APP_NAME')
            version = app.config.get('VERSION')
            mcp_url = app.config.get('MCP_WEATHER_URL')
            openai_model = app.config.get('OPENAI_MODEL')
            
            logger.info(f"📱 App Name: {app_name}")
            logger.info(f"🏷️ Version: {version}")
            logger.info(f"🔗 MCP URL: {mcp_url}")
            logger.info(f"🤖 OpenAI Model: {openai_model}")
            
            # Check if environment variables are being used
            env_mcp_url = os.getenv('MCP_WEATHER_URL')
            env_openai_model = os.getenv('OPENAI_MODEL')
            
            logger.info(f"🌍 ENV MCP_WEATHER_URL: {env_mcp_url}")
            logger.info(f"🌍 ENV OPENAI_MODEL: {env_openai_model}")
            
            if app_name and version:
                logger.info("✅ Configuration loaded successfully")
                return True
            else:
                logger.error("❌ Configuration values missing")
                return False
                
    except Exception as e:
        logger.error(f"❌ Environment test failed: {str(e)}", exc_info=True)
        return False

def main() -> None:
    """Main test runner with comprehensive error handling."""
    try:
        print("🚀 Starting FastMCP 2.7+ compatibility tests...")
        
        # Test 1: Basic functionality
        success1 = asyncio.run(test_simple_call())
        
        # Test 2: Fallback functionality  
        success2 = asyncio.run(test_fallback_individual_calls())
        
        # Test 3: Environment variable loading
        success3 = test_environment_loading()
        
        if success1 and success2 and success3:
            print("\n🎉 All tests passed! FastMCP 2.7+ integration is working correctly!")
            sys.exit(0)
        elif success1 and success2:
            print("\n⚠️ Basic tests passed but environment variable loading needs attention")
            sys.exit(1)
        elif success1:
            print("\n⚠️ Basic tests passed but fallback needs attention")
            sys.exit(1)
        else:
            print("\n💥 Tests failed - check server and configuration")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 