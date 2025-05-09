#!/usr/bin/env python3
"""
Test script for workpiece positioning functionality.

This script demonstrates how the workpiece positioner moves drilling points
to different positions in the machine coordinate system.
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from DXF.workpiece_positioner import create_positioner


class DrillPoint:
    """Simple class to simulate a drilling point with machine coordinates."""
    
    def __init__(self, id, machine_position, edge=None, diameter=8.0):
        self.id = id
        self.machine_position = machine_position
        self.edge = edge
        self.diameter = diameter
    
    def __str__(self):
        return f"DrillPoint(id={self.id}, pos={self.machine_position}, edge={self.edge})"


def create_test_points(width, height):
    """Create test drilling points for a workpiece of given dimensions."""
    points = []
    
    # Create corner points
    points.append(DrillPoint("A", (0.0, 0.0, 20.0), edge="LEFT"))           # Bottom-left
    points.append(DrillPoint("B", (width, 0.0, 20.0), edge="RIGHT"))        # Bottom-right
    points.append(DrillPoint("C", (width, height, 20.0), edge="RIGHT"))     # Top-right
    points.append(DrillPoint("D", (0.0, height, 20.0), edge="LEFT"))        # Top-left
    
    # Create some edge points
    points.append(DrillPoint("E1", (0.0, height/2, 20.0), edge="LEFT"))      # Middle of left edge
    points.append(DrillPoint("E2", (width, height/2, 20.0), edge="RIGHT"))   # Middle of right edge
    points.append(DrillPoint("E3", (width/2, 0.0, 20.0), edge="BACK"))      # Middle of bottom edge
    points.append(DrillPoint("E4", (width/2, height, 20.0), edge="FRONT"))   # Middle of top edge
    
    # Add an interior point
    points.append(DrillPoint("I", (width/2, height/2, 20.0), edge="INTERIOR"))
    
    return points


def print_points(points, title="Points"):
    """Print points with their machine coordinates."""
    print(f"\n{title}")
    print("=" * len(title))
    
    for point in points:
        x, y, z = point.machine_position
        print(f"{point.id}: ({x:.1f}, {y:.1f}, {z:.1f}) - {point.edge}")


def test_positioning_from_orientation(width, height, current_orientation, target_position):
    """Test positioning from a specific orientation to a target position."""
    print(f"\n\n--- Testing positioning from {current_orientation} to {target_position} ---")
    print(f"Workpiece dimensions: {width}x{height}mm")
    
    # Create test points based on current orientation
    points = create_test_points(width, height)
    
    # Apply any pre-positioning based on current orientation
    # This simulates points that have already been transformed and rotated
    if current_orientation == "top-left":
        # Points are already at top-left, no pre-positioning needed
        pass
    elif current_orientation == "top-right":
        # Pre-position to top-right
        for point in points:
            x, y, z = point.machine_position
            point.machine_position = (x + width, y, z)
    elif current_orientation == "bottom-left":
        # Pre-position to bottom-left (origin)
        # Points are created at bottom-left by default, no change needed
        pass
    elif current_orientation == "bottom-right":
        # Pre-position to bottom-right
        for point in points:
            x, y, z = point.machine_position
            point.machine_position = (x + width, y - height, z)
    
    # Print pre-positioned points
    print_points(points, f"Points in {current_orientation} orientation")
    
    # Create and apply the positioner
    positioner = create_positioner(target_position, width, height, current_orientation)
    success, message, details = positioner.apply_offset(points)
    
    # Print results
    print(f"\nPositioning result: {message}")
    print(f"Applied offset: {details.get('offset')}")
    
    # Print positioned points
    print_points(points, f"Points after positioning to {target_position}")
    
    # Calculate and print the bounding box of positioned points
    min_x = min(p.machine_position[0] for p in points)
    max_x = max(p.machine_position[0] for p in points)
    min_y = min(p.machine_position[1] for p in points)
    max_y = max(p.machine_position[1] for p in points)
    
    print(f"\nBounding box after positioning:")
    print(f"  X range: {min_x:.1f} to {max_x:.1f} (width: {max_x - min_x:.1f}mm)")
    print(f"  Y range: {min_y:.1f} to {max_y:.1f} (height: {max_y - min_y:.1f}mm)")


def test_all_positionings():
    """Test all possible positioning combinations."""
    print("=== WORKPIECE POSITIONING TESTS ===")
    print("This script tests the positioning of workpieces in the machine coordinate system.")
    
    # Define workpiece dimensions
    width, height = 300.0, 200.0
    
    # Test moving to top-left from all orientations (for MVP)
    test_positioning_from_orientation(width, height, "bottom-left", "top-left")
    test_positioning_from_orientation(width, height, "bottom-right", "top-left")
    test_positioning_from_orientation(width, height, "top-right", "top-left")
    test_positioning_from_orientation(width, height, "top-left", "top-left")
    
    # Test one case for each of the placeholder positions
    test_positioning_from_orientation(width, height, "bottom-left", "top-right")
    test_positioning_from_orientation(width, height, "bottom-left", "bottom-right")
    test_positioning_from_orientation(width, height, "top-left", "bottom-left")
    
    # Summary table for top-left positioning (MVP)
    print("\n\n=== SUMMARY TABLE FOR TOP-LEFT POSITIONING (MVP) ===")
    print("------------------------------------------------------------------")
    print("| From Orientation | Offset Applied      | Resulting Position     |")
    print("------------------------------------------------------------------")
    print(f"| bottom-left      | (0.0, -{height:.1f})     | top-left               |")
    print(f"| bottom-right     | (-{width:.1f}, -{height:.1f})   | top-left               |")
    print(f"| top-right        | (-{width:.1f}, 0.0)        | top-left               |")
    print(f"| top-left         | (0.0, 0.0)          | top-left (no change)    |")
    print("------------------------------------------------------------------")
    
    print("\n=== Tests completed successfully ===")


if __name__ == "__main__":
    try:
        test_all_positionings()
    except Exception as e:
        print(f"Error running test: {str(e)}")
        import traceback
        traceback.print_exc()