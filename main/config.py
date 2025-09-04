# Load environment variables first, before any config class definitions
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional, continue without it if not installed
    pass

import os
import json
from pyservicebinding import binding

basedir = os.getcwd()

class Config:
    """Base configuration class with all application settings."""
    
    # Application Info
    VERSION = '2.0.0-ai'
    APP_NAME = 'Surfers AI'
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SESSION_COOKIE_HTTPONLY = False
    DEBUG = False
    TESTING = False
    ENV = 'unset'
    
    # Server Settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '8080'))
    USER_PORT = os.environ.get('USER_PORT') or "8080"
    
    # AI Configuration - Core Settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')
    
    # MCP Configuration
    MCP_WEATHER_URL = os.environ.get('MCP_WEATHER_URL', 'http://localhost:8000')
    MCP_TIMEOUT = int(os.environ.get('MCP_TIMEOUT', '30'))
    
    # External API Keys
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    WILLYWEATHER_API_KEY = os.environ.get('WILLYWEATHER_API_KEY')
    
    # File Paths
    DATA_FILE = os.environ.get('DATA_FILE') or f'{basedir}/main/data/data.json'
    LOG_FILE = os.environ.get('LOG_FILE') or f'{basedir}/logs/app.log'
    
    # External Services
    API_URL = os.environ.get('API_URL') or "http://surfersapi:8080"
    
    # Cloud Foundry / VCAP Services Detection
    if 'VCAP_SERVICES' in os.environ:
        _vcap_services = json.loads(os.environ['VCAP_SERVICES'])
        
        # Handle GenAI tile service binding
        if 'weather-chat' in _vcap_services:
            _genai = _vcap_services['weather-chat'][0]['credentials']
            OPENAI_API_KEY = _genai.get('api_key')
            OPENAI_MODEL = _genai.get('model', 'gpt-4o')
            print("GenAI service binding detected")
    else:
        # Service Binding Detection (Kubernetes/OpenShift)
        try:
            _sb = binding.ServiceBinding()
            
            # Check for GenAI service binding
            _genai = _sb.bindings('weather-chat')
            if _genai:
                OPENAI_API_KEY = _genai[0].get('api_key')
                OPENAI_MODEL = _genai[0].get('model', 'gpt-4o')
                print("GenAI service binding detected")
            
            # Check for API binding
            _api = _sb.bindings('api')
            if _api:
                API_URL = _api[0]['url']
        except binding.ServiceBindingRootMissingError:
            pass  # No service bindings available
        except Exception as e:
            print(f"Service binding error: {e}")

    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Security Settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Performance Settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300'))

    @staticmethod
    def init_app(app):
        """Initialize application with this config."""
        # Validate required settings
        if not app.config.get('OPENAI_API_KEY'):
            print("WARNING: OPENAI_API_KEY not configured - AI features will not work")
        
        # Ensure log directory exists
        import os
        log_dir = os.path.dirname(app.config.get('LOG_FILE', ''))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """Production configuration."""
    ENV = 'production'
    DEBUG = False
    
    # Production-specific settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or None  # Must be set in production
    WTF_CSRF_ENABLED = True
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production-specific validation
        if not app.config.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY must be set in production")
        if not app.config.get('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY must be set in production")


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    ENV = 'testing'
    WTF_CSRF_ENABLED = False
    
    # Testing-specific overrides
    MCP_WEATHER_URL = 'http://localhost:8000'  # Mock server for tests
    CACHE_TYPE = 'null'  # Disable caching in tests


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 