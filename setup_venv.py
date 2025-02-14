"""
Virtual environment setup script for AI Documentation System.
Creates and configures a virtual environment with required dependencies.
"""
import os
import sys
import subprocess
import platform
from pathlib import Path
import venv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VenvSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.requirements_path = self.project_root / "requirements_minimal.txt"
        
        # Platform-specific settings
        self.is_windows = platform.system().lower() == "windows"
        self.python_executable = "python.exe" if self.is_windows else "python"
        self.pip_executable = "pip.exe" if self.is_windows else "pip"
        
    def create_requirements(self):
        """Create minimal requirements file."""
        requirements = """
# Core dependencies
pydantic==2.0.0
python-dotenv==0.19.0
openai==1.0.0
redis==4.5.0
tiktoken==0.5.0

# Testing
pytest==7.0.0
pytest-asyncio==0.21.0
pytest-mock==3.10.0

# Development
black==22.3.0
flake8==4.0.1

# API
Flask==2.3.3
aiohttp==3.9.1
asyncio==3.4.3

# Logging
python-json-logger==2.0.7
"""
        self.requirements_path.write_text(requirements.strip())
        logger.info(f"Created requirements file: {self.requirements_path}")
        
    def setup_venv(self):
        """Create and configure virtual environment."""
        try:
            # Create venv
            logger.info(f"Creating virtual environment at: {self.venv_path}")
            venv.create(self.venv_path, with_pip=True)
            
            # Get paths
            scripts_path = self.venv_path / ("Scripts" if self.is_windows else "bin")
            python_path = scripts_path / self.python_executable
            pip_path = scripts_path / self.pip_executable
            
            # Upgrade pip
            logger.info("Upgrading pip...")
            subprocess.run(
                [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
                check=True
            )
            
            # Install requirements
            logger.info("Installing requirements...")
            subprocess.run(
                [str(pip_path), "install", "-r", str(self.requirements_path)],
                check=True
            )
            
            # Create activation script
            self.create_activation_script(scripts_path)
            
            logger.info("Virtual environment setup complete!")
            self.print_instructions()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during setup: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
            
    def create_activation_script(self, scripts_path: Path):
        """Create convenient activation script."""
        if self.is_windows:
            activate_script = self.project_root / "activate.bat"
            content = f"@echo off\ncall {scripts_path}\\activate.bat"
        else:
            activate_script = self.project_root / "activate.sh"
            content = f"#!/bin/bash\nsource {scripts_path}/activate"
            
        activate_script.write_text(content)
        logger.info(f"Created activation script: {activate_script}")
        
        if not self.is_windows:
            # Make shell script executable
            activate_script.chmod(0o755)
            
    def print_instructions(self):
        """Print usage instructions."""
        activation_cmd = "activate.bat" if self.is_windows else "source activate.sh"
        
        print("\nSetup complete! To use the virtual environment:")
        print(f"1. Activate: {activation_cmd}")
        print("2. Run simulator: python src/ui/documentation_simulator.py")
        print("3. Deactivate: deactivate")
        
def main():
    """Main setup function."""
    try:
        setup = VenvSetup()
        
        # Create requirements file
        setup.create_requirements()
        
        # Setup virtual environment
        setup.setup_venv()
        
    except KeyboardInterrupt:
        logger.info("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 