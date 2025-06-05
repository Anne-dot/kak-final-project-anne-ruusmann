"""
Workpiece rotator module for rotating coordinates and workpiece orientation.

This module provides functionality for rotating drilling operations and workpiece geometry
through 90-degree increments, calculating dimensions from point C position.
"""

import sys
from pathlib import Path
from typing import Any

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import utilities
from Utils.error_utils import ErrorHandler, ErrorSeverity, ValidationError
from Utils.logging_utils import setup_logger


class WorkpieceRotator:
    """
    Class for handling workpiece rotation operations.

    This class provides functionality for rotating coordinates, points, and
    determining workpiece orientation based on point C coordinates.
    """

    def __init__(self):
        """Initialize the workpiece rotator."""
        self.logger = setup_logger(__name__)
        self.logger.info("WorkpieceRotator initialized")

    def rotate_coordinates_90(self, x: float, y: float) -> tuple[float, float]:
        """
        Rotate 2D coordinates 90 degrees clockwise.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Tuple of (new_x, new_y) after rotation
        """
        # 90° clockwise rotation: (x,y) -> (y,-x)
        return y, -x

    def rotate_point_90(self, point: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """
        Rotate a point 90 degrees clockwise.

        Rotates both the position and extrusion vector (if present) of the point.
        This function modifies the point in-place.

        Args:
            point: Dictionary with 'position' and optional 'extrusion_vector'

        Returns:
            Tuple of (success, message, details) with rotation result
        """
        try:
            # Validate point has required properties
            if "position" not in point:
                return ErrorHandler.from_exception(
                    ValidationError(
                        message="Point missing 'position' attribute", severity=ErrorSeverity.ERROR
                    )
                )

            # Get position coordinates
            x, y, z = point["position"]

            # Store original position
            point["original_position"] = (x, y, z)

            # Rotate position coordinates
            new_x, new_y = self.rotate_coordinates_90(x, y)

            # Update position with rotated coordinates
            point["position"] = (new_x, new_y, z)

            # If point has extrusion vector, rotate it too
            if "extrusion_vector" in point:
                ex, ey, ez = point["extrusion_vector"]

                # Store original extrusion vector
                point["original_extrusion_vector"] = (ex, ey, ez)

                # Rotate extrusion vector coordinates
                new_ex, new_ey = self.rotate_coordinates_90(ex, ey)

                # Update extrusion vector with rotated coordinates
                point["extrusion_vector"] = (new_ex, new_ey, ez)

            # Return success with rotated point
            return ErrorHandler.create_success_response(
                message="Point rotated 90° clockwise",
                data={"original_position": (x, y, z), "rotated_position": point["position"]},
            )

        except Exception as e:
            # Log and return error
            self.logger.error(f"Error rotating point: {e!s}")
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Failed to rotate point: {e!s}", severity=ErrorSeverity.ERROR
                )
            )

    def get_orientation_from_point_c(self, point_c: tuple[float, float, float]) -> str:
        """
        Determine orientation based on point C's coordinates.

        Point C is the corner opposite to the origin (0,0).

        Args:
            point_c: (x, y, z) coordinates of point C

        Returns:
            Orientation as string ('bottom-left', 'top-left', 'top-right', or 'bottom-right')
        """
        cx, cy, _ = point_c

        # Determine orientation based on point C's quadrant
        if cx > 0 and cy > 0:
            return "bottom-left"
        if cx > 0 and cy < 0:
            return "top-left"
        if cx < 0 and cy < 0:
            return "top-right"
        if cx < 0 and cy > 0:
            return "bottom-right"
        # Handle edge case (shouldn't happen in practice)
        self.logger.warning(f"Unexpected point C coordinates: {point_c}")
        return "unknown"

    def get_dimensions_from_point_c(self, point_c: tuple[float, float, float]) -> dict[str, float]:
        """
        Calculate workpiece dimensions based on point C's coordinates.

        Args:
            point_c: (x, y, z) coordinates of point C

        Returns:
            Dictionary with 'width' and 'height' calculated from point C
        """
        cx, cy, _ = point_c

        # Absolute values give dimensions regardless of orientation
        width = abs(cx)
        height = abs(cy)

        return {"width": width, "height": height}

    def transform_drilling_data(self, data: dict) -> tuple[bool, str, dict[str, Any]]:
        """
        Transform complete drilling data including workpiece and drill points.

        Args:
            data: Dictionary with 'workpiece' and 'drill_points'

        Returns:
            Tuple of (success, message, details) with transformation result
        """
        if not data:
            return ErrorHandler.from_exception(
                ValidationError(
                    message="No data provided for transformation", severity=ErrorSeverity.ERROR
                )
            )

        try:
            # Extract workpiece and drill points
            workpiece = data.get("workpiece", {})
            drill_points = data.get("drill_points", [])

            # Validate required components
            if not workpiece:
                return ErrorHandler.from_exception(
                    ValidationError(message="Missing workpiece data", severity=ErrorSeverity.ERROR)
                )

            if "corner_points" not in workpiece:
                return ErrorHandler.from_exception(
                    ValidationError(
                        message="Workpiece missing 'corner_points' attribute",
                        severity=ErrorSeverity.ERROR,
                    )
                )

            corner_points = workpiece["corner_points"]
            if len(corner_points) < 4:
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=f"Workpiece has insufficient corner points ({len(corner_points)})",
                        severity=ErrorSeverity.ERROR,
                    )
                )

            # Store original values
            original_corner_points = corner_points.copy()
            original_dimensions = {
                "width": workpiece.get("width", 0),
                "height": workpiece.get("height", 0),
                "thickness": workpiece.get("thickness", 0),
            }

            # 1. ROTATE ALL POINTS TOGETHER (Corner points and drill points)

            # Rotate corner points (except origin which stays at 0,0,0)
            rotated_corner_points = [original_corner_points[0]]  # Origin stays at (0,0,0)

            for i in range(1, len(original_corner_points)):
                x, y, z = original_corner_points[i]
                rotated_x, rotated_y = self.rotate_coordinates_90(x, y)
                rotated_corner_points.append((rotated_x, rotated_y, z))

            # Update workpiece with rotated corner points
            workpiece["corner_points"] = rotated_corner_points

            # Rotate drill points
            successfully_rotated = 0
            errors = 0

            for point in drill_points:
                success, _, _ = self.rotate_point_90(point)
                if success:
                    successfully_rotated += 1
                else:
                    errors += 1

            # 2. DETERMINE NEW ORIENTATION AND DIMENSIONS AFTER ROTATION

            # Get the rotated point C (opposite corner from origin)
            rotated_point_c = rotated_corner_points[2]

            # Determine orientation after rotation
            orientation = self.get_orientation_from_point_c(rotated_point_c)

            # Calculate dimensions from point C after rotation
            rotated_dimensions = self.get_dimensions_from_point_c(rotated_point_c)

            # Update workpiece with rotated dimensions (not positioning)
            workpiece["width_after_rotation"] = rotated_dimensions["width"]
            workpiece["height_after_rotation"] = rotated_dimensions["height"]

            # Create success message
            success_msg = (
                f"Transformed workpiece to {orientation} orientation and "
                f"rotated {successfully_rotated} drill points"
            )
            if errors > 0:
                success_msg += f" ({errors} points failed)"

            # Return comprehensive results
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "workpiece": workpiece,
                    "drill_points": drill_points,
                    "original_dimensions": original_dimensions,
                    "rotated_dimensions": rotated_dimensions,
                    "original_corner_points": original_corner_points,
                    "rotated_corner_points": rotated_corner_points,
                    "orientation": orientation,
                    "successfully_rotated": successfully_rotated,
                    "errors": errors,
                },
            )

        except Exception as e:
            # Log and return error
            self.logger.error(f"Error in data transformation: {e!s}")
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Failed to transform drilling data: {e!s}",
                    severity=ErrorSeverity.ERROR,
                )
            )


# Example usage if run directly
if __name__ == "__main__":
    # Create test data
    test_workpiece = {
        "width": 500,
        "height": 300,
        "thickness": 20,
        "corner_points": [
            (0, 0, 0),  # Origin
            (500, 0, 0),  # Width edge
            (500, 300, 0),  # Opposite corner (point C)
            (0, 300, 0),  # Height edge
        ],
    }

    test_drill_points = [
        {"position": (100, 50, 0), "extrusion_vector": (0, 0, 1), "diameter": 8.0},
        {"position": (400, 200, 0), "extrusion_vector": (1, 0, 0), "diameter": 10.0},
    ]

    test_data = {"workpiece": test_workpiece, "drill_points": test_drill_points}

    # Create rotator and transform data
    rotator = WorkpieceRotator()
    success, message, result = rotator.transform_drilling_data(test_data)

    # Print results
    print(f"Transformation: {'Success' if success else 'Failed'}")
    print(f"Message: {message}")

    if success:
        print("\nOriginal Workpiece:")
        original_corners = result["original_corner_points"]
        print(f"Corner points: {original_corners}")
        print(
            f"Dimensions: {result['original_dimensions']['width']}x"
            f"{result['original_dimensions']['height']}"
        )

        print("\nTransformed Workpiece:")
        rotated_corners = result["rotated_corner_points"]
        print(f"Corner points: {rotated_corners}")
        print(
            f"Rotated dimensions: {result['rotated_dimensions']['width']}x"
            f"{result['rotated_dimensions']['height']}"
        )
        print(f"Orientation: {result['orientation']}")

        print("\nDrill Points (Original → Rotated):")
        for i, point in enumerate(test_data["drill_points"]):
            original = point.get("original_position", "Unknown")
            rotated = point["position"]
            print(f"Point {i + 1}: {original} → {rotated}")

        print("\nExtrusion Vectors (Original → Rotated):")
        for i, point in enumerate(test_data["drill_points"]):
            if "extrusion_vector" in point:
                original_vector = point.get("original_extrusion_vector", "Unknown")
                rotated_vector = point["extrusion_vector"]
                print(f"Vector {i + 1}: {original_vector} → {rotated_vector}")
