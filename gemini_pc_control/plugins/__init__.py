"""Plugins package for Gemini PC Control."""

from gemini_pc_control.plugins.base_plugin import BasePlugin
from gemini_pc_control.plugins.command_plugin import CommandPlugin, CommandPluginInterface
from gemini_pc_control.plugins.plugin_manager import PluginManager

__all__ = [
    "BasePlugin",
    "CommandPlugin",
    "CommandPluginInterface",
    "PluginManager",
] 