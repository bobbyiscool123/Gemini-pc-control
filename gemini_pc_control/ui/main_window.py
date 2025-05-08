"""Main window UI component for Gemini PC Control."""

import sys
from typing import Optional, Callable, Any, Dict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel, QStatusBar,
    QMessageBox, QMenu, QMenuBar, QDialog, QDialogButtonBox,
    QFormLayout, QComboBox, QCheckBox, QTabWidget, QSplitter
)
from PyQt6.QtGui import QAction, QIcon, QTextCursor, QFont, QPixmap
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread

from loguru import logger

from gemini_pc_control.config import default_config


class CommandWorker(QThread):
    """Worker thread for executing commands without blocking the UI."""
    
    finished = pyqtSignal(bool, str)  # Success flag, Result message
    progress = pyqtSignal(str)  # Progress message
    
    def __init__(self, callback_fn: Callable, *args, **kwargs):
        """Initialize the worker with the function to call."""
        super().__init__()
        self.callback_fn = callback_fn
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        """Execute the callback function in a separate thread."""
        try:
            # Execute the callback
            result = self.callback_fn(*self.args, **self.kwargs)
            self.finished.emit(True, str(result))
        except Exception as e:
            logger.error(f"Error in worker thread: {e}", exc_info=True)
            self.finished.emit(False, f"Error: {str(e)}")


class MainWindow(QMainWindow):
    """Main window for the Gemini PC Control application."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle(default_config.ui.title)
        self.resize(default_config.ui.width, default_config.ui.height)
        
        # Initialize UI elements
        self._init_ui()
        
        # Connect signals
        self._connect_signals()
        
        logger.debug("Main window initialized")
    
    def _init_ui(self):
        """Initialize UI components."""
        # Central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_layout.addWidget(self.main_splitter)
        
        # Output area
        self.output_widget = QWidget()
        self.output_layout = QVBoxLayout(self.output_widget)
        
        self.output_label = QLabel("Output:")
        self.output_layout.addWidget(self.output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_layout.addWidget(self.output_text)
        
        # Command input area
        self.input_widget = QWidget()
        self.input_layout = QVBoxLayout(self.input_widget)
        
        self.input_label = QLabel("Enter a command:")
        self.input_layout.addWidget(self.input_label)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("How can I help you?")
        self.input_layout.addWidget(self.input_field)
        
        # Buttons
        self.button_layout = QHBoxLayout()
        
        self.send_button = QPushButton("Send")
        self.send_button.setDefault(True)
        self.button_layout.addWidget(self.send_button)
        
        self.clear_button = QPushButton("Clear")
        self.button_layout.addWidget(self.clear_button)
        
        self.exit_button = QPushButton("Exit")
        self.button_layout.addWidget(self.exit_button)
        
        self.input_layout.addLayout(self.button_layout)
        
        # Add widgets to splitter
        self.main_splitter.addWidget(self.output_widget)
        self.main_splitter.addWidget(self.input_widget)
        self.main_splitter.setStretchFactor(0, 3)  # Output takes more space
        self.main_splitter.setStretchFactor(1, 1)  # Input takes less space
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create menu bar
        self._create_menu_bar()
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        save_action = QAction("&Save Log", self)
        save_action.setStatusTip("Save the current log")
        save_action.triggered.connect(self._save_log)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Exit", self)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        
        clear_action = QAction("&Clear Output", self)
        clear_action.setStatusTip("Clear the output window")
        clear_action.triggered.connect(self._clear_output)
        edit_menu.addAction(clear_action)
        
        # Settings menu
        settings_menu = menu_bar.addMenu("&Settings")
        
        preferences_action = QAction("&Preferences", self)
        preferences_action.setStatusTip("Configure application settings")
        preferences_action.triggered.connect(self._open_preferences)
        settings_menu.addAction(preferences_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.setStatusTip("About Gemini PC Control")
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
    
    def _connect_signals(self):
        """Connect UI element signals to slots."""
        # Button connections
        self.send_button.clicked.connect(self._on_send)
        self.clear_button.clicked.connect(self._clear_output)
        self.exit_button.clicked.connect(self.close)
        
        # Enter key in input field
        self.input_field.returnPressed.connect(self._on_send)
    
    def _on_send(self):
        """Handle send button or Enter key press."""
        user_input = self.input_field.text().strip()
        if not user_input:
            return
        
        # Display user input in output area
        self._append_to_output(f"You: {user_input}")
        
        # Clear input field
        self.input_field.clear()
        
        # Disable input until command completes
        self._set_input_enabled(False)
        self.status_bar.showMessage("Processing...")
        
        # Signal that command processing should begin
        # In a full implementation, this would connect to a controller
        self._process_command(user_input)
    
    def _process_command(self, command: str):
        """Process the user command (placeholder for actual implementation)."""
        # This is just a placeholder - in the real app this would start 
        # the screenshot and AI processing
        self._append_to_output("System: Command received. Processing...")
        
        # Simulate processing with a worker thread
        self.worker = CommandWorker(lambda: f"Simulated response for: {command}")
        self.worker.finished.connect(self._on_command_finished)
        self.worker.start()
    
    def _on_command_finished(self, success: bool, result: str):
        """Handle command execution completion."""
        if success:
            self._append_to_output(f"System: {result}")
        else:
            self._append_to_output(f"Error: {result}")
        
        # Re-enable input
        self._set_input_enabled(True)
        self.status_bar.showMessage("Ready")
    
    def _set_input_enabled(self, enabled: bool):
        """Enable or disable input components."""
        self.input_field.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
    
    def _append_to_output(self, text: str):
        """Append text to the output area."""
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)
        self.output_text.insertPlainText(f"{text}\n")
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def _clear_output(self):
        """Clear the output area."""
        self.output_text.clear()
    
    def _save_log(self):
        """Save the current log to a file."""
        # Placeholder - would open a file dialog and save the log
        self.status_bar.showMessage("Log saving not implemented yet")
    
    def _open_preferences(self):
        """Open the preferences dialog."""
        # Placeholder - would open a preferences dialog
        self.status_bar.showMessage("Preferences dialog not implemented yet")
    
    def _show_about_dialog(self):
        """Show the about dialog."""
        QMessageBox.about(
            self, 
            "About Gemini PC Control",
            f"<h3>Gemini PC Control</h3>"
            f"<p>Version: 1.0.0</p>"
            f"<p>A modern application for controlling your PC with natural language commands.</p>"
            f"<p>Powered by Google Gemini AI.</p>"
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Confirm exit
        reply = QMessageBox.question(
            self, 
            "Exit Confirmation",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clean up resources
            logger.info("Application exit requested")
            event.accept()
        else:
            event.ignore() 