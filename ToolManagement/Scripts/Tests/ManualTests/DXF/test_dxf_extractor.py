"""
Manual test for DXFExtractor functionality.

This script tests the DXFExtractor class that coordinates both workpiece
and drill point extraction from DXF files. It includes a file selector
to choose which test file to process and tests validation cases.
"""

import os
import sys
import tempfile
from pathlib import Path

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import ezdxf for DXF creation and our modules
import ezdxf

from DXF.extractor import DXFExtractor
from DXF.parser import DXFParser
from Utils.ui_utils import UIUtils


def process_file(file_path):
    """Process a single DXF file with the DXFExtractor."""
    print(f"\nProcessing file: {file_path.name}")
    print("-" * 50)

    if not file_path.exists():
        print("File not found, skipping")
        return

    # Parse the DXF file
    parser = DXFParser()
    success, message, result = parser.parse(file_path)

    if not success:
        print(f"Failed to parse DXF file: {message}")
        return

    print(f"DXF parsing: {message}")

    # Extract all entities
    document = result["document"]
    extractor = DXFExtractor()
    success, message, extract_result = extractor.process(document)

    # Display results
    print(f"DXF extraction: {message}")

    if success:
        # Get extraction results
        workpiece = extract_result.get("workpiece")
        drill_points = extract_result.get("drill_points", [])
        skipped = extract_result.get("skipped_drill_points", 0)
        issues = extract_result.get("issues", [])

        # Print workpiece info
        if workpiece:
            print("\nWorkpiece Data:")
            print(
                f"{'Dimensions':<15}: {workpiece['width']:.2f} x {workpiece['height']:.2f} x {workpiece['thickness']:.2f} mm"
            )
            print(f"{'Layer':<15}: {workpiece['layer']}")
            print(f"{'Corner Points':<15}: {len(workpiece['corner_points'])}")

            # Print ALL corner points
            print("\nCorner Points:")
            for i, point in enumerate(workpiece["corner_points"]):
                print(f"  {i + 1}: ({point[0]:.2f}, {point[1]:.2f}, {point[2]:.2f})")

        # Print drill points info
        if drill_points:
            print("\nDrill Points:")
            print(f"{'#':<4} {'Position':<24} {'Diam':<8} {'Depth':<8} {'Direction':<14} {'Layer'}")
            print("-" * 85)

            for i, point in enumerate(drill_points):
                pos = point.get("position", (0, 0, 0))
                pos_str = f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})"
                diam = point.get("diameter", 0)
                depth = point.get("depth", 0)
                direction = point.get("direction", (0, 0, 0))
                layer = point.get("layer", "")

                print(
                    f"{i + 1:<4} {pos_str:<24} {diam:<8.2f} {depth:<8.2f} {direction!s:<14} {layer}"
                )

        # Print information about skipped points
        if skipped > 0:
            print(f"\nSkipped {skipped} drill points due to validation issues")

        # Print issues info
        if issues:
            print("\nIssues Detected:")
            for i, issue in enumerate(issues):
                print(
                    f"  {i + 1}. {issue['entity_type']} on layer {issue['layer']} at {issue['position']}"
                )

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

    # Get test files from the test data directory
    test_data_dir = Path(__file__).parent.parent.parent / "TestData" / "DXF"

    # List of valid test files to try
    test_files = [
        test_data_dir / "Bottom_2_f0.dxf",
        test_data_dir / "Back_5_f0.dxf",
        test_data_dir / "Left Side_3_f1.dxf",
        test_data_dir / "Right Side_4_f0.dxf",
        test_data_dir / "complex_case.dxf",
    ]

    # List of files expected to fail
    fail_files = [test_data_dir / "empty.dxf", test_data_dir / "invalid_test.dxf"]

    print("\n--- Testing Valid DXF Files ---")
    for file_path in test_files:
        process_file(file_path)

    print("\n--- Testing Invalid DXF Files ---")
    for file_path in fail_files:
        process_file(file_path)


def create_test_file_missing_workpiece():
    """Create a test file with drill points but no workpiece."""
    try:
        # Create a new DXF file
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Add drill points without a workpiece
        msp.add_circle(
            center=(10, 10, 0), radius=4.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P15.0"}
        )
        msp.add_circle(
            center=(30, 10, 0), radius=5.0, dxfattribs={"layer": "EDGE.DRILL_D10.0_P20.0"}
        )

        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".dxf", delete=False)
        doc.saveas(temp_file.name)
        return temp_file.name
    except Exception as e:
        print(f"Error creating test file: {e!s}")
        return None


def create_test_file_missing_drills():
    """Create a test file with workpiece but no drill points."""
    try:
        # Create a new DXF file
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Add a workpiece without drill points
        points = [(0, 0), (500, 0), (500, 400), (0, 400), (0, 0)]
        msp.add_lwpolyline(points, dxfattribs={"layer": "PANEL_Egger22mm"})

        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".dxf", delete=False)
        doc.saveas(temp_file.name)
        return temp_file.name
    except Exception as e:
        print(f"Error creating test file: {e!s}")
        return None


def test_validation_cases():
    """Test validation with specially created test cases."""
    print("\nTesting validation cases:")
    print("=" * 50)

    # Test case 1: Missing workpiece
    print("\nTest Case 1: Missing Workpiece")
    print("-" * 50)

    test_file = create_test_file_missing_workpiece()
    if not test_file:
        print("Failed to create test file")
        return

    print(f"Created test file: {test_file}")

    # Parse and extract
    parser = DXFParser()
    success, message, result = parser.parse(test_file)

    if success:
        document = result["document"]
        extractor = DXFExtractor()
        success, message, extract_result = extractor.process(document)

        print(f"DXF extraction: {message}")

        # Should fail due to missing workpiece
        if not success and "workpiece" in message.lower():
            print("Test PASSED: Correctly failed due to missing workpiece")
        else:
            print(
                f"Test FAILED: Unexpected result: {'Success' if success else 'Failed but not due to workpiece'}"
            )

    # Clean up
    try:
        os.unlink(test_file)
    except:
        pass

    # Test case 2: Missing drill points
    print("\nTest Case 2: Missing Drill Points")
    print("-" * 50)

    test_file = create_test_file_missing_drills()
    if not test_file:
        print("Failed to create test file")
        return

    print(f"Created test file: {test_file}")

    # Parse and extract
    parser = DXFParser()
    success, message, result = parser.parse(test_file)

    if success:
        document = result["document"]
        extractor = DXFExtractor()
        success, message, extract_result = extractor.process(document)

        print(f"DXF extraction: {message}")

        # Should fail due to missing drill points
        if not success and "drill point" in message.lower():
            print("Test PASSED: Correctly failed due to missing drill points")
        else:
            print(
                f"Test FAILED: Unexpected result: {'Success' if success else 'Failed but not due to drill points'}"
            )

    # Clean up
    try:
        os.unlink(test_file)
    except:
        pass


def run_test():
    """Run all DXF extractor tests."""
    print("\nDXFExtractor Test")
    print("=" * 50)

    while True:
        print("\nTest Options:")
        print("1. Select and test a specific file")
        print("2. Test all available files")
        print("3. Run validation test cases")
        print("4. Run all tests")
        print("0. Exit")

        choice = input("\nSelect an option: ")

        if choice == "1":
            test_with_selector()
        elif choice == "2":
            test_all_files()
        elif choice == "3":
            test_validation_cases()
        elif choice == "4":
            test_all_files()
            test_validation_cases()
        elif choice == "0":
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    run_test()
