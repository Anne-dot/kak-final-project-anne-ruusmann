"""
Drill point grouper module for grouping drilling operations by properties.

This module provides functionality for organizing drill points into logical groups
based on diameter and direction to optimize machine operations.
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


class DrillPointGrouper:
    """
    Class for grouping drill points by common properties.
    
    This class provides functionality for organizing drill points into logical
    groups based on properties like diameter and drilling direction to optimize
    machine operations.
    """
    
    def __init__(self):
        """Initialize the drill point grouper."""
        self.logger = setup_logger(__name__)
        self.logger.info("DrillPointGrouper initialized")
    
    def group_drilling_points(self, data: Dict) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Group drill points by diameter and direction.
        
        Args:
            data: Dictionary with 'drill_points'
            
        Returns:
            Tuple of (success, message, data) with grouped drilling information
        """
        if not data or 'drill_points' not in data:
            return ErrorHandler.from_exception(
                ValidationError(
                    message="No drill points provided for grouping",
                    severity=ErrorSeverity.ERROR
                )
            )
        
        try:
            # Extract drill points
            drill_points = data['drill_points']
            
            # Check if drill points list is empty
            if not drill_points:
                return ErrorHandler.from_exception(
                    ValidationError(
                        message="Empty drill points list for grouping",
                        severity=ErrorSeverity.ERROR
                    )
                )
            
            # Create groups dictionary
            groups = {}
            
            # Group points by diameter and direction
            for point in drill_points:
                # Validate point has diameter
                if 'diameter' not in point:
                    return ErrorHandler.from_exception(
                        ValidationError(
                            message="Drill point missing diameter",
                            severity=ErrorSeverity.ERROR
                        )
                    )
                
                # Get direction (from extrusion_vector or direction)
                direction = point.get('extrusion_vector', point.get('direction'))
                if not direction:
                    return ErrorHandler.from_exception(
                        ValidationError(
                            message="Drill point missing direction vector",
                            severity=ErrorSeverity.ERROR
                        )
                    )
                
                # Create group key
                diameter = point['diameter']
                group_key = (diameter, direction)
                
                # Add to groups dictionary
                if group_key not in groups:
                    groups[group_key] = []
                
                # Add point to its group
                groups[group_key].append(point)
                
                # Add group_key to point for reference
                point['group_key'] = group_key
            
            # Add the groups to the result
            result = data.copy()
            result['grouped_points'] = groups
            
            # Return success
            return ErrorHandler.create_success_response(
                message=f"Grouped {len(drill_points)} drill points into {len(groups)} groups",
                data=result
            )
            
        except Exception as e:
            # Log and return error
            self.logger.error(f"Error grouping drill points: {str(e)}")
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Failed to group drill points: {str(e)}",
                    severity=ErrorSeverity.ERROR
                )
            )


# Example usage if run directly
if __name__ == "__main__":
    # Create test data
    test_drill_points = [
        {
            'position': (100, 50, 0),
            'extrusion_vector': (0, 0, 1),
            'diameter': 8.0
        },
        {
            'position': (200, 100, 0),
            'extrusion_vector': (0, 0, 1),
            'diameter': 8.0
        },
        {
            'position': (300, 150, 0),
            'extrusion_vector': (1, 0, 0),
            'diameter': 8.0
        },
        {
            'position': (400, 200, 0),
            'extrusion_vector': (1, 0, 0),
            'diameter': 10.0
        }
    ]
    
    test_data = {
        'drill_points': test_drill_points
    }
    
    # Create grouper and group points
    grouper = DrillPointGrouper()
    success, message, result = grouper.group_drilling_points(test_data)
    
    # Print results
    print(f"Grouping: {'Success' if success else 'Failed'}")
    print(f"Message: {message}")
    
    if success:
        groups = result['grouped_points']
        
        print("\nDrill Point Groups:")
        for (diameter, direction), points in groups.items():
            print(f"\nGroup: {diameter}mm, direction={direction}")
            print(f"Contains {len(points)} points:")
            
            for i, point in enumerate(points, 1):
                position = point['position']
                print(f"  {i}. Position: {position}")
            
        print("\nPoints with Group Keys:")
        for i, point in enumerate(result['drill_points'], 1):
            print(f"Point {i}: diameter={point['diameter']}, group_key={point['group_key']}")