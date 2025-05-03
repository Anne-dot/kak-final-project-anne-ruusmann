"""
Window detection module for monitoring open file windows.

This module provides functions to detect if specific files are currently
open in applications like Notepad or Wordpad, which is useful for
preventing concurrent file access issues.

Note: This functionality is Windows-specific. On other platforms,
the detection always returns False.
"""

import subprocess
import logging
import platform
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from Utils.config import AppConfig

def is_tool_data_open() -> bool:
    """
    Check if tool-data file is currently open in Notepad or Wordpad.
    
    On Windows: Uses PowerShell to query window titles and checks for tool-data
    related filename patterns in the window titles.
    
    On other platforms: Always returns False as Notepad/Wordpad are Windows-specific.
    
    Returns:
        bool: True if tool-data file is open, False otherwise
    """
    # Skip actual detection on non-Windows platforms
    if platform.system() != "Windows":
        logging.debug(f"Window detection not supported on {platform.system()}")
        return False
        
    # Window title check for various possible filename patterns
    name_variants = AppConfig.file_patterns.TOOL_DATA_WINDOW_PATTERNS

    try:
        # Use PowerShell to get window titles of Notepad and Wordpad processes
        result = subprocess.run(
            ['powershell', '-Command',
             'Get-Process | Where-Object {$_.MainWindowTitle -and ($_.ProcessName -eq "notepad" -or $_.ProcessName -eq "wordpad")} | Select-Object -ExpandProperty MainWindowTitle'],
            capture_output=True, text=True
        )

        # Check each window title for tool-data patterns
        titles = result.stdout.lower().splitlines()
        for title in titles:
            for name in name_variants:
                if name.lower() in title:
                    logging.info("Tool data file is open in editor.")
                    return True

        logging.debug("Tool data file is not currently open.")
        return False

    except Exception as e:
        logging.error(f"Error checking window status: {e}")
        return False

# Example use
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = is_tool_data_open()
    print(f"Is tool data file open: {result}")
    print(f"Platform: {platform.system()}")