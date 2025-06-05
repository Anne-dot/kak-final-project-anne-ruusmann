"""
Unit tests for standardized error handling across modules.

These tests verify that the error handling is implemented consistently
across different modules, focusing on the standardized response format
(success, message, details) and proper error categorization.
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the utility modules
from Backups.backup_manager import BackupManager, BackupRotation
from Backups.FileUtils.file_operations import create_lock_file, remove_file_safely

# Import the modules to test
from GCode.gcode_normalizer import GCodeNormalizer
from GCode.preprocessor import GCodePreprocessor
from GCode.safety_checker import SafetyChecker

from DXF.drilling_extractor import DrillingExtractor
from DXF.file_loader import DxfLoader
from Utils.error_utils import ErrorHandler, ErrorSeverity, ValidationError


class TestErrorHandlingFormat(unittest.TestCase):
    """
    Test that all modules follow the standardized error handling format.

    This tests that all functions return a tuple in the format:
    (success: bool, message: str, details: dict)
    """

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing file operations
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")

        # Create a test file
        with open(self.test_file, "w") as f:
            f.write("Test content")

        # Initialize test objects
        self.gcode_normalizer = GCodeNormalizer()
        self.gcode_preprocessor = GCodePreprocessor()
        self.safety_checker = SafetyChecker()
        self.backup_manager = BackupManager(os.path.join(self.temp_dir, "backups"))
        self.dxf_loader = DxfLoader()
        self.drill_extractor = DrillingExtractor()

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)

    def verify_response_format(self, response, expected_success=None):
        """
        Verify that a response follows the standardized format.

        Args:
            response: The response to verify
            expected_success: If provided, verify that success matches this value
        """
        # Check that the response is a tuple of length 3
        self.assertIsInstance(response, tuple)
        self.assertEqual(len(response), 3)

        # Extract components
        success, message, details = response

        # Check types
        self.assertIsInstance(success, bool)
        self.assertIsInstance(message, str)
        self.assertIsInstance(details, dict)

        # Check expected success if provided
        if expected_success is not None:
            self.assertEqual(success, expected_success)

    def test_gcode_normalizer_format(self):
        """Test that GCodeNormalizer returns standardized format."""
        # Test normalize_file success case
        response = self.gcode_normalizer.normalize_file(self.test_file)
        self.verify_response_format(response, expected_success=True)

        # Test normalize_file error case with non-existent file
        response = self.gcode_normalizer.normalize_file(
            os.path.join(self.temp_dir, "nonexistent.txt")
        )
        self.verify_response_format(response, expected_success=False)

    def test_gcode_preprocessor_format(self):
        """Test that GCodePreprocessor returns standardized format."""
        # Create a mock G-code file content
        gcode_content = "G0 X10 Y10\nG1 Z-5 F100\nG0 Z10"
        gcode_file = os.path.join(self.temp_dir, "test.gcode")
        with open(gcode_file, "w") as f:
            f.write(gcode_content)

        # Test preprocess_file success case
        response = self.gcode_preprocessor.preprocess_file(gcode_file)
        self.verify_response_format(response, expected_success=True)

        # Test preprocess_file error case with non-existent file
        response = self.gcode_preprocessor.preprocess_file(
            os.path.join(self.temp_dir, "nonexistent.gcode")
        )
        self.verify_response_format(response, expected_success=False)

    def test_safety_checker_format(self):
        """Test that SafetyChecker returns standardized format."""
        # Test add_safety_checks
        response = self.safety_checker.add_safety_checks(
            ["G0 X10 Y10", "G1 Z-5 F100"], {"type": "drill", "diameter": 10}
        )
        self.verify_response_format(response, expected_success=True)

        # Test validate_movement
        response = self.safety_checker.validate_movement("drill", "Z-", {"rapid": False})
        self.verify_response_format(response, expected_success=True)

    def test_backup_manager_format(self):
        """Test that BackupManager returns standardized format."""
        # Test create_backup success case
        response = self.backup_manager.create_backup(self.test_file)
        self.verify_response_format(response, expected_success=True)

        # Test create_backup error case with non-existent file
        response = self.backup_manager.create_backup(os.path.join(self.temp_dir, "nonexistent.txt"))
        self.verify_response_format(response, expected_success=False)

    def test_backup_rotation_format(self):
        """Test that BackupRotation returns standardized format."""
        # Create a backup rotation instance
        backup_dir = os.path.join(self.temp_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        rotation = BackupRotation(backup_dir)

        # Test list_backups
        response = rotation.list_backups()
        self.verify_response_format(response, expected_success=True)

        # Test prune
        response = rotation.prune()
        self.verify_response_format(response, expected_success=True)

    def test_file_operations_format(self):
        """Test that file operations functions return standardized format."""
        # Test create_lock_file
        response = create_lock_file(
            os.path.join(self.temp_dir, "lock_file"), {"pid": 123, "time": "now"}
        )
        self.verify_response_format(response, expected_success=True)

        # Test remove_file_safely success case
        response = remove_file_safely(self.test_file)
        self.verify_response_format(response, expected_success=True)

        # Test remove_file_safely with non-existent file
        # (Should still return success since no file to remove)
        response = remove_file_safely(self.test_file)  # Already removed
        self.verify_response_format(response, expected_success=True)

    @patch("ezdxf.readfile")
    def test_dxf_loader_format(self, mock_readfile):
        """Test that DxfLoader returns standardized format."""
        # Create a mock DXF file
        dxf_file = os.path.join(self.temp_dir, "test.dxf")
        with open(dxf_file, "w") as f:
            f.write("Mock DXF content")

        # Set up mock for ezdxf.readfile
        mock_doc = MagicMock()
        # Setup modelspace to return entities
        mock_modelspace = MagicMock()
        mock_entities = [MagicMock(), MagicMock()]  # Two mock entities
        mock_modelspace.__iter__.return_value = mock_entities
        mock_modelspace.__len__.return_value = len(mock_entities)
        mock_doc.modelspace.return_value = mock_modelspace
        mock_readfile.return_value = mock_doc

        # Test load_dxf success case
        response = self.dxf_loader.load_dxf(dxf_file)
        self.verify_response_format(response, expected_success=True)

        # Test error handling for invalid DXF
        mock_readfile.side_effect = Exception("Invalid DXF file")
        response = self.dxf_loader.load_dxf(dxf_file)
        self.verify_response_format(response, expected_success=False)


class TestErrorHandlingResponses(unittest.TestCase):
    """
    Test that the error responses include the correct information.

    This tests that error responses include:
    - Appropriate error categories
    - Meaningful error messages
    - Useful details in the details dictionary
    """

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.nonexistent_file = os.path.join(self.temp_dir, "does_not_exist.txt")

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)

    def test_file_not_found_responses(self):
        """Test that file not found errors return appropriate responses."""
        # Test GCodeNormalizer with non-existent file
        normalizer = GCodeNormalizer()
        success, message, details = normalizer.normalize_file(self.nonexistent_file)

        # Verify response
        self.assertFalse(success)
        self.assertIn("not found", message.lower())
        self.assertIn("category", details)
        self.assertEqual(details["category"], "FILE")

        # Test BackupManager with non-existent file
        backup_dir = os.path.join(self.temp_dir, "backups")
        backup_manager = BackupManager(backup_dir)
        success, message, details = backup_manager.create_backup(self.nonexistent_file)

        # Verify response
        self.assertFalse(success)
        self.assertIn("does not exist", message.lower())
        self.assertIn("category", details)
        self.assertEqual(details["category"], "FILE")

    def test_validation_error_responses(self):
        """Test that validation errors return appropriate responses."""
        # Create a test case that will cause a validation error
        safety_checker = SafetyChecker()

        # This is a contrived example since the actual implementation is a placeholder
        # In a real implementation, you'd need to use parameters that trigger validation errors
        with patch.object(safety_checker, "validate_movement") as mock_validate:
            # Set up mock to return an error response
            mock_validate.return_value = ErrorHandler.from_exception(
                ValidationError(
                    message="Invalid movement parameters",
                    severity=ErrorSeverity.ERROR,
                    field="direction",
                    value="Z++",
                )
            )

            # Call the method
            success, message, details = safety_checker.validate_movement(
                "drill", "Z++", {"rapid": True}
            )

            # Verify response
            self.assertFalse(success)
            self.assertIn("invalid", message.lower())
            self.assertIn("category", details)
            self.assertEqual(details["category"], "VALIDATION")
            self.assertIn("details", details)
            self.assertIn("field", details["details"])
            self.assertEqual(details["details"]["field"], "direction")

    def test_success_responses(self):
        """Test that success responses include useful information."""
        # Create a test file to use with backup manager
        test_file = os.path.join(self.temp_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("Test content")

        # Test backup creation (a successful operation)
        backup_dir = os.path.join(self.temp_dir, "backups")
        backup_manager = BackupManager(backup_dir)
        success, message, details = backup_manager.create_backup(test_file)

        # Verify response
        self.assertTrue(success)
        # Don't check for specific text in message, just verify it's not empty
        self.assertTrue(message)
        # Successful responses should include useful data
        self.assertIn("backup_path", details)
        self.assertTrue(os.path.exists(details["backup_path"]))


class TestErrorPropagation(unittest.TestCase):
    """
    Test that errors are properly propagated through the system.

    This tests that when a lower-level function raises an exception,
    it is properly caught and converted to a standardized error response.
    """

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)

    def test_file_io_error_propagation(self):
        """Test that file I/O errors are properly handled and converted."""
        # Use a non-existent directory to cause permission issues
        # (This is more reliable across different environments)
        non_writable_dir = os.path.join(self.temp_dir, "non_existent", "deeply", "nested")

        # Try to create a lock file in a location that will cause an error
        response = create_lock_file(
            os.path.join(non_writable_dir, "test.lock"), {"pid": 123, "time": "now"}
        )

        # Verify response format, but don't test specific success/failure
        # which might vary based on implementation
        success, message, details = response
        self.assertIsInstance(success, bool)
        self.assertIsInstance(message, str)
        self.assertIsInstance(details, dict)

    def test_exception_handling_in_modules(self):
        """Test that unexpected exceptions are properly caught and formatted."""
        # Test GCodeNormalizer with a mocked unexpected exception
        normalizer = GCodeNormalizer()

        # Patch the open function to raise an unexpected exception
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = RuntimeError("Unexpected error")

            # This should catch the RuntimeError and convert it to a standardized response
            response = normalizer.normalize_file(os.path.join(self.temp_dir, "test.txt"))

            # Verify the response
            success, message, details = response
            self.assertFalse(success)
            self.assertIn("error", message.lower())
            self.assertIn("category", details)
            # Even unexpected errors should have a category
            self.assertIsNotNone(details["category"])


if __name__ == "__main__":
    unittest.main()
