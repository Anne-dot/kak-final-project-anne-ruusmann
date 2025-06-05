#!/usr/bin/env python3
"""
DXF Module Pipeline Test.

This script tests the complete processing pipeline for the DXF package:
1. Parse DXF files using DXFParser
2. Extract workpiece and drill points using DXFExtractor
3. Translate visual coordinates using VisualCoordinateTranslator

Usage:
    python test_dxf_processing_pipeline.py
"""

import sys
from pathlib import Path

# Add parent directory to Python path for proper imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent  # Need one more level after moving to DXF subfolder
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import DXF modules
from DXF.extractor import DXFExtractor
from DXF.parser import DXFParser
from DXF.visual_coordinate_translator import VisualCoordinateTranslator

# Import utility modules
from Utils.ui_utils import UIUtils


def process_dxf_file(dxf_file_path):
    """Process a DXF file through the complete pipeline."""
    UIUtils.print_separator(f"Processing DXF File: {Path(dxf_file_path).name}")

    # STEP 1: Parse DXF file
    UIUtils.print_separator("Step 1: Parse DXF File")
    parser = DXFParser()
    parse_success, parse_message, parse_result = parser.parse(dxf_file_path)

    if not parse_success:
        print(f"ERROR: {parse_message}")
        return False, "Parsing failed", None

    print(f"SUCCESS: {parse_message}")
    print(f"   Found {parse_result['entity_count']} entities")

    # STEP 2: Extract workpiece and drill points
    UIUtils.print_separator("Step 2: Extract Workpiece and Drill Points")
    document = parse_result["document"]
    extractor = DXFExtractor()
    extract_success, extract_message, extract_result = extractor.process(document)

    if not extract_success:
        print(f"ERROR: {extract_message}")
        return False, "Extraction failed", None

    print(f"SUCCESS: {extract_message}")

    # Display FULL workpiece information
    workpiece = extract_result["workpiece"]
    print("\nWORKPIECE DETAILS:")
    print("-" * 80)
    print(f"Width: {workpiece['width']}")
    print(f"Height: {workpiece['height']}")
    print(f"Thickness: {workpiece['thickness']}")
    print(f"Layer: {workpiece.get('layer', 'N/A')}")
    print(f"Entity Type: {workpiece.get('entity_type', 'N/A')}")

    print("\nCorner Points:")
    for i, point in enumerate(workpiece["corner_points"]):
        print(f"  Point {i}: ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")

    # Display ALL available keys in workpiece
    print("\nAll workpiece keys:")
    for key in sorted(workpiece.keys()):
        print(f"  - {key}: {type(workpiece[key]).__name__}")

    # Display ALL drill points with FULL details
    drill_points = extract_result["drill_points"]
    print(f"\nDRILL POINTS: {len(drill_points)} total")
    print("-" * 80)

    if drill_points:
        # Show keys in first drill point
        first_point = drill_points[0]
        print("Drill point structure (keys in first point):")
        for key in sorted(first_point.keys()):
            print(f"  - {key}: {type(first_point[key]).__name__}")

        # Display all points with full details
        print("\nAll Drill Points:")
        for i, point in enumerate(drill_points):
            print(f"\nPoint {i}:")
            for key, value in sorted(point.items()):
                print(f"  {key}: {value}")

    # Display any skipped points or issues
    if "skipped_drill_points" in extract_result:
        print(f"\nSkipped drill points: {extract_result['skipped_drill_points']}")

    if "issues" in extract_result:
        print("\nIssues detected:")
        for i, issue in enumerate(extract_result["issues"]):
            print(f"  Issue {i}:")
            for key, value in issue.items():
                print(f"    {key}: {value}")

    # Display all keys in extraction result
    print("\nExtraction result keys:")
    for key in sorted(extract_result.keys()):
        value_type = type(extract_result[key]).__name__
        if isinstance(extract_result[key], list):
            value_info = f"{value_type} of length {len(extract_result[key])}"
        else:
            value_info = value_type
        print(f"  - {key}: {value_info}")

    # STEP 3: Translate visual coordinates to physical space
    UIUtils.print_separator("Step 3: Translate Coordinates")
    translator = VisualCoordinateTranslator()
    translate_success, translate_message, translate_result = translator.translate_coordinates(
        drill_points, workpiece
    )

    if not translate_success:
        print(f"ERROR: {translate_message}")
        return False, "Translation failed", None

    print(f"SUCCESS: {translate_message}")

    # Display ALL keys in translation result
    print("\nTranslation result keys:")
    for key in sorted(translate_result.keys()):
        print(f"  - {key}: {type(translate_result[key]).__name__}")

    # Display workpiece data after translation (if modified)
    if "workpiece" in translate_result:
        workpiece_after = translate_result["workpiece"]
        print("\nWorkpiece after translation:")
        for key, value in sorted(workpiece_after.items()):
            if key == "corner_points":
                print(f"  {key}:")
                for i, point in enumerate(value):
                    print(f"    Point {i}: ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")
            else:
                print(f"  {key}: {value}")

    # Display ALL translated points with FULL details
    translated_points = translate_result["drill_points"]
    print(f"\nTRANSLATED POINTS: {len(translated_points)} total")
    print("-" * 80)

    if translated_points:
        # Show keys in first translated point
        first_point = translated_points[0]
        print("Translated point structure (keys in first point):")
        for key in sorted(first_point.keys()):
            print(f"  - {key}: {type(first_point[key]).__name__}")

        # Display all translated points with full details
        print("\nAll Translated Points:")
        for i, point in enumerate(translated_points):
            print(f"\nPoint {i}:")
            for key, value in sorted(point.items()):
                # Format position tuples for better readability
                if key in ("position", "original_position") and isinstance(value, tuple):
                    x, y, z = value
                    print(f"  {key}: ({x:.1f}, {y:.1f}, {z:.1f})")
                else:
                    print(f"  {key}: {value}")

    # Compare original and translated points in a table format
    print("\nOriginal vs Translated Positions:")
    print("-" * 80)
    print(f"{'#':^5} {'Original Position':^30} {'Translated Position':^30} {'Direction':^20}")
    print("-" * 80)

    for i, point in enumerate(translated_points):
        orig_pos = point.get("original_position", (0, 0, 0))
        pos = point.get("position", (0, 0, 0))
        direction = point.get("direction", (0, 0, 0))

        # Format position strings with proper rounding
        orig_pos_str = f"({orig_pos[0]:.1f}, {orig_pos[1]:.1f}, {orig_pos[2]:.1f})"
        pos_str = f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})"
        dir_str = str(direction)

        print(f"{i:^5} {orig_pos_str:^30} {pos_str:^30} {dir_str:^20}")

    # Pipeline completed successfully
    return True, "DXF pipeline completed successfully", translate_result


def main():
    """Main function to run the DXF pipeline test."""
    UIUtils.print_separator("DXF Processing Pipeline Test")

    # Get path to test data directory using cross-platform approach
    test_data_dir = scripts_dir / "Tests" / "TestData" / "DXF"
    # Verify path exists
    print(f"Looking for test files in: {test_data_dir}")
    if not test_data_dir.exists():
        print(f"WARNING: Test data directory not found: {test_data_dir}")
        # Try alternative path
        test_data_dir = Path(scripts_dir) / "TestData" / "DXF"
        print(f"Trying alternative path: {test_data_dir}")

    # Use UI utility to select a DXF file
    dxf_file = UIUtils.select_dxf_file(str(test_data_dir))

    if not dxf_file:
        print("No file selected. Using default: complex_case.dxf")
        dxf_file = test_data_dir / "complex_case.dxf"

    # Ensure the file exists
    dxf_path = Path(dxf_file)
    if not dxf_path.exists():
        print(f"ERROR: File not found: {dxf_file}")
        print("Available test files:")
        found_files = list(test_data_dir.glob("*.dxf"))
        if found_files:
            for i, path in enumerate(found_files, 1):
                print(f"  {i}. {path.name}")
            print("\nPlease select one of these files when you run the test again.")
        else:
            print("No .dxf files found in the test directory.")
        return

    # Process the DXF file through the pipeline
    success, message, result = process_dxf_file(dxf_file)

    # Print final result
    if success:
        UIUtils.print_separator("Pipeline Completed Successfully")
        print(f"\nSUCCESS: {message}")
        print("\nThe translated data is now ready for the ProcessingEngine")
    else:
        UIUtils.print_separator("Pipeline Failed")
        print(f"\nERROR: {message}")

    # Keep console open for viewing results
    UIUtils.keep_terminal_open()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {e!s}")
        import traceback

        traceback.print_exc()
        # Keep console open on error
        UIUtils.keep_terminal_open("An error occurred during processing.")
