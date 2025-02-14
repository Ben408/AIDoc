"""
Configuration settings for the AI Documentation System.
"""
from typing import Dict, Any, Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    """System configuration settings."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 2000
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Documentation Paths
    LOCAL_DOCS_PATH: str = r"C:\Users\bjcor\Desktop\Sage Local\Documentation"
    CACHE_PATH: str = "src/data/cache"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance Monitoring
    ENABLE_PERFORMANCE_MONITORING: bool = True
    PERFORMANCE_METRICS_TTL: int = 86400  # 24 hours
    
    # Error Handling
    ERROR_LOG_PATH: str = "logs/errors.log"
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "openai": {
                "api_key": self.OPENAI_API_KEY,
                "model": self.OPENAI_MODEL,
                "temperature": self.OPENAI_TEMPERATURE,
                "max_tokens": self.OPENAI_MAX_TOKENS
            },
            "redis": {
                "host": self.REDIS_HOST,
                "port": self.REDIS_PORT,
                "db": self.REDIS_DB,
                "password": self.REDIS_PASSWORD
            },
            "paths": {
                "local_docs": self.LOCAL_DOCS_PATH,
                "cache": self.CACHE_PATH
            },
            "logging": {
                "level": self.LOG_LEVEL,
                "format": self.LOG_FORMAT
            },
            "performance": {
                "enabled": self.ENABLE_PERFORMANCE_MONITORING,
                "metrics_ttl": self.PERFORMANCE_METRICS_TTL
            },
            "error_handling": {
                "log_path": self.ERROR_LOG_PATH,
                "max_retries": self.MAX_RETRIES,
                "retry_delay": self.RETRY_DELAY
            }
        }

# Create settings instance
settings = Settings() 