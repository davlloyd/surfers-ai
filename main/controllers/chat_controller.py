from flask import Blueprint, request, jsonify, current_app
from main.models.geo_model import GeoChatModel
from main.clients.mcp_client import MCPWeatherClient
import asyncio
from functools import wraps
import logging
import json
import time

chat_bp = Blueprint('chat_bp', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

# Cache for MCP status
mcp_status_cache = {
    "data": None,
    "last_updated": 0
}
CACHE_TIMEOUT = 30  # seconds

# Shared MCP client instance
_mcp_client = None

def get_mcp_client():
    """Get or create the shared MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        mcp_url = current_app.config.get('MCP_WEATHER_URL')
        _mcp_client = MCPWeatherClient(mcp_url)
    return _mcp_client

def get_geo_chat_model():
    """Create GeoChatModel with configuration from current app."""
    return GeoChatModel(
        api_key=current_app.config.get('OPENAI_API_KEY'),
        mcp_url=current_app.config.get('MCP_WEATHER_URL'),
        model_name=current_app.config.get('OPENAI_MODEL', 'gpt-4o')
    )

def async_route(f):
    """Decorator to handle async routes."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

async def get_mcp_status(force_refresh=False):
    """Get MCP server status, using cache unless force_refresh is True."""
    now = time.time()
    if not force_refresh and mcp_status_cache["data"] and (now - mcp_status_cache["last_updated"]) < CACHE_TIMEOUT:
        current_app.logger.info("Using cached MCP status.")
        return mcp_status_cache["data"]

    try:
        client = get_mcp_client()
        current_app.logger.info(f"Checking MCP server at: {client.base_url}")
        
        # Get health status
        health_result = await client.health_check()
        if "error" in health_result:
            raise Exception(health_result["error"])
        
        # Get available tools using FastMCP 2.7+ patterns
        tools_result = await client.list_tools()
        tools = tools_result.get("tools", []) if "error" not in tools_result else []
        
        # Get available resources using FastMCP 2.7+ patterns
        resources_result = await client.list_resources()
        resources = resources_result.get("resources", []) if "error" not in resources_result else []
        
        current_app.logger.info(f"MCP server status: {health_result.get('status', 'unknown')}")
        current_app.logger.info(f"Available tools: {len(tools)}")
        current_app.logger.info(f"Available resources: {len(resources)}")
        
        # Build response data
        response_data = {
            'status': health_result.get("status", "unknown"),
            'service_info': {
                'name': health_result.get("service_name", "WillyWeather MCP"),
                'version': health_result.get("version", "1.0.0"),
                'dependencies': health_result.get("dependencies", {})
            },
            'capabilities': {
                'tools': len(tools),
                'resources': len(resources)
            },
            'tools': [
                {
                    "name": tool["name"],
                    "description": tool["description"]
                }
                for tool in tools
            ],
            'resources': [
                {
                    "name": resource["name"],
                    "description": resource["description"],
                    "mime_type": resource["mime_type"]
                }
                for resource in resources
            ]
        }
        
        # Cache the successful response
        mcp_status_cache["data"] = response_data
        mcp_status_cache["last_updated"] = time.time()
        
        return response_data
            
    except Exception as e:
        current_app.logger.error(f"MCP server connection error: {str(e)}", exc_info=True)
        
        # Cache the error response
        error_response = {
            'status': 'unavailable',
            'error': str(e),
            'details': 'Failed to connect to MCP server. Please check if the server is running.'
        }
        mcp_status_cache["data"] = error_response
        mcp_status_cache["last_updated"] = time.time()
        
        return error_response

@chat_bp.route('/mcp-status', methods=['GET'])
@async_route
async def check_mcp_status():
    """Check MCP server status and available tools using modern FastMCP 2.7+ patterns."""
    status = await get_mcp_status()
    if status.get('status') == 'unavailable':
        return jsonify(status), 503
    return jsonify(status)

@chat_bp.route('/chat', methods=['POST'])
@async_route
async def handle_chat():
    """
    Receives a POST request with a 'message' field,
    queries both OpenAI and the MCP weather server for information,
    and returns the combined reply as JSON.
    """
    try:
        data = request.get_json(force=True)
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({'reply': "Please enter a message."}), 400

        try:
            # Create model instance with current app config
            geo_chat_model = get_geo_chat_model()
            reply = await geo_chat_model.get_location_info(user_message)
            return jsonify({'reply': reply})
        except Exception as model_exc:
            current_app.logger.error(f"Model error: {model_exc}")
            return jsonify({'reply': "Sorry, I couldn't retrieve information at this time."}), 500

    except Exception as req_exc:
        current_app.logger.error(f"Request parsing error: {req_exc}")
        return jsonify({'reply': "Invalid request format."}), 400

@chat_bp.route('/mcp-info', methods=['GET'])
@async_route
async def get_mcp_info():
    """Get detailed MCP server information and resources using FastMCP 2.7+ patterns."""
    status = await get_mcp_status()
    if status.get('status') == 'unavailable':
        return jsonify(status), 503
        
    try:
        client = get_mcp_client()
        server_info_result = await client.read_resource("config://server/info")
        if "error" in server_info_result:
            current_app.logger.warning(f"Could not read server info resource: {server_info_result['error']}")
            server_info_data = {}
        else:
            server_info_data = server_info_result if isinstance(server_info_result, dict) else {}
        
        return jsonify({
            'status': 'available',
            'server_info': server_info_data
        })
    except Exception as e:
        current_app.logger.error(f"Failed to read server info: {e}")
        return jsonify({
            'status': 'partial',
            'error': 'Could not retrieve server info resource',
            'details': str(e)
        }), 206

@chat_bp.route('/mcp-tools', methods=['GET'])
@async_route  
async def get_mcp_tools():
    """Get detailed list of available MCP tools using FastMCP 2.7+ patterns."""
    status = await get_mcp_status()
    if status.get('status') == 'unavailable':
        return jsonify(status), 503
        
    return jsonify({
        'status': 'success',
        'tools': status.get('tools', [])
    })

@chat_bp.route('/mcp-resources', methods=['GET'])
@async_route
async def get_mcp_resources():
    """Get detailed list of available MCP resources using FastMCP 2.7+ patterns."""
    status = await get_mcp_status()
    if status.get('status') == 'unavailable':
        return jsonify(status), 503
        
    return jsonify({
        'status': 'success',
        'resources': status.get('resources', [])
    })

# Export alias for app.py import
chat_controller = chat_bp
