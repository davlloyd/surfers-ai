#!/usr/bin/env python3
"""
Surfers AI Web Application with FastMCP 2.7+ and Python 3.11+ support.

This Flask application provides a web interface for surf and weather information
using AI assistance and MCP server integration.
"""
import sys
import os
from typing import Dict, Any

# Runtime check for Python 3.11+
if sys.version_info < (3, 11):
    print("Error: This application requires Python 3.11 or newer.")
    print(f"Current version: {sys.version}")
    sys.exit(1)

# Load environment variables FIRST, before any config imports
from dotenv import load_dotenv
load_dotenv()

# Now import the rest after environment variables are loaded
from main import create_app

# Create app using config system
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # Use config values instead of direct environment access
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 8080)
    debug = app.config.get('DEBUG', False)
    
    print(f"🚀 Starting {app.config.get('APP_NAME', 'Surfers AI')} v{app.config.get('VERSION')}")
    print(f"🐍 Python {sys.version_info.major}.{sys.version_info.minor}+ with FastMCP 2.7+")
    print(f"🌐 Server will run on {host}:{port}")
    print(f"⚙️  Environment: {app.config.get('ENV')}")
    
    app.run(debug=debug, host=host, port=port)
