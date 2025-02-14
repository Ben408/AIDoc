"""
Utility script to setup and verify symbolic links for local documentation.
"""
import os
import sys
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SymlinkSetup:
    def __init__(self):
        self.source_path = Path(r"C:\Users\bjcor\Desktop\Sage Local\Documentation")
        self.target_path = Path("src/data/local_docs")
        
    def check_admin(self) -> bool:
        """Check if script is running with admin privileges."""
        try:
            return os.getuid() == 0
        except AttributeError:
            # Windows-specific check
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
            
    def verify_paths(self) -> bool:
        """Verify source path exists and target path is valid."""
        if not self.source_path.exists():
            logger.error(f"Source path does not exist: {self.source_path}")
            return False
            
        # Create parent directories if needed
        self.target_path.parent.mkdir(parents=True, exist_ok=True)
        return True
        
    def create_symlink(self) -> bool:
        """Create the symbolic link."""
        try:
            # Remove existing symlink if it exists
            if self.target_path.exists():
                if self.target_path.is_symlink():
                    self.target_path.unlink()
                else:
                    logger.error(f"Target path exists and is not a symlink: {self.target_path}")
                    return False
                    
            # Create new symlink
            self.target_path.symlink_to(self.source_path, target_is_directory=True)
            logger.info(f"Successfully created symlink: {self.target_path} -> {self.source_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create symlink: {str(e)}")
            return False
            
    def verify_symlink(self) -> bool:
        """Verify the symlink is working correctly."""
        try:
            if not self.target_path.exists():
                logger.error("Symlink does not exist")
                return False
                
            if not self.target_path.is_symlink():
                logger.error("Path exists but is not a symlink")
                return False
                
            # Try to read from symlink
            test_file = next(self.target_path.iterdir(), None)
            if test_file is None:
                logger.error("Cannot read from symlink")
                return False
                
            logger.info("Symlink verification successful")
            return True
            
        except Exception as e:
            logger.error(f"Symlink verification failed: {str(e)}")
            return False
            
    def setup(self) -> bool:
        """Complete setup process."""
        if not self.check_admin():
            logger.error("This script requires administrator privileges")
            logger.info("Please run this script as administrator")
            return False
            
        if not self.verify_paths():
            return False
            
        if not self.create_symlink():
            return False
            
        if not self.verify_symlink():
            return False
            
        logger.info("Symlink setup completed successfully")
        return True

def main():
    """Main entry point."""
    setup = SymlinkSetup()
    if not setup.setup():
        sys.exit(1)

if __name__ == "__main__":
    main() 