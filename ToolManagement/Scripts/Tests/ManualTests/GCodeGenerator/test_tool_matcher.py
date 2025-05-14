"""
Manual test for the Tool Matcher module.

This test demonstrates how the ToolMatcher finds appropriate tools
for drilling operations based on diameter and direction.
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
from GCodeGenerator.tool_matcher import ToolMatcher


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


def print_tool_match(group_key: Tuple, result: Dict[str, Any]) -> None:
    """Print formatted tool match results."""
    diameter, direction = group_key
    
    print(f"Drill Specification:")
    print(f"  Diameter: {diameter} mm")
    print(f"  Direction: {direction}")
    print("\nMatched Tool:")
    print(f"  Tool #: {result['tool_number']}")
    print(f"  Description: {result.get('description', 'N/A')}")
    print(f"  Diameter: {result['diameter']} mm")
    print(f"  Direction Code: {result['direction']}")
    
    # Print additional details if available
    optional_fields = [
        ("tool_type", "Tool Type"),
        ("tool_length", "Tool Length"),
        ("max_working_length", "Max Working Length"),
        ("tool_holder_z_offset", "Z Offset"),
        ("in_spindle", "In Spindle")
    ]
    
    print("\nAdditional Tool Details:")
    for field, label in optional_fields:
        if field in result:
            if field == "in_spindle":
                value = "Yes" if result[field] else "No"
            else:
                value = result[field]
            print(f"  {label}: {value}")


def test_standard_cases(automated=False) -> None:
    """Test standard tool matching cases."""
    print_header("Testing Standard Tool Matching Cases")
    
    # Create tool matcher with default path
    matcher = ToolMatcher()
    
    # Define test cases
    test_cases = [
        (8.0, (0.0, 0.0, 1.0)),    # 8mm vertical (direction 5)
        (10.0, (1.0, 0.0, 0.0)),   # 10mm horizontal X+ (direction 1)
        (12.0, (-1.0, 0.0, 0.0)),  # 12mm horizontal X- (direction 2)
        (10.0, (0.0, 1.0, 0.0)),   # 10mm horizontal Y+ (direction 3)
        (10.0, (0.0, -1.0, 0.0)),  # 10mm horizontal Y- (direction 4)
    ]
    
    # Test each case
    for group_key in test_cases:
        diameter, direction = group_key
        print_subheader(f"{diameter}mm Drill in Direction {direction}")
        
        success, message, result = matcher.match_tool_to_group(group_key)
        
        if success:
            print(f"SUCCESS: {message}")
            print_tool_match(group_key, result)
        else:
            print(f"ERROR: {message}")
            print(f"No matching tool found for {diameter}mm drill in direction {direction}")
        
        if not automated:
            print("\nPress Enter to continue...")
            input()


def test_edge_cases(automated=False) -> None:
    """Test edge cases and error handling."""
    print_header("Testing Edge Cases")
    
    # Create tool matcher with default path
    matcher = ToolMatcher()
    
    # Test non-existent diameter
    print_subheader("Non-existent Diameter")
    diameter, direction = 99.0, (0.0, 0.0, 1.0)
    
    success, message, result = matcher.match_tool_to_group((diameter, direction))
    
    if success:
        print(f"SUCCESS: {message}")
        print_tool_match((diameter, direction), result)
    else:
        print(f"Expected Error: {message}")
    
    if not automated:
        print("\nPress Enter to continue...")
        input()
    
    # Test invalid direction vector
    print_subheader("Invalid Direction Vector")
    diameter, direction = 8.0, (0.5, 0.5, 0.0)
    
    success, message, result = matcher.match_tool_to_group((diameter, direction))
    
    if success:
        print(f"SUCCESS: {message}")
        print_tool_match((diameter, direction), result)
    else:
        print(f"Expected Error: {message}")
    
    if not automated:
        print("\nPress Enter to continue...")
        input()


def test_direction_mapping(automated=False) -> None:
    """Test the direction vector to code mapping."""
    print_header("Testing Direction Mapping")
    
    # Create tool matcher
    matcher = ToolMatcher()
    
    # Define test vectors
    test_vectors = [
        ((1.0, 0.0, 0.0), "Left to Right (X+)"),
        ((-1.0, 0.0, 0.0), "Right to Left (X-)"),
        ((0.0, 1.0, 0.0), "Front to Back (Y+)"),
        ((0.0, -1.0, 0.0), "Back to Front (Y-)"),
        ((0.0, 0.0, 1.0), "Vertical (Z+)"),
        ((0.5, 0.5, 0.0), "Invalid")
    ]
    
    print("{:<20} {:<15} {:<20}".format("Direction Vector", "Direction Code", "Description"))
    print("-" * 60)
    
    for vector, description in test_vectors:
        code = matcher._convert_vector_to_direction_code(vector)
        code_str = str(code) if code is not None else "None"
        
        print("{:<20} {:<15} {:<20}".format(str(vector), code_str, description))
    
    if not automated:
        print("\nPress Enter to continue...")
        input()


def main() -> None:
    """Main test function."""
    while True:
        print("\nTool Matcher Test Options:")
        print("1. Test standard tool matching cases")
        print("2. Test edge cases and error handling")
        print("3. Test direction vector mapping")
        print("0. Exit")
        
        choice = input("\nSelect an option: ")
        
        if choice == "0":
            break
        elif choice == "1":
            test_standard_cases()
        elif choice == "2":
            test_edge_cases()
        elif choice == "3":
            test_direction_mapping()
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    # For automated testing
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--diagnose":
        print_header("Running Automated Diagnostics")
        test_standard_cases(automated=True)
        test_edge_cases(automated=True)
        test_direction_mapping(automated=True)
    else:
        # Normal interactive mode
        main()