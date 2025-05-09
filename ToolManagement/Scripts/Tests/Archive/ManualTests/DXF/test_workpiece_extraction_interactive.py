#!/usr/bin/env python3
"""
Interactive test for workpiece extraction functionality.

This test script:
1. Allows selection of a DXF file using terminal UI
2. Extracts complete workpiece information
3. Displays detailed geometry data for horizontal drilling
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import modules
from DXF.file_loader import DxfLoader
from DXF.workpiece_extractor import WorkpieceExtractor
from Utils.ui_utils import UIUtils
from Utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Set up path to test data
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_dir = os.path.join(test_data_dir, "DXF")

def display_workpiece_info(workpiece_info):
    """Display complete workpiece information in an organized format."""
    UIUtils.print_separator("WORKPIECE INFORMATION")
    
    # Dimensions section
    print("\n[DIMENSIONS]")
    dimensions = workpiece_info['dimensions']
    print(f"  Width:  {dimensions['width']:.2f} mm")
    print(f"  Height: {dimensions['height']:.2f} mm")
    print(f"  Depth:  {dimensions['depth']:.2f} mm")
    print(f"  Bounding Box: ({dimensions['min_x']:.2f}, {dimensions['min_y']:.2f}) to ({dimensions['max_x']:.2f}, {dimensions['max_y']:.2f})")
    
    # Material info
    print("\n[MATERIAL]")
    print(f"  Thickness: {workpiece_info['material_thickness']:.2f} mm")
    
    # Orientation info
    print("\n[ORIENTATION]")
    orientation = workpiece_info['orientation']
    print(f"  Aligned with origin: {'YES' if orientation['origin_aligned'] else 'NO'}")
    print(f"  Aligned with axes:   {'YES' if orientation['axis_aligned'] else 'NO'}")
    print(f"  Angle to X-axis:     {orientation['angle_to_x_axis']:.2f} degrees")
    print(f"  Offset from origin:  ({orientation['origin_offset_x']:.2f}, {orientation['origin_offset_y']:.2f})")
    
    # Reference points
    print("\n[REFERENCE POINTS]")
    points = workpiece_info['reference_points']
    for point_name, coordinates in points.items():
        print(f"  {point_name.ljust(25)}: ({coordinates[0]:.2f}, {coordinates[1]:.2f})")
    
    # Additional info
    print("\n[ADDITIONAL INFO]")
    print(f"  Boundary count: {workpiece_info['boundary_count']}")

def main():
    """Run the interactive workpiece extraction test."""
    print("=== Workpiece Extraction Interactive Test ===")
    print("This test extracts workpiece geometry from a DXF file\n")
    
    # Initialize objects
    loader = DxfLoader()
    extractor = WorkpieceExtractor()
    
    # Let user select a DXF file
    print(f"Looking for DXF files in: {dxf_dir}")
    dxf_file_path = UIUtils.select_dxf_file(dxf_dir)
    if not dxf_file_path:
        print("No DXF file selected. Exiting.")
        UIUtils.keep_terminal_open("Test aborted - no file selected.")
        sys.exit(1)
    
    print(f"\nSelected DXF file: {os.path.basename(dxf_file_path)}")
    
    # Step 1: Load the DXF file
    print("\nStep 1: Loading DXF file...")
    success, message, details = loader.load_dxf(dxf_file_path)
    
    if not success:
        print(f"Error loading DXF: {message}")
        UIUtils.keep_terminal_open("Test failed at DXF loading stage.")
        sys.exit(1)
    
    print(f"SUCCESS: DXF loaded successfully")
    dxf_doc = details.get('document')
    
    # Step 2: Extract workpiece information
    print("\nStep 2: Extracting workpiece information...")
    success, message, workpiece_info = extractor.extract_workpiece_info(dxf_doc)
    
    if not success:
        print(f"Error extracting workpiece info: {message}")
        UIUtils.keep_terminal_open("Test failed at workpiece extraction stage.")
        sys.exit(1)
    
    print(f"SUCCESS: Workpiece information extracted successfully")
    
    # Step 3: Display workpiece information
    display_workpiece_info(workpiece_info)
    
    # Keep the terminal open until user presses Enter
    UIUtils.keep_terminal_open("Workpiece extraction test completed successfully.")

if __name__ == "__main__":
    main()