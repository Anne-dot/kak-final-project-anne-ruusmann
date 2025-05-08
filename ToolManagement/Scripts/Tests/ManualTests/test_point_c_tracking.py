#!/usr/bin/env python3
"""
Test script for point C tracking during workpiece rotation.

This script demonstrates how point C is used to determine the workpiece orientation
after rotation.
"""

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from DXF.workpiece_rotator import WorkpieceRotator

def test_point_c_tracking():
    """Test how point C coordinates change during rotation and determine orientation."""
    print("=== POINT C TRACKING DURING ROTATION ===")
    
    # Create a workpiece rotator with known dimensions
    rotator = WorkpieceRotator()
    width, height = 300.0, 500.0
    thickness = 20.0
    
    print(f"Setting up workpiece: {width}x{height}x{thickness}mm")
    success, message, details = rotator.set_dimensions(width, height, thickness)
    
    # Print initial state
    point_c = details.get('point_c', (0, 0))
    orientation = details.get('orientation', 'unknown')
    
    print("\nINITIAL STATE:")
    print(f"  Dimensions: {width} x {height}mm")
    print(f"  Point C: {point_c}")
    print(f"  Orientation: {orientation}")
    
    # Apply 90° rotation
    print("\nApplying 90° rotation...")
    success, message, details = rotator.rotate_90_clockwise()
    
    # Print state after 90° rotation
    point_c = details.get('point_c', (0, 0))
    orientation = details.get('orientation', 'unknown')
    angle = details.get('rotation_angle', 0)
    dimensions = f"{details.get('width', 0)} x {details.get('height', 0)}mm"
    
    print("\nAFTER 90° ROTATION:")
    print(f"  Dimensions: {dimensions}")
    print(f"  Point C: {point_c}")
    print(f"  Orientation: {orientation}")
    print(f"  Rotation Angle: {angle}°")
    
    # Apply 90° rotation (180° total)
    print("\nApplying second 90° rotation (180° total)...")
    success, message, details = rotator.rotate_90_clockwise()
    
    # Print state after 180° rotation
    point_c = details.get('point_c', (0, 0))
    orientation = details.get('orientation', 'unknown')
    angle = details.get('rotation_angle', 0)
    dimensions = f"{details.get('width', 0)} x {details.get('height', 0)}mm"
    
    print("\nAFTER 180° ROTATION:")
    print(f"  Dimensions: {dimensions}")
    print(f"  Point C: {point_c}")
    print(f"  Orientation: {orientation}")
    print(f"  Rotation Angle: {angle}°")
    
    # Apply 90° rotation (270° total)
    print("\nApplying third 90° rotation (270° total)...")
    success, message, details = rotator.rotate_90_clockwise()
    
    # Print state after 270° rotation
    point_c = details.get('point_c', (0, 0))
    orientation = details.get('orientation', 'unknown')
    angle = details.get('rotation_angle', 0)
    dimensions = f"{details.get('width', 0)} x {details.get('height', 0)}mm"
    
    print("\nAFTER 270° ROTATION:")
    print(f"  Dimensions: {dimensions}")
    print(f"  Point C: {point_c}")
    print(f"  Orientation: {orientation}")
    print(f"  Rotation Angle: {angle}°")
    
    # Apply 90° rotation (360° total, back to start)
    print("\nApplying fourth 90° rotation (360° total, back to start)...")
    success, message, details = rotator.rotate_90_clockwise()
    
    # Print state after 360° rotation
    point_c = details.get('point_c', (0, 0))
    orientation = details.get('orientation', 'unknown')
    angle = details.get('rotation_angle', 0)
    dimensions = f"{details.get('width', 0)} x {details.get('height', 0)}mm"
    
    print("\nAFTER 360° ROTATION (FULL CIRCLE):")
    print(f"  Dimensions: {dimensions}")
    print(f"  Point C: {point_c}")
    print(f"  Orientation: {orientation}")
    print(f"  Rotation Angle: {angle}°")
    
    # Print summary table
    print("\n=== ORIENTATION SUMMARY TABLE ===")
    print("---------------------------------------------------------")
    print("| Rotation | Dimensions | Point C            | Orientation |")
    print("---------------------------------------------------------")
    print(f"| 0°       | {width} x {height}mm | ({width}, {height})    | bottom-left  |")
    print(f"| 90°      | {height} x {width}mm | ({height}, -{width})   | top-left     |")
    print(f"| 180°     | {width} x {height}mm | (-{width}, -{height})   | top-right    |")
    print(f"| 270°     | {height} x {width}mm | (-{height}, {width})    | bottom-right |")
    print("---------------------------------------------------------")
    
    print("\n=== Test completed successfully ===")

if __name__ == "__main__":
    try:
        test_point_c_tracking()
    except Exception as e:
        print(f"Error running test: {str(e)}")
        import traceback
        traceback.print_exc()