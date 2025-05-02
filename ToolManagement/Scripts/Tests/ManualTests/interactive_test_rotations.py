"""
Interactive test script for workpiece rotation experiments using OOP principles.

This script lets you:
1. Select a DXF file
2. View the original corner points
3. Rotate the workpiece 90° clockwise repeatedly
4. Reset to original position at any time

Usage:
    python rotation_test_oop.py
"""

import os
import sys
import platform

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import project modules
from DXF.file_loader import DxfLoader
from DXF.workpiece_extractor import WorkpieceExtractor
from Utils.ui_utils import UIUtils
from Utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Set up path to test data
test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "TestData")
dxf_dir = os.path.join(test_data_dir, "DXF")


class WorkpieceRotator:
    """Handles workpiece rotation operations."""
    
    def __init__(self, original_corners):
        """
        Initialize the workpiece rotator.
        
        Args:
            original_corners: Dictionary of original corner points
        """
        self.original_corners = original_corners
        self.current_corners = original_corners.copy()
        self.rotation_count = 0
    
    def rotate_90_clockwise(self):
        """
        Rotate the workpiece 90 degrees clockwise.
        
        Returns:
            Dictionary of rotated corner points
        """
        rotated_corners = {}
        for key, point in self.current_corners.items():
            # Apply rotation formula (x,y) -> (y,-x)
            x, y = point
            rotated_corners[key] = (y, -x)
        
        self.current_corners = rotated_corners
        self.rotation_count += 1
        return self.current_corners
    
    def reset_to_original(self):
        """
        Reset to original position.
        
        Returns:
            Dictionary of original corner points
        """
        self.current_corners = self.original_corners.copy()
        self.rotation_count = 0
        return self.current_corners
    
    def get_rotation_angle(self):
        """
        Get the current rotation angle in degrees.
        
        Returns:
            Rotation angle (0°, 90°, 180°, 270°)
        """
        return (self.rotation_count % 4) * 90
    
    def get_orientation(self):
        """
        Determine workpiece orientation based on point C coordinates.
        
        Returns:
            String indicating orientation
        """
        x_c, y_c = self.current_corners['corner_point_c']
        
        if x_c > 0 and y_c > 0:
            return "Bottom-Left"
        elif x_c > 0 and y_c < 0:
            return "Top-Left"
        elif x_c < 0 and y_c < 0:
            return "Top-Right"
        elif x_c < 0 and y_c > 0:
            return "Bottom-Right"
        else:
            return "Unknown orientation"
    
    def calculate_dimensions(self):
        """
        Calculate workpiece dimensions based on corner coordinates.
        
        Returns:
            Tuple of (width, height)
        """
        # Get all coordinates
        x_values = [abs(point[0]) for point in self.current_corners.values()]
        y_values = [abs(point[1]) for point in self.current_corners.values()]
        
        # Width and height are the maximum values
        width = max(x_values)
        height = max(y_values)
        
        return width, height


class WorkpieceDisplay:
    """Handles display of workpiece information."""
    
    @staticmethod
    def format_point(point):
        """
        Format coordinate point for display.
        
        Args:
            point: (x, y) coordinate tuple
            
        Returns:
            Formatted string representation
        """
        return f"({point[0]:.1f}, {point[1]:.1f})"
    
    @staticmethod
    def display_corners(rotator):
        """
        Display corner points in a readable format.
        
        Args:
            rotator: WorkpieceRotator instance
        """
        corners = rotator.current_corners
        rotation_count = rotator.rotation_count
        rotation_angle = rotator.get_rotation_angle()
        orientation = rotator.get_orientation()
        width, height = rotator.calculate_dimensions()
        
        print(f"\n=== Corner Points (Rotation #{rotation_count} - {rotation_angle}°) ===")
        print(f"Reference corner: Corner A {WorkpieceDisplay.format_point(corners['corner_point_a'])}")
        print(f"Workpiece orientation: {orientation}")
        print(f"Corner A: {WorkpieceDisplay.format_point(corners['corner_point_a'])}")
        print(f"Corner B: {WorkpieceDisplay.format_point(corners['corner_point_b'])}")
        print(f"Corner C: {WorkpieceDisplay.format_point(corners['corner_point_c'])}")
        print(f"Corner D: {WorkpieceDisplay.format_point(corners['corner_point_d'])}")
        print(f"\nCurrent dimensions: {width:.1f} x {height:.1f}")
    
    @staticmethod
    def display_workpiece_info(dimensions):
        """
        Display original workpiece information.
        
        Args:
            dimensions: Dictionary of workpiece dimensions
        """
        print("\n=== Original Workpiece Information ===")
        print(f"Width: {dimensions.get('width', 0):.1f}mm")
        print(f"Height: {dimensions.get('height', 0):.1f}mm")
        print(f"Thickness: {dimensions.get('depth', 0):.1f}mm")


def run_interactive_test(dxf_file_path=None):
    """
    Run an interactive test for workpiece rotation.
    
    Args:
        dxf_file_path: Path to DXF file (if None, will prompt for selection)
    """
    print(f"\n=== Workpiece Rotation Test ===")
    print(f"Running on {platform.system()} platform")
    
    # Let user select a DXF file if not provided
    if dxf_file_path is None:
        dxf_file_path = UIUtils.select_dxf_file(dxf_dir)
        if not dxf_file_path:
            print("No DXF file selected. Exiting.")
            return
    
    print(f"Using DXF file: {os.path.basename(dxf_file_path)}")
    
    # Load DXF file
    loader = DxfLoader()
    success, doc, message = loader.load_dxf(dxf_file_path)
    if not success:
        print(f"Error loading DXF: {message}")
        return
    
    # Extract workpiece info
    workpiece_extractor = WorkpieceExtractor()
    success, workpiece_info, message = workpiece_extractor.extract_workpiece_info(doc)
    if not success:
        print(f"Error extracting workpiece info: {message}")
        return
    
    # Get corner points
    reference_points = workpiece_info.get('reference_points', {})
    dimensions = workpiece_info.get('dimensions', {})
    
    # Extract corner points with neutral names
    original_corners = {
        'corner_point_a': reference_points.get('corner_bl', (0, 0)),
        'corner_point_b': reference_points.get('corner_br', (100, 0)),
        'corner_point_c': reference_points.get('corner_tr', (100, 100)),
        'corner_point_d': reference_points.get('corner_tl', (0, 100))
    }
    
    # Create rotator
    rotator = WorkpieceRotator(original_corners)
    
    # Display original workpiece info
    WorkpieceDisplay.display_workpiece_info(dimensions)
    WorkpieceDisplay.display_corners(rotator)
    
    # Interactive rotation loop
    while True:
        print("\n=== Options ===")
        print("1. Rotate 90° clockwise")
        print("2. Reset to original position")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            # Rotate 90 degrees clockwise
            rotator.rotate_90_clockwise()
            WorkpieceDisplay.display_corners(rotator)
            
        elif choice == "2":
            # Reset to original position
            rotator.reset_to_original()
            WorkpieceDisplay.display_corners(rotator)
            
        elif choice == "3":
            # Exit the program
            print("\nExiting...")
            break
            
        else:
            print("\nInvalid choice, please try again.")


if __name__ == "__main__":
    run_interactive_test()