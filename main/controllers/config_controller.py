from flask import Blueprint, jsonify, request, current_app
import os

config_bp = Blueprint('config_bp', __name__)

@config_bp.route('/config', methods=['GET'])
def get_config():
    """Get current configuration settings."""
    return jsonify({
        "status": "success",
        "config": {
            "openai_model": current_app.config.get('OPENAI_MODEL', 'gpt-4o'),
            "mcp_weather_url": current_app.config.get('MCP_WEATHER_URL'),
            "flask_env": os.getenv('FLASK_ENV', 'development'),
            "debug": current_app.config.get('DEBUG', False)
        }
    })

@config_bp.route('/config/model', methods=['GET'])
def get_model_config():
    """Get current OpenAI model configuration."""
    return jsonify({
        "status": "success",
        "model_name": current_app.config.get('OPENAI_MODEL', 'gpt-4o'),
        "configured_via": "environment" if os.getenv('OPENAI_MODEL') else "default"
    })

@config_bp.route('/config/model', methods=['PUT'])
def update_model_config():
    """Update OpenAI model configuration (runtime only, not persistent)."""
    try:
        data = request.get_json()
        if not data or 'model_name' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'model_name' in request body"
            }), 400
        
        model_name = data['model_name'].strip()
        if not model_name:
            return jsonify({
                "status": "error",
                "message": "Model name cannot be empty"
            }), 400
        
        # Update runtime configuration
        old_model = current_app.config.get('OPENAI_MODEL', 'gpt-4o')
        current_app.config['OPENAI_MODEL'] = model_name
        
        return jsonify({
            "status": "success",
            "message": f"Model name updated from '{old_model}' to '{model_name}'",
            "previous_model": old_model,
            "new_model": model_name,
            "note": "This change is runtime only. To persist across restarts, set the OPENAI_MODEL environment variable."
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error updating model configuration: {str(e)}"
        }), 500

@config_bp.route('/config/environment', methods=['GET'])
def get_environment_info():
    """Get environment variable information."""
    env_vars = {
        'OPENAI_MODEL': {
            'value': os.getenv('OPENAI_MODEL'),
            'current': current_app.config.get('OPENAI_MODEL', 'gpt-4o'),
            'default': 'gpt-4o'
        },
        'OPENAI_API_KEY': {
            'value': '***REDACTED***' if os.getenv('OPENAI_API_KEY') else None,
            'configured': bool(os.getenv('OPENAI_API_KEY'))
        },
        'MCP_WEATHER_URL': {
            'value': os.getenv('MCP_WEATHER_URL'),
            'current': current_app.config.get('MCP_WEATHER_URL'),
            'default': 'http://localhost:8000/mcp'
        },
        'FLASK_ENV': {
            'value': os.getenv('FLASK_ENV'),
            'current': os.getenv('FLASK_ENV', 'development'),
            'default': 'development'
        }
    }
    
    return jsonify({
        "status": "success",
        "environment_variables": env_vars,
        "configuration_priority": "Environment variables override defaults. Runtime updates via API don't persist across restarts."
    })

@config_bp.route('/config/status')
def get_config_status():
    """Get the current configuration status."""
    try:
        flask_env = os.getenv('FLASK_ENV', 'development')
        config_class = current_app.config['__class__'].__name__ if '__class__' in current_app.config else 'Unknown'
        
        return jsonify({
            'status': 'ok',
            'flask_env': flask_env,
            'config_class': config_class,
            'environment': current_app.config.get('ENV', 'development'),
            'debug': current_app.config.get('DEBUG', False),
            'mcp_weather_url': current_app.config.get('MCP_WEATHER_URL'),
            'port': current_app.config.get('PORT'),
            'cloud_foundry': {
                'enabled': bool(os.getenv('CF_INSTANCE_INDEX')),
                'instance_index': os.getenv('CF_INSTANCE_INDEX'),
                'instance_guid': os.getenv('CF_INSTANCE_GUID')
            }
        })
    except Exception as e:
        current_app.logger.error(f"Configuration error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 