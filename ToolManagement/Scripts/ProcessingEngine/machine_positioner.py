"""
Machine positioner module for positioning workpieces and drill points on the CNC machine.

This module provides functionality for calculating offsets and applying them to
workpiece corner points and drill points, ensuring proper positioning in machine space.
"""

import os
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import utilities
from Utils.error_utils import ErrorHandler, ValidationError, ErrorSeverity
from Utils.logging_utils import setup_logger


class MachinePositioner:
    """
    Class for handling workpiece positioning operations.
    
    This class provides functionality for calculating machine offsets based on
    workpiece orientation and applying them to corner points and drill points.
    """
    
    def __init__(self):
        """Initialize the machine positioner with logger only."""
        self.logger = setup_logger(__name__)
        self.logger.info("MachinePositioner initialized")
    
    def position_for_top_left_machine(self, data: Dict) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Position workpiece with top-left corner at machine origin.
        
        This determines the correct offset based on point C's position 
        (the corner point opposite to origin) after rotation.
        
        Args:
            data: Dictionary with 'workpiece' and 'drill_points'
            
        Returns:
            Tuple of (success, message, details) with positioning result
        """
        if not data:
            return ErrorHandler.from_exception(
                ValidationError(
                    message="No data provided for positioning",
                    severity=ErrorSeverity.ERROR
                )
            )
        
        try:
            # Extract workpiece and drill points
            workpiece = data.get('workpiece', {})
            drill_points = data.get('drill_points', [])
            
            # Validate workpiece data
            validation_result = self._validate_workpiece_data(workpiece)
            if not validation_result[0]:
                return validation_result
            
            # Get corner points and point C
            corner_points = workpiece['corner_points']
            if len(corner_points) < 4:
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=f"Workpiece has insufficient corner points ({len(corner_points)})",
                        severity=ErrorSeverity.ERROR
                    )
                )
            
            # Get point C (the corner point opposite to origin)
            point_c = corner_points[2]
            x_c, y_c, z_c = point_c
            
            # Store original values before applying offset
            original_corner_points = corner_points.copy()
            
            # Calculate offset based on point C's position
            offset_x, offset_y = self._determine_offset(x_c, y_c)
            
            # Apply offset to corner points
            machine_corner_points = []
            for corner in corner_points:
                machine_corner = self._apply_offset_to_coordinates(corner, (offset_x, offset_y))
                machine_corner_points.append(machine_corner)
            
            # Apply offset to drill points
            machine_drill_points = []
            
            for point in drill_points:
                # Validate drill point has position
                if 'position' not in point:
                    return ErrorHandler.from_exception(
                        ValidationError(
                            message=f"Drill point missing required 'position' attribute: {point}",
                            severity=ErrorSeverity.ERROR
                        )
                    )
                
                # Create a copy of the point
                machine_point = point.copy()
                
                # Store original position
                machine_point['original_position'] = point['position']
                
                # Apply offset to position
                machine_point['machine_position'] = self._apply_offset_to_coordinates(
                    point['position'], (offset_x, offset_y))
                
                machine_drill_points.append(machine_point)
            
            # Create updated workpiece with machine coordinates
            positioned_workpiece = workpiece.copy()
            positioned_workpiece['machine_corner_points'] = machine_corner_points
            positioned_workpiece['original_corner_points'] = original_corner_points
            positioned_workpiece['machine_offset'] = (offset_x, offset_y)
            
            # Round offset values for display
            rounded_offset_x = round(offset_x, 1)
            rounded_offset_y = round(offset_y, 1)
            
            # Create success message
            success_msg = (f"Positioned workpiece with offset ({rounded_offset_x}, {rounded_offset_y}) "
                           f"and transformed {len(machine_drill_points)} drill points")
                
            # Return comprehensive results
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    'workpiece': positioned_workpiece,
                    'drill_points': machine_drill_points,
                    'original_corner_points': original_corner_points,
                    'machine_corner_points': machine_corner_points,
                    'offset': (offset_x, offset_y)
                }
            )
                
        except Exception as e:
            # Log and return error
            self.logger.error(f"Error in workpiece positioning: {str(e)}")
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Failed to position workpiece: {str(e)}",
                    severity=ErrorSeverity.ERROR
                )
            )
    
    def _validate_workpiece_data(self, workpiece: Dict) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate workpiece data for positioning.
        
        Args:
            workpiece: Workpiece dictionary to validate
            
        Returns:
            Tuple of (success, message, details) with validation result
        """
        # Check if workpiece data exists
        if not workpiece:
            return ErrorHandler.from_exception(
                ValidationError(
                    message="Missing workpiece data",
                    severity=ErrorSeverity.ERROR
                )
            )
        
        # Check if corner points exist
        if 'corner_points' not in workpiece:
            return ErrorHandler.from_exception(
                ValidationError(
                    message="Workpiece missing 'corner_points' attribute",
                    severity=ErrorSeverity.ERROR
                )
            )
        
        # Validation passed
        return True, "Workpiece data valid", {}
        
    def _determine_offset(self, x_c: float, y_c: float) -> Tuple[float, float]:
        """
        Calculate the offset needed to position workpiece with top-left corner at machine origin.
        
        Given point C (the corner opposite to origin), we can determine:
        - If x_c is negative, we need to shift right by |x_c|
        - If y_c is positive, we need to shift down by |y_c|
        
        Args:
            x_c: X coordinate of point C (corner opposite to origin)
            y_c: Y coordinate of point C (corner opposite to origin)
            
        Returns:
            Tuple of (offset_x, offset_y) to apply to all coordinates
        """
        self.logger.debug(f"Determining offset for point C at ({x_c}, {y_c})")
        
        # Calculate x offset - if point C is to the left of origin, shift right
        offset_x = -x_c if x_c < 0 else 0
        
        # Calculate y offset - if point C is above origin, shift down
        offset_y = -y_c if y_c > 0 else 0
        
        self.logger.debug(f"Calculated offset: ({offset_x}, {offset_y})")
        return (offset_x, offset_y)
    
    def _apply_offset_to_coordinates(self, 
                                    coordinates: Tuple[float, float, float], 
                                    offset: Tuple[float, float]) -> Tuple[float, float, float]:
        """
        Apply offset to a single 3D coordinate.
        
        Args:
            coordinates: (x, y, z) coordinates to offset
            offset: (offset_x, offset_y) to apply
            
        Returns:
            (new_x, new_y, z) with offset applied
        """
        x, y, z = coordinates
        offset_x, offset_y = offset
        
        # Round to 0.1mm for consistency with other modules
        new_x = round(x + offset_x, 1)
        new_y = round(y + offset_y, 1)
        
        return (new_x, new_y, z)
    
    def get_orientation_name(self, point_c: Tuple[float, float, float]) -> str:
        """
        Get the orientation name based on point C's position.
        
        Args:
            point_c: Point C coordinates (x, y, z)
            
        Returns:
            String describing the orientation
        """
        x_c, y_c, _ = point_c
        
        if x_c > 0 and y_c > 0:
            return "bottom-left"
        elif x_c < 0 and y_c > 0:
            return "bottom-right"
        elif x_c < 0 and y_c < 0:
            return "top-right"
        elif x_c > 0 and y_c < 0:
            return "top-left"
        else:
            return "unknown"
    
    # Placeholder methods for other positioning strategies (not implemented in MVP)
    def position_for_bottom_left_machine(self, data: Dict) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Position workpiece with bottom-left corner at machine origin.
        
        Note: Not implemented in MVP.
        """
        self.logger.warning("position_for_bottom_left_machine not implemented in MVP")
        return ErrorHandler.from_exception(
            ValidationError(
                message="position_for_bottom_left_machine not implemented in MVP",
                severity=ErrorSeverity.ERROR
            )
        )
    
    def position_for_top_right_machine(self, data: Dict) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Position workpiece with top-right corner at machine origin.
        
        Note: Not implemented in MVP.
        """
        self.logger.warning("position_for_top_right_machine not implemented in MVP")
        return ErrorHandler.from_exception(
            ValidationError(
                message="position_for_top_right_machine not implemented in MVP",
                severity=ErrorSeverity.ERROR
            )
        )
    
    def position_for_bottom_right_machine(self, data: Dict) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Position workpiece with bottom-right corner at machine origin.
        
        Note: Not implemented in MVP.
        """
        self.logger.warning("position_for_bottom_right_machine not implemented in MVP")
        return ErrorHandler.from_exception(
            ValidationError(
                message="position_for_bottom_right_machine not implemented in MVP",
                severity=ErrorSeverity.ERROR
            )
        )


# Example usage if run directly
if __name__ == "__main__":
    # Create test data - after rotation is applied
    test_workpiece = {
        'width': 500,
        'height': 300,
        'thickness': 20,
        'corner_points': [
            (0, 0, 0),           # Origin
            (0, 300, 0),         # Rotated Width edge
            (500, 300, 0),       # Rotated Point C (opposite corner)
            (500, 0, 0)          # Rotated Height edge
        ]
    }
    
    test_drill_points = [
        {
            'position': (50, 100, 0),
            'extrusion_vector': (0, 0, 1),
            'diameter': 8.0
        },
        {
            'position': (200, 400, 0),
            'extrusion_vector': (1, 0, 0),
            'diameter': 10.0
        }
    ]
    
    test_data = {
        'workpiece': test_workpiece,
        'drill_points': test_drill_points
    }
    
    # Create positioner and transform data
    positioner = MachinePositioner()
    success, message, result = positioner.position_for_top_left_machine(test_data)
    
    # Print results
    print(f"Positioning: {'Success' if success else 'Failed'}")
    print(f"Message: {message}")
    
    if success:
        print("\nWorkpiece Offsets:")
        print(f"Offset: {result['offset']}")
        
        print("\nOriginal Corner Points:")
        for i, point in enumerate(result['original_corner_points']):
            print(f"Corner {i}: {point}")
        
        print("\nMachine Corner Points:")
        for i, point in enumerate(result['machine_corner_points']):
            print(f"Corner {i}: {point}")
        
        print("\nDrill Points (Original → Machine):")
        for i, point in enumerate(result['drill_points']):
            original = point.get('original_position', 'Unknown')
            machine = point.get('machine_position', 'Unknown')
            print(f"Point {i+1}: {original} → {machine}")