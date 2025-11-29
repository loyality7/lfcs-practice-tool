"""
Initialization module for LFCS Practice Tool
Handles setting up the user's workspace with necessary data files.
"""

import os
import shutil
import logging
import importlib.resources
from pathlib import Path

logger = logging.getLogger(__name__)

def initialize_workspace(base_path: str = ".") -> None:
    """
    Initialize the workspace by copying necessary data files if they don't exist.
    
    Args:
        base_path: The directory to initialize (defaults to current directory)
    """
    base_path = Path(base_path).resolve()
    logger.info(f"Initializing workspace at {base_path}")
    
    # Define source and destination paths
    data_items = {
        "scenarios": "scenarios",
        "learn_modules": "learn_modules",
        "schema.sql": "database/schema.sql"
    }
    
    for source_name, dest_rel_path in data_items.items():
        dest_path = base_path / dest_rel_path
        
        # Skip if destination already exists
        if dest_path.exists():
            logger.debug(f"Path {dest_path} already exists, skipping")
            continue
            
        logger.info(f"Installing {source_name} to {dest_path}")
        
        try:
            # Create parent directories if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try to find the data directory relative to this file
            current_file = Path(__file__)
            # src/utils/init.py -> src/data
            local_data_path = current_file.parent.parent / "data" / source_name
            
            if local_data_path.exists():
                _copy_path(local_data_path, dest_path)
                continue
            
            # If not found locally, try importlib.resources (for installed package)
            try:
                # We assume data files are in src.data package
                # Note: This requires src.data to be a package (have __init__.py)
                # or we use files() from python 3.9+
                
                # For directories, it's a bit more complex with importlib.resources
                # We'll try to find the package path
                import src.data
                package_path = Path(src.data.__file__).parent
                source_path = package_path / source_name
                
                if source_path.exists():
                    _copy_path(source_path, dest_path)
                    continue
                    
            except Exception as e:
                logger.warning(f"Could not locate {source_name} using package resources: {e}")
            
            logger.warning(f"Could not find source for {source_name}")

        except Exception as e:
            logger.error(f"Failed to install {source_name}: {e}")

def _copy_path(src: Path, dest: Path):
    """Copy a file or directory"""
    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
