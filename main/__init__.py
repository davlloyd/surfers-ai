from flask import Flask
from .controllers.map_controller import map_bp
from .controllers.chat_controller import chat_bp
from .controllers.config_controller import config_bp
from config import config
import logging
import os

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Determine configuration to use
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Load the appropriate configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Register blueprints
    app.register_blueprint(map_bp)
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(config_bp, url_prefix='/api')

    # Setup logging
    if not app.debug:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)

    # Global error handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled Exception: {e}")
        return "An internal server error occurred.", 500

    return app
