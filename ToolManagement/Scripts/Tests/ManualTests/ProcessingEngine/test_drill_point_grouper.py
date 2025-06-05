"""
Manual test for the Drill Point Grouper module.

This test demonstrates grouping drill points by diameter and direction
to optimize machine operations.
"""

import sys
from pathlib import Path

# Path setup for imports
current_dir = Path(__file__).parent.absolute()
scripts_dir = current_dir.parent.parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import modules to test
from ProcessingEngine.drill_point_grouper import DrillPointGrouper


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


def print_drill_points_table(drill_points: list[dict]) -> None:
    """Print a formatted table of drill points."""
    print(
        "{:<4} {:<30} {:<15} {:<15} {:<20}".format(
            "#", "Position", "Diameter", "Direction", "Group Key"
        )
    )
    print("-" * 85)

    for i, point in enumerate(drill_points, 1):
        position = point.get("position", (0, 0, 0))
        diameter = point.get("diameter", 0)

        # Handle direction from either extrusion_vector or direction
        direction = point.get("extrusion_vector", point.get("direction", (0, 0, 0)))

        # Format values for display
        position_str = "({:.1f}, {:.1f}, {:.1f})".format(*position)
        direction_str = "({}, {}, {})".format(*direction)
        group_key = point.get("group_key", "None")

        print(
            f"{i:<4} {position_str:<30} {diameter:<15.2f} mm {direction_str:<15} {group_key!s:<20}"
        )

    print("-" * 85)


def print_groups_summary(groups: dict) -> None:
    """Print a summary of the groups."""
    print("{:<4} {:<20} {:<15} {:<10}".format("#", "Group Key", "Direction", "Count"))
    print("-" * 50)

    for i, ((diameter, direction), points) in enumerate(groups.items(), 1):
        direction_str = "({}, {}, {})".format(*direction)

        print(f"{i:<4} {diameter:<20.2f} mm {direction_str:<15} {len(points):<10}")

    print("-" * 50)
    print(f"Total groups: {len(groups)}")


def create_test_drill_points() -> list[dict]:
    """Create test drill points with mixed diameters and directions."""
    return [
        # 8mm Z-direction
        {
            "position": (100, 50, 0),
            "extrusion_vector": (0, 0, 1),  # Z+
            "diameter": 8.0,
        },
        {
            "position": (200, 100, 0),
            "extrusion_vector": (0, 0, 1),  # Z+
            "diameter": 8.0,
        },
        # 8mm X-direction
        {
            "position": (300, 150, 0),
            "extrusion_vector": (1, 0, 0),  # X+
            "diameter": 8.0,
        },
        {
            "position": (350, 175, 0),
            "extrusion_vector": (1, 0, 0),  # X+
            "diameter": 8.0,
        },
        # 10mm X-direction
        {
            "position": (400, 200, 0),
            "extrusion_vector": (1, 0, 0),  # X+
            "diameter": 10.0,
        },
        # 10mm Y-direction
        {
            "position": (500, 250, 0),
            "extrusion_vector": (0, 1, 0),  # Y+
            "diameter": 10.0,
        },
        # 12mm Y-direction
        {
            "position": (550, 275, 0),
            "extrusion_vector": (0, 1, 0),  # Y+
            "diameter": 12.0,
        },
    ]


def test_grouping() -> None:
    """Test the grouping functionality."""
    print_header("Testing Drill Point Grouper")

    # Create test data
    drill_points = create_test_drill_points()
    test_data = {"drill_points": drill_points}

    # Print original drill points
    print_subheader("Original Drill Points")
    print_drill_points_table(drill_points)

    # Create grouper
    grouper = DrillPointGrouper()

    # Group the points
    print_subheader("Grouping Drill Points")
    success, message, result = grouper.group_drilling_points(test_data)

    print(f"Grouping result: {message}")

    if not success:
        print(f"Error: {message}")
        return

    # Print groups summary
    print_subheader("Groups Summary")
    print_groups_summary(result["grouped_points"])

    # Print grouped drill points
    print_subheader("Drill Points with Group Keys")
    print_drill_points_table(result["drill_points"])

    # Print each group
    print_subheader("Detailed Group Contents")

    for (diameter, direction), points in result["grouped_points"].items():
        direction_str = "({}, {}, {})".format(*direction)

        print(f"\nGroup: {diameter} mm, Direction: {direction_str}")
        print(f"Contains {len(points)} points:")

        for i, point in enumerate(points, 1):
            position = point["position"]
            position_str = "({:.1f}, {:.1f}, {:.1f})".format(*position)

            print(f"  {i}. Position: {position_str}")


def test_invalid_data() -> None:
    """Test with invalid data."""
    print_header("Testing Invalid Data")

    grouper = DrillPointGrouper()

    # Test with missing diameter
    print_subheader("Testing Point Missing Diameter")
    invalid_data = {
        "drill_points": [
            {
                "position": (100, 50, 0),
                "extrusion_vector": (0, 0, 1),
                # Missing diameter
            }
        ]
    }

    success, message, _ = grouper.group_drilling_points(invalid_data)
    print(f"Result: {'Success' if success else 'Failed'}")
    print(f"Message: {message}")

    # Test with missing direction
    print_subheader("Testing Point Missing Direction")
    invalid_data = {
        "drill_points": [
            {
                "position": (100, 50, 0),
                "diameter": 8.0,
                # Missing direction
            }
        ]
    }

    success, message, _ = grouper.group_drilling_points(invalid_data)
    print(f"Result: {'Success' if success else 'Failed'}")
    print(f"Message: {message}")


def main() -> None:
    """Main test function."""
    while True:
        print("\nTest Options:")
        print("1. Test normal grouping functionality")
        print("2. Test with invalid data")
        print("0. Exit")

        choice = input("\nSelect an option: ")

        if choice == "0":
            break
        if choice == "1":
            test_grouping()
        elif choice == "2":
            test_invalid_data()
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    # For automated testing
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--diagnose":
        print_header("Running Automated Diagnostics")
        test_grouping()
    else:
        # Normal interactive mode
        main()
