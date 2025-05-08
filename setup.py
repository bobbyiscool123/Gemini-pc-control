#!/usr/bin/env python3
"""Setup script for the Gemini PC Control application."""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from setuptools import setup, find_packages, Command


def print_step(step_num, message):
    """Print a step in the setup process."""
    print(f"\n[Step {step_num}] {message}")
    print("=" * 60)


def run_command(command, shell=False):
    """Run a command and print output."""
    print(f"> {' '.join(command) if isinstance(command, list) else command}")
    try:
        if shell:
            process = subprocess.run(command, shell=True, check=True, text=True)
        else:
            process = subprocess.run(command, check=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return False


def detect_python():
    """Find the correct Python executable."""
    # Try python3 first, then python
    for cmd in ["python3", "python"]:
        try:
            version = subprocess.check_output([cmd, "--version"], text=True)
            print(f"Found {version.strip()}")
            return cmd
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    print("Error: Could not find Python 3.x. Please install Python 3.11 or later.")
    sys.exit(1)


def setup_virtual_environment(python_cmd):
    """Set up a virtual environment."""
    venv_dir = "venv"
    
    # Check if venv already exists
    if os.path.exists(venv_dir):
        response = input(f"Virtual environment '{venv_dir}' already exists. Recreate? (y/n): ")
        if response.lower() == 'y':
            shutil.rmtree(venv_dir)
        else:
            print(f"Using existing virtual environment '{venv_dir}'.")
            return venv_dir
    
    # Create virtual environment
    if not run_command([python_cmd, "-m", "venv", venv_dir]):
        print(f"Error creating virtual environment. Trying alternative method...")
        try:
            import venv
            venv.create(venv_dir, with_pip=True)
        except Exception as e:
            print(f"Error: Could not create virtual environment: {e}")
            sys.exit(1)
    
    print(f"Virtual environment created at '{venv_dir}'")
    return venv_dir


def get_venv_activate_script(venv_dir):
    """Get the path to the activate script."""
    if platform.system() == "Windows":
        return os.path.join(venv_dir, "Scripts", "activate.bat")
    else:
        return os.path.join(venv_dir, "bin", "activate")


def get_venv_python(venv_dir):
    """Get the path to the Python executable in the virtual environment."""
    if platform.system() == "Windows":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        return os.path.join(venv_dir, "bin", "python")


def install_dependencies(venv_python):
    """Install dependencies."""
    # Install dependencies
    if not run_command([venv_python, "-m", "pip", "install", "--upgrade", "pip"]):
        print("Warning: Failed to upgrade pip, continuing anyway...")
    
    # Try to install dependencies
    print("Installing dependencies...")
    result = run_command([venv_python, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Check for common errors
    if not result:
        print("\n" + "=" * 60)
        print("DEPENDENCY INSTALLATION ERROR")
        print("=" * 60)
        print("\nSome dependencies could not be installed. This is often due to missing system packages.")
        
        if platform.system() == "Linux":
            print("\nFor Debian/Ubuntu, try installing these system dependencies:")
            print("  sudo apt-get update")
            print("  sudo apt-get install -y python3-dev python3-venv qt6-base-dev libqt6-dev")
            print("  sudo apt-get install -y build-essential libssl-dev libffi-dev")
        
        elif platform.system() == "Darwin":  # macOS
            print("\nFor macOS, try installing these with Homebrew:")
            print("  brew install qt@6")
            print("  export PATH=\"/opt/homebrew/opt/qt@6/bin:$PATH\"")
        
        elif platform.system() == "Windows":
            print("\nFor Windows, you may need to install:")
            print("  - Microsoft Visual C++ Build Tools")
            print("  - Qt6 (Download from https://www.qt.io/download)")
        
        print("\nAfter installing system dependencies, run this script again.")
        print("Alternatively, you can install without GUI components:")
        print(f"  {venv_python} -m pip install -r requirements-minimal.txt")
        
        # Create a minimal requirements file without PyQt6
        with open("requirements.txt", "r") as f:
            reqs = f.readlines()
        
        with open("requirements-minimal.txt", "w") as f:
            for req in reqs:
                if not req.strip().startswith("PyQt6"):
                    f.write(req)
            f.write("# PyQt6 dependency removed for minimal installation\n")
        
        print("\nCreated requirements-minimal.txt with GUI dependencies removed.")
        
        response = input("\nContinue with minimal installation (no GUI)? (y/n): ")
        if response.lower() == 'y':
            print("Installing minimal dependencies...")
            result = run_command([venv_python, "-m", "pip", "install", "-r", "requirements-minimal.txt"])
            if not result:
                print("Error: Failed to install minimal dependencies.")
                sys.exit(1)
            print("Minimal dependencies installed. Note that GUI features will not work.")
        else:
            print("Installation not completed. Please install system dependencies and try again.")
            sys.exit(1)
    
    # Ask if development dependencies should be installed
    response = input("Install development dependencies? (y/n): ")
    if response.lower() == 'y':
        run_command([venv_python, "-m", "pip", "install", "-r", "requirements-dev.txt"])


def create_run_script(venv_dir):
    """Create a run script for easy execution."""
    if platform.system() == "Windows":
        script_name = "run_app.bat"
        with open(script_name, "w") as f:
            f.write(f"@echo off\n")
            f.write(f"call {venv_dir}\\Scripts\\activate.bat\n")
            f.write(f"python app.py %*\n")
    else:
        script_name = "run_app.sh"
        with open(script_name, "w") as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"source {venv_dir}/bin/activate\n")
            f.write(f"python app.py \"$@\"\n")
        
        # Make the script executable
        os.chmod(script_name, 0o755)
    
    print(f"Created run script: {script_name}")
    return script_name


def setup_env_file():
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
    else:
        print("API key file (.env) already exists.")


def setup_environment():
    """Set up the entire environment."""
    print("\n" + "=" * 60)
    print("Gemini PC Control - Environment Setup")
    print("=" * 60)
    
    # Step 1: Detect Python
    print_step(1, "Detecting Python")
    python_cmd = detect_python()
    
    # Step 2: Create virtual environment
    print_step(2, "Setting up virtual environment")
    venv_dir = setup_virtual_environment(python_cmd)
    venv_python = get_venv_python(venv_dir)
    
    # Step 3: Install dependencies
    print_step(3, "Installing dependencies")
    install_dependencies(venv_python)
    
    # Step 4: Create run script
    print_step(4, "Creating run script")
    run_script = create_run_script(venv_dir)
    
    # Step 5: Set up .env file
    print_step(5, "Setting up environment file")
    setup_env_file()
    
    # Done
    print("\n" + "=" * 60)
    print("Setup complete!")
    print(f"To run the application, use: ./{run_script}")
    print("=" * 60)


class SetupEnvironmentCommand(Command):
    """Custom setup.py command to set up the development environment."""
    
    description = "Set up development environment with venv and dependencies"
    user_options = []
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def run(self):
        setup_environment()


# Check for direct environment setup call
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "setup_env":
    setup_environment()
    sys.exit(0)

# Print setup information for standard runs
elif __name__ == "__main__" and not any(arg.startswith("--") for arg in sys.argv[1:]):
    print("""
======================================================
Gemini PC Control Installation
======================================================

This is the setup file for Gemini PC Control.

To set up a development environment with virtual environment:
  python setup.py setup_env

For standard pip installation:
  pip install .
  
======================================================
""")

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gemini-pc-control",
    version="1.0.0",
    author="Gemini PC Control Team",
    author_email="example@example.com",
    description="Control your PC with natural language using Google Gemini AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gemini-pc-control",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gemini-pc-control=gemini_pc_control.main:main",
        ],
    },
    cmdclass={
        'setup_env': SetupEnvironmentCommand,
    },
) 