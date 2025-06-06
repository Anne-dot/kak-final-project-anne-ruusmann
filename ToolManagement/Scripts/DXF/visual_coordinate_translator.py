"""
Visual coordinate translator for converting DXF coordinates to workpiece space.

This module transforms extracted DXF drill point coordinates to physical
workpiece coordinates for CNC machining operations.
"""

import os
import sys
from typing import Any

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import utilities
from Utils.error_utils import ErrorHandler, ErrorSeverity, ValidationError
from Utils.logging_utils import setup_logger


class VisualCoordinateTranslator:
    """
    Transforms DXF coordinates to physical workpiece coordinates.

    This translator specifically handles horizontal drilling operations,
    converting from CAD space to machine operation space.
    """

    def __init__(self):
        """Initialize the visual coordinate translator."""
        self.logger = setup_logger(__name__)

    def translate_coordinates(
        self, drill_points: list[dict], workpiece: dict
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Translate DXF coordinates to physical workpiece coordinates.

        Args:
            drill_points: List of drill point dictionaries from extractor
            workpiece: Workpiece dictionary from extractor with dimensions

        Returns:
            tuple: (success, message, data) where:
                - success is a boolean indicating if translation was successful
                - message contains success details or error message
                - data contains translated drilling information
        """
        try:
            # Create a copy of the input data with translated points
            translated_data = {"drill_points": [], "workpiece": workpiece.copy()}

            # Validate and round workpiece dimensions
            success, message, dimensions = self._validate_workpiece(workpiece)
            if not success:
                return success, message, dimensions

            workpiece_width = dimensions["width"]
            workpiece_height = dimensions["height"]
            workpiece_thickness = dimensions["thickness"]

            # Track counts for reporting
            x_direction_count = 0
            y_direction_count = 0
            skipped_count = 0

            # Process each drill point
            for point in drill_points:
                # Validate point has required fields
                if not self._has_required_fields(point):
                    skipped_count += 1
                    continue

                # Get original coordinates and extrusion_vector
                original_coords = point["position"]
                extrusion_vector = point["extrusion_vector"]

                # Detect drilling direction
                is_x_direction = self._is_x_direction_drilling(extrusion_vector)
                is_y_direction = self._is_y_direction_drilling(extrusion_vector)

                # Skip if not a horizontal drilling operation
                if not (is_x_direction or is_y_direction):
                    self.logger.warning(f"Unsupported drilling direction: {extrusion_vector}")
                    skipped_count += 1
                    continue

                # Translate based on drilling direction
                if is_x_direction:
                    translated_point = self._translate_x_direction(
                        point, original_coords, workpiece_height, workpiece_thickness
                    )
                    translated_data["drill_points"].append(translated_point)
                    x_direction_count += 1

                elif is_y_direction:
                    translated_point = self._translate_y_direction(
                        point, original_coords, workpiece_width, workpiece_thickness
                    )
                    translated_data["drill_points"].append(translated_point)
                    y_direction_count += 1

            # Check if we translated any points
            total_translated = x_direction_count + y_direction_count
            if total_translated == 0:
                return ErrorHandler.from_exception(
                    ValidationError(
                        message="No valid horizontal drilling points found for translation",
                        severity=ErrorSeverity.WARNING,
                    )
                )

            # Return success with translated data
            message = (
                f"Translated {total_translated} horizontal drill points "
                f"({x_direction_count} X-direction, {y_direction_count} Y-direction, "
                f"{skipped_count} skipped)"
            )

            return ErrorHandler.create_success_response(message=message, data=translated_data)

        except Exception as e:
            # Log and return error
            self.logger.error(f"Error in coordinate translation: {e!s}")
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Failed to translate coordinates: {e!s}", severity=ErrorSeverity.ERROR
                )
            )

    def _validate_workpiece(self, workpiece: dict) -> tuple[bool, str, dict]:
        """
        Validate workpiece data and round dimensions.

        Args:
            workpiece: Workpiece dictionary

        Returns:
            tuple: (success, message, dimensions)
        """
        # Check for required fields
        required_fields = ["width", "height", "thickness"]
        if not all(field in workpiece for field in required_fields):
            return ErrorHandler.from_exception(
                ValidationError(
                    message="Workpiece missing required dimensions", severity=ErrorSeverity.ERROR
                )
            )

        # Round dimensions to 0.1mm
        try:
            dimensions = {
                "width": round(float(workpiece["width"]), 1),
                "height": round(float(workpiece["height"]), 1),
                "thickness": round(float(workpiece["thickness"]), 1),
            }

            # Validate positive dimensions
            if any(value <= 0 for value in dimensions.values()):
                return ErrorHandler.from_exception(
                    ValidationError(
                        message="Workpiece dimensions must be positive",
                        severity=ErrorSeverity.ERROR,
                    )
                )

            return True, "Valid workpiece dimensions", dimensions

        except (ValueError, TypeError) as e:
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Invalid workpiece dimensions: {e!s}", severity=ErrorSeverity.ERROR
                )
            )

    def _has_required_fields(self, point: dict) -> bool:
        """
        Check if a drill point has all required fields.

        Args:
            point: Drill point dictionary

        Returns:
            bool: True if valid, False otherwise
        """
        # Check required fields exist
        required_fields = ["position", "diameter", "depth", "extrusion_vector"]
        if not all(field in point for field in required_fields):
            self.logger.warning(f"Drill point missing required fields: {point}")
            return False

        # Check position has 3 coordinates
        try:
            position = point["position"]
            if len(position) != 3:
                self.logger.warning(f"Invalid position format: {position}")
                return False
        except (TypeError, AttributeError):
            self.logger.warning(f"Invalid position type: {type(position).__name__}")
            return False

        # Check extrusion_vector has 3 components
        try:
            extrusion_vector = point["extrusion_vector"]
            if len(extrusion_vector) != 3:
                self.logger.warning(f"Invalid extrusion_vector format: {extrusion_vector}")
                return False
        except (TypeError, AttributeError):
            self.logger.warning(f"Invalid extrusion_vector type: {type(extrusion_vector).__name__}")
            return False

        return True

    def _is_x_direction_drilling(self, extrusion_vector) -> bool:
        """
        Check if extrusion vector indicates X-direction drilling.

        Args:
            extrusion_vector: Extrusion vector (x, y, z)

        Returns:
            bool: True if X-direction drilling
        """
        try:
            x, y, z = extrusion_vector
            # Check if this is an X-direction vector with exact equality
            return abs(x) == 1.0 and y == 0.0 and z == 0.0
        except (ValueError, TypeError, AttributeError):
            return False

    def _is_y_direction_drilling(self, extrusion_vector) -> bool:
        """
        Check if extrusion vector indicates Y-direction drilling.

        Args:
            extrusion_vector: Extrusion vector (x, y, z)

        Returns:
            bool: True if Y-direction drilling
        """
        try:
            x, y, z = extrusion_vector
            # Check if this is a Y-direction vector with exact equality
            return x == 0.0 and abs(y) == 1.0 and z == 0.0
        except (ValueError, TypeError, AttributeError):
            return False

    def _is_z_direction_drilling(self, extrusion_vector) -> bool:
        """
        Check if extrusion vector indicates Z-direction drilling (vertical).

        Args:
            extrusion_vector: Extrusion vector (x, y, z)

        Returns:
            bool: True if Z-direction drilling
        """
        try:
            x, y, z = extrusion_vector
            # Check if this is a Z-direction vector with exact equality
            return x == 0.0 and y == 0.0 and abs(z) == 1.0
        except (ValueError, TypeError, AttributeError):
            return False

    def _translate_x_direction(
        self,
        point: dict,
        original_coords: tuple[float, float, float],
        workpiece_height: float,
        workpiece_thickness: float,
    ) -> dict:
        """
        Translate coordinates for X-direction drilling.

        Args:
            point: Original drill point dictionary
            original_coords: Original (x, y, z) coordinates
            workpiece_height: Height of workpiece
            workpiece_thickness: Thickness of workpiece

        Returns:
            dict: Translated drill point dictionary
        """
        original_x, original_y, original_z = original_coords

        # Apply X-direction translation formulas
        translated_x = round(abs(original_z), 1)
        translated_y = round(abs(original_x), 1)
        translated_z = round(workpiece_thickness + original_y, 1)

        # Create translated point
        translated_point = point.copy()
        translated_point["position"] = (translated_x, translated_y, translated_z)
        translated_point["original_position"] = original_coords

        return translated_point

    def _translate_y_direction(
        self,
        point: dict,
        original_coords: tuple[float, float, float],
        workpiece_width: float,
        workpiece_thickness: float,
    ) -> dict:
        """
        Translate coordinates for Y-direction drilling.

        Args:
            point: Original drill point dictionary
            original_coords: Original (x, y, z) coordinates
            workpiece_width: Width of workpiece
            workpiece_thickness: Thickness of workpiece

        Returns:
            dict: Translated drill point dictionary
        """
        original_x, original_y, original_z = original_coords

        # Apply Y-direction translation formulas
        translated_x = round(workpiece_width - abs(original_x), 1)
        translated_y = round(abs(original_z), 1)
        translated_z = round(workpiece_thickness + original_y, 1)

        # Create translated point
        translated_point = point.copy()
        translated_point["position"] = (translated_x, translated_y, translated_z)
        translated_point["original_position"] = original_coords

        return translated_point
