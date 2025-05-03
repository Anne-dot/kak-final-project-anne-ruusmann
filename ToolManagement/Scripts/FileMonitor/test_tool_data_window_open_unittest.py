"""
Unit tests for window detection functionality.

These tests verify that the window detection functions correctly
identify when tool data files are open in Notepad.
"""

import subprocess
import time
import unittest
import logging
from pathlib import Path
import os

from window_detector import is_tool_data_open

class TestToolDataWindow(unittest.TestCase):
    """Tests for detecting when tool data files are open in editors."""
    
    def setUp(self):
        """Set up test environment with a sample tool data file."""
        self.test_file = Path("tool-data.txt")
        self.test_file.write_text("Test content.")
        
        # Configure logging for tests
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting window detection test")

    def test_tool_data_open_close(self):
        """
        Test detection of tool data file being opened and closed.
        
        This test opens a sample file in Notepad, verifies it's detected 
        as open, then closes Notepad and verifies it's detected as closed.
        """
        # Open file in Notepad
        self.logger.info("Opening test file in Notepad")
        proc = subprocess.Popen(["notepad.exe", str(self.test_file)])
        time.sleep(2)  # Give it time to fully open

        # Check that it's detected as open
        self.assertTrue(is_tool_data_open())
        self.logger.info("File correctly detected as open")

        # Close Notepad
        self.logger.info("Closing Notepad")
        subprocess.run(["taskkill", "/IM", "notepad.exe", "/F"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        time.sleep(2)  # Give it time to close

        # Check that it's detected as closed
        self.assertFalse(is_tool_data_open())
        self.logger.info("File correctly detected as closed")

    def tearDown(self):
        """Clean up test file if it exists."""
        if self.test_file.exists():
            self.test_file.unlink()
            self.logger.info("Test file removed")

if __name__ == "__main__":
    unittest.main()

