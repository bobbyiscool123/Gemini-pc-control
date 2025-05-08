# Gemini PC Control

Control your PC with natural language commands using Google's Gemini AI.

## Architecture Modernization

This project has undergone significant architecture modernization to improve maintainability, extensibility, and performance. The key improvements include:

### 1. Modular Architecture

The application now follows a modular architecture with separate components:

- **UI**: Modern PyQt6 interface with proper separation from business logic
- **AI**: Enhanced Gemini API integration with context tracking
- **System**: Core system operations (screenshots, command execution)
- **Models**: Structured data models for commands and responses
- **Plugins**: Extensible plugin system for custom functionality

### 2. Dependency Management

- Proper `requirements.txt` with pinned versions
- Development dependencies in `requirements-dev.txt`
- Setup.py for proper packaging and installation

### 3. Latest Gemini API

- Updated to use the latest Google Gemini API
- Structured prompts with context
- Function calling for better command generation
- Support for multimodal input

### 4. Logging System

- Comprehensive logging with loguru
- Log rotation and management
- Structured JSON logging
- Performance tracking

### 5. Plugin System

- Extensible plugin architecture
- Support for custom commands
- Clean API for third-party developers
- Plugin dependency management

## Installation

### Prerequisites

- Python 3.11 or higher
- Google API key for Gemini (you'll be prompted to enter this on first run)

#### System Dependencies

Some dependencies require system-level packages, particularly for the GUI:

**Debian/Ubuntu:**
```
sudo apt-get update
sudo apt-get install -y python3-dev python3-venv
sudo apt-get install -y qt6-base-dev libqt6-dev  # For PyQt6
sudo apt-get install -y build-essential libssl-dev libffi-dev
```

**macOS:**
```
brew install qt@6
export PATH="/opt/homebrew/opt/qt@6/bin:$PATH"
```

**Windows:**
- Microsoft Visual C++ Build Tools
- Qt6 (Download from https://www.qt.io/download)

### Install from Source

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/gemini-pc-control.git
   cd gemini-pc-control
   ```

2. Create a virtual environment:
   ```
   # Option 1: Using venv (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Option 2: Using virtualenv
   virtualenv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Option 3: Using conda
   conda create -n gemini-pc-control python=3.11
   conda activate gemini-pc-control
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. For development, install development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

5. Run the application:
   ```
   python app.py
   ```
   
   On first run, you'll be prompted to enter your Gemini API key. You can get a key from: https://aistudio.google.com/app/apikey

### Quick Setup (Automated)

For a quick automated setup, use the setup command:
```
python setup.py setup_env
```

This will:
- Create a virtual environment
- Install all dependencies
- Set up the application for you

### Install via Pip

```
pip install gemini-pc-control
```

## Usage

### Running the Application

```
python app.py
```

Or if installed via pip:

```
gemini-pc-control
```

### Command Line Options

- `--config`: Path to custom configuration file
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Developing Plugins

Plugins allow you to extend the functionality of Gemini PC Control. To create a plugin:

1. Create a new directory in the `plugins` directory with your plugin name
2. Create a `manifest.json` file with metadata about your plugin
3. Implement the required plugin interface

Example `manifest.json`:
```json
{
    "id": "example-plugin",
    "name": "Example Plugin",
    "version": "1.0.0",
    "main_module": "main",
    "main_class": "ExamplePlugin",
    "description": "An example plugin demonstrating the plugin system",
    "author": "Your Name",
    "min_app_version": "1.0.0",
    "max_app_version": "2.0.0",
    "dependencies": []
}
```

Example plugin implementation:
```python
from gemini_pc_control.plugins.command_plugin import CommandPlugin

class ExamplePlugin(CommandPlugin):
    @property
    def id(self) -> str:
        return "example-plugin"
    
    @property
    def name(self) -> str:
        return "Example Plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def get_commands(self) -> List[str]:
        return ["hello"]
    
    def execute_command(self, command: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if command == "hello":
            return {"message": "Hello, world!"}
        return None
    
    def get_command_help(self, command: str) -> str:
        if command == "hello":
            return "Displays a hello world message"
        return super().get_command_help(command)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.