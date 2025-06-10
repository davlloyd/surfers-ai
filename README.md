# surfers-ai

AI assistant for surf location reporting and forecasts using configurable OpenAI models and FastMCP 2.7+ client patterns.

## Features

- Interactive chat interface for surf and weather queries
- Integration with MCP weather server using FastMCP 2.7+ standards
- Configurable OpenAI model selection (default: gpt-4o)
- Map-based location interface
- Real-time weather and surf condition reporting
- Modern async client patterns with proper connection management
- Enhanced error handling and response parsing

## FastMCP 2.7+ Compliance

This client implementation uses modern FastMCP 2.7+ patterns including:
- Async context managers for connection management
- Proper response content parsing with `.content` attribute handling
- Enhanced error handling for connection and timeout issues
- Support for both tools and resources listing
- Resource reading capabilities with JSON/text content handling

## Configuration

### OpenAI Model
The AI model can be configured via environment variable:
```bash
export OPENAI_MODEL=gpt-4o  # Default
# or
export OPENAI_MODEL=gpt-4-turbo
# or  
export OPENAI_MODEL=gpt-3.5-turbo
```

For detailed configuration options, see [AI_CONFIG.md](AI_CONFIG.md).

### Other Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `MCP_WEATHER_URL`: URL of the MCP weather server (default: http://localhost:8000/mcp)
- `FLASK_ENV`: Environment (development/production)

## API Endpoints

### Configuration
- `GET /api/config`: Get current configuration
- `GET /api/config/model`: Get current model configuration
- `PUT /api/config/model`: Update model configuration (runtime only)

### Chat & MCP
- `POST /api/chat`: Send chat message for location/weather query
- `GET /api/mcp-status`: Get MCP server status and capabilities
- `GET /api/mcp-info`: Get detailed server information
- `GET /api/mcp-tools`: List available MCP tools
- `GET /api/mcp-resources`: List available MCP resources

## Testing

Run the test client to verify FastMCP 2.7+ functionality:
```bash
python test_client.py
```

This will test both direct FastMCP client usage and the enhanced wrapper client.

## Development

1. Install dependencies: `pip install -r requirements.txt`
2. Set required environment variables
3. Start the MCP weather server (see surfers-mcpserver-weather)
4. Run: `python app.py`

## Deployment

See `manifest.yml` for Cloud Foundry deployment configuration.
