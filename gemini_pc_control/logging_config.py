"""Logging configuration module for Gemini PC Control."""

import os
import sys
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from gemini_pc_control.config import default_config


def configure_logging() -> None:
    """Configure the logging system based on application config."""
    # Create logs directory if it doesn't exist
    log_dir = Path(default_config.app_dir) / default_config.logging.log_dir
    os.makedirs(log_dir, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with color formatting
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=default_config.logging.console_level,
        colorize=True,
    )
    
    # Add rotating file handler for general logs
    logger.add(
        str(log_dir / "gemini_pc_control_{time:YYYY-MM-DD}.log"),
        rotation=default_config.logging.max_file_size,
        retention=default_config.logging.retention,
        compression=default_config.logging.compression,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=default_config.logging.file_level,
    )
    
    # Add error logging to separate file
    logger.add(
        str(log_dir / "error_{time:YYYY-MM-DD}.log"),
        rotation="10MB",
        retention="90 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
    )
    
    # Add JSON structured logging for machine processing
    logger.add(
        str(log_dir / "structured_{time:YYYY-MM-DD}.json"),
        rotation="50MB",
        retention="60 days",
        serialize=True,  # Outputs JSON
        level="INFO",
    )
    
    logger.info("Logging system initialized")


# Performance tracking decorator
def log_performance(func):
    """Decorator to log function performance."""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logger.debug(f"Function {func.__name__} took {elapsed_time:.4f} seconds to execute")
        return result
    
    return wrapper


# Custom contextvars-based request context for tracking request flow
def get_request_context():
    """Get request context for the current execution context."""
    import uuid
    import contextlib
    from contextvars import ContextVar
    
    _request_id_var = ContextVar("request_id", default=None)
    
    @contextlib.contextmanager
    def request_context(request_id=None):
        if request_id is None:
            request_id = str(uuid.uuid4())
        token = _request_id_var.set(request_id)
        try:
            yield request_id
        finally:
            _request_id_var.reset(token)
    
    def get_request_id():
        return _request_id_var.get()
    
    return request_context, get_request_id

# Create request context utilities
request_context, get_request_id = get_request_context()


# Initialize logging system
configure_logging() 