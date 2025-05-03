"""
FileMonitor package for detecting open files and windows.

This package provides utilities for detecting when files are open
in applications like Notepad or Wordpad, which is useful for 
preventing concurrent access issues with tool data files.

Classes and Functions:
    - is_tool_data_open: Detects if the tool-data file is currently open
"""

from .window_detector import is_tool_data_open

__all__ = ['is_tool_data_open']