"""
Manual test script for window detection functionality.

This script provides a simple way to manually test if the tool data
file is detected as open in Notepad or WordPad.

Note: This test is Windows-specific and will be skipped on other platforms.

Usage:
    python test_window_detector_manual.py [path_to_file]
"""

import logging
import os
import platform
import sys
import time

# Skip test on non-Windows platforms
if platform.system() != "Windows":
    print(f"Skipping window detection test on {platform.system()} - Windows required.")
    sys.exit(0)

# Add FileMonitor directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from FileMonitor import is_tool_data_open

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def print_header(text):
    """Print a header with decorative borders."""
    border = "=" * 60
    print(f"\n{border}")
    print(f"{text.center(60)}")
    print(f"{border}\n")


def test_file_detection(file_path):
    """
    Test if file is detected as open in Notepad or WordPad.

    Args:
        file_path: Path to the file to check
    """
    print_header("WINDOW DETECTOR MANUAL TEST")

    # Normalize path
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return

    print(f"Testing file: {file_path}")
    print(f"Filename: {os.path.basename(file_path)}")

    # First test with file hopefully NOT open
    print("\nTEST 1: Checking if file is currently open...")
    result = is_tool_data_open()

    if result:
        print("File IS currently open")
        print("Please close the file and run the test again.")
        return
    print("File is NOT currently open in any supported editor.")

    # Instructions for user
    print("\n" + "-" * 60)
    print("INSTRUCTIONS:")
    print("1. Please open the file in Notepad now")
    print("2. Waiting 20 seconds...")
    print("-" * 60)

    # Wait for user to open file
    time.sleep(20)

    # Test again after file should be open
    print("\nTEST 2: Checking if file is now open...")
    result = is_tool_data_open()

    if result:
        print("SUCCESS: File detected as open")
    else:
        print("FAILED: File not detected as open in any supported editor.")
        print("This could mean:")
        print("- The file wasn't opened yet")
        print("- The file was opened in an unsupported editor")
        print("- The detection failed")

    print("\n" + "-" * 60)
    print("TEST COMPLETE")
    print("-" * 60)


if __name__ == "__main__":
    # Get file path from command line or use default from TestData
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Use a test file from the TestData directory
        test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")

        # Try DXF file first
        dxf_file = os.path.join(test_data_dir, "DXF", "Bottom_2_f0.dxf")

        # If DXF file doesn't exist, try a GCode file
        if not os.path.exists(dxf_file):
            file_path = os.path.join(test_data_dir, "Gcode", "001.txt")
        else:
            file_path = dxf_file

    # Run test
    test_file_detection(file_path)
