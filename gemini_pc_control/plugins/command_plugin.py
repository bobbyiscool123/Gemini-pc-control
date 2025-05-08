"""Command plugin interface for extending the application with custom commands."""

from typing import Dict, List, Any, Optional
from abc import abstractmethod

from gemini_pc_control.plugins.base_plugin import BasePlugin


class CommandPluginInterface:
    """Interface for plugins that add custom commands."""
    
    @abstractmethod
    def get_commands(self) -> List[str]:
        """
        Get the list of command names this plugin provides.
        
        Returns:
            List of command names
        """
        return []
    
    @abstractmethod
    def execute_command(self, command: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute a command with the given context and return the result.
        
        Args:
            command: Command name to execute
            context: Command execution context
            
        Returns:
            Optional result data
        """
        return None
    
    @abstractmethod
    def get_command_help(self, command: str) -> str:
        """
        Get the help text for a specific command.
        
        Args:
            command: Command name
            
        Returns:
            Help text
        """
        return f"Help for {command}"
    
    def get_command_autocomplete(self, command_prefix: str) -> List[str]:
        """
        Get autocompletion suggestions for a command prefix.
        
        Args:
            command_prefix: Partial command to autocomplete
            
        Returns:
            List of completion suggestions
        """
        return [cmd for cmd in self.get_commands() if cmd.startswith(command_prefix)]
    
    def get_command_examples(self, command: str) -> List[Dict[str, str]]:
        """
        Get usage examples for a command.
        
        Args:
            command: Command name
            
        Returns:
            List of example dictionaries with 'prompt' and 'description' keys
        """
        return []


class CommandPlugin(BasePlugin, CommandPluginInterface):
    """Base class for plugins that add custom commands."""
    
    def get_commands(self) -> List[str]:
        """Get the list of command names this plugin provides."""
        return []
    
    def execute_command(self, command: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a command with the given context and return the result."""
        return None
    
    def get_command_help(self, command: str) -> str:
        """Get the help text for a specific command."""
        return f"Help for {command}"
    
    def get_function_declarations(self) -> List[Dict[str, Any]]:
        """
        Get function declarations for use with the Gemini function calling API.
        
        Returns:
            List of function declarations
        """
        return [] 