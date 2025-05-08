#!/usr/bin/env python3
"""
Test script for analyzing workpiece orientation and point locations after rotation.

This script helps understand how point coordinates change after various rotations,
and how they relate to the workpiece orientation.
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from DXF.workpiece_rotator import WorkpieceRotator
from DXF.workpiece_positioner import create_positioner


class SimplePoint:
    """Simple class for a point with machine coordinates."""
    
    def __init__(self, id, machine_position, edge=None):
        self.id = id
        self.machine_position = machine_position
        self.edge = edge
    
    def __str__(self):
        return f"Point({self.id}): {self.machine_position} - {self.edge}"


def create_test_workpiece(width, height):
    """Create test points for a workpiece with given dimensions."""
    # Create corner points
    points = [
        SimplePoint("A", (0.0, 0.0, 0.0), "LEFT"),             # Bottom-left corner
        SimplePoint("B", (width, 0.0, 0.0), "RIGHT"),          # Bottom-right corner
        SimplePoint("C", (width, height, 0.0), "RIGHT"),       # Top-right corner
        SimplePoint("D", (0.0, height, 0.0), "LEFT"),          # Top-left corner
        SimplePoint("E", (width/2, height/2, 0.0), "INTERIOR") # Center point
    ]
    return points


def print_points_table(points, title):
    """Print a table of points with their coordinates."""
    print(f"\n--- {title} ---")
    print(f"{'ID':<5} | {'Edge':<8} | {'X':<8} | {'Y':<8} | {'Z':<8}")
    print("-" * 45)
    
    for point in points:
        x, y, z = point.machine_position
        print(f"{point.id:<5} | {point.edge:<8} | {x:<8.1f} | {y:<8.1f} | {z:<8.1f}")


def test_rotation_analysis():
    """Test to analyze point coordinates after rotation."""
    print("=== ROTATION ORIENTATION ANALYSIS ===")
    
    # Define workpiece dimensions
    width, height = 100.0, 200.0
    print(f"Workpiece dimensions: {width}x{height}mm")
    
    # Create a workpiece rotator
    rotator = WorkpieceRotator()
    rotator.set_dimensions(width, height, 20.0)
    
    # Create test points for the workpiece
    points = create_test_workpiece(width, height)
    
    # Print original points
    print_points_table(points, "Original Points (Origin = Bottom-Left)")
    print(f"Workpiece orientation: {rotator.get_orientation()}")
    
    # Rotate 90° and print points
    rotator.rotate_90_clockwise()
    rotator.rotate_points(points)
    print_points_table(points, "After 90° Rotation (Origin = Top-Left)")
    print(f"Workpiece orientation: {rotator.get_orientation()}")
    print(f"Point C (opposite to origin): {rotator.point_c}")
    
    # Rotate another 90° (180° total) and print points
    rotator.rotate_90_clockwise()
    rotator.rotate_points(points)
    print_points_table(points, "After 180° Rotation (Origin = Top-Right)")
    print(f"Workpiece orientation: {rotator.get_orientation()}")
    print(f"Point C (opposite to origin): {rotator.point_c}")
    
    # Rotate another 90° (270° total) and print points
    rotator.rotate_90_clockwise()
    rotator.rotate_points(points)
    print_points_table(points, "After 270° Rotation (Origin = Bottom-Right)")
    print(f"Workpiece orientation: {rotator.get_orientation()}")
    print(f"Point C (opposite to origin): {rotator.point_c}")
    
    # Test positioning after rotation
    print("\n=== POSITIONING AFTER ROTATION ===")
    
    # Create a new workpiece and rotator
    rotator = WorkpieceRotator()
    rotator.set_dimensions(width, height, 20.0)
    original_points = create_test_workpiece(width, height)
    
    # Apply 90° rotation
    rotator.rotate_90_clockwise()
    rotator.rotate_points(original_points)
    
    print_points_table(original_points, "After 90° Rotation (top-left)")
    print(f"Workpiece orientation: {rotator.get_orientation()}")
    
    # Position from top-left to bottom-left
    points_copy = [SimplePoint(p.id, p.machine_position, p.edge) for p in original_points]
    current_orientation = rotator.get_orientation()
    
    print("\nPositioning from top-left to bottom-left...")
    positioner = create_positioner("bottom-left", width, height, current_orientation)
    positioner.apply_offset(points_copy)
    
    print_points_table(points_copy, "After Positioning to Bottom-Left")
    
    # Position from top-left to top-right
    points_copy = [SimplePoint(p.id, p.machine_position, p.edge) for p in original_points]
    
    print("\nPositioning from top-left to top-right...")
    positioner = create_positioner("top-right", width, height, current_orientation)
    positioner.apply_offset(points_copy)
    
    print_points_table(points_copy, "After Positioning to Top-Right")
    
    # Analyze negative coordinates and interpretation
    print("\n=== ANALYSIS OF NEGATIVE COORDINATES ===")
    print("In machine coordinates after rotation:")
    print("1. Negative X: Point is to the left of the origin")
    print("2. Negative Y: Point is above the origin")
    print("3. For consistency with machine coordinates, we should:")
    print("   - Maintain (0,0) as the default origin point")
    print("   - Apply offsets to ensure all points have meaningful machine coordinates")
    print("   - Map orientation (top-left, bottom-right, etc.) to absolute machine positions")
    print("\nIn the top-left orientation after 90° rotation:")
    print("- X increases to the right, Y increases downward")
    print("- The workpiece extends into negative Y space")
    print("- This is consistent with a top-left coordinate system")


if __name__ == "__main__":
    try:
        test_rotation_analysis()
    except Exception as e:
        print(f"Error running test: {str(e)}")
        import traceback
        traceback.print_exc()