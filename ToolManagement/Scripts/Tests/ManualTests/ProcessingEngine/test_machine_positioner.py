"""
Manual test for the Machine Positioner module.

This test demonstrates positioning workpieces and drill points in machine space
by applying the appropriate offsets based on workpiece orientation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import modules to test
from ProcessingEngine.machine_positioner import MachinePositioner
from ProcessingEngine.workpiece_rotator import WorkpieceRotator


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


def print_workpiece_info(workpiece: Dict) -> None:
    """Print formatted workpiece information."""
    print("Workpiece Information:")
    print(f"Width: {workpiece.get('width', 0):.1f} mm")
    print(f"Height: {workpiece.get('height', 0):.1f} mm")
    print(f"Thickness: {workpiece.get('thickness', 0):.1f} mm")
    
    # Print corner points if available
    if 'corner_points' in workpiece:
        print("\nCorner Points:")
        for i, point in enumerate(workpiece['corner_points']):
            print(f"Corner {i}: {point}")


def print_corner_points_comparison(original_corners: List[Tuple], machine_corners: List[Tuple]) -> None:
    """Print a comparison table of original and machine corner points."""
    print("{:<10} {:<30} {:<30}".format(
        "Corner", "Original Position", "Machine Position"
    ))
    print("-" * 70)
    
    for i, (orig, mach) in enumerate(zip(original_corners, machine_corners)):
        orig_str = f"({orig[0]:.1f}, {orig[1]:.1f}, {orig[2]:.1f})"
        mach_str = f"({mach[0]:.1f}, {mach[1]:.1f}, {mach[2]:.1f})"
        
        print("{:<10} {:<30} {:<30}".format(
            f"Corner {i}", orig_str, mach_str
        ))
    
    print("-" * 70)


def print_drill_points_comparison(drill_points: List[Dict]) -> None:
    """Print a comparison table of original and machine drill point positions."""
    print("{:<4} {:<30} {:<30} {:<15}".format(
        "#", "Original Position", "Machine Position", "Diameter"
    ))
    print("-" * 80)
    
    for i, point in enumerate(drill_points, 1):
        orig_pos = point.get("original_position", point.get("position", (0, 0, 0)))
        mach_pos = point.get("machine_position", (0, 0, 0))
        diameter = point.get("diameter", 0)
        
        orig_str = f"({orig_pos[0]:.1f}, {orig_pos[1]:.1f}, {orig_pos[2]:.1f})"
        mach_str = f"({mach_pos[0]:.1f}, {mach_pos[1]:.1f}, {mach_pos[2]:.1f})"
        
        print("{:<4} {:<30} {:<30} {:<15.2f} mm".format(
            i, orig_str, mach_str, diameter
        ))
    
    print("-" * 80)


def create_test_workpiece(quadrant: int) -> Dict:
    """Create a test workpiece in the specified quadrant."""
    if quadrant == 1:
        # Q1: x>0, y>0
        return {
            'width': 500,
            'height': 300,
            'thickness': 20,
            'corner_points': [
                (0, 0, 0),           # Origin
                (0, 300, 0),         # Height edge
                (500, 300, 0),       # Point C (opposite)
                (500, 0, 0)          # Width edge
            ]
        }
    elif quadrant == 2:
        # Q2: x<0, y>0
        return {
            'width': 500,
            'height': 300,
            'thickness': 20,
            'corner_points': [
                (0, 0, 0),           # Origin
                (-500, 0, 0),        # Width edge
                (-500, 300, 0),      # Point C (opposite)
                (0, 300, 0)          # Height edge
            ]
        }
    elif quadrant == 3:
        # Q3: x<0, y<0
        return {
            'width': 500,
            'height': 300,
            'thickness': 20,
            'corner_points': [
                (0, 0, 0),           # Origin
                (-500, 0, 0),        # Width edge
                (-500, -300, 0),     # Point C (opposite)
                (0, -300, 0)         # Height edge
            ]
        }
    else:  # quadrant == 4
        # Q4: x>0, y<0
        return {
            'width': 500,
            'height': 300,
            'thickness': 20,
            'corner_points': [
                (0, 0, 0),           # Origin
                (500, 0, 0),         # Width edge
                (500, -300, 0),      # Point C (opposite)
                (0, -300, 0)         # Height edge
            ]
        }


def create_test_drill_points() -> List[Dict]:
    """Create test drill points."""
    return [
        {
            "position": (100, 100, 0),
            "extrusion_vector": (0, 0, 1),
            "diameter": 8.0
        },
        {
            "position": (400, 200, 0),
            "extrusion_vector": (1, 0, 0),
            "diameter": 10.0
        },
        {
            "position": (-100, 150, 0),
            "extrusion_vector": (0, 1, 0),
            "diameter": 12.0
        }
    ]


def test_positioning_with_workpiece(workpiece: Dict, drill_points: List[Dict], rotation_count: int = 0) -> None:
    """Test the positioning process with a given workpiece."""
    # Create data structure
    test_data = {
        'workpiece': workpiece,
        'drill_points': drill_points
    }
    
    # Optionally rotate the workpiece multiple times
    if rotation_count > 0:
        rotator = WorkpieceRotator()
        for i in range(rotation_count):
            print_subheader(f"Rotating workpiece (iteration {i+1})")
            success, message, result = rotator.transform_drilling_data(test_data)
            
            if success:
                test_data = {
                    'workpiece': result['workpiece'],
                    'drill_points': result['drill_points']
                }
                print(f"Rotation result: {message}")
            else:
                print(f"Rotation failed: {message}")
                return
    
    # Display pre-positioning state
    print_subheader("Before Positioning")
    print_workpiece_info(test_data['workpiece'])
    
    # Get point C and determine orientation
    point_c = test_data['workpiece']['corner_points'][2]
    
    # Create positioner
    positioner = MachinePositioner()
    orientation = positioner.get_orientation_name(point_c)
    
    print(f"\nPoint C: {point_c}")
    print(f"Orientation: {orientation}")
    
    # Apply positioning
    print_subheader("Applying Machine Positioning")
    success, message, result = positioner.position_for_top_left_machine(test_data)
    
    if not success:
        print(f"Positioning failed: {message}")
        return
    
    print(f"Positioning result: {message}")
    print(f"Applied offset: {result['offset']}")
    
    # Print corner points comparison
    print_subheader("Corner Points Comparison")
    print_corner_points_comparison(
        result['original_corner_points'], 
        result['machine_corner_points']
    )
    
    # Print drill points comparison
    print_subheader("Drill Points Comparison")
    print_drill_points_comparison(result['drill_points'])


def test_positioning_in_all_quadrants() -> None:
    """Test positioning with workpieces in all quadrants."""
    drill_points = create_test_drill_points()
    
    for quadrant in range(1, 5):
        print_header(f"Testing Workpiece in Quadrant {quadrant}")
        workpiece = create_test_workpiece(quadrant)
        test_positioning_with_workpiece(workpiece, drill_points)


def test_positioning_after_rotation() -> None:
    """Test positioning after rotation."""
    drill_points = create_test_drill_points()
    workpiece = create_test_workpiece(1)  # Start with Q1
    
    print_header("Testing Positioning After Rotation")
    test_positioning_with_workpiece(workpiece, drill_points, rotation_count=1)


def main() -> None:
    """Main test function."""
    print_header("Machine Positioner Test")
    
    while True:
        print("\nTest Options:")
        print("1. Test with workpiece in Quadrant 1 (x>0, y>0)")
        print("2. Test with workpiece in Quadrant 2 (x<0, y>0)")
        print("3. Test with workpiece in Quadrant 3 (x<0, y<0)")
        print("4. Test with workpiece in Quadrant 4 (x>0, y<0)")
        print("5. Test with workpieces in all quadrants")
        print("6. Test positioning after rotation")
        print("0. Exit")
        
        choice = input("\nSelect an option: ")
        
        if choice == "0":
            break
        elif choice in ["1", "2", "3", "4"]:
            quadrant = int(choice)
            workpiece = create_test_workpiece(quadrant)
            drill_points = create_test_drill_points()
            test_positioning_with_workpiece(workpiece, drill_points)
        elif choice == "5":
            test_positioning_in_all_quadrants()
        elif choice == "6":
            test_positioning_after_rotation()
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    # For automated diagnostics
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--diagnose":
        print_header("Running Automated Diagnostics")
        test_positioning_in_all_quadrants()
    else:
        # Normal interactive mode
        main()