"""
Utility modules for the CNC milling project.

This package contains core utility modules used throughout the application,
providing consistent functionality for file operations, error handling,
path management, and logging.

Modules:
    config: Centralized configuration constants and settings
    error_utils: Standardized error handling and custom exceptions
    file_utils: Safe file operations with locking mechanisms
    file_lock_utils: File locking functionality to prevent concurrent access
    logging_utils: Consistent logging setup across the application
    path_utils: Cross-platform path handling and directory management
    ui_utils: Platform-independent user interface utilities
"""

# Import key classes to make them available at package level
from .config import AppConfig
from .error_utils import ErrorSeverity, ErrorCategory, BaseError, FileError, ValidationError, ConfigurationError, ErrorHandler
from .file_lock_utils import FileLock
from .file_loader import BaseFileLoader
from .file_utils import FileUtils
from .logging_utils import setup_logger, log_exception, get_log_path
from .path_utils import PathUtils

# Define publicly available items
__all__ = [
    # config
    'AppConfig',
    
    # error_utils
    'ErrorSeverity', 'ErrorCategory', 'BaseError', 'FileError', 
    'ValidationError', 'ConfigurationError', 'ErrorHandler',
    
    # file_lock_utils
    'FileLock',
    
    # file_loader
    'BaseFileLoader',
    
    # file_utils
    'FileUtils',
    
    # logging_utils
    'setup_logger', 'log_exception', 'get_log_path',
    
    # path_utils
    'PathUtils'
]