import os
from cfenv import AppEnv

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
    MCP_WEATHER_URL = os.getenv('MCP_WEATHER_URL', 'http://localhost:8000/mcp')
    PORT = int(os.getenv('PORT', 8080))

    @staticmethod
    def init_app(app):
        # Check if running on Cloud Foundry
        if os.getenv('CF_INSTANCE_INDEX'):
            cf_config = CloudFoundryConfig()
            app.config.update(cf_config.get_config())

class DevelopmentConfig(Config):
    DEBUG = True
    MCP_WEATHER_URL = os.getenv('MCP_WEATHER_URL', 'http://localhost:8000/mcp')
    PORT = int(os.getenv('PORT', 8080))

class ProductionConfig(Config):
    DEBUG = False
    MCP_WEATHER_URL = os.getenv('MCP_WEATHER_URL', 'http://localhost:8000/mcp')
    PORT = int(os.getenv('PORT', 8080))

class CloudFoundryConfig:
    def __init__(self):
        self.env = AppEnv()
        
    def get_config(self):
        return {
            'OPENAI_API_KEY': self._get_service_credential('openai', 'api_key'),
            'OPENAI_MODEL': os.getenv('OPENAI_MODEL', 'gpt-4o'),
            'SECRET_KEY': os.getenv('SECRET_KEY', self.env.get_credential('secret_key'))
        }
    
    def _get_service_credential(self, service_name, credential_key):
        service = self.env.get_service(name=service_name)
        return service.credentials.get(credential_key) if service else None

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
