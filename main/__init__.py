#!/usr/bin/env python3
"""
Flask application factory for Surfers AI with FastMCP 2.7+ and Python 3.11+ support.
"""
import sys
import logging
from flask import Flask
from main import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration using the config system
    app.config.from_object(config.config[config_name])
    config.config[config_name].init_app(app)
    
    with app.app_context():
        app.logger.info(f'Setting up {app.config.get("APP_NAME")} v{app.config.get("VERSION")}')
        app.logger.info(f'Environment: {app.config.get("ENV")}')
        app.logger.info(f'OpenAI Model: {app.config.get("OPENAI_MODEL")}')
        app.logger.info(f'MCP URL: {app.config.get("MCP_WEATHER_URL")}')
        
        # Import and register controller blueprints
        app.logger.info('Import controller blueprints')
        from main.controllers.chat_controller import chat_controller
        from main.controllers.config_controller import config_controller
        from main.controllers.map_controller import map_controller, map_api_controller
        
        app.logger.info('Registering chat controller blueprint')
        app.register_blueprint(chat_controller)
        app.logger.info('Registering config controller blueprint')
        app.register_blueprint(config_controller)
        app.logger.info('Registering map controller blueprint')
        app.register_blueprint(map_controller)
        app.logger.info('Registering map API controller blueprint')
        app.register_blueprint(map_api_controller)
        
        # Context processor for template variables
        @app.context_processor
        def inject_config():
            """Inject config variables into all templates."""
            return {
                'config': app.config,
                'locationnames': []  # Empty for AI version - no database
            }

    return app
