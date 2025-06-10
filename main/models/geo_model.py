import os
import openai
from typing import Dict, Any, Optional, List, Tuple
from main.clients.mcp_client import MCPWeatherClient
from openai import AsyncOpenAI
import logging

OPENAI_API_BASE_URL = "https://api.openai.com/v1/models"

class GeoChatModel:
    def __init__(self, api_key: str, mcp_url: str, model_name: str = "gpt-4o"):
        """Initialize the model with API key, MCP URL, and model name."""
        self.api_key = api_key
        self.model_name = model_name
        self.client = AsyncOpenAI(api_key=api_key)
        self.weather_client = MCPWeatherClient(mcp_url)
        
    async def get_location_info(self, query: str) -> str:
        """Process a location query and return relevant information.
        
        Args:
            query: User's location query
            
        Returns:
            Formatted response with location and weather information
        """
        try:
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
            
            if not location_name:
                return "Could not extract a valid location name from your message. Please provide a city name."
            
            # First try to find the location
            location_data = await self.weather_client.lookup_location(location_name)
            if "error" in location_data:
                return f"Error looking up location: {location_data['error']}"
            
            if not location_data.get("locations"):
                return f"Sorry, I couldn't find any locations matching '{location_name}'"
            
            location = location_data["locations"][0]
            location_id = location["id"]
            
            # Get all weather data in a single request
            data = await self.weather_client.get_location_data(location_id)
            if "error" in data:
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
            
            messages = [
                {"role": "system", "content": "You are a helpful surf and weather assistant. Format the data into a natural, conversational response."},
                {"role": "user", "content": f"Here is the data for {location_name}: {context}. Please format it into a natural response focusing on surf conditions if available."}
            ]
            
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"Error formatting response: {str(e)}"
                
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    async def close(self):
        """Close all client connections."""
        try:
            await self.weather_client.close()
        except Exception as e:
            logger.error(f"Error closing weather client: {e}", exc_info=True)
