"""
Test for DrillPointExtractor strict validation.

This script tests the DrillPointExtractor with real DXF files and with
specially created test cases to verify strict validation of required parameters.
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

from DXF.extractor import DrillPointExtractor
from DXF.parser import DXFParser


def test_real_files():
    """Test drill extraction with real DXF files."""
    print("\nTesting with real DXF files:")
    print("-" * 50)

    # Get test files from the test data directory
    test_data_dir = Path(__file__).parent.parent.parent / "TestData" / "DXF"

    # List of test files to try
    test_files = [
        test_data_dir / "Bottom_2_f0.dxf",
        test_data_dir / "Back_5_f0.dxf",
        test_data_dir / "Left Side_3_f1.dxf",
    ]

    for test_file in test_files:
        print(f"\nTesting file: {test_file.name}")

        if not test_file.exists():
            print("  File not found, skipping")
            continue

        # Parse the DXF file
        parser = DXFParser()
        success, message, result = parser.parse(test_file)

        if not success:
            print(f"  Failed to parse DXF file: {message}")
            continue

        print(f"  DXF parsing: {message}")

        # Extract drill points
        document = result["document"]
        extractor = DrillPointExtractor()
        success, message, extract_result = extractor.extract(document)

        # Display results
        print(f"  Drill extraction: {message}")

        if success:
            drill_points = extract_result.get("drill_points", [])
            skipped = extract_result.get("skipped_count", 0)
            issues = extract_result.get("issues", [])

            print(f"  Found {len(drill_points)} drill points, {skipped} points skipped")

            if issues:
                print("\n  Issues detected:")
                for i, issue in enumerate(issues):
                    print(
                        f"    {i + 1}. {issue['entity_type']} on layer {issue['layer']} at {issue['position']}"
                    )

            if drill_points:
                # Print ALL drill points
                print("\n  Drill Points Summary:")
                print(
                    f"  {'#':<4} {'Position':<24} {'Diam':<8} {'Depth':<8} {'Direction':<14} {'Layer'}"
                )
                print("  " + "-" * 85)

                for i, point in enumerate(drill_points):
                    pos = point.get("position", (0, 0, 0))
                    pos_str = f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})"
                    diam = point.get("diameter", 0)
                    depth = point.get("depth", 0)
                    direction = point.get("direction", (0, 0, 0))
                    layer = point.get("layer", "")

                    print(
                        f"  {i + 1:<4} {pos_str:<24} {diam:<8.2f} {depth:<8.2f} {direction!s:<14} {layer}"
                    )
        else:
            print(f"  Error: {message}")


def create_test_file_missing_depth():
    """Create a test file with missing depth parameter."""
    # Create a new DXF file
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Add a circle with missing depth info
    msp.add_circle(center=(10, 10, 0), radius=4.0, dxfattribs={"layer": "EDGE.DRILL_D8.0"})

    # Add a circle with proper parameters (control)
    msp.add_circle(center=(30, 10, 0), radius=4.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P15.0"})

    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix=".dxf", delete=False)
    doc.saveas(temp_file.name)

    return temp_file.name


def create_test_file_invalid_values():
    """Create a test file with invalid parameter values."""
    # Create a new DXF file
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Add a circle with zero depth
    msp.add_circle(center=(10, 10, 0), radius=4.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P0.0"})

    # Add a circle with negative depth
    msp.add_circle(center=(30, 10, 0), radius=4.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P-5.0"})

    # Add a circle with zero radius but valid layer info
    msp.add_circle(center=(50, 10, 0), radius=0.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P15.0"})

    # Add a proper circle (control)
    msp.add_circle(center=(70, 10, 0), radius=4.0, dxfattribs={"layer": "EDGE.DRILL_D8.0_P15.0"})

    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix=".dxf", delete=False)
    doc.saveas(temp_file.name)

    return temp_file.name


def test_validation_cases():
    """Test strict validation with specially created test cases."""
    print("\nTesting validation cases:")
    print("-" * 50)

    # Test case 1: Missing depth parameter
    print("\nTest Case 1: Missing Depth Parameter")
    test_file = create_test_file_missing_depth()
    print(f"  Created test file: {test_file}")

    # Parse and extract
    parser = DXFParser()
    success, message, result = parser.parse(test_file)

    if success:
        document = result["document"]
        extractor = DrillPointExtractor()
        success, message, extract_result = extractor.extract(document)

        print(f"  Drill extraction: {message}")

        if success:
            drill_points = extract_result.get("drill_points", [])
            skipped = extract_result.get("skipped_count", 0)

            print(f"  Extracted {len(drill_points)} drill points, {skipped} points skipped")

            # Should extract only the valid point and skip the one missing depth
            if len(drill_points) == 1 and skipped == 1:
                print("  ✓ Correctly skipped point with missing depth parameter")
            else:
                print(f"  ✗ Unexpected results: {len(drill_points)} extracted, {skipped} skipped")

    # Clean up
    os.unlink(test_file)

    # Test case 2: Invalid parameter values
    print("\nTest Case 2: Invalid Parameter Values")
    test_file = create_test_file_invalid_values()
    print(f"  Created test file: {test_file}")

    # Parse and extract
    parser = DXFParser()
    success, message, result = parser.parse(test_file)

    if success:
        document = result["document"]
        extractor = DrillPointExtractor()
        success, message, extract_result = extractor.extract(document)

        print(f"  Drill extraction: {message}")

        if success:
            drill_points = extract_result.get("drill_points", [])
            skipped = extract_result.get("skipped_count", 0)

            print(f"  Extracted {len(drill_points)} drill points, {skipped} points skipped")

            # Should extract only the valid point and skip the invalid ones
            if len(drill_points) == 1 and skipped == 3:
                print("  ✓ Correctly skipped points with invalid parameters")
            else:
                print(f"  ✗ Unexpected results: {len(drill_points)} extracted, {skipped} skipped")

    # Clean up
    os.unlink(test_file)


def run_test():
    """Run all drill extraction validation tests."""
    print("\nDrillPointExtractor Validation Test")
    print("=" * 30)

    # Test with real files
    test_real_files()

    # Test validation cases
    test_validation_cases()


if __name__ == "__main__":
    run_test()
