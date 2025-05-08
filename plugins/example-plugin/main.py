"""Example plugin for Gemini PC Control."""

from typing import Dict, List, Any, Optional

from gemini_pc_control.plugins.command_plugin import CommandPlugin


class ExamplePlugin(CommandPlugin):
    """Example plugin demonstrating the plugin system."""
    
    @property
    def id(self) -> str:
        """Get the unique identifier for this plugin."""
        return "example-plugin"
    
    @property
    def name(self) -> str:
        """Get the display name for this plugin."""
        return "Example Plugin"
    
    @property
    def version(self) -> str:
        """Get the version of this plugin."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Get the description of this plugin."""
        return "An example plugin demonstrating the plugin system"
    
    @property
    def author(self) -> str:
        """Get the author of this plugin."""
        return "Gemini PC Control Team"
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the plugin with the given context."""
        # Store references to the application components
        self.context_manager = context.get("context_manager")
        self.gemini_client = context.get("gemini_client")
        self.config = context.get("app_config")
        
        # Log initialization
        from loguru import logger
        logger.info(f"Initialized plugin: {self.name}")
    
    def get_commands(self) -> List[str]:
        """Get the list of command names this plugin provides."""
        return ["hello", "set_preference", "get_preference"]
    
    def execute_command(self, command: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a command with the given context and return the result."""
        from loguru import logger
        
        if command == "hello":
            return {"message": "Hello from the example plugin!"}
        
        elif command == "set_preference":
            key = context.get("key")
            value = context.get("value")
            
            if not key or not value:
                return {"error": "Missing key or value"}
            
            # Store the preference in the context manager
            if self.context_manager:
                self.context_manager.set_user_preference(key, value)
                logger.info(f"Set preference {key}={value}")
                return {"success": True, "key": key, "value": value}
            else:
                return {"error": "Context manager not available"}
        
        elif command == "get_preference":
            key = context.get("key")
            
            if not key:
                return {"error": "Missing key"}
            
            # Retrieve the preference from the context manager
            if self.context_manager:
                value = self.context_manager.get_user_preference(key)
                return {"key": key, "value": value}
            else:
                return {"error": "Context manager not available"}
        
        return None
    
    def get_command_help(self, command: str) -> str:
        """Get the help text for a specific command."""
        if command == "hello":
            return "Displays a hello message from the example plugin"
        elif command == "set_preference":
            return "Sets a user preference (Usage: set_preference key=value)"
        elif command == "get_preference":
            return "Gets a user preference (Usage: get_preference key)"
        
        return super().get_command_help(command)
    
    def get_function_declarations(self) -> List[Dict[str, Any]]:
        """Get function declarations for the Gemini function calling API."""
        return [
            {
                "name": "execute_example_plugin_hello",
                "description": "Display a hello message from the example plugin",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "execute_example_plugin_set_preference",
                "description": "Set a user preference",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Preference key"
                        },
                        "value": {
                            "type": "string",
                            "description": "Preference value"
                        }
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "execute_example_plugin_get_preference",
                "description": "Get a user preference",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Preference key"
                        }
                    },
                    "required": ["key"]
                }
            }
        ]
    
    def shutdown(self) -> None:
        """Perform cleanup when the plugin is being disabled or unloaded."""
        from loguru import logger
        logger.info(f"Shutdown plugin: {self.name}")
        
        # Clear references
        self.context_manager = None
        self.gemini_client = None
        self.config = None 