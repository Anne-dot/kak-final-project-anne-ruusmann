#!/usr/bin/env python3
"""
Test script for edge reclassification with tabular output.

This script displays original and rotated edges side-by-side in a table format
for easier comparison of how edge designations change during rotation.
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from DXF.workpiece_rotator import WorkpieceRotator


class DrillPoint:
    """Simple class to simulate a drilling point with direction vector."""
    
    def __init__(self, id, position, edge, extrusion_vector, diameter=8.0):
        self.id = id
        self.position = position
        self.edge = edge
        self.extrusion_vector = extrusion_vector
        self.diameter = diameter
        self.machine_position = None
        # Store original values for comparison
        self.original_edge = edge
        self.original_extrusion = extrusion_vector


def create_test_points():
    """Create test drilling points with edge and extrusion vector information."""
    points = []
    
    # Create points for LEFT edge (extrusion vector points along -X axis)
    points.append(DrillPoint("L1", (-10, 5, -500), "LEFT", (-1, 0, 0)))
    points.append(DrillPoint("L2", (-10, 50, -500), "LEFT", (-1, 0, 0)))
    
    # Create points for RIGHT edge (extrusion vector points along +X axis)
    points.append(DrillPoint("R1", (10, 5, 0), "RIGHT", (1, 0, 0)))
    points.append(DrillPoint("R2", (10, 50, 0), "RIGHT", (1, 0, 0)))
    
    # Create points for FRONT edge (extrusion vector points along +Y axis)
    points.append(DrillPoint("F1", (100, 10, 0), "FRONT", (0, 1, 0)))
    points.append(DrillPoint("F2", (300, 10, 0), "FRONT", (0, 1, 0)))
    
    # Create points for BACK edge (extrusion vector points along -Y axis)
    points.append(DrillPoint("B1", (100, -10, -600), "BACK", (0, -1, 0)))
    points.append(DrillPoint("B2", (300, -10, -600), "BACK", (0, -1, 0)))
    
    # Create a VERTICAL point for completeness
    points.append(DrillPoint("V1", (200, 200, 0), "VERTICAL", (0, 0, 1)))
    
    return points


def assign_machine_coordinates(points, width, height):
    """Assign mock machine coordinates to the drilling points."""
    for point in points:
        if point.edge == "LEFT":
            point.machine_position = (0.0, height - point.position[1], 20.0)
        elif point.edge == "RIGHT":
            point.machine_position = (width, height - point.position[1], 20.0)
        elif point.edge == "FRONT":
            point.machine_position = (width - point.position[0], height, 20.0)
        elif point.edge == "BACK":
            point.machine_position = (width - point.position[0], 0.0, 20.0)
        elif point.edge == "VERTICAL":
            point.machine_position = (point.position[0], point.position[1], 0.0)
    
    return points


def format_edge_tables(original_points, points_90, points_180, points_270):
    """Format the points into side-by-side tables for comparison."""
    
    # Format header
    header = f"{'ID':<5} | {'ORIG':<8} | {'90°':<8} | {'180°':<8} | {'270°':<8}"
    separator = "-" * len(header)
    
    print("\n=== EDGE TRANSITION TABLE ===")
    print(separator)
    print(header)
    print(separator)
    
    # Format rows
    for i, orig_point in enumerate(original_points):
        id = orig_point.id
        edge_orig = orig_point.edge
        edge_90 = points_90[i].edge if i < len(points_90) else "N/A"
        edge_180 = points_180[i].edge if i < len(points_180) else "N/A"
        edge_270 = points_270[i].edge if i < len(points_270) else "N/A"
        
        row = f"{id:<5} | {edge_orig:<8} | {edge_90:<8} | {edge_180:<8} | {edge_270:<8}"
        print(row)
    
    print(separator)
    print()


def format_extrusion_tables(original_points, points_90, points_180, points_270):
    """Format the extrusion vectors into side-by-side tables for comparison."""
    
    # Format header
    header = f"{'ID':<5} | {'ORIG':<12} | {'90°':<12} | {'180°':<12} | {'270°':<12}"
    separator = "-" * len(header)
    
    print("\n=== EXTRUSION VECTOR TABLE ===")
    print(separator)
    print(header)
    print(separator)
    
    # Format rows
    for i, orig_point in enumerate(original_points):
        id = orig_point.id
        extr_orig = f"({orig_point.original_extrusion[0]}, {orig_point.original_extrusion[1]})"
        
        if i < len(points_90):
            extr_90 = f"({points_90[i].extrusion_vector[0]}, {points_90[i].extrusion_vector[1]})"
        else:
            extr_90 = "N/A"
            
        if i < len(points_180):
            extr_180 = f"({points_180[i].extrusion_vector[0]}, {points_180[i].extrusion_vector[1]})"
        else:
            extr_180 = "N/A"
            
        if i < len(points_270):
            extr_270 = f"({points_270[i].extrusion_vector[0]}, {points_270[i].extrusion_vector[1]})"
        else:
            extr_270 = "N/A"
        
        row = f"{id:<5} | {extr_orig:<12} | {extr_90:<12} | {extr_180:<12} | {extr_270:<12}"
        print(row)
    
    print(separator)
    print()


def format_coordinate_tables(original_points, points_90, points_180, points_270):
    """Format the machine coordinates into side-by-side tables for comparison."""
    
    # Format header
    header = f"{'ID':<5} | {'ORIG':<20} | {'90°':<20} | {'180°':<20} | {'270°':<20}"
    separator = "-" * len(header)
    
    print("\n=== MACHINE COORDINATE TABLE ===")
    print(separator)
    print(header)
    print(separator)
    
    # Format rows
    for i, orig_point in enumerate(original_points):
        id = orig_point.id
        
        if orig_point.machine_position:
            x, y, z = orig_point.machine_position
            coord_orig = f"({x:.1f}, {y:.1f}, {z:.1f})"
        else:
            coord_orig = "None"
        
        if i < len(points_90) and points_90[i].machine_position:
            x, y, z = points_90[i].machine_position
            coord_90 = f"({x:.1f}, {y:.1f}, {z:.1f})"
        else:
            coord_90 = "N/A"
            
        if i < len(points_180) and points_180[i].machine_position:
            x, y, z = points_180[i].machine_position
            coord_180 = f"({x:.1f}, {y:.1f}, {z:.1f})"
        else:
            coord_180 = "N/A"
            
        if i < len(points_270) and points_270[i].machine_position:
            x, y, z = points_270[i].machine_position
            coord_270 = f"({x:.1f}, {y:.1f}, {z:.1f})"
        else:
            coord_270 = "N/A"
        
        row = f"{id:<5} | {coord_orig:<20} | {coord_90:<20} | {coord_180:<20} | {coord_270:<20}"
        print(row)
    
    print(separator)
    print()


def test_all_rotations():
    """Test all rotation angles and display results in tabular format."""
    print("=== EDGE ROTATION TABULAR COMPARISON ===")
    print("This test shows edge transitions across different rotation angles.")
    
    # Create a workpiece rotator with known dimensions
    width, height, thickness = 600.0, 700.0, 20.0
    
    # Create test points to use for all rotations
    original_points = create_test_points()
    original_points = assign_machine_coordinates(original_points, width, height)
    
    # Create points for 90° rotation
    points_90 = create_test_points()
    points_90 = assign_machine_coordinates(points_90, width, height)
    rotator_90 = WorkpieceRotator()
    rotator_90.set_dimensions(width, height, thickness)
    rotator_90.rotate_90_clockwise()
    rotator_90.rotate_points(points_90, update_edges=True)
    
    # Create points for 180° rotation
    points_180 = create_test_points()
    points_180 = assign_machine_coordinates(points_180, width, height)
    rotator_180 = WorkpieceRotator()
    rotator_180.set_dimensions(width, height, thickness)
    rotator_180.rotate_90_clockwise()
    rotator_180.rotate_90_clockwise()
    rotator_180.rotate_points(points_180, update_edges=True)
    
    # Create points for 270° rotation
    points_270 = create_test_points()
    points_270 = assign_machine_coordinates(points_270, width, height)
    rotator_270 = WorkpieceRotator()
    rotator_270.set_dimensions(width, height, thickness)
    rotator_270.rotate_90_clockwise()
    rotator_270.rotate_90_clockwise()
    rotator_270.rotate_90_clockwise()
    rotator_270.rotate_points(points_270, update_edges=True)
    
    # Print workpiece dimensions and point C information after each rotation
    print("\n=== WORKPIECE AND POINT C INFORMATION ===")
    original_rotator = WorkpieceRotator()
    original_rotator.set_dimensions(width, height, thickness)
    print(f"Original:     {width} x {height} mm   |  Point C: ({width}, {height})  |  Orientation: bottom-left")
    print(f"90° Rotation:  {rotator_90.current_width} x {rotator_90.current_height} mm  |  Point C: {rotator_90.point_c}  |  Orientation: {rotator_90.get_orientation()}")
    print(f"180° Rotation: {rotator_180.current_width} x {rotator_180.current_height} mm  |  Point C: {rotator_180.point_c}  |  Orientation: {rotator_180.get_orientation()}")
    print(f"270° Rotation: {rotator_270.current_width} x {rotator_270.current_height} mm  |  Point C: {rotator_270.point_c}  |  Orientation: {rotator_270.get_orientation()}")
    
    # Display results in tabular format
    format_edge_tables(original_points, points_90, points_180, points_270)
    format_extrusion_tables(original_points, points_90, points_180, points_270)
    format_coordinate_tables(original_points, points_90, points_180, points_270)
    
    # Display summary of edge transitions
    print("\n=== EDGE TRANSITION SUMMARY ===")
    print("90° Rotation:  LEFT→FRONT, RIGHT→BACK, FRONT→RIGHT, BACK→LEFT")
    print("180° Rotation: LEFT→RIGHT, RIGHT→LEFT, FRONT→BACK, BACK→FRONT")
    print("270° Rotation: LEFT→BACK, RIGHT→FRONT, FRONT→LEFT, BACK→RIGHT")
    print("VERTICAL edge remains VERTICAL in all rotations")
    
    # Show coordinate transition patterns
    print("\n=== COORDINATE TRANSFORMATION PATTERNS ===")
    print("For a point (x,y,z):")
    print("90° rotation:  (x,y,z) → (y,-x,z)")
    print("180° rotation: (x,y,z) → (-x,-y,z)")
    print("270° rotation: (x,y,z) → (-y,x,z)")
    
    # Point C transition summary
    print("\n=== POINT C AND ORIENTATION SUMMARY ===")
    print("---------------------------------------------------------")
    print("| Rotation | Point C            | Orientation  |")
    print("---------------------------------------------------------")
    print(f"| 0°       | ({width}, {height})    | bottom-left  |")
    print(f"| 90°      | ({height}, -{width})   | top-left     |")
    print(f"| 180°     | (-{width}, -{height})  | top-right    |")
    print(f"| 270°     | (-{height}, {width})   | bottom-right |")
    print("---------------------------------------------------------")
    
    print("\n=== Test completed successfully ===")


if __name__ == "__main__":
    try:
        test_all_rotations()
    except Exception as e:
        print(f"Error running test: {str(e)}")
        import traceback
        traceback.print_exc()