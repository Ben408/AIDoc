"""
Entry point for the Documentation Simulator.
"""
import os
import sys
from pathlib import Path

def run():
    """Run the simulator with proper path setup."""
    try:
        # Add project root to Python path
        project_root = Path(__file__).parent
        sys.path.append(str(project_root))
        
        # Import and run simulator
        from src.ui.documentation_simulator import main
        main()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPython path:")
        for path in sys.path:
            print(f"  {path}")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    run() 