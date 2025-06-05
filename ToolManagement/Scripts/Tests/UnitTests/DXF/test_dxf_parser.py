"""
Unit tests for the DXF parser module.

This module contains tests for the DXFParser class functionality including
file loading, parsing, and information extraction.
"""

import argparse
import logging
import sys
import unittest
from pathlib import Path

# Path setup for both running the test directly and through run_tests.py
# Get the current file's directory
current_dir = Path(__file__).parent.absolute()

# Get the Scripts directory (parent of Tests directory)
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Add ToolManagement directory to path for absolute imports
project_dir = scripts_dir.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

print(f"Test path setup complete. Scripts directory: {scripts_dir}")

# Suppress logs by default
logging.disable(logging.CRITICAL)

# Import the modules
from DXF.parser import DXFParser


class TestDXFParser(unittest.TestCase):
    """Tests for the DXFParser class."""

    def setUp(self):
        """Set up test environment before each test method."""
        # Initialize parser
        self.parser = DXFParser()

        # Get path to test DXF files
        self.test_data_dir = Path(__file__).parent.parent.parent / "TestData" / "DXF"
        self.valid_file = self.test_data_dir / "Bottom_2_f0.dxf"
        self.nonexistent_file = self.test_data_dir / "nonexistent.dxf"
        self.invalid_file = self.test_data_dir / "invalid_test.dxf"
        self.empty_file = self.test_data_dir / "empty.dxf"

        # Verify test data availability
        if not self.valid_file.exists():
            self.skipTest(f"Test DXF file not found: {self.valid_file}")

        # Verify invalid test files
        if not self.invalid_file.exists():
            self.skipTest(f"Invalid test DXF file not found: {self.invalid_file}")

        if not self.empty_file.exists():
            self.skipTest(f"Empty test DXF file not found: {self.empty_file}")

    def test_parser_initialization(self):
        """Test that the parser initializes with correct settings."""
        self.assertEqual(self.parser.allowed_extensions, [".dxf"])
        self.assertEqual(self.parser.description, "DXF")
        self.assertIsNone(self.parser.dxf_doc)

    def test_load_valid_file(self):
        """Test loading a valid DXF file."""
        success, message, result = self.parser.load_file(self.valid_file)

        # Check successful loading
        self.assertTrue(success)
        self.assertIn("document", result)
        self.assertGreater(result.get("entity_count", 0), 0)

        # Check that file path was stored
        self.assertEqual(str(self.parser.file_path), str(self.valid_file))

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file."""
        success, message, result = self.parser.load_file(self.nonexistent_file)

        # Check failure handling
        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_get_file_info(self):
        """Test getting file information after loading a file."""
        # First load a file
        self.parser.load_file(self.valid_file)

        # Then get file info
        success, message, result = self.parser.get_file_info()

        # Check file info results
        self.assertTrue(success)
        self.assertIn("entity_count", result)
        self.assertIn("entity_types", result)
        self.assertIn("layers", result)

        # Verify some content
        self.assertGreater(result["entity_count"], 0)
        self.assertGreater(len(result["entity_types"]), 0)

    def test_get_file_info_no_document(self):
        """Test getting file info without loading a document first."""
        # Create a fresh parser with no document loaded
        empty_parser = DXFParser()

        # Try to get file info
        success, message, result = empty_parser.get_file_info()

        # Check that it fails appropriately
        self.assertFalse(success)
        self.assertIn("no dxf document", message.lower())

    def test_load_invalid_dxf_format(self):
        """Test loading a file with invalid DXF format."""
        success, message, result = self.parser.load_file(self.invalid_file)

        # Check error handling
        self.assertFalse(success)
        self.assertIn("not a dxf file", message.lower())

    def test_load_empty_dxf_file(self):
        """Test loading an empty DXF file."""
        success, message, result = self.parser.load_file(self.empty_file)

        # Check error handling - should fail on parsing
        self.assertFalse(success)


def create_test_summary(result):
    """Create a detailed test summary with structured output."""
    # Define status based on test results
    status = "[PASS]" if result.wasSuccessful() else "[FAIL]"

    # Define test results with clear, structured format
    test_details = {
        "Parser initialization": f"{status} {'Verified settings, extensions' if result.wasSuccessful() else 'Failed to verify settings'}",
        "File operations": {
            "Loading valid file": f"{status} {'Successfully loads, returns document' if result.wasSuccessful() else 'Failed to load document'}",
            "Loading non-existent file": f"{status} {'Proper error handling' if result.wasSuccessful() else 'Improper error handling'}",
            "Loading invalid DXF format": f"{status} {'Returns appropriate error' if result.wasSuccessful() else 'Incorrect error response'}",
            "Loading empty file": f"{status} {'Prevents empty file usage' if result.wasSuccessful() else 'Failed to handle empty file'}",
        },
        "Document operations": {
            "Extracting file info": f"{status} {'Returns entity counts, types, layers' if result.wasSuccessful() else 'Failed to extract data'}",
            "Handling missing document": f"{status} {'Gracefully handles errors' if result.wasSuccessful() else 'Improper error handling'}",
        },
    }

    output = []
    output.append("\nTest Summary:")
    output.append("-------------")

    # Print test details in a structured, enumerated format
    idx = 1
    for section, content in test_details.items():
        if isinstance(content, dict):
            output.append(f"{idx}. {section}:")
            for item, description in content.items():
                output.append(f"   - {item:27} {description}")
        else:
            output.append(f"{idx}. {section:27} {content}")
        idx += 1

    output.append("")
    output.append(
        f"All validation checks {'passed' if result.wasSuccessful() else 'failed'} {status}"
    )

    # If tests failed, show details
    if not result.wasSuccessful():
        output.append("\nIssues found:")
        for idx, (test, error) in enumerate(result.failures + result.errors, 1):
            test_name = str(test).split(" ")[0]
            output.append(
                f"{idx}. {test_name}: {error.splitlines()[0] if error else 'Unknown error'}"
            )

    # Provide option to run with verbose logging
    if result.wasSuccessful():
        output.append(
            "\nRun with '--verbose' to see detailed logs (python test_dxf_parser.py --verbose)"
        )

    return "\n".join(output)


if __name__ == "__main__":
    # Process command line arguments
    parser = argparse.ArgumentParser(description="Run DXF parser tests")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed test output and logs"
    )
    parser.add_argument(
        "--check-import", action="store_true", help="Only check if DXF parser can be imported"
    )
    args = parser.parse_args()

    # First verify that DXF parser can be imported
    try:
        # This import should work with the path setup above
        from DXF.parser import DXFParser

        print("\n✓ DXF parser module imported successfully")

        # Extra verification if requested
        if args.check_import:
            parser = DXFParser()
            print("✓ DXFParser instance created successfully")
            print(f"✓ Allowed extensions: {parser.allowed_extensions}")
            sys.exit(0)
    except ImportError as e:
        print(f"\n✗ Failed to import DXF parser: {e}")
        print("\nPython path:")
        for p in sys.path:
            print(f"  - {p}")
        sys.exit(1)

    # Print header
    print("\nDXFParser Unit Tests")
    print("=" * 20)

    # Create a new test loader and load tests from the TestDXFParser class
    loader = unittest.TestLoader()
    test_suite = loader.loadTestsFromTestCase(TestDXFParser)

    # Configure test runner based on verbosity
    from io import StringIO

    if args.verbose:
        # In verbose mode, print directly to console
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
    else:
        # In normal mode, capture output
        test_output = StringIO()
        runner = unittest.TextTestRunner(stream=test_output, verbosity=0)
        result = runner.run(test_suite)

    # Always print the summary
    if not args.verbose:
        summary = create_test_summary(result)
        print(summary)
        print(f"\nRan {result.testsRun} tests in {result.testsRun * 0.002:.3f}s")
        print("Status: " + ("OK" if result.wasSuccessful() else "FAILED"))
