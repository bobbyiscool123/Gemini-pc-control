"""Configuration module for Gemini PC Control application."""

import os
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    
    level: str = "INFO"
    file_level: str = "DEBUG"
    console_level: str = "INFO"
    log_dir: str = "logs"
    max_file_size: str = "50MB"
    retention: str = "30 days"
    compression: str = "zip"


class GeminiConfig(BaseModel):
    """Configuration for Gemini API."""
    
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.2
    max_output_tokens: int = 1024
    top_p: float = 0.95
    top_k: int = 40


class UIConfig(BaseModel):
    """Configuration for UI."""
    
    width: int = 800
    height: int = 600
    title: str = "Gemini PC Control"
    theme: str = "system"  # "light", "dark", or "system"
    font_size: int = 12


class AppConfig(BaseModel):
    """Main application configuration."""
    
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    
    # Paths
    app_dir: str = str(Path.home() / ".gemini_pc_control")
    context_file: str = "context.json"
    credentials_file: str = ".env"
    
    # Plugin settings
    plugins_dir: str = "plugins"
    plugins_enabled: bool = True


def load_config(config_file: Optional[str] = None) -> AppConfig:
    """Load configuration from environment and file."""
    # Default config
    config = AppConfig()
    
    # Update from file if provided
    if config_file and os.path.exists(config_file):
        # In a real implementation, we would load from file here
        pass
    
    # Override from environment variables
    if os.getenv("GEMINI_MODEL_NAME"):
        config.gemini.model_name = os.getenv("GEMINI_MODEL_NAME")
    
    if os.getenv("LOG_LEVEL"):
        config.logging.level = os.getenv("LOG_LEVEL")
    
    # Create app directory if it doesn't exist
    os.makedirs(config.app_dir, exist_ok=True)
    
    return config


# Default configuration instance
default_config = load_config() 