"""
Test for WorkpieceExtractor functionality.

This script tests the WorkpieceExtractor with all available DXF files from the test data
directory and verifies extraction of corner points and thickness information.
Includes a file selector to choose specific files to test.
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
from DXF.parser import DXFParser
from DXF.extractor import WorkpieceExtractor
from Utils.ui_utils import UIUtils

def process_file(file_path):
    """Test workpiece extraction on a specific file."""
    print(f"\nProcessing file: {file_path.name}")
    print("-" * 50)
    
    if not file_path.exists():
        print(f"File not found, skipping")
        return
    
    # Step 1: Parse the DXF file
    parser = DXFParser()
    success, message, result = parser.parse(file_path)
    
    if not success:
        print(f"Failed to parse DXF file: {message}")
        return
    
    print(f"DXF parsing: {message}")
    
    # Step 2: Extract workpiece
    document = result["document"]
    extractor = WorkpieceExtractor()
    success, message, extract_result = extractor.extract(document)
    
    # Step 3: Display results
    print(f"Workpiece extraction: {message}")
    
    if success:
        workpiece = extract_result.get("workpiece")
        if workpiece:
            print("\nWorkpiece Data:")
            print(f"{'Dimensions':<15}: {workpiece['width']:.2f} x {workpiece['height']:.2f} x {workpiece['thickness']:.2f} mm")
            print(f"{'Layer':<15}: {workpiece['layer']}")
            print(f"{'Entity Type':<15}: {workpiece['entity_type']}")
            print(f"{'Corner Points':<15}: {len(workpiece['corner_points'])}")
            
            # Print ALL corner points
            print("\nCorner Points:")
            for i, point in enumerate(workpiece['corner_points']):
                print(f"  {i+1}: ({point[0]:.2f}, {point[1]:.2f}, {point[2]:.2f})")
        else:
            print("No workpiece data returned")
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
    
    # Test all available files
    test_files = [
        test_data_dir / "Bottom_2_f0.dxf",
        test_data_dir / "Back_5_f0.dxf",
        test_data_dir / "Left Side_3_f1.dxf",
        test_data_dir / "Right Side_4_f0.dxf",
        test_data_dir / "complex_case.dxf"
    ]
    
    # Test files expected to fail
    fail_files = [
        test_data_dir / "empty.dxf",
        test_data_dir / "invalid_test.dxf"
    ]
    
    print("\n--- Testing Valid DXF Files ---")
    for file_path in test_files:
        process_file(file_path)
    
    print("\n--- Testing Invalid DXF Files ---")
    for file_path in fail_files:
        process_file(file_path)

def test_missing_thickness_case():
    """Test case with missing thickness in layer name."""
    print("\nTesting case with missing thickness")
    print("-" * 50)
    
    # Create a test file with missing thickness info
    try:
        # Create a new DXF file
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        
        # Add a polyline without thickness info in layer name
        points = [(0, 0), (500, 0), (500, 400), (0, 400), (0, 0)]
        msp.add_lwpolyline(points, dxfattribs={"layer": "OUTLINE_MISSING_THICKNESS"})
        
        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
        doc.saveas(temp_file.name)
        print(f"Created test file: {temp_file.name}")
        
        # Parse and extract
        parser = DXFParser()
        success, message, result = parser.parse(temp_file.name)
        
        if success:
            document = result["document"]
            extractor = WorkpieceExtractor()
            success, message, extract_result = extractor.extract(document)
            
            # Should fail due to missing thickness
            if not success:
                print(f"Test PASSED: Correctly failed: {message}")
            else:
                print(f"Test FAILED: Unexpectedly succeeded when thickness is missing")
        else:
            print(f"Failed to parse test file: {message}")
        
        # Clean up
        try:
            os.unlink(temp_file.name)
        except:
            pass
        
    except Exception as e:
        print(f"Error creating test file: {str(e)}")

def run_test():
    """Run workpiece extraction test with menu options."""
    print("\nWorkpieceExtractor Test")
    print("=" * 50)
    
    while True:
        print("\nTest Options:")
        print("1. Select and test a specific file")
        print("2. Test all available files")
        print("3. Test case with missing thickness")
        print("4. Run all tests")
        print("0. Exit")
        
        choice = input("\nSelect an option: ")
        
        if choice == "1":
            test_with_selector()
        elif choice == "2":
            test_all_files()
        elif choice == "3":
            test_missing_thickness_case()
        elif choice == "4":
            test_all_files()
            test_missing_thickness_case()
        elif choice == "0":
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    run_test()