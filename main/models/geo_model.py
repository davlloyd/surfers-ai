import os
import openai
from typing import Dict, Any, Optional, List, Tuple
from main.clients.mcp_client import MCPWeatherClient
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)
OPENAI_API_BASE_URL = "https://api.openai.com/v1/models"

class GeoChatModel:
    def __init__(self, api_key: str, mcp_url: str, model_name: str = "gpt-4o"):
        """Initialize the model with API key, MCP URL, and model name."""
        self.api_key = api_key
        self.model_name = model_name
        self.client = AsyncOpenAI(api_key=api_key)
        self.weather_client = MCPWeatherClient(mcp_url)
        logger.info(f"Initialized GeoChatModel with MCP URL: {mcp_url}, Model: {model_name}")
        
    async def get_location_info(self, query: str) -> str:
        """Process a location query and return relevant information.
        
        Args:
            query: User's location query
            
        Returns:
            Formatted response with location and weather information
        """
        try:
            logger.info(f"Processing location query: {query}")
            
            # Extract city name from chat message
            # Common patterns in chat messages:
            # - "What's the weather in {city}, {state}?"
            # - "Tell me about {city}, {state}"
            # - "Get weather for {city} {state}"
            # - "{city} {state} weather"
            
            # List of words to remove from the query
            filter_words = [
                "what's", "what", "is", "the", "weather", "in", "at", "tell", "me", "about",
                "get", "for", "please", "show", "lookup", "find", "search"
            ]
            
            # Australian state abbreviations and full names to filter out
            state_names = [
                "nsw", "new south wales",
                "vic", "victoria",
                "qld", "queensland",
                "wa", "western australia",
                "sa", "south australia",
                "tas", "tasmania",
                "nt", "northern territory",
                "act", "australian capital territory"
            ]
            
            # Convert to lowercase and split into words
            # First handle comma-separated state (e.g., "Sydney, NSW")
            parts = query.lower().split(',')
            if len(parts) > 1:
                # Take only the first part (city name) if comma-separated
                query = parts[0]
            
            words = query.lower().split()
            
            # Remove common words, punctuation, and state names
            city_words = []
            i = 0
            while i < len(words):
                word = words[i].strip('?.,!')
                
                # Skip if it's a filter word
                if word in filter_words:
                    i += 1
                    continue
                
                # Check for two-word state names
                if i < len(words) - 1:
                    two_words = f"{word} {words[i+1]}"
                    if two_words in state_names:
                        i += 2
                        continue
                
                # Check for single-word state names
                if word in state_names:
                    i += 1
                    continue
                
                city_words.append(word)
                i += 1
            
            # Rejoin remaining words as the city name
            location_name = " ".join(city_words).strip()
            logger.info(f"Extracted location name: '{location_name}'")
            
            if not location_name:
                logger.warning("Could not extract location name from query")
                return "Could not extract a valid location name from your message. Please provide a city name."
            
            # First try to find the location
            logger.info(f"Looking up location: {location_name}")
            location_data = await self.weather_client.lookup_location(location_name)
            logger.info(f"Location lookup result: {location_data}")
            
            if "error" in location_data:
                logger.error(f"Location lookup error: {location_data['error']}")
                return f"Error looking up location: {location_data['error']}"
            
            if not location_data.get("locations"):
                logger.warning(f"No locations found for: {location_name}")
                return f"Sorry, I couldn't find any locations matching '{location_name}'"
            
            location = location_data["locations"][0]
            location_id = location["id"]
            logger.info(f"Found location ID: {location_id}")
            
            # Get all weather data in a single request
            logger.info(f"Getting weather data for location ID: {location_id}")
            try:
                data = await self.weather_client.get_location_data(location_id)
                logger.info(f"Weather data result keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
            except Exception as e:
                logger.error(f"Error with get_location_data, trying individual calls: {str(e)}")
                # Fallback to individual calls if get_location_data fails
                try:
                    weather_data = await self.weather_client.get_weather(location_id)
                    swell_data = await self.weather_client.get_swell(location_id)
                    wind_data = await self.weather_client.get_wind(location_id)
                    
                    # Check for errors
                    if "error" in weather_data:
                        return f"Error getting weather data: {weather_data['error']}"
                    if "error" in swell_data:
                        return f"Error getting swell data: {swell_data['error']}"
                    if "error" in wind_data:
                        return f"Error getting wind data: {wind_data['error']}"
                    
                    # Combine the data in the expected format
                    data = {
                        "weather": weather_data,
                        "swell": swell_data,
                        "wind": wind_data
                    }
                    logger.info("Successfully retrieved data using individual calls")
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}", exc_info=True)
                    return f"Error getting weather data: {str(fallback_error)}"
            
            if "error" in data:
                logger.error(f"Weather data error: {data['error']}")
                return f"Error getting weather data: {data['error']}"
            
            # Get location data from cache to avoid another lookup
            cached_location = await self.weather_client.get_location_by_id(location_id)
            if not cached_location:
                cached_location = location  # Fallback to the original location data if not in cache
            
            # Format response using OpenAI
            context = {
                "location": cached_location,
                **data  # This includes weather, swell, and wind data
            }
            
            # Create a more readable weather summary for the AI
            weather_summary = self._format_weather_for_ai(data.get("weather"))
            
            # Create swell summary
            swell_summary = self._format_swell_for_ai(data.get("swell"))
            
            # Create wind summary
            wind_summary = self._format_wind_for_ai(data.get("wind"))
            
            # Combine all summaries for the AI prompt
            combined_summary = f"Location: {cached_location.get('name', location_name)}"
            if weather_summary:
                combined_summary += f"\nWeather: {weather_summary}"
            if swell_summary:
                combined_summary += f"\nSwell: {swell_summary}"
            if wind_summary:
                combined_summary += f"\nWind: {wind_summary}"
            
            logger.info(f"Sending context to OpenAI with model: {self.model_name}")
            messages = [
                {"role": "system", "content": "You are a helpful surf and weather assistant. Format the data into a natural, conversational response focusing on current conditions and surf suitability."},
                {"role": "user", "content": f"Please provide a natural weather and surf report for {location_name} based on this data:\n\n{combined_summary}\n\nMake it conversational and mention surf conditions if swell data is available."}
            ]
            
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )
                result = response.choices[0].message.content
                logger.info(f"OpenAI response length: {len(result)} chars")
                return result
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
                return f"Error generating response: {str(e)}"
        except Exception as e:
            logger.error(f"Error in get_location_info: {str(e)}", exc_info=True)
            return f"Error processing your request: {str(e)}"
    
    async def close(self):
        """Close all client connections."""
        try:
            await self.weather_client.close()
        except Exception as e:
            logger.error(f"Error closing weather client: {e}", exc_info=True)

    def _format_weather_for_ai(self, weather_data):
        """Format weather data for AI consumption."""
        if not weather_data:
            return None
        
        try:
            # Check if we have entries array
            if "entries" in weather_data and weather_data["entries"]:
                # Get the most recent entry
                latest = weather_data["entries"][0]
                return (
                    f"Temperature: {latest.get('min', 'N/A')}°C to {latest.get('max', 'N/A')}°C, "
                    f"Conditions: {latest.get('precis', 'N/A')}"
                )
            return None
        except Exception as e:
            logger.error(f"Error formatting weather data: {e}")
            return None

    def _format_swell_for_ai(self, swell_data):
        """Format swell data for AI consumption."""
        if not swell_data:
            return None
        
        try:
            # Check if we have entries array
            if "entries" in swell_data and swell_data["entries"]:
                # Get the most recent entry
                latest = swell_data["entries"][0]
                return (
                    f"Height: {latest.get('height', 'N/A')}m, "
                    f"Direction: {latest.get('directionText', 'N/A')}, "
                    f"Period: {latest.get('period', 'N/A')}s"
                )
            elif "message" in swell_data:
                return swell_data["message"]
            return None
        except Exception as e:
            logger.error(f"Error formatting swell data: {e}")
            return None

    def _format_wind_for_ai(self, wind_data):
        """Format wind data for AI consumption."""
        if not wind_data:
            return None
        
        try:
            # Check if we have entries array
            if "entries" in wind_data and wind_data["entries"]:
                # Get the most recent entry
                latest = wind_data["entries"][0]
                return (
                    f"Speed: {latest.get('speed', 'N/A')}km/h, "
                    f"Direction: {latest.get('directionText', 'N/A')}"
                )
            return None
        except Exception as e:
            logger.error(f"Error formatting wind data: {e}")
            return None
