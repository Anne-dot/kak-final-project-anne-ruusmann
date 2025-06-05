"""
Drilling operations module for G-code generation.

This module provides functionality for generating G-code sequences
for horizontal drilling operations.
"""

import sys
from pathlib import Path
from typing import Any

# Add parent directory to Python path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import utilities
# Import local modules
from GCodeGenerator.machine_settings import MachineSettings
from Utils.error_utils import ErrorHandler, ErrorSeverity, ValidationError
from Utils.logging_utils import log_exception, setup_logger

# Set up logger for this module
logger = setup_logger(__name__)


def _validate_drill_point(drill_point: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    """
    Validate drill point data has required fields.

    Args:
        drill_point: Dictionary with drilling parameters

    Returns:
        tuple: (success, message, validated_data)
    """
    if not drill_point:
        return False, "No drill point data provided", {}

    position = drill_point.get("machine_position")
    depth = drill_point.get("depth")
    direction = drill_point.get("extrusion_vector")

    if not position:
        return False, "Missing machine_position", {}
    if depth is None:
        return False, "Missing drilling depth", {}
    if not direction:
        return False, "Missing extrusion_vector", {}

    return True, "Valid drill point", {"position": position, "depth": depth, "direction": direction}


def _get_drilling_axis(direction: tuple[float, float, float]) -> tuple[str, int]:
    """
    Determine drilling axis and direction from extrusion vector.

    Args:
        direction: Extrusion vector (x, y, z)

    Returns:
        tuple: (axis, sign) e.g., ('X', 1) for X+ direction
    """
    x, y, z = direction

    if x > 0:
        return "X", 1  # X+ direction
    if x < 0:
        return "X", -1  # X- direction
    if y > 0:
        return "Y", 1  # Y+ direction
    if y < 0:
        return "Y", -1  # Y- direction
    # Should not happen for horizontal drilling
    return "", 0


def _generate_move_to_depth(position: tuple[float, float, float]) -> list[str]:
    """
    Generate G-code to move from safe height to drilling depth.

    Args:
        position: Machine position (x, y, z)

    Returns:
        list: G-code lines
    """
    x, y, z = position
    return [f"G00 Z{z:.3f} (Lower to drilling depth)"]


def _generate_drilling_moves(
    axis: str,
    direction_sign: int,
    depth: float,
    approach_distance: float,
    drilling_feed: float,
    retract_feed: float,
) -> list[str]:
    """
    Generate incremental drilling and retract moves.

    Args:
        axis: 'X' or 'Y'
        direction_sign: 1 or -1
        depth: Drilling depth
        approach_distance: Safety approach distance
        drilling_feed: Feed rate for drilling
        retract_feed: Feed rate for retraction

    Returns:
        list: G-code lines
    """
    # Calculate total drilling distance
    drill_distance = depth + approach_distance

    # Generate moves
    lines = [
        "G91 (Switch to incremental mode)",
        f"G01 {axis}{drill_distance * direction_sign:.3f} F{drilling_feed:.1f} (Drill)",
        f"G01 {axis}{-drill_distance * direction_sign:.3f} F{retract_feed:.1f} (Retract)",
        "G90 (Return to absolute mode)",
    ]

    return lines


def generate_drilling_sequence(
    drill_point: dict[str, Any], machine_settings: MachineSettings
) -> tuple[bool, str, dict[str, Any]]:
    """
    Generate G-code sequence for a single horizontal drilling operation.

    Args:
        drill_point: Dictionary containing drilling parameters
        machine_settings: MachineSettings instance for parameters

    Returns:
        tuple: (success, message, details)
    """
    try:
        # Step 1: Validate input
        valid, message, data = _validate_drill_point(drill_point)
        if not valid:
            return ErrorHandler.from_exception(
                ValidationError(message, severity=ErrorSeverity.ERROR)
            )

        # Step 2: Get drilling parameters
        position = data["position"]
        depth = data["depth"]
        direction = data["direction"]

        # Step 3: Determine drilling axis
        axis, direction_sign = _get_drilling_axis(direction)
        if not axis:
            return ErrorHandler.from_exception(
                ValidationError("Invalid drilling direction", severity=ErrorSeverity.ERROR)
            )

        # Step 4: Get machine settings
        approach_distance = machine_settings.get_approach_distance()
        drilling_feed = machine_settings.get_feed_rate("drilling")
        retract_feed = machine_settings.get_feed_rate("retraction")

        # Step 5: Build G-code sequence
        gcode_lines = []

        # Move to drilling depth
        gcode_lines.extend(_generate_move_to_depth(position))

        # Drilling moves
        gcode_lines.extend(
            _generate_drilling_moves(
                axis, direction_sign, depth, approach_distance, drilling_feed, retract_feed
            )
        )

        # Return to safe height
        safe_z = machine_settings.get_safe_z_height()
        gcode_lines.append(f"G53 G00 Z{safe_z:.3f} (Return to safe height)")

        return ErrorHandler.create_success_response(
            f"Generated {len(gcode_lines)} lines for {axis}{'+' if direction_sign > 0 else '-'} drilling",
            {"gcode_lines": gcode_lines},
        )

    except Exception as e:
        log_exception(logger, e, "Error generating drilling sequence")
        return ErrorHandler.from_exception(e)


if __name__ == "__main__":
    """Test the drilling operations module with sample data."""

    # Initialize machine settings
    settings = MachineSettings()

    # Test data from ProcessingEngine (after rotation and positioning)
    test_cases = [
        {
            "name": "X+ drilling (8mm, 15mm deep)",
            "drill_point": {
                "position": (100.0, 200.0, 0.0),
                "machine_position": (100.0, 200.0, 9.0),  # Z=9 for center of 18mm workpiece
                "diameter": 8.0,
                "depth": 15.0,
                "extrusion_vector": (1.0, 0.0, 0.0),  # X+ direction
                "direction": 1,
                "group_key": (8.0, (1.0, 0.0, 0.0)),
            },
        },
        {
            "name": "Y- drilling (10mm, 20mm deep)",
            "drill_point": {
                "position": (150.0, 300.0, 0.0),
                "machine_position": (150.0, 300.0, 9.0),
                "diameter": 10.0,
                "depth": 20.0,
                "extrusion_vector": (0.0, -1.0, 0.0),  # Y- direction
                "direction": 4,
                "group_key": (10.0, (0.0, -1.0, 0.0)),
            },
        },
    ]

    print("=" * 60)
    print("Testing Drilling Operations Module")
    print("=" * 60)

    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print("-" * 40)

        success, message, details = generate_drilling_sequence(test["drill_point"], settings)

        print(f"Success: {success}")
        print(f"Message: {message}")

        if success and "gcode_lines" in details:
            print("\nGenerated G-code:")
            for line in details["gcode_lines"]:
                print(f"  {line}")
        else:
            print(f"Error details: {details}")

    print("\n" + "=" * 60)
