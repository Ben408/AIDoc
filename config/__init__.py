"""
Configuration package initialization.
This makes the config directory a Python package and allows for importing settings.
"""
from .settings import Settings

# Create a global settings instance
settings = Settings() 