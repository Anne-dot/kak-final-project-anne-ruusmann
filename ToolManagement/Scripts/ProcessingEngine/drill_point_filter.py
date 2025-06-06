"""
Drill point filtering module for MVP limitations.

This module filters drill points based on current machine capabilities,
specifically filtering out vertical drilling operations for the MVP.
"""

import os
import sys
from typing import Any

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Utils.error_utils import ErrorHandler
from Utils.logging_utils import setup_logger


class DrillPointFilter:
    """
    Filters drill points based on machine capabilities and MVP limitations.
    
    MVP: Only horizontal drilling is supported (X+, X-, Y+, Y- directions).
    Vertical drilling (Z+ direction) is filtered out.
    """
    
    def __init__(self):
        """Initialize the drill point filter."""
        self.logger = setup_logger(__name__)
        self.logger.info("DrillPointFilter initialized")
        
    def filter_for_horizontal_drilling(self, data: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """
        Filter drill points to include only horizontal drilling operations.
        
        Removes all drill points with vertical extrusion vectors (0.0, 0.0, 1.0).
        
        Args:
            data: Dictionary containing 'drill_points' list
            
        Returns:
            tuple: (success, message, data) where data includes:
                - All original data
                - Filtered drill_points (horizontal only)
                - Statistics about filtering
        """
        try:
            # Validate input
            if not data or "drill_points" not in data:
                return ErrorHandler.create_success_response(
                    "No drill points to filter",
                    data
                )
            
            original_points = data["drill_points"]
            if not original_points:
                return ErrorHandler.create_success_response(
                    "Empty drill points list",
                    data
                )
            
            # Filter points
            horizontal_points = []
            vertical_points = []
            
            for point in original_points:
                # Get extrusion vector
                extrusion_vector = point.get("extrusion_vector")
                
                if not extrusion_vector:
                    self.logger.warning(f"Point missing extrusion_vector: {point}")
                    continue
                
                # Check if vertical (Z+ direction)
                if extrusion_vector == (0.0, 0.0, 1.0):
                    vertical_points.append(point)
                else:
                    horizontal_points.append(point)
            
            # Log filtering results
            self.logger.info(
                f"Filtered drill points: {len(horizontal_points)} horizontal, "
                f"{len(vertical_points)} vertical (removed)"
            )
            
            # Create result data
            result_data = data.copy()
            result_data["drill_points"] = horizontal_points
            
            # Add filtering statistics
            result_data["filtering_stats"] = {
                "original_count": len(original_points),
                "horizontal_count": len(horizontal_points),
                "vertical_count": len(vertical_points),
                "vertical_removed": len(vertical_points) > 0
            }
            
            # Success message
            if vertical_points:
                message = (
                    f"Filtered {len(vertical_points)} vertical drilling points. "
                    f"Keeping {len(horizontal_points)} horizontal points."
                )
            else:
                message = f"All {len(horizontal_points)} points are horizontal drilling."
            
            return ErrorHandler.create_success_response(message, result_data)
            
        except Exception as e:
            self.logger.error(f"Error filtering drill points: {str(e)}")
            return ErrorHandler.from_exception(e)


# Example usage
if __name__ == "__main__":
    # Test data with mixed drilling directions
    # Rectangle workpiece: 600x400mm
    # Horizontal drilling is into edges at specific Z heights
    test_data = {
        "workpiece": {"width": 600, "height": 400, "thickness": 22},
        "drill_points": [
            # X+ drilling from left edge (X=0)
            {"position": (0, 200, 9), "extrusion_vector": (1.0, 0.0, 0.0), "diameter": 8.0},
            
            # Z+ vertical drilling from top (should be filtered)
            {"position": (150, 250, 22), "extrusion_vector": (0.0, 0.0, 1.0), "diameter": 5.0},
            
            # X- drilling from right edge (X=600)
            {"position": (600, 300, 12), "extrusion_vector": (-1.0, 0.0, 0.0), "diameter": 8.0},
            
            # Y+ drilling from front edge (Y=0)
            {"position": (300, 0, 10), "extrusion_vector": (0.0, 1.0, 0.0), "diameter": 8.0},
            
            # Another vertical drilling (should be filtered)
            {"position": (450, 150, 22), "extrusion_vector": (0.0, 0.0, 1.0), "diameter": 5.0},
        ]
    }
    
    filter = DrillPointFilter()
    success, message, result = filter.filter_for_horizontal_drilling(test_data)
    
    print(f"Success: {success}")
    print(f"Message: {message}")
    print(f"Stats: {result.get('filtering_stats')}")
    print(f"Remaining points: {len(result['drill_points'])}")
    print("\nRemaining drill points:")
    for point in result['drill_points']:
        print(f"  Position: {point['position']}, Vector: {point['extrusion_vector']}")