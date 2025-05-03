"""
DEPRECATED: File locking implementation has been moved to Utils.file_lock_utils

This module is retained for backward compatibility and simply imports and re-exports
the consolidated FileLock implementation from Utils.file_lock_utils.

For all new code, use:
    from Utils.file_lock_utils import FileLock
"""

import os
import sys
import logging

# Add parent directory to path so we can import from Utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the consolidated FileLock implementation
from Utils.file_lock_utils import FileLock

# Log a deprecation warning
logging.warning(
    "Backups.file_lock is deprecated. Please use Utils.file_lock_utils instead."
)
