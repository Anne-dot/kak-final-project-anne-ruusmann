"""
Manual test for DrillPointExtractor functionality.

This script loads test DXF files and runs the drill point extractor
to verify extraction works correctly for both successful and failing cases.
Includes a file selector to choose specific files to test.
"""

import sys
from pathlib import Path

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import the modules
from DXF.extractor import DrillPointExtractor
from DXF.parser import DXFParser
from Utils.ui_utils import UIUtils


def process_file(file_path):
    """Test drill point extraction on a specific file."""
    print(f"\nProcessing file: {file_path.name}")
    print("-" * 50)

    # Check if test file exists
    if not file_path.exists():
        print("File not found, skipping")
        return

    # Step 1: Parse the DXF file
    parser = DXFParser()
    success, message, result = parser.parse(file_path)

    if not success:
        print(f"Failed to parse DXF file: {message}")
        return

    print(f"DXF parsing: {message}")

    # Step 2: Extract drill points
    document = result["document"]
    extractor = DrillPointExtractor()
    success, message, extract_result = extractor.extract(document)

    # Step 3: Display results
    print(f"Drill extraction: {message}")

    if success:
        drill_points = extract_result.get("drill_points", [])
        print(f"Found {len(drill_points)} drill points")

        # Print all drill points in a simple tabular format
        if drill_points:
            # Print header
            print("\nDrill Points Table:")
            print(
                f"{'#':<4} {'Position':<30} {'Diameter':<10} {'Depth':<10} {'Direction':<15} {'Layer':<30}"
            )
            print("-" * 100)

            # Print each point as a row
            for i, point in enumerate(drill_points):
                pos = point.get("position", (0, 0, 0))
                pos_str = f"({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})"

                print(
                    f"{i + 1:<4} {pos_str:<30} "
                    f"{point.get('diameter', 0):.2f} mm  "
                    f"{point.get('depth', 0):.2f} mm  "
                    f"{point.get('direction', (0, 0, 0))!s:<15} "
                    f"{point.get('layer', ''):<30}"
                )

            # Print total count
            print("-" * 100)
            print(f"Total drill points found: {len(drill_points)}")
        else:
            print("No drill points found.")
    else:
        print(f"Error: {message}")


def test_with_selector():
    """Test with a file selector for choosing test files."""
    print("\nSelect a DXF file to test:")
    print("=" * 50)

    # Get test files from the test data directory
    test_data_dir = Path(__file__).parent.parent.parent / "TestData" / "DXF"

    # Use UI utility to select a file
    selected_file = UIUtils.select_dxf_file(str(test_data_dir))

    if selected_file:
        process_file(Path(selected_file))
    else:
        print("No file selected.")


def test_all_files():
    """Test all available DXF files."""
    print("\nTesting all available DXF files:")
    print("=" * 50)

    # Test file paths - use all available test files
    test_data_dir = Path(__file__).parent.parent.parent / "TestData" / "DXF"

    # Test successful cases
    test_files = [
        test_data_dir / "Bottom_2_f0.dxf",
        test_data_dir / "Back_5_f0.dxf",
        test_data_dir / "Left Side_3_f1.dxf",
        test_data_dir / "Right Side_4_f0.dxf",
        test_data_dir / "complex_case.dxf",
    ]

    # Test files expected to fail
    fail_files = [test_data_dir / "empty.dxf", test_data_dir / "invalid_test.dxf"]

    print("\n--- Testing Valid DXF Files ---")
    for file_path in test_files:
        process_file(file_path)

    print("\n--- Testing Invalid DXF Files ---")
    for file_path in fail_files:
        process_file(file_path)


def run_test():
    """Run drill point extraction test with menu options."""
    print("\nDrillPointExtractor Test")
    print("=" * 50)

    while True:
        print("\nTest Options:")
        print("1. Select and test a specific file")
        print("2. Test all available files")
        print("0. Exit")

        choice = input("\nSelect an option: ")

        if choice == "1":
            test_with_selector()
        elif choice == "2":
            test_all_files()
        elif choice == "0":
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    run_test()
