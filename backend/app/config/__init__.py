"""Configuration module for AI Exam Evaluator"""

import yaml
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get config path
CONFIG_PATH = Path(__file__).parent / "config.yaml"

class Config:
    """Global configuration loader"""
    
    _config = None
    
    @classmethod
    def load(cls):
        """Load configuration from YAML file"""
        if cls._config is None:
            with open(CONFIG_PATH, 'r') as f:
                cls._config = yaml.safe_load(f)
        return cls._config
    
    @classmethod
    def get(cls, key_path: str, default=None):
        """
        Get configuration value by dot-separated path
        
        Args:
            key_path: Dot-separated path (e.g., 'ocr.timeout')
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        config = cls.load()
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    @classmethod
    def get_ocr_api_key(cls):
        """Get OCR API key from environment"""
        return os.getenv('OCR_API_KEY')
    
    @classmethod
    def get_ollama_host(cls):
        """Get Ollama host from environment or config"""
        return os.getenv('OLLAMA_HOST', cls.get('ollama.host'))
    
    @classmethod
    def get_model(cls, model_type: str):
        """
        Get model name by type
        
        Args:
            model_type: 'mapping' or 'evaluation'
        
        Returns:
            Model name
        """
        env_key = f"{model_type.upper()}_MODEL"
        env_value = os.getenv(env_key)
        
        if env_value:
            return env_value
        
        return cls.get(f'ollama.models.{model_type}')

# Initialize configuration on import
config = Config.load()
