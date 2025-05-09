"""
Module for workpiece positioning operations.

This module provides functionality for positioning a workpiece in various
locations in the machine coordinate system after transformation and rotation.

Key features:
- Position workpieces in different corners of the machine (top-left, top-right, etc.)
- Apply appropriate offsets to all drilling points
- Account for current orientation when calculating offsets
"""

from typing import List, Dict, Tuple, Optional, Any, Union
import math

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception
from Utils.error_utils import ErrorHandler, BaseError, ValidationError, ErrorSeverity, ErrorCategory

# Set up logger
logger = setup_logger(__name__)


class BasePositioner:
    """
    Base class for workpiece positioning operations.
    
    This serves as the common interface and provides functionality shared
    by all position-specific implementations.
    """
    
    def __init__(self, workpiece_width: float, workpiece_height: float, current_orientation: str):
        """
        Initialize the base positioner.
        
        Args:
            workpiece_width: Current width of the workpiece after any rotations (mm)
            workpiece_height: Current height of the workpiece after any rotations (mm)
            current_orientation: Current orientation of the workpiece based on point C
                                 ("bottom-left", "top-left", "top-right", "bottom-right")
        """
        self.workpiece_width = workpiece_width
        self.workpiece_height = workpiece_height
        self.current_orientation = current_orientation
        
        # Store the applied offset for reference
        self.applied_offset = (0.0, 0.0)
        
        # Target position (to be set by child classes)
        self.target_position = "unknown"
        
        logger.info(f"BasePositioner initialized with {workpiece_width}x{workpiece_height}mm workpiece, "
                   f"current orientation: {current_orientation}")
    
    def calculate_offset(self) -> Tuple[float, float]:
        """
        Calculate the offset needed to move workpiece to desired position.
        
        This is an abstract method to be implemented by child classes.
        
        Returns:
            Tuple of (x_offset, y_offset) in mm
        """
        raise NotImplementedError("This method must be implemented by child classes")
    
    def apply_offset(self, points: List[Any]) -> Tuple[bool, str, Dict]:
        """
        Apply the calculated offset to all points.
        
        Args:
            points: List of drilling point objects with machine_position attribute
            
        Returns:
            Tuple of (success, message, details)
        """
        if not points:
            warning_msg = "No points provided to apply offset"
            logger.warning(warning_msg)
            return ErrorHandler.create_success_response(
                message=warning_msg,
                data={
                    "points": [],
                    "offset": (0.0, 0.0),
                    "target_position": self.target_position
                }
            )
        
        try:
            # Calculate the offset based on current orientation and target position
            x_offset, y_offset = self.calculate_offset()
            self.applied_offset = (x_offset, y_offset)
            
            # Stats for tracking
            stats = {
                "total_points": len(points),
                "offset_applied": 0,
                "errors": 0
            }
            
            # Apply offset to each point
            for point in points:
                if hasattr(point, 'machine_position') and point.machine_position:
                    try:
                        # Extract original position
                        mx, my, mz = point.machine_position
                        
                        # Apply offset
                        new_position = (mx + x_offset, my + y_offset, mz)
                        
                        # Update position
                        point.machine_position = new_position
                        
                        # Add a record of the applied offset
                        if not hasattr(point, 'applied_offsets'):
                            point.applied_offsets = []
                        point.applied_offsets.append({
                            'offset': (x_offset, y_offset),
                            'target_position': self.target_position
                        })
                        
                        # Update stats
                        stats["offset_applied"] += 1
                    except Exception as e:
                        logger.warning(f"Error applying offset to point: {str(e)}")
                        stats["errors"] += 1
                else:
                    logger.warning(f"Point has no machine_position attribute, skipping offset application")
                    stats["errors"] += 1
            
            success_msg = f"Applied offset ({x_offset:.1f}, {y_offset:.1f}) to {stats['offset_applied']} points"
            if stats["errors"] > 0:
                success_msg += f" ({stats['errors']} errors)"
                
            logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "points": points,
                    "offset": (x_offset, y_offset),
                    "target_position": self.target_position,
                    "original_orientation": self.current_orientation,
                    "stats": stats
                }
            )
            
        except Exception as e:
            error_msg = f"Error applying offset to points: {str(e)}"
            log_exception(logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "points_count": len(points)
                    }
                )
            )


class TopLeftPositioner(BasePositioner):
    """
    Positions the workpiece in the top-left corner of the machine coordinate system.
    
    This is the primary implementation for the MVP.
    """
    
    def __init__(self, workpiece_width: float, workpiece_height: float, current_orientation: str):
        """Initialize the top-left positioner."""
        super().__init__(workpiece_width, workpiece_height, current_orientation)
        self.target_position = "top-left"
        
        logger.info(f"TopLeftPositioner initialized, target position: top-left")
    
    def calculate_offset(self) -> Tuple[float, float]:
        """
        Calculate offset to move workpiece to top-left position.
        
        Based on the current orientation, calculate the offset needed to
        move the workpiece to the top-left corner of the machine.
        
        Returns:
            Tuple of (x_offset, y_offset) in mm
        """
        # Different offset calculations depending on current orientation
        if self.current_orientation == "top-left":
            # Already in top-left position, no offset needed
            return (0.0, 0.0)
            
        elif self.current_orientation == "top-right":
            # Move from top-right to top-left (shift left by width)
            return (-self.workpiece_width, 0.0)
            
        elif self.current_orientation == "bottom-left":
            # Move from bottom-left to top-left (shift up by height)
            return (0.0, -self.workpiece_height)
            
        elif self.current_orientation == "bottom-right":
            # Move from bottom-right to top-left (shift left and up)
            return (-self.workpiece_width, -self.workpiece_height)
            
        else:
            logger.warning(f"Unknown orientation: {self.current_orientation}, using zero offset")
            return (0.0, 0.0)


class TopRightPositioner(BasePositioner):
    """
    Positions the workpiece in the top-right corner of the machine coordinate system.
    
    This is a placeholder implementation for future enhancement.
    """
    
    def __init__(self, workpiece_width: float, workpiece_height: float, current_orientation: str):
        """Initialize the top-right positioner."""
        super().__init__(workpiece_width, workpiece_height, current_orientation)
        self.target_position = "top-right"
        
        logger.info(f"TopRightPositioner initialized, target position: top-right")
    
    def calculate_offset(self) -> Tuple[float, float]:
        """
        Calculate offset to move workpiece to top-right position.
        
        Placeholder implementation with basic functionality.
        
        Returns:
            Tuple of (x_offset, y_offset) in mm
        """
        # Different offset calculations depending on current orientation
        if self.current_orientation == "top-right":
            # Already in top-right position, no offset needed
            return (0.0, 0.0)
            
        elif self.current_orientation == "top-left":
            # Move from top-left to top-right (shift right by width)
            return (self.workpiece_width, 0.0)
            
        elif self.current_orientation == "bottom-right":
            # Move from bottom-right to top-right (shift up by height)
            return (0.0, -self.workpiece_height)
            
        elif self.current_orientation == "bottom-left":
            # Move from bottom-left to top-right (shift right and up)
            return (self.workpiece_width, -self.workpiece_height)
            
        else:
            logger.warning(f"Unknown orientation: {self.current_orientation}, using zero offset")
            return (0.0, 0.0)


class BottomLeftPositioner(BasePositioner):
    """
    Positions the workpiece in the bottom-left corner of the machine coordinate system.
    
    This is a placeholder implementation for future enhancement.
    """
    
    def __init__(self, workpiece_width: float, workpiece_height: float, current_orientation: str):
        """Initialize the bottom-left positioner."""
        super().__init__(workpiece_width, workpiece_height, current_orientation)
        self.target_position = "bottom-left"
        
        logger.info(f"BottomLeftPositioner initialized, target position: bottom-left")
    
    def calculate_offset(self) -> Tuple[float, float]:
        """
        Calculate offset to move workpiece to bottom-left position.
        
        Placeholder implementation with basic functionality.
        
        Returns:
            Tuple of (x_offset, y_offset) in mm
        """
        # Different offset calculations depending on current orientation
        if self.current_orientation == "bottom-left":
            # Already in bottom-left position, no offset needed
            return (0.0, 0.0)
            
        elif self.current_orientation == "bottom-right":
            # Move from bottom-right to bottom-left (shift left by width)
            return (-self.workpiece_width, 0.0)
            
        elif self.current_orientation == "top-left":
            # Move from top-left to bottom-left (shift down by height)
            return (0.0, self.workpiece_height)
            
        elif self.current_orientation == "top-right":
            # Move from top-right to bottom-left (shift left and down)
            return (-self.workpiece_width, self.workpiece_height)
            
        else:
            logger.warning(f"Unknown orientation: {self.current_orientation}, using zero offset")
            return (0.0, 0.0)


class BottomRightPositioner(BasePositioner):
    """
    Positions the workpiece in the bottom-right corner of the machine coordinate system.
    
    This is a placeholder implementation for future enhancement.
    """
    
    def __init__(self, workpiece_width: float, workpiece_height: float, current_orientation: str):
        """Initialize the bottom-right positioner."""
        super().__init__(workpiece_width, workpiece_height, current_orientation)
        self.target_position = "bottom-right"
        
        logger.info(f"BottomRightPositioner initialized, target position: bottom-right")
    
    def calculate_offset(self) -> Tuple[float, float]:
        """
        Calculate offset to move workpiece to bottom-right position.
        
        Placeholder implementation with basic functionality.
        
        Returns:
            Tuple of (x_offset, y_offset) in mm
        """
        # Different offset calculations depending on current orientation
        if self.current_orientation == "bottom-right":
            # Already in bottom-right position, no offset needed
            return (0.0, 0.0)
            
        elif self.current_orientation == "bottom-left":
            # Move from bottom-left to bottom-right (shift right by width)
            return (self.workpiece_width, 0.0)
            
        elif self.current_orientation == "top-right":
            # Move from top-right to bottom-right (shift down by height)
            return (0.0, self.workpiece_height)
            
        elif self.current_orientation == "top-left":
            # Move from top-left to bottom-right (shift right and down)
            return (self.workpiece_width, self.workpiece_height)
            
        else:
            logger.warning(f"Unknown orientation: {self.current_orientation}, using zero offset")
            return (0.0, 0.0)


def create_positioner(target_position: str, workpiece_width: float, workpiece_height: float, 
                     current_orientation: str) -> BasePositioner:
    """
    Factory function to create the appropriate positioner based on target position.
    
    Args:
        target_position: Desired position ("top-left", "top-right", "bottom-left", "bottom-right")
        workpiece_width: Current width of the workpiece after any rotations (mm)
        workpiece_height: Current height of the workpiece after any rotations (mm)
        current_orientation: Current orientation of the workpiece based on point C
                            ("bottom-left", "top-left", "top-right", "bottom-right")
        
    Returns:
        An instance of the appropriate positioner
    """
    if target_position == "top-left":
        return TopLeftPositioner(workpiece_width, workpiece_height, current_orientation)
    elif target_position == "top-right":
        return TopRightPositioner(workpiece_width, workpiece_height, current_orientation)
    elif target_position == "bottom-left":
        return BottomLeftPositioner(workpiece_width, workpiece_height, current_orientation)
    elif target_position == "bottom-right":
        return BottomRightPositioner(workpiece_width, workpiece_height, current_orientation)
    else:
        logger.warning(f"Unknown target position: {target_position}, defaulting to top-left")
        return TopLeftPositioner(workpiece_width, workpiece_height, current_orientation)


# Example usage if run directly
if __name__ == "__main__":
    # Create a simple test
    class TestPoint:
        def __init__(self, machine_position):
            self.machine_position = machine_position
    
    # Create test points
    points = [
        TestPoint((0.0, 0.0, 20.0)),    # Origin
        TestPoint((100.0, 0.0, 20.0)),  # Right edge
        TestPoint((0.0, 200.0, 20.0)),  # Top edge
        TestPoint((100.0, 200.0, 20.0)) # Top-right corner
    ]
    
    # Test positioning from bottom-left to top-left
    positioner = create_positioner("top-left", 100.0, 200.0, "bottom-left")
    success, message, details = positioner.apply_offset(points)
    
    print(f"Positioning result: {message}")
    print(f"Applied offset: {details.get('offset')}")
    
    # Print original and new positions
    for i, point in enumerate(points):
        print(f"Point {i+1}: {point.machine_position}")