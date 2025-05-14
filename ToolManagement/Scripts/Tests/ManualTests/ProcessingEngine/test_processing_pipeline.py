"""
Integration test for the complete ProcessingEngine pipeline.

This test demonstrates the full processing pipeline:
1. Rotation via WorkpieceRotator
2. Positioning via MachinePositioner
3. Grouping via DrillPointGrouper
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import modules to test
from ProcessingEngine.workpiece_rotator import WorkpieceRotator
from ProcessingEngine.machine_positioner import MachinePositioner
from ProcessingEngine.drill_point_grouper import DrillPointGrouper


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70 + "\n")


def print_subheader(title: str) -> None:
    """Print a formatted subheader."""
    print("\n" + "-" * 70)
    print(title.center(70))
    print("-" * 70 + "\n")


def print_json_summary(data: Dict, title: str = None) -> None:
    """Print a summary of the JSON data."""
    if title:
        print(f"\n{title}:")
    
    # Check for workpiece data
    if "workpiece" in data:
        workpiece = data["workpiece"]
        print("\nWorkpiece:")
        print(f"  Width: {workpiece.get('width', 'N/A')}")
        print(f"  Height: {workpiece.get('height', 'N/A')}")
        print(f"  Thickness: {workpiece.get('thickness', 'N/A')}")
        
        # Print rotated dimensions if available
        if "width_after_rotation" in workpiece:
            print(f"  Width after rotation: {workpiece.get('width_after_rotation', 'N/A')}")
            print(f"  Height after rotation: {workpiece.get('height_after_rotation', 'N/A')}")
        
        # Print machine offset if available
        if "machine_offset" in workpiece:
            print(f"  Machine offset: {workpiece.get('machine_offset', 'N/A')}")
        
        # Print corner points
        if "corner_points" in workpiece:
            print("\n  Corner Points:")
            for i, point in enumerate(workpiece["corner_points"]):
                print(f"    Corner {i}: {point}")
        
        # Print machine corner points if available
        if "machine_corner_points" in workpiece:
            print("\n  Machine Corner Points:")
            for i, point in enumerate(workpiece["machine_corner_points"]):
                print(f"    Corner {i}: {point}")
    
    # Check for drill points
    if "drill_points" in data:
        drill_points = data["drill_points"]
        print(f"\nDrill Points: {len(drill_points)} points")
        
        # Print first 3 points (with more info if available)
        for i, point in enumerate(drill_points[:3], 1):
            position = point.get("position", "N/A")
            diameter = point.get("diameter", "N/A")
            direction = point.get("extrusion_vector", point.get("direction", "N/A"))
            
            print(f"\n  Point {i}:")
            print(f"    Position: {position}")
            
            # Print original position if available
            if "original_position" in point:
                print(f"    Original Position: {point['original_position']}")
            
            # Print machine position if available
            if "machine_position" in point:
                print(f"    Machine Position: {point['machine_position']}")
            
            print(f"    Diameter: {diameter}")
            print(f"    Direction: {direction}")
            
            # Print group key if available
            if "group_key" in point:
                print(f"    Group Key: {point['group_key']}")
        
        if len(drill_points) > 3:
            print(f"\n  ... and {len(drill_points) - 3} more points")
    
    # Check for grouped points
    if "grouped_points" in data:
        grouped_points = data["grouped_points"]
        group_count = len(grouped_points)
        
        print(f"\nGrouped Points: {group_count} groups")
        
        # Show group summaries
        for i, ((diameter, direction), points) in enumerate(grouped_points.items(), 1):
            print(f"  Group {i}: {len(points)} points with {diameter}mm, direction={direction}")


def print_module_result(success: bool, message: str, additional_info: str = None) -> None:
    """Print the result of a module execution."""
    status = "SUCCESS" if success else "FAILED"
    print(f"Status: {status}")
    print(f"Message: {message}")
    
    if additional_info:
        print(f"Additional: {additional_info}")


def create_test_data() -> Dict:
    """Create test data for the processing pipeline."""
    return {
        "workpiece": {
            "width": 600.0,
            "height": 400.0,
            "thickness": 18.0,
            "corner_points": [
                (0, 0, 0),       # Origin point
                (600, 0, 0),     # Width edge
                (600, 400, 0),   # Point C (opposite corner)
                (0, 400, 0)      # Height edge
            ]
        },
        "drill_points": [
            # Vertical drilling (Z+)
            {
                "position": (100, 100, 0),
                "extrusion_vector": (0, 0, 1),
                "diameter": 8.0,
                "depth": 15.0
            },
            {
                "position": (200, 200, 0),
                "extrusion_vector": (0, 0, 1),
                "diameter": 8.0,
                "depth": 15.0
            },
            # Horizontal drilling (X+)
            {
                "position": (300, 300, 0),
                "extrusion_vector": (1, 0, 0),
                "diameter": 10.0,
                "depth": 20.0
            },
            # Horizontal drilling (Y+)
            {
                "position": (400, 100, 0),
                "extrusion_vector": (0, 1, 0),
                "diameter": 12.0,
                "depth": 25.0
            },
            # Another vertical drilling with different diameter
            {
                "position": (500, 300, 0),
                "extrusion_vector": (0, 0, 1),
                "diameter": 6.0,
                "depth": 10.0
            }
        ]
    }


def run_full_pipeline(data: Dict, rotation_steps: int = 1) -> Optional[Dict]:
    """
    Run the full ProcessingEngine pipeline.
    
    Args:
        data: Input data with workpiece and drill points
        rotation_steps: Number of 90° rotations to apply (0-3)
        
    Returns:
        Processed data or None if any stage fails
    """
    print_header("PROCESSING ENGINE PIPELINE TEST")
    print_json_summary(data, "Input Data")
    
    # Initialize modules
    rotator = WorkpieceRotator()
    positioner = MachinePositioner()
    grouper = DrillPointGrouper()
    
    current_data = data
    
    # 1. Rotation (optional)
    if rotation_steps > 0:
        print_subheader("STAGE 1: WORKPIECE ROTATION")
        
        for i in range(rotation_steps):
            print(f"\nApplying rotation {i+1} of {rotation_steps}...")
            success, message, result = rotator.transform_drilling_data(current_data)
            print_module_result(success, message)
            
            if not success:
                print("Pipeline aborted: Rotation failed")
                return None
            
            current_data = result
        
        print_json_summary(current_data, "After Rotation")
    
    # 2. Machine Positioning
    print_subheader("STAGE 2: MACHINE POSITIONING")
    success, message, result = positioner.position_for_top_left_machine(current_data)
    print_module_result(success, message)
    
    if not success:
        print("Pipeline aborted: Positioning failed")
        return None
    
    current_data = result
    print_json_summary(current_data, "After Positioning")
    
    # 3. Drill Point Grouping
    print_subheader("STAGE 3: DRILL POINT GROUPING")
    success, message, result = grouper.group_drilling_points(current_data)
    print_module_result(success, message)
    
    if not success:
        print("Pipeline aborted: Grouping failed")
        return None
    
    current_data = result
    print_json_summary(current_data, "After Grouping")
    
    # Pipeline complete
    print_subheader("PIPELINE COMPLETE")
    print("All processing stages completed successfully")
    
    return current_data


def test_pipeline_with_different_rotations() -> None:
    """Test the pipeline with different rotation configurations."""
    for rotations in range(4):
        print_header(f"TESTING WITH {rotations} ROTATIONS")
        
        # Create fresh test data for each test
        test_data = create_test_data()
        
        # Run the pipeline
        result = run_full_pipeline(test_data, rotations)
        
        # Separator between tests
        print("\n" + "=" * 70 + "\n")


def interactive_menu() -> None:
    """Display an interactive menu for testing."""
    while True:
        print("\nProcessingEngine Pipeline Test")
        print("1. Run pipeline with no rotation")
        print("2. Run pipeline with 1 rotation (90°)")
        print("3. Run pipeline with 2 rotations (180°)")
        print("4. Run pipeline with 3 rotations (270°)")
        print("5. Test all rotation configurations")
        print("0. Exit")
        
        choice = input("\nEnter your choice: ")
        
        if choice == "0":
            break
        elif choice == "1":
            test_data = create_test_data()
            run_full_pipeline(test_data, 0)
        elif choice == "2":
            test_data = create_test_data()
            run_full_pipeline(test_data, 1)
        elif choice == "3":
            test_data = create_test_data()
            run_full_pipeline(test_data, 2)
        elif choice == "4":
            test_data = create_test_data()
            run_full_pipeline(test_data, 3)
        elif choice == "5":
            test_pipeline_with_different_rotations()
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    # Handle command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--diagnose":
            # Run automated test
            test_data = create_test_data()
            run_full_pipeline(test_data, 1)
        elif sys.argv[1].isdigit():
            # Run with specified rotation
            rotations = int(sys.argv[1])
            test_data = create_test_data()
            run_full_pipeline(test_data, rotations)
    else:
        # Interactive mode
        interactive_menu()