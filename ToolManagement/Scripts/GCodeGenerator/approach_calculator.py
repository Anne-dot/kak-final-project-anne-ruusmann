"""
Approach position calculator for drilling operations.

This module calculates safe approach positions based on drill location
and direction to ensure the tool starts outside the workpiece.
"""

import os
import sys
from typing import Any

# Add parent directory to Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import utilities
from Utils.error_utils import ErrorHandler, ErrorSeverity, ValidationError
from Utils.logging_utils import setup_logger

# Import local modules
from GCodeGenerator.machine_settings import MachineSettings


class ApproachCalculator:
    """
    Calculator for determining safe approach positions for drilling.
    
    Calculates the position where the drill should start, ensuring it's
    outside the workpiece by the approach distance.
    """

    def __init__(self, machine_settings: MachineSettings | None = None):
        """
        Initialize the approach calculator.
        
        Args:
            machine_settings: Optional MachineSettings instance
        """
        self.logger = setup_logger(__name__)
        self.machine_settings = machine_settings or MachineSettings()
        
        self.logger.info("ApproachCalculator initialized")

    def calculate_approach_position(
        self, 
        machine_position: tuple[float, float, float], 
        extrusion_vector: tuple[float, float, float]
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Calculate approach position for safe drilling start.
        
        For edge drilling, approach is always OUTSIDE the workpiece:
        - X+ drilling (from left): approach X = X - approach_distance
        - X- drilling (from right): approach X = X + approach_distance  
        - Y+ drilling (from front): approach Y = Y - approach_distance
        - Y- drilling (from back): approach Y = Y + approach_distance
        
        Args:
            machine_position: (x, y, z) drill point position
            extrusion_vector: (x, y, z) drilling direction vector
            
        Returns:
            tuple: (success, message, details) with approach position
        """
        try:
            x, y, z = machine_position
            approach_distance = self.machine_settings.get_approach_distance()
            
            # Calculate based on direction
            if extrusion_vector == (1.0, 0.0, 0.0):    # X+
                approach_pos = (x - approach_distance, y)
            elif extrusion_vector == (-1.0, 0.0, 0.0): # X-
                approach_pos = (x + approach_distance, y)
            elif extrusion_vector == (0.0, 1.0, 0.0):  # Y+
                approach_pos = (x, y - approach_distance)
            elif extrusion_vector == (0.0, -1.0, 0.0): # Y-
                approach_pos = (x, y + approach_distance)
            else:
                # Fail explicitly - user needs to know during MVP testing
                return ErrorHandler.from_exception(
                    ValidationError(
                        f"Unsupported drilling direction: {extrusion_vector}",
                        severity=ErrorSeverity.ERROR
                    )
                )
            
            self.logger.debug(
                f"Calculated approach position {approach_pos} for drill at {machine_position}"
            )
            
            return ErrorHandler.create_success_response(
                "Approach position calculated",
                {"position": approach_pos}
            )
            
        except Exception as e:
            return ErrorHandler.from_exception(e)


# Example usage if run directly
if __name__ == "__main__":
    calculator = ApproachCalculator()
    
    # Test cases with realistic positions
    test_cases = [
        # X+ drilling from left edge
        ((0, -200, 9), (1.0, 0.0, 0.0)),
        # X- drilling from right edge  
        ((600, -200, 9), (-1.0, 0.0, 0.0)),
        # Y+ drilling from front edge
        ((300, -400, 9), (0.0, 1.0, 0.0)),
        # Y- drilling from back edge
        ((300, 0, 9), (0.0, -1.0, 0.0))
    ]
    
    print("Testing Approach Calculator")
    print("=" * 50)
    
    for position, direction in test_cases:
        print(f"\nDrill position: {position}")
        print(f"Direction: {direction}")
        
        success, message, result = calculator.calculate_approach_position(position, direction)
        
        if success:
            print(f"Approach position: {result['position']}")
        else:
            print(f"Error: {message}")