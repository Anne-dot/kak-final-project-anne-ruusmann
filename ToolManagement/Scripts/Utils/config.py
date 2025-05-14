#!/usr/bin/env python3
"""
Configuration module for centralized constants and settings.

This module provides centralized access to configuration constants
used throughout the application, including paths, timeouts, and
application settings.

Configuration categories:
    - Paths: File and directory paths
    - Timeouts: Various operation timeouts
    - Limits: Numeric limits and constraints
    - File Patterns: File naming and matching patterns
    - G-Code Settings: Default G-code parameters
    - UI Settings: User interface text and settings

Classes:
    AppConfig: Main configuration class with nested configuration categories
"""

import os
import platform
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any


class PathConfig:
    """Configuration for file system paths."""
    
    # Base directories
    MACH3_DIR_NAME = "Mach3"
    TOOL_MANAGEMENT_DIR_NAME = "ToolManagement"
    
    # Subdirectories
    DATA_DIR_NAME = "Data"
    BACKUPS_DIR_NAME = "Backups"
    LOGS_DIR_NAME = "Logs"
    SCRIPTS_DIR_NAME = "Scripts"
    TESTS_DIR_NAME = "Tests"
    TEST_DATA_DIR_NAME = "TestData"
    DXF_TEST_DATA_DIR_NAME = "DXF"
    GCODE_TEST_DATA_DIR_NAME = "Gcode"
    
    # Files
    TOOL_DATA_FILENAME = "tool-data.csv"
    TOOL_DATA_BACKUP_FILENAME = "tool-data.csv.bak"
    
    # Default paths based on script location
    if platform.system() == "Windows":
        DEFAULT_MACH3_ROOT = Path("C:/Mach3")
    else:
        # Use script location to determine Mach3 root directory
        # Start with current file's directory (Utils)
        current_dir = Path(__file__).resolve().parent
        
        # If in Utils directory, go up to Scripts then to Mach3 root
        if current_dir.name.lower() == 'utils':
            scripts_dir = current_dir.parent
            if scripts_dir.name.lower() == 'scripts':
                DEFAULT_MACH3_ROOT = scripts_dir.parent.parent
            else:
                DEFAULT_MACH3_ROOT = scripts_dir.parent
        else:
            # Fallback to parent of parent
            DEFAULT_MACH3_ROOT = current_dir.parent.parent
    
    @classmethod
    def get_tool_management_dir(cls) -> Path:
        """Returns the path to the ToolManagement directory."""
        return cls.DEFAULT_MACH3_ROOT / cls.TOOL_MANAGEMENT_DIR_NAME
    
    @classmethod
    def get_data_dir(cls) -> Path:
        """Returns the path to the Data directory."""
        return cls.get_tool_management_dir() / cls.DATA_DIR_NAME
    
    @classmethod
    def get_backups_dir(cls) -> Path:
        """Returns the path to the Backups directory."""
        return cls.get_tool_management_dir() / cls.BACKUPS_DIR_NAME
    
    @classmethod
    def get_logs_dir(cls) -> Path:
        """Returns the path to the Logs directory."""
        return cls.get_tool_management_dir() / cls.LOGS_DIR_NAME
    
    @classmethod
    def get_tool_data_path(cls) -> Path:
        """Returns the path to the tool-data.csv file."""
        return cls.get_data_dir() / cls.TOOL_DATA_FILENAME
    
    @classmethod
    def get_tool_data_backup_path(cls) -> Path:
        """Returns the path to the tool-data.csv.bak file."""
        return cls.get_data_dir() / cls.TOOL_DATA_BACKUP_FILENAME


class TimeoutConfig:
    """Configuration for timeouts."""
    
    # File operation timeouts (in seconds)
    DEFAULT_LOCK_TIMEOUT = 30.0
    BACKUP_LOCK_TIMEOUT = 1800.0  # 30 minutes
    
    # UI timeouts
    UI_RESPONSE_TIMEOUT = 5.0
    
    # Network timeouts
    NETWORK_TIMEOUT = 10.0


class LimitConfig:
    """Configuration for numeric limits and constraints."""
    
    # Backup limits
    DEFAULT_MAX_BACKUPS = 10
    EXTENDED_MAX_BACKUPS = 20
    
    # Numeric tolerances
    COORDINATE_TOLERANCE = 0.0001


class FilePatternConfig:
    """Configuration for file patterns and naming conventions."""
    
    # Log file pattern
    LOG_FILE_PATTERN = "system_%Y%m%d.log"
    
    # File extensions
    DXF_FILE_EXTENSION = ".dxf"
    GCODE_FILE_EXTENSION = ".nc"
    
    # File dialog filters
    DXF_FILE_FILTER = "DXF Files (*.dxf)"
    ALL_FILES_FILTER = "All Files (*.*)"
    
    # Window detection patterns
    TOOL_DATA_WINDOW_PATTERNS = ["tool-data", "*tool-data"]


class GCodeConfig:
    """Configuration for G-code generation and processing."""
    
    # Default G-code modal states
    DEFAULT_PLANE = "G17"  # XY plane
    DEFAULT_UNITS = "G21"  # millimeters
    DEFAULT_POSITIONING = "G90"  # absolute
    DEFAULT_FEEDRATE_MODE = "G94"  # units per minute


class ToolConfig:
    """Configuration for tool management and matching."""
    
    # Tool types
    TOOL_TYPE_MILL = "Mill"
    TOOL_TYPE_SAW = "Saw"
    TOOL_TYPE_VERTICAL_DRILL = "VerticalDrill"
    TOOL_TYPE_HORIZONTAL_DRILL = "HorizontalDrill"
    
    # Tool direction codes from CSV
    DIRECTION_LEFT_TO_RIGHT = 1  # X+ (Left to Right)
    DIRECTION_RIGHT_TO_LEFT = 2  # X- (Right to Left)
    DIRECTION_FRONT_TO_BACK = 3  # Y+ (Front to Back)
    DIRECTION_BACK_TO_FRONT = 4  # Y- (Back to Front)
    DIRECTION_VERTICAL = 5       # Z+ (Vertical, Top to Bottom)
    
    # Direction vector to tool_direction code mapping
    DIRECTION_VECTOR_MAPPING = {
        (1.0, 0.0, 0.0): DIRECTION_LEFT_TO_RIGHT,   # X+
        (-1.0, 0.0, 0.0): DIRECTION_RIGHT_TO_LEFT,  # X-
        (0.0, 1.0, 0.0): DIRECTION_FRONT_TO_BACK,   # Y+
        (0.0, -1.0, 0.0): DIRECTION_BACK_TO_FRONT,  # Y-
        (0.0, 0.0, 1.0): DIRECTION_VERTICAL         # Z+
    }


class UIConfig:
    """Configuration for user interface elements."""
    
    # Dialog titles
    DXF_FILE_SELECT_TITLE = "Select DXF File"
    TOOL_DATA_SELECT_TITLE = "Select Tool Data File"
    
    # Message texts
    FILE_LOCKED_MESSAGE = "File is currently locked by another process"
    OPERATION_SUCCESSFUL_MESSAGE = "Operation completed successfully"


class LoggingConfig:
    """Configuration for logging."""
    
    # Default log levels
    DEFAULT_FILE_LOG_LEVEL = "INFO"
    DEFAULT_CONSOLE_LOG_LEVEL = "WARNING"
    
    # Log format
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class AppConfig:
    """
    Main application configuration class.
    
    This class provides centralized access to all configuration categories.
    """
    
    # Configuration categories
    paths = PathConfig
    timeouts = TimeoutConfig
    limits = LimitConfig
    file_patterns = FilePatternConfig
    gcode = GCodeConfig
    tool = ToolConfig
    ui = UIConfig
    logging = LoggingConfig
    
    @classmethod
    def get_platform(cls) -> str:
        """Returns the current platform name."""
        return platform.system()
    
    @classmethod
    def is_windows(cls) -> bool:
        """Returns True if running on Windows."""
        return cls.get_platform() == "Windows"
    
    @classmethod
    def is_linux(cls) -> bool:
        """Returns True if running on Linux."""
        return cls.get_platform() == "Linux"
    
    @classmethod
    def is_mac(cls) -> bool:
        """Returns True if running on macOS."""
        return cls.get_platform() == "Darwin"


# Export the main configuration class for direct import
__all__ = ['AppConfig']