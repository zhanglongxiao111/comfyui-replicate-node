#!/usr/bin/env python3
"""
Installation script for ComfyUI Replicate Nodes
"""

import os
import sys
import subprocess
import json

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def create_config_template():
    """Create a config template if it doesn't exist"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        template = {
            "replicate_api_token": "",
            "_comment": "Enter your Replicate API token here"
        }
        try:
            with open(config_path, 'w') as f:
                json.dump(template, f, indent=2)
            print("✓ Config template created")
        except Exception as e:
            print(f"Warning: Could not create config template: {e}")

def verify_installation():
    """Verify that all required files are present"""
    required_files = [
        '__init__.py',
        'requirements.txt',
        'core/__init__.py',
        'core/replicate_client.py',
        'core/utils.py',
        'core/nodes.py'
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print("Error: Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        return False

    print("✓ All required files present")
    return True

def main():
    """Main installation process"""
    print("ComfyUI Replicate Nodes Installation")
    print("=" * 40)

    # Check Python version
    if not check_python_version():
        return False

    # Verify files
    if not verify_installation():
        return False

    # Install dependencies
    if not install_dependencies():
        return False

    # Create config template
    create_config_template()

    print("\n" + "=" * 40)
    print("Installation completed successfully!")
    print("\nNext steps:")
    print("1. Get your Replicate API token from https://replicate.com")
    print("2. Start ComfyUI")
    print("3. Add a 'Replicate Config' node to configure your API token")
    print("4. Check README.md for detailed usage instructions")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)