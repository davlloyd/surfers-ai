# Surfers AI Web Application

A Flask web application that provides an AI-powered chat interface for surfers, with weather and surf condition information.

## Requirements

- Python 3.12+
- Flask
- FastMCP 2.7+
- OpenAI API key (for standalone mode)

## Installation

```bash
# Install the package
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Configuration

### Standalone Mode

1. Create a `.env` file in the project root:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o

# Server Configuration
PORT=8080
HOST=0.0.0.0

# MCP Configuration
MCP_WEATHER_URL=http://localhost:8000
MCP_TIMEOUT=30

# Optional: External API Keys
GOOGLE_API_KEY=your_google_api_key
WILLYWEATHER_API_KEY=your_willyweather_api_key

# Optional: Logging
LOG_LEVEL=INFO
```

2. Run the application:
```bash
# Development mode
flask run

# Production mode
gunicorn --bind 0.0.0.0:8080 "app:create_app()"
```

### Cloud Foundry Mode

1. Create the GenAI service:
```bash
cf create-service weather-chat standard weather-chat
```

2. Deploy the application with the MCP weather URL:
```bash
# Using cf push with variables
cf push --var mcp_weather_url=http://your-mcp-server-url

# Or using a vars file (vars.yml)
cf push --vars-file vars.yml
```

Example vars.yml:
```yaml
mcp_weather_url: http://your-mcp-server-url
```

The application will automatically detect the Cloud Foundry environment and use the GenAI tile service binding.

## Development

```bash
# Run tests
pytest

# Format code
black .

# Lint code
flake8
```

## Environment Variables

### Required Variables

#### Standalone Mode
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4o)

#### Cloud Foundry Mode
- `MCP_WEATHER_URL`: URL of the MCP weather server (set via manifest variables)

### Optional Variables
- `PORT`: Server port (default: 8080)
- `HOST`: Server host (default: 0.0.0.0)
- `MCP_TIMEOUT`: MCP request timeout in seconds (default: 30)
- `GOOGLE_API_KEY`: Google API key for additional features
- `WILLYWEATHER_API_KEY`: WillyWeather API key for additional features
- `LOG_LEVEL`: Logging level (default: INFO)
- `CACHE_TYPE`: Cache type (default: simple)
- `CACHE_DEFAULT_TIMEOUT`: Cache timeout in seconds (default: 300)

## License

This project is licensed under the MIT License.
