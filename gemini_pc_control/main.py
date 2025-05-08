"""Main entry point for the Gemini PC Control application."""

import os
import sys
import argparse
from typing import Dict, Any, List, Optional

from PyQt6.QtWidgets import QApplication
from loguru import logger

from gemini_pc_control.config import default_config, load_config
from gemini_pc_control.logging_config import request_context
from gemini_pc_control.ui.main_window import MainWindow
from gemini_pc_control.ai.gemini_client import GeminiClient
from gemini_pc_control.ai.context_manager import ContextManager
from gemini_pc_control.system.screenshot import ScreenshotManager
from gemini_pc_control.system.command_executor import CommandExecutor
from gemini_pc_control.plugins.plugin_manager import PluginManager


class Application:
    """Main application class for Gemini PC Control."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the application.
        
        Args:
            config_file: Path to configuration file
        """
        # Check for and create .env if needed
        self._ensure_env_file()
        
        # Initialize components
        self.config = load_config(config_file)
        self.gemini_client = GeminiClient()
        self.context_manager = ContextManager()
        self.screenshot_manager = ScreenshotManager()
        self.command_executor = CommandExecutor()
        self.plugin_manager = PluginManager()
        
        # Set up plugin system
        if self.config.plugins_enabled:
            self._setup_plugins()
        
        # Load previous context if available
        self._load_context()
        
        logger.info("Application initialized")
    
    def _ensure_env_file(self) -> None:
        """Ensure .env file exists, prompting user to create it if needed."""
        env_paths = [
            ".env",  # Project root
            os.path.join(os.path.expanduser("~"), ".gemini_pc_control", ".env")  # User home dir
        ]
        
        # Check if any .env exists
        env_exists = any(os.path.exists(path) for path in env_paths)
        
        if not env_exists:
            try:
                print("=" * 50)
                print("Gemini PC Control - First Run Setup")
                print("=" * 50)
                print("\nNo API key found. You need a Google Gemini API key to use this application.")
                print("Get your API key from: https://aistudio.google.com/app/apikey\n")
                
                api_key = input("Please enter your Gemini API key: ").strip()
                
                if not api_key:
                    print("No API key provided. Application will exit.")
                    sys.exit(1)
                
                # Create .env in project root
                with open(".env", "w") as f:
                    f.write(f"GEMINI_API_KEY={api_key}\n")
                
                print("\nAPI key saved successfully to .env file.")
                print("=" * 50)
            
            except Exception as e:
                print(f"Error creating .env file: {e}")
                print("Please create a .env file manually with your GEMINI_API_KEY.")
                sys.exit(1)
    
    def _setup_plugins(self) -> None:
        """Set up the plugin system."""
        try:
            discovered_plugins = self.plugin_manager.discover_plugins()
            if discovered_plugins:
                logger.info(f"Discovered {len(discovered_plugins)} plugins: {', '.join(discovered_plugins)}")
                
                # Create plugin context
                plugin_context = {
                    "app_config": self.config,
                    "gemini_client": self.gemini_client,
                    "context_manager": self.context_manager,
                    "screenshot_manager": self.screenshot_manager,
                    "command_executor": self.command_executor,
                }
                
                # Initialize plugins
                initialized_plugins = self.plugin_manager.initialize_plugins(plugin_context)
                logger.info(f"Initialized {len(initialized_plugins)} plugins")
            else:
                logger.info("No plugins discovered")
        except Exception as e:
            logger.error(f"Error setting up plugins: {e}", exc_info=True)
    
    def _load_context(self) -> None:
        """Load previous context if available."""
        try:
            context_file = os.path.join(self.config.app_dir, self.config.context_file)
            if os.path.exists(context_file):
                success = self.context_manager.load_from_disk(context_file)
                if success:
                    logger.info("Previous context loaded successfully")
        except Exception as e:
            logger.error(f"Error loading context: {e}", exc_info=True)
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Exit code
        """
        try:
            # Create Qt application
            app = QApplication(sys.argv)
            app.setApplicationName("Gemini PC Control")
            
            # Create and show main window
            main_window = MainWindow()
            main_window.show()
            
            # Connect the main window signal to the process_command method
            # (in a full implementation, we would use a proper controller architecture)
            main_window._process_command = self.process_command
            
            # Run application event loop
            return app.exec()
        
        except Exception as e:
            logger.error(f"Error running application: {e}", exc_info=True)
            return 1
        
        finally:
            # Cleanup on exit
            self._cleanup()
    
    def process_command(self, user_prompt: str) -> str:
        """
        Process a user command through the Gemini AI.
        
        Args:
            user_prompt: User's natural language command
            
        Returns:
            Response text
        """
        with request_context():
            try:
                logger.info(f"Processing command: {user_prompt}")
                
                # Capture screenshot
                screenshot_id, image_base64 = self.screenshot_manager.capture_screenshot()
                
                # Get context for the AI
                context_data = self.context_manager.get_context_for_prompt()
                
                # Generate command using Gemini
                response = self.gemini_client.generate_command(
                    user_prompt=user_prompt,
                    image_base64=image_base64,
                    context_data=context_data
                )
                
                # Execute the command
                success, command = self.command_executor.execute_ai_response(
                    response=response,
                    user_prompt=user_prompt,
                    screenshot_id=screenshot_id
                )
                
                # Update context with the command and result
                self.context_manager.add_command(
                    user_prompt=user_prompt,
                    command=command.raw_response,
                    result="Success" if success else f"Failed: {command.error_message}",
                    screenshot_id=screenshot_id
                )
                
                # Save context periodically
                self.context_manager.save_to_disk()
                
                if success:
                    result = f"Command executed: {command.raw_response}"
                else:
                    result = f"Command failed: {command.error_message}"
                
                return result
            
            except Exception as e:
                error_msg = f"Error processing command: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return error_msg
    
    def _cleanup(self) -> None:
        """Clean up resources before exiting."""
        try:
            # Shut down plugins
            if self.config.plugins_enabled:
                self.plugin_manager.shutdown_plugins()
            
            # Save context
            self.context_manager.save_to_disk()
            
            # Clean up screenshot store (remove old screenshots)
            # In a full implementation, this would be done by ScreenshotManager
            # self.screenshot_manager.cleanup_old_screenshots()
            
            logger.info("Application cleanup completed")
        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Gemini PC Control")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--log-level", help="Logging level")
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Override log level if specified
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    
    # Create and run application
    app = Application(config_file=args.config)
    return app.run()


if __name__ == "__main__":
    sys.exit(main()) 