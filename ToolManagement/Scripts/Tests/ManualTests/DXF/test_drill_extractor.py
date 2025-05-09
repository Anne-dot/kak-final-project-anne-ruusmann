"""
Manual test for DrillPointExtractor functionality.

This script loads a test DXF file and runs the drill point extractor
to verify extraction works correctly.
"""

import os
import sys
from pathlib import Path

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import the modules
from DXF.parser import DXFParser
from DXF.extractor import DrillPointExtractor

# Test file paths
test_data_dir = Path(__file__).parent.parent.parent / "TestData" / "DXF"
test_file = test_data_dir / "Bottom_2_f0.dxf"  # Use one of your existing test files

def run_test():
    """Run drill point extraction test."""
    print("\nDrillPointExtractor Test")
    print("=" * 30)
    
    # Check if test file exists
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return
    
    print(f"Using test file: {test_file}")
    
    # Step 1: Parse the DXF file
    parser = DXFParser()
    success, message, result = parser.parse(test_file)
    
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
            print(f"{'#':<4} {'Position':<30} {'Diameter':<10} {'Depth':<10} {'Direction':<15} {'Layer':<30}")
            print("-" * 100)
            
            # Print each point as a row
            for i, point in enumerate(drill_points):
                pos = point.get("position", (0, 0, 0))
                pos_str = f"({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})"
                
                print(f"{i+1:<4} {pos_str:<30} "
                      f"{point.get('diameter', 0):.2f} mm  "
                      f"{point.get('depth', 0):.2f} mm  "
                      f"{str(point.get('direction', (0,0,0))):<15} "
                      f"{point.get('layer', ''):<30}")
            
            # Print total count
            print("-" * 100)
            print(f"Total drill points found: {len(drill_points)}")
        else:
            print("No drill points found.")
    else:
        print(f"Error: {message}")

if __name__ == "__main__":
    run_test()