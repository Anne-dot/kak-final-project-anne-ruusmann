"""
Manual test for the DXF Visual Coordinate Translator.

This test demonstrates the translation of drilling coordinates from DXF space 
to physical workpiece space for horizontal drilling operations.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import modules to test
from DXF.parser import DXFParser
from DXF.extractor import DXFExtractor, DrillPointExtractor, WorkpieceExtractor
from DXF.visual_coordinate_translator import VisualCoordinateTranslator


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50 + "\n")


def print_subheader(title: str) -> None:
    """Print a formatted subheader."""
    print("\n" + "-" * 50)
    print(title)
    print("-" * 50 + "\n")


def print_drill_points_table(drill_points: List[Dict]) -> None:
    """Print a formatted table of drill points."""
    # Print header
    print("{:<4} {:<30} {:<10} {:<10} {:<15} {:<30}".format(
        "#", "Position", "Diameter", "Depth", "Direction", "Layer"
    ))
    print("-" * 100)

    # Print each point
    for i, point in enumerate(drill_points, 1):
        position = point.get("position", (0, 0, 0))
        diameter = point.get("diameter", 0)
        depth = point.get("depth", 0)
        direction = point.get("direction", (0, 0, 0))
        layer = point.get("layer", "")

        position_str = "({:.2f}, {:.2f}, {:.2f})".format(*position)

        print("{:<4} {:<30} {:<10.2f} mm {:<10.2f} mm {:<15} {:<30}".format(
            i, position_str, diameter, depth, str(direction), layer
        ))

    print("-" * 100)
    print(f"Total drill points: {len(drill_points)}")


def print_direction_vector_diagnostics(drill_points: List[Dict]) -> None:
    """Print detailed diagnostic information about direction vectors."""
    print("\nDirection Vector Diagnostics:")
    print("-" * 50)
    print("{:<4} {:<15} {:<20} {:<40}".format(
        "#", "Direction", "Type", "Is Horizontal?"
    ))
    print("-" * 80)

    for i, point in enumerate(drill_points, 1):
        direction = point.get("direction", None)
        direction_type = type(direction).__name__

        # Check if it's a horizontal drilling vector
        is_x_direction = False
        is_y_direction = False

        # Extract vector components for analysis
        try:
            x, y, z = direction
            # Print detailed values to understand what's happening
            print(f"  Components: x={x} (type: {type(x)}), y={y}, z={z}")
            print(f"  Checks: abs(x)==1.0: {abs(x)==1.0}, y==0.0: {y==0.0}, z==0.0: {z==0.0}")

            is_x_direction = (abs(x) == 1.0 and y == 0.0 and z == 0.0)
            is_y_direction = (x == 0.0 and abs(y) == 1.0 and z == 0.0)
        except (TypeError, ValueError) as e:
            print(f"  Error unpacking direction: {str(e)}")

        if is_x_direction:
            horizontal_str = "Yes (X-direction)"
        elif is_y_direction:
            horizontal_str = "Yes (Y-direction)"
        else:
            horizontal_str = "No"

        print("{:<4} {:<15} {:<20} {:<40}".format(
            i, str(direction), direction_type, horizontal_str
        ))

    print("-" * 80)


def print_translated_points_table(original_points: List[Dict], translated_points: List[Dict]) -> None:
    """Print a formatted comparison table of original and translated points."""
    # Print header
    print("{:<4} {:<30} {:<30} {:<15}".format(
        "#", "Original Position", "Translated Position", "Direction"
    ))
    print("-" * 85)
    
    # Print each point pair
    for i, (orig, trans) in enumerate(zip(original_points, translated_points), 1):
        orig_pos = orig.get("position", (0, 0, 0))
        trans_pos = trans.get("position", (0, 0, 0))
        direction = orig.get("direction", (0, 0, 0))
        
        orig_pos_str = "({:.2f}, {:.2f}, {:.2f})".format(*orig_pos)
        trans_pos_str = "({:.2f}, {:.2f}, {:.2f})".format(*trans_pos)
        
        print("{:<4} {:<30} {:<30} {:<15}".format(
            i, orig_pos_str, trans_pos_str, str(direction)
        ))
    
    print("-" * 85)


def process_file(file_path: str) -> None:
    """Process a DXF file and demonstrate coordinate translation."""
    print_subheader(f"Processing file: {os.path.basename(file_path)}")
    
    # Parse the DXF file
    parser = DXFParser()
    parse_success, parse_message, parse_result = parser.parse(file_path)
    
    if not parse_success:
        print(f"ERROR: {parse_message}")
        return
    
    print(f"DXF parsing: {parse_message}")
    
    # Extract workpiece and drill points
    extractor = DXFExtractor()
    extract_success, extract_message, extract_result = extractor.process(parse_result["document"])
    
    if not extract_success:
        print(f"ERROR: {extract_message}")
        return
    
    print(f"DXF extraction: {extract_message}")
    
    # Get the extracted data
    workpiece = extract_result.get("workpiece", {})
    drill_points = extract_result.get("drill_points", [])
    
    # Print workpiece information
    print("\nWorkpiece Information:")
    print(f"Width: {workpiece.get('width', 0):.1f} mm")
    print(f"Height: {workpiece.get('height', 0):.1f} mm")
    print(f"Thickness: {workpiece.get('thickness', 0):.1f} mm")
    
    # Print original drill points
    print("\nOriginal Drill Points:")
    print_drill_points_table(drill_points)

    # Print diagnostic information about direction vectors
    print_direction_vector_diagnostics(drill_points)

    # Translate coordinates
    translator = VisualCoordinateTranslator()
    translate_success, translate_message, translate_result = translator.translate_coordinates(
        drill_points, workpiece
    )
    
    if not translate_success:
        print(f"ERROR: {translate_message}")
        return
    
    print(f"\nTranslation: {translate_message}")
    
    # Get translated points
    translated_points = translate_result.get("drill_points", [])
    
    # Print comparison of original and translated points
    print("\nCoordinate Translation Results:")
    print_translated_points_table(drill_points, translated_points)


def select_file() -> str:
    """Present a menu to select a test file."""
    # Get path to test DXF files
    test_data_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "../../TestData/DXF"
    ))
    
    # List available DXF files
    dxf_files = [f for f in os.listdir(test_data_dir) if f.endswith('.dxf')]
    dxf_files.sort()
    
    # Valid files for testing horizontal drilling
    valid_test_files = [
        "Bottom_2_f0.dxf",
        "Back_5_f0.dxf",
        "Left Side_3_f1.dxf",
        "Right Side_4_f0.dxf",
        "complex_case.dxf"
    ]
    
    # Filter to valid test files if they exist
    test_files = [f for f in dxf_files if f in valid_test_files]
    if not test_files:
        test_files = dxf_files
    
    # Print selection menu
    print("\nAvailable DXF test files:")
    for i, file_name in enumerate(test_files, 1):
        print(f"{i}. {file_name}")
    
    # Add option to test all files
    print(f"{len(test_files) + 1}. Test all available files")
    print("0. Exit")
    
    # Get user selection
    while True:
        try:
            choice = input("\nSelect an option: ")
            if choice == "0":
                return None
            
            option = int(choice)
            if option == len(test_files) + 1:
                return "ALL"
            elif 1 <= option <= len(test_files):
                return os.path.join(test_data_dir, test_files[option - 1])
            else:
                print("Invalid option. Please try again.")
        except ValueError:
            print("Invalid option. Please try again.")


def test_specific_file(file_path: str) -> None:
    """Test coordinate translation on a specific file."""
    process_file(file_path)


def test_all_files() -> None:
    """Test coordinate translation on all valid test files."""
    test_data_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "../../TestData/DXF"
    ))
    
    # Valid files for testing horizontal drilling
    valid_test_files = [
        "Bottom_2_f0.dxf",
        "Back_5_f0.dxf",
        "Left Side_3_f1.dxf",
        "Right Side_4_f0.dxf",
        "complex_case.dxf"
    ]
    
    # Test valid files
    print_subheader("Testing Valid DXF Files")
    for file_name in valid_test_files:
        file_path = os.path.join(test_data_dir, file_name)
        if os.path.exists(file_path):
            process_file(file_path)


def main() -> None:
    """Main test function."""
    print_header("Visual Coordinate Translator Test")
    
    while True:
        print("\nTest Options:")
        print("1. Select and test a specific file")
        print("2. Test all available files")
        print("0. Exit")
        
        choice = input("\nSelect an option: ")
        
        if choice == "0":
            break
        elif choice == "1":
            file_path = select_file()
            if file_path:
                if file_path == "ALL":
                    test_all_files()
                else:
                    test_specific_file(file_path)
        elif choice == "2":
            test_all_files()
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    # For automated diagnostics, run test on complex_case.dxf
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--diagnose":
        print_header("Running Automated Diagnostics")
        test_data_dir = Path(__file__).parent.parent.parent / "TestData" / "DXF"
        test_file = test_data_dir / "Bottom_2_f0.dxf"  # Test with X-direction drilling
        if test_file.exists():
            process_file(test_file)
        else:
            print(f"Test file not found: {test_file}")
    else:
        # Normal interactive mode
        main()