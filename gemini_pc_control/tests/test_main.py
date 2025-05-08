"""Tests for the main application."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from gemini_pc_control.main import Application


class TestApplication(unittest.TestCase):
    """Tests for the Application class."""
    
    @patch("gemini_pc_control.main.GeminiClient")
    @patch("gemini_pc_control.main.ContextManager")
    @patch("gemini_pc_control.main.ScreenshotManager")
    @patch("gemini_pc_control.main.CommandExecutor")
    @patch("gemini_pc_control.main.PluginManager")
    def test_application_initialization(
        self, 
        mock_plugin_manager, 
        mock_command_executor, 
        mock_screenshot_manager, 
        mock_context_manager, 
        mock_gemini_client
    ):
        """Test that the Application class initializes correctly."""
        # Set up mocks
        mock_plugin_manager_instance = mock_plugin_manager.return_value
        mock_plugin_manager_instance.discover_plugins.return_value = []
        
        mock_context_manager_instance = mock_context_manager.return_value
        mock_context_manager_instance.load_from_disk.return_value = False
        
        # Create application instance
        app = Application()
        
        # Check that all components were initialized
        self.assertIsNotNone(app.config)
        self.assertIsNotNone(app.gemini_client)
        self.assertIsNotNone(app.context_manager)
        self.assertIsNotNone(app.screenshot_manager)
        self.assertIsNotNone(app.command_executor)
        self.assertIsNotNone(app.plugin_manager)
        
        # Verify plugin discovery was called
        mock_plugin_manager_instance.discover_plugins.assert_called_once()
    
    @patch("gemini_pc_control.main.GeminiClient")
    @patch("gemini_pc_control.main.ContextManager")
    @patch("gemini_pc_control.main.ScreenshotManager")
    @patch("gemini_pc_control.main.CommandExecutor")
    @patch("gemini_pc_control.main.PluginManager")
    def test_process_command(
        self, 
        mock_plugin_manager, 
        mock_command_executor, 
        mock_screenshot_manager, 
        mock_context_manager, 
        mock_gemini_client
    ):
        """Test that the process_command method works correctly."""
        # Set up mocks
        mock_screenshot_manager_instance = mock_screenshot_manager.return_value
        mock_screenshot_manager_instance.capture_screenshot.return_value = ("screenshot_id", "base64_data")
        
        mock_context_manager_instance = mock_context_manager.return_value
        mock_context_manager_instance.get_context_for_prompt.return_value = {}
        
        mock_gemini_client_instance = mock_gemini_client.return_value
        mock_response = MagicMock()
        mock_gemini_client_instance.generate_command.return_value = mock_response
        
        mock_command_executor_instance = mock_command_executor.return_value
        mock_command = MagicMock()
        mock_command.raw_response = "test command"
        mock_command.error_message = None
        mock_command_executor_instance.execute_ai_response.return_value = (True, mock_command)
        
        # Create application instance
        app = Application()
        
        # Process a command
        result = app.process_command("test command")
        
        # Verify the expected calls
        mock_screenshot_manager_instance.capture_screenshot.assert_called_once()
        mock_context_manager_instance.get_context_for_prompt.assert_called_once()
        mock_gemini_client_instance.generate_command.assert_called_once_with(
            user_prompt="test command",
            image_base64="base64_data",
            context_data={}
        )
        mock_command_executor_instance.execute_ai_response.assert_called_once_with(
            response=mock_response,
            user_prompt="test command",
            screenshot_id="screenshot_id"
        )
        mock_context_manager_instance.add_command.assert_called_once()
        mock_context_manager_instance.save_to_disk.assert_called_once()
        
        # Check result
        self.assertIn("Command executed", result)


if __name__ == "__main__":
    unittest.main() 