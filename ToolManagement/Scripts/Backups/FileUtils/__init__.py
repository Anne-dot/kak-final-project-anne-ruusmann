"""
FileUtils package for FileLock system.

This package contains utility modules for file operations and lock detection
used by the main FileLock class.

Functions:
    - check_file_locked: Checks if a file is locked by another process
    - create_lock_file: Creates a lock file to indicate file in use
    - remove_file_safely: Removes a file with proper error handling
    - backup_file: Creates a backup copy of a file
"""

# Import key functions to make them available at package level
from .lock_detection import check_file_locked
from .file_operations import create_lock_file, remove_file_safely, backup_file

# Define publicly available items
__all__ = [
    'check_file_locked',
    'create_lock_file',
    'remove_file_safely',
    'backup_file'
]

# Version information
__version__ = "1.0.0"
