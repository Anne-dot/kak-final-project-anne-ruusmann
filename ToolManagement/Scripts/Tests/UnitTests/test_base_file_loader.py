"""
Unit tests for the base FileLoader class.

These tests verify that the base file loading functionality works correctly,
including validation, error handling, and generic file loading operations.
"""

import unittest
import os
import sys
import tempfile
import platform
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock the logging_utils module to avoid file creation during tests
sys.modules['Utils.logging_utils'] = MagicMock()
from Utils.logging_utils import setup_logger, log_exception

# Import the module to test
from Utils.file_loader import BaseFileLoader
from Utils.error_utils import ErrorHandler


# Create a concrete implementation of BaseFileLoader for testing
class TestableFileLoader(BaseFileLoader):
    """Concrete implementation of BaseFileLoader for testing."""
    
    def __init__(self, allowed_extensions=None, description="Test"):
        super().__init__(allowed_extensions, description)
        self.loaded_content = None
    
    def load_file(self, file_path=None):
        """Implement the abstract method for testing."""
        # If no path provided, prompt for file selection
        if file_path is None:
            file_path = self.select_file()
            
            # Check if user canceled file selection
            if not file_path:
                return False, "File selection canceled", {"error": "canceled"}
        
        # Validate file
        success, message, details = self.validate_file(file_path)
        if not success:
            return success, message, details
        
        # Load file
        try:
            with open(file_path, 'r') as f:
                self.loaded_content = f.read()
            
            return ErrorHandler.create_success_response(
                message=f"Loaded {self.description} file successfully",
                data={"content": self.loaded_content}
            )
        except Exception as e:
            return ErrorHandler.from_exception(e)
    
    def get_file_info(self, file_content=None):
        """Implement the abstract method for testing."""
        content = file_content or self.loaded_content
        
        if not content:
            return False, "No content loaded", {"error": "no_content"}
        
        # Return some simple file info
        lines = content.splitlines()
        return ErrorHandler.create_success_response(
            message=f"Got info for {self.description} file",
            data={
                "line_count": len(lines),
                "char_count": len(content)
            }
        )


class TestBaseFileLoader(unittest.TestCase):
    """Tests for the BaseFileLoader abstract class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a valid test file
        self.valid_file_path = os.path.join(self.test_dir, "valid_test.txt")
        with open(self.valid_file_path, 'w') as f:
            f.write("Test content\nSecond line")
        
        # Create a file with different extension
        self.wrong_ext_file_path = os.path.join(self.test_dir, "wrong_ext.dat")
        with open(self.wrong_ext_file_path, 'w') as f:
            f.write("Wrong extension file")
            
        # Set up mocks for logging
        setup_logger.return_value = MagicMock()
        
        # Create the loader instance for testing
        self.loader = TestableFileLoader(allowed_extensions=['.txt', '.csv'])
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_validate_file_success(self):
        """Test successful file validation."""
        success, message, details = self.loader.validate_file(self.valid_file_path)
        
        self.assertTrue(success)
        self.assertIn("valid", message)
    
    def test_validate_file_nonexistent(self):
        """Test validation with non-existent file."""
        success, message, details = self.loader.validate_file(
            os.path.join(self.test_dir, "nonexistent.txt")
        )
        
        self.assertFalse(success)
        self.assertIn("not found", message)
    
    def test_validate_file_wrong_extension(self):
        """Test validation with incorrect file extension."""
        success, message, details = self.loader.validate_file(self.wrong_ext_file_path)
        
        self.assertFalse(success)
        self.assertIn("valid extension", message)
    
    def test_load_file_success(self):
        """Test successful file loading."""
        success, message, details = self.loader.load_file(self.valid_file_path)
        
        self.assertTrue(success)
        self.assertEqual(details.get("content"), "Test content\nSecond line")
    
    @patch('Utils.file_loader.platform.system')
    @patch('Utils.file_loader.filedialog.askopenfilename')
    def test_select_file_windows(self, mock_askopenfilename, mock_system):
        """Test file selection on Windows."""
        # Mock Windows platform
        mock_system.return_value = "Windows"
        
        # Mock file dialog response
        mock_askopenfilename.return_value = "C:/Path/to/selected.txt"
        
        # Test file selection
        selected_file = self.loader.select_file()
        
        # Verify results
        self.assertEqual(selected_file, "C:/Path/to/selected.txt")
        mock_askopenfilename.assert_called_once()
    
    @unittest.skipIf(platform.system() == 'Windows', "Skipping Linux-specific test on Windows")
    @patch('Utils.file_loader.platform.system')
    @patch('Utils.file_loader.os.listdir')
    @patch('builtins.input')
    def test_select_file_linux(self, mock_input, mock_listdir, mock_system):
        """Test file selection on Linux."""
        # Mock Linux platform
        mock_system.return_value = "Linux"
        
        # Mock directory listing
        mock_listdir.return_value = ["test1.txt", "test2.txt", "not_a_txt.dat"]
        
        # Mock user input
        mock_input.return_value = "1"  # User selects the first file
        
        # Mock test_data_dir existence check
        with patch('Utils.file_loader.os.path.exists', return_value=True):
            # Test file selection with hard-coded test dir
            selected_file = self.loader.select_file(test_data_dir=self.test_dir)
        
        # The selected file should be test1.txt in the test dir
        expected_path = os.path.join(self.test_dir, "test1.txt")
        self.assertEqual(selected_file, expected_path)
        mock_input.assert_called_once()
    
    def test_get_file_info(self):
        """Test getting file info."""
        # First load a file
        self.loader.load_file(self.valid_file_path)
        
        # Then get info
        success, message, details = self.loader.get_file_info()
        
        self.assertTrue(success)
        self.assertEqual(details.get("line_count"), 2)
        # Depending on line endings, could be 23 or 24 characters
        self.assertIn(details.get("char_count"), [23, 24])  # "Test content\nSecond line"


if __name__ == '__main__':
    unittest.main()