"""Plugin manager for discovering and loading plugins."""

import json
import os
import sys
from importlib import import_module
from typing import Dict, List, Type, Optional, Any, Tuple

from loguru import logger

from gemini_pc_control.config import default_config
from gemini_pc_control.logging_config import log_performance
from gemini_pc_control.plugins.base_plugin import BasePlugin


class PluginManager:
    """Manage plugin discovery, loading, and lifecycle."""
    
    def __init__(self, plugin_directory: Optional[str] = None):
        """
        Initialize the plugin manager.
        
        Args:
            plugin_directory: Directory to search for plugins. Defaults to config value.
        """
        self.plugin_directory = plugin_directory or os.path.join(default_config.app_dir, default_config.plugins_dir)
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}
        
        # Create plugin directory if it doesn't exist
        os.makedirs(self.plugin_directory, exist_ok=True)
        
        logger.debug(f"Initialized plugin manager with directory: {self.plugin_directory}")
    
    @log_performance
    def discover_plugins(self) -> List[str]:
        """
        Discover all plugins in the plugin directory.
        
        Returns:
            List of discovered plugin IDs
        """
        if not os.path.exists(self.plugin_directory):
            logger.warning(f"Plugin directory does not exist: {self.plugin_directory}")
            return []
        
        # Add plugin directory to path
        plugin_path = os.path.abspath(self.plugin_directory)
        if plugin_path not in sys.path:
            sys.path.insert(0, plugin_path)
        
        discovered_plugins = []
        
        for item in os.listdir(self.plugin_directory):
            plugin_dir = os.path.join(self.plugin_directory, item)
            
            if not os.path.isdir(plugin_dir):
                continue
            
            manifest_path = os.path.join(plugin_dir, "manifest.json")
            if not os.path.exists(manifest_path):
                logger.warning(f"Skipping directory {item}: No manifest.json found")
                continue
            
            try:
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                
                plugin_id = manifest.get("id")
                main_module = manifest.get("main_module")
                main_class = manifest.get("main_class")
                
                if not all([plugin_id, main_module, main_class]):
                    logger.warning(f"Skipping plugin {item}: Invalid manifest (missing required fields)")
                    continue
                
                # Import the plugin module
                module_path = f"{item}.{main_module}"
                try:
                    module = import_module(module_path)
                    plugin_class = getattr(module, main_class)
                    
                    # Validate the plugin class
                    if not issubclass(plugin_class, BasePlugin):
                        logger.warning(f"Skipping plugin {plugin_id}: Main class does not inherit from BasePlugin")
                        continue
                    
                    # Register the plugin class
                    self.plugin_classes[plugin_id] = plugin_class
                    discovered_plugins.append(plugin_id)
                    
                    logger.info(f"Discovered plugin: {plugin_id} ({plugin_class.__name__})")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Failed to load plugin {plugin_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing plugin {item}: {str(e)}", exc_info=True)
        
        return discovered_plugins
    
    @log_performance
    def initialize_plugins(self, context: Dict[str, Any]) -> List[str]:
        """
        Initialize all discovered plugins with the given context.
        
        Args:
            context: Context to pass to the plugins
            
        Returns:
            List of successfully initialized plugin IDs
        """
        initialized_plugins = []
        
        # Sort plugins by dependencies
        plugin_order = self._sort_plugins_by_dependencies()
        
        for plugin_id in plugin_order:
            try:
                plugin_class = self.plugin_classes[plugin_id]
                plugin = plugin_class()
                plugin.initialize(context)
                self.plugins[plugin_id] = plugin
                initialized_plugins.append(plugin_id)
                
                logger.info(f"Initialized plugin: {plugin_id}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin {plugin_id}: {str(e)}", exc_info=True)
        
        return initialized_plugins
    
    def _sort_plugins_by_dependencies(self) -> List[str]:
        """
        Sort plugins by dependencies to ensure proper initialization order.
        
        Returns:
            List of plugin IDs in correct initialization order
        """
        # Create dependency graph
        graph = {plugin_id: set(self._get_plugin_dependencies(plugin_id)) for plugin_id in self.plugin_classes}
        
        # Topological sort
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(plugin_id):
            if plugin_id in temp_visited:
                logger.error(f"Circular dependency detected for plugin: {plugin_id}")
                return
            
            if plugin_id in visited:
                return
            
            temp_visited.add(plugin_id)
            
            for dep in graph.get(plugin_id, set()):
                if dep in self.plugin_classes:
                    visit(dep)
            
            temp_visited.remove(plugin_id)
            visited.add(plugin_id)
            result.append(plugin_id)
        
        for plugin_id in self.plugin_classes:
            if plugin_id not in visited:
                visit(plugin_id)
        
        return result
    
    def _get_plugin_dependencies(self, plugin_id: str) -> List[str]:
        """Get dependencies for a plugin by instantiating it temporarily."""
        try:
            plugin_class = self.plugin_classes[plugin_id]
            # Create temporary instance to get dependencies
            temp_instance = plugin_class()
            return temp_instance.dependencies
        except Exception as e:
            logger.error(f"Error getting dependencies for plugin {plugin_id}: {e}", exc_info=True)
            return []
    
    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get a plugin instance by ID."""
        return self.plugins.get(plugin_id)
    
    def get_all_plugins(self) -> List[BasePlugin]:
        """Get all active plugin instances."""
        return list(self.plugins.values())
    
    def get_plugin_info(self) -> List[Dict[str, Any]]:
        """Get information about all active plugins."""
        return [
            {
                "id": plugin.id,
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "dependencies": plugin.dependencies,
                "configuration": plugin.get_configuration()
            }
            for plugin in self.plugins.values()
        ]
    
    @log_performance
    def shutdown_plugins(self) -> None:
        """Shutdown all active plugins."""
        # Shutdown in reverse initialization order
        plugin_ids = list(self.plugins.keys())
        plugin_ids.reverse()
        
        for plugin_id in plugin_ids:
            try:
                plugin = self.plugins[plugin_id]
                plugin.shutdown()
                logger.info(f"Shutdown plugin: {plugin_id}")
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_id}: {str(e)}", exc_info=True)
        
        self.plugins.clear()
    
    def configure_plugin(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Configure a plugin with the given options."""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            logger.warning(f"Cannot configure plugin {plugin_id}: Plugin not found")
            return False
        
        try:
            plugin.configure(config)
            logger.info(f"Configured plugin: {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Error configuring plugin {plugin_id}: {e}", exc_info=True)
            return False 