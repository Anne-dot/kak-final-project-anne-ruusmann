"""
Manual test for the Machine Settings module.

This test demonstrates how the MachineSettings class
provides machine-specific settings for G-code generation.
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

# Import module to test
from GCodeGenerator.machine_settings import MachineSettings
from Utils.config import AppConfig


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")


def print_subheader(title: str) -> None:
    """Print a formatted subheader."""
    print("\n" + "-" * 50)
    print(title)
    print("-" * 50 + "\n")


def print_gcode_block(gcode_items: List[Dict[str, str]], settings: MachineSettings) -> None:
    """Print formatted G-code items."""
    for i, item in enumerate(gcode_items):
        line_num = settings.get_line_number(i)
        command = item["command"]
        
        # Format comment if present
        if "comment" in item and item["comment"]:
            comment = settings.format_comment(item["comment"])
            print(f"{line_num} {command} {comment}")
        else:
            print(f"{line_num} {command}")


def test_workpiece_dimension_handling(automated=False) -> None:
    """Test how workpiece dimensions are handled and displayed."""
    print_header("Testing Workpiece Dimension Handling")
    
    # Create machine settings with default configuration
    settings = MachineSettings()
    
    # Test data with different dimensions
    test_workpieces = {
        "Small Standard": {"width": 400.0, "height": 500.0, "thickness": 18.0},
        "Large Standard": {"width": 400.0, "height": 700.0, "thickness": 18.0},
        "With Decimals": {"width": 400.123, "height": 500.567, "thickness": 18.999},
        "Thin Material": {"width": 400.0, "height": 500.0, "thickness": 5.5},
        "Thick Material": {"width": 400.0, "height": 500.0, "thickness": 30.0}
    }
    
    for name, dimensions in test_workpieces.items():
        print_subheader(f"{name} Workpiece")
        
        print(f"Raw dimensions: width={dimensions['width']}, height={dimensions['height']}, thickness={dimensions['thickness']}")
        
        # Generate header for this workpiece
        header = settings.get_default_gcode_header(dimensions, f"{name.lower().replace(' ', '_')}.nc")
        
        print("\nGenerated G-code Header:")
        print_gcode_block(header, settings)
        
        if not automated:
            print("\nPress Enter to continue...")
            input()


def test_coordinate_system_selection(automated=False) -> None:
    """Test coordinate system selection based on workpiece height."""
    print_header("Testing Coordinate System Selection")
    
    # Create machine settings
    settings = MachineSettings()
    
    # Get the threshold from config
    threshold = AppConfig.gcode.WORKPIECE_HEIGHT_THRESHOLD
    
    print(f"Coordinate system threshold: {threshold}mm")
    print(f"Small workpieces (height <= {threshold}mm) use {AppConfig.gcode.COORDINATE_SYSTEM_SMALL}")
    print(f"Large workpieces (height > {threshold}mm) use {AppConfig.gcode.COORDINATE_SYSTEM_LARGE}")
    
    # Test heights around the threshold
    test_heights = [
        threshold - 100, 
        threshold - 10,
        threshold - 1, 
        threshold, 
        threshold + 1, 
        threshold + 10,
        threshold + 100
    ]
    
    print("\nTesting different workpiece heights:")
    for height in test_heights:
        dimensions = {"width": 400.0, "height": height, "thickness": 18.0}
        cs = settings.get_coordinate_system(dimensions)
        print(f"Height: {height}mm -> {cs['command']} ({cs['comment']})")
    
    if not automated:
        print("\nPress Enter to continue...")
        input()


def test_vector_to_axis_mapping(automated=False) -> None:
    """Test mapping between direction vectors and machine axes."""
    print_header("Testing Direction Vector Mapping")
    
    # Create machine settings
    settings = MachineSettings()
    
    # Define test vectors
    test_vectors = [
        (1.0, 0.0, 0.0),     # X+
        (-1.0, 0.0, 0.0),    # X-
        (0.0, 1.0, 0.0),     # Y+
        (0.0, -1.0, 0.0),    # Y-
        (0.5, 0.5, 0.0),     # Invalid
        (0.707, 0.707, 0.0)  # Another invalid
    ]
    
    print("Direction Vector      Axis    Direction    Description")
    print("-" * 60)
    
    for vector in test_vectors:
        info = settings.get_vector_axis_info(vector)
        print(f"{str(vector):<20} {info['axis']:<7} {info['direction']:<11} {info['description']}")
    
    if not automated:
        print("\nPress Enter to continue...")
        input()


def test_positioning_commands(automated=False) -> None:
    """Test positioning commands for horizontal drilling."""
    print_header("Testing Positioning Commands")
    
    # Create machine settings
    settings = MachineSettings()
    
    # Get positioning commands
    commands = settings.get_positioning_commands()
    
    print("Command Purpose        M-Code")
    print("-" * 40)
    
    for purpose, code in commands.items():
        print(f"{purpose:<20} {code}")
        
    print("\nNote: These M-codes must be defined in your Mach3 configuration.")
    print("They handle the specialized positioning for horizontal drilling.")
    
    if not automated:
        print("\nPress Enter to continue...")
        input()


def test_gcode_header_and_footer(automated=False) -> None:
    """Test G-code header and footer generation."""
    print_header("Testing G-code Header and Footer Generation")
    
    # Create machine settings
    settings = MachineSettings()
    
    # Test workpiece
    dimensions = {"width": 400.0, "height": 500.0, "thickness": 18.0}
    
    # Generate header
    header = settings.get_default_gcode_header(dimensions, "test_program.nc")
    
    print_subheader("G-code Header")
    print_gcode_block(header, settings)
    
    # Generate footer
    footer = settings.get_default_gcode_footer()
    
    print_subheader("G-code Footer")
    print_gcode_block(footer, settings)
    
    if not automated:
        print("\nPress Enter to continue...")
        input()


def main() -> None:
    """Main test function."""
    print_header("Machine Settings Module Test")
    
    print("This test demonstrates the functionality of the MachineSettings class,")
    print("which provides machine-specific settings for G-code generation,")
    print("particularly for horizontal drilling operations.")
    
    while True:
        print("\nTest Options:")
        print("1. Test Workpiece Dimension Handling")
        print("2. Test Coordinate System Selection")
        print("3. Test Direction Vector Mapping")
        print("4. Test Positioning Commands")
        print("5. Test G-code Header and Footer Generation")
        print("0. Exit")
        
        choice = input("\nSelect an option: ")
        
        if choice == "0":
            break
        elif choice == "1":
            test_workpiece_dimension_handling()
        elif choice == "2":
            test_coordinate_system_selection()
        elif choice == "3":
            test_vector_to_axis_mapping()
        elif choice == "4":
            test_positioning_commands()
        elif choice == "5":
            test_gcode_header_and_footer()
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    # For automated testing
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--diagnose":
        print_header("Running Automated Diagnostics")
        test_workpiece_dimension_handling(automated=True)
        test_coordinate_system_selection(automated=True)
        test_vector_to_axis_mapping(automated=True)
        test_positioning_commands(automated=True)
        test_gcode_header_and_footer(automated=True)
    else:
        # Normal interactive mode
        main()