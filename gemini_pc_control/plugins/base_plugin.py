"""Base plugin interface for the Gemini PC Control plugin system."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BasePlugin(ABC):
    """Base class for all plugins."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Get the unique identifier for this plugin."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the display name for this plugin."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Get the version of this plugin."""
        pass
    
    @property
    def description(self) -> str:
        """Get the description of this plugin."""
        return ""
    
    @property
    def author(self) -> str:
        """Get the author of this plugin."""
        return "Unknown"
    
    @property
    def dependencies(self) -> List[str]:
        """Get the list of plugin IDs this plugin depends on."""
        return []
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the plugin with the given context."""
        pass
    
    def shutdown(self) -> None:
        """Perform cleanup when the plugin is being disabled or unloaded."""
        pass
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get the configuration options for this plugin."""
        return {}
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the plugin with the given options."""
        pass 