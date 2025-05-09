"""
Module for workpiece rotation operations.

This module provides functionality for rotating workpieces and their associated drilling
coordinates. It supports both automatic rotation (when dimensions exceed machine limits)
and manual rotation capabilities.

Key features:
- Rotate workpiece dimensions (swapping width/height)
- Rotate machine coordinates for drilling points
- Track rotation state
- Support 90° clockwise rotation increments
"""

from typing import List, Dict, Tuple, Optional, Any, Union
import math

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception
from Utils.error_utils import ErrorHandler, BaseError, ValidationError, ErrorSeverity, ErrorCategory

# Set up logger
logger = setup_logger(__name__)


class WorkpieceRotator:
    """
    Class for handling workpiece rotation operations.
    
    This class provides functionality to rotate a workpiece and its associated
    drilling points. It supports 90-degree clockwise rotations and tracks
    the current rotation state.
    """
    
    def __init__(self):
        """Initialize the workpiece rotator."""
        # Workpiece dimensions
        self.original_width = 0.0
        self.original_height = 0.0
        self.original_thickness = 0.0
        
        self.current_width = 0.0
        self.current_height = 0.0
        self.current_thickness = 0.0
        
        # Rotation tracking
        self.rotation_count = 0
        
        # Maximum height before automatic rotation (mm)
        self.max_height_threshold = 800.0
        
        # Corner tracking
        # Point A is always at (0,0) and is the fixed origin point
        # Point C is the opposite corner and is tracked through rotations
        # Based on C's coordinates, we can determine the workpiece orientation
        self.point_c = (10000.0, 12000.0)  # Placeholder value, will be set when dimensions are defined
        
        # We can determine orientation based on point C's coordinates:
        # - If C is (width, height) → orientation is bottom-left
        # - If C is (height, -width) → orientation is top-left
        # - If C is (-width, -height) → orientation is top-right
        # - If C is (-height, width) → orientation is bottom-right
        
        logger.info("WorkpieceRotator initialized")
    
    def set_dimensions(self, width: float, height: float, thickness: float) -> Tuple[bool, str, Dict]:
        """
        Set workpiece dimensions.
        
        Args:
            width: Workpiece width in mm
            height: Workpiece height in mm
            thickness: Workpiece thickness in mm
            
        Returns:
            Tuple of (success, message, details)
        """
        # Validate dimensions
        if width <= 0 or height <= 0 or thickness <= 0:
            error_msg = "Invalid workpiece dimensions (must be positive)"
            logger.error(error_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={
                        "error": "invalid_dimensions",
                        "width": width,
                        "height": height,
                        "thickness": thickness
                    }
                )
            )
        
        # Set original dimensions
        self.original_width = width
        self.original_height = height
        self.original_thickness = thickness
        
        # Set current dimensions (initially same as original)
        self.current_width = width
        self.current_height = height
        self.current_thickness = thickness
        
        # Reset rotation tracking
        self.rotation_count = 0
        
        # Initialize corner points
        self._initialize_corner_points(width, height)
        
        success_msg = f"Dimensions set: {width}x{height}x{thickness}mm"
        logger.info(success_msg)
        
        return ErrorHandler.create_success_response(
            message=success_msg,
            data={
                "width": width,
                "height": height,
                "thickness": thickness,
                "rotation": 0,
                "point_c": self.point_c,
                "orientation": self.get_orientation()
            }
        )
    
    def _initialize_corner_points(self, width: float, height: float) -> None:
        """
        Initialize point C based on current dimensions.
        
        Point C is the corner opposite to the origin (0,0) and is used to 
        determine the orientation of the workpiece after rotation.
        
        Args:
            width: Workpiece width in mm
            height: Workpiece height in mm
        """
        # Initialize point C at the top-right corner (opposite to origin)
        self.point_c = (width, height)
        
        # When point C has positive coordinates, we're in bottom-left orientation
        # This is the default/initial orientation
        
        logger.info(f"Point C initialized at: {self.point_c}")
                   
    def _rotate_point_c(self) -> None:
        """
        Rotate point C based on current rotation angle.
        
        This updates point C's coordinates and is used to determine
        the orientation of the workpiece after rotation.
        """
        # Get current point C coordinates
        cx, cy = self.point_c
        
        # For 90° clockwise rotation: (x,y) → (y,-x)
        self.point_c = (cy, -cx)
        
        logger.info(f"Point C rotated to: {self.point_c}")
        logger.info(f"Orientation after rotation: {self.get_orientation()}")
    
    def get_orientation(self) -> str:
        """
        Determine the orientation based on point C's coordinates.
        
        Orientation mapping based on point C position:
        - If C is (width, height) → orientation is bottom-left
        - If C is (height, -width) → orientation is top-left
        - If C is (-width, -height) → orientation is top-right
        - If C is (-height, width) → orientation is bottom-right
        
        Returns:
            Orientation as string: 'bottom-left', 'top-left', 'top-right', or 'bottom-right'
        """
        cx, cy = self.point_c
        
        # Determine orientation based on point C's quadrant
        if cx > 0 and cy > 0:
            return "bottom-left"
        elif cx > 0 and cy < 0:
            return "top-left"
        elif cx < 0 and cy < 0:
            return "top-right"
        elif cx < 0 and cy > 0:
            return "bottom-right"
        else:
            logger.warning(f"Unexpected point C coordinates: {self.point_c}")
            return "unknown"
    
    def set_from_workpiece_info(self, workpiece_info: Dict) -> Tuple[bool, str, Dict]:
        """
        Set dimensions from workpiece info dictionary.
        
        Args:
            workpiece_info: Dictionary with workpiece information
            
        Returns:
            Tuple of (success, message, details)
        """
        if not workpiece_info:
            error_msg = "No workpiece information provided"
            logger.error(error_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={"error": "missing_workpiece_info"}
                )
            )
        
        try:
            # Extract dimensions
            dimensions = workpiece_info.get('dimensions', {})
            
            if not dimensions:
                error_msg = "Missing dimensions in workpiece info"
                logger.error(error_msg)
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=error_msg,
                        severity=ErrorSeverity.ERROR,
                        details={"error": "missing_dimensions"}
                    )
                )
            
            width = dimensions.get('width', 0.0)
            height = dimensions.get('height', 0.0)
            thickness = dimensions.get('depth', 0.0) or dimensions.get('thickness', 0.0)
            
            return self.set_dimensions(width, height, thickness)
            
        except Exception as e:
            error_msg = f"Error setting parameters from workpiece info: {str(e)}"
            log_exception(logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def rotate_90_clockwise(self) -> Tuple[bool, str, Dict]:
        """
        Rotate the workpiece 90 degrees clockwise.
        
        This rotates the workpiece by swapping width and height and updates point C.
        
        Returns:
            Tuple of (success, message, details)
        """
        try:
            # Swap width and height for 90° rotation
            self.current_width, self.current_height = self.current_height, self.current_width
            
            # Increment rotation counter
            self.rotation_count = (self.rotation_count + 1) % 4
            
            # Rotate point C to track orientation
            self._rotate_point_c()
            
            # Get current rotation angle
            angle = self.get_rotation_angle()
            
            # Get current orientation based on point C
            orientation = self.get_orientation()
            
            success_msg = f"Rotated 90° clockwise (total: {angle}°)"
            logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "width": self.current_width,
                    "height": self.current_height,
                    "thickness": self.current_thickness,
                    "rotation_count": self.rotation_count,
                    "rotation_angle": angle,
                    "point_c": self.point_c,
                    "orientation": orientation
                }
            )
            
        except Exception as e:
            error_msg = f"Error during rotation: {str(e)}"
            log_exception(logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def rotate_point(self, point: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Rotate a 3D point by the current rotation angle.
        
        Args:
            point: (x, y, z) coordinates to rotate
            
        Returns:
            Rotated (x, y, z) coordinates
        """
        x, y, z = point
        angle = self.get_rotation_angle()
        
        # Apply rotation based on current angle
        if angle == 0:
            return (x, y, z)  # No rotation
        elif angle == 90:
            return (y, -x, z)  # 90° clockwise
        elif angle == 180:
            return (-x, -y, z)  # 180° rotation
        elif angle == 270:
            return (-y, x, z)  # 270° clockwise (90° counterclockwise)
        
        return (x, y, z)  # Default case (should not happen)
    
    def rotate_direction_vector(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Rotate a 3D direction vector by the current rotation angle.
        
        Args:
            vector: (vx, vy, vz) direction vector to rotate
            
        Returns:
            Rotated (vx, vy, vz) direction vector
        """
        vx, vy, vz = vector
        angle = self.get_rotation_angle()
        
        # For direction vectors, we need specific handling that preserves 
        # the relationship with the edge designations
        if angle == 0:
            return (vx, vy, vz)  # No rotation
        elif angle == 90:
            # For 90° rotation: (x,y) → (y,-x)
            return (vy, -vx, vz)
        elif angle == 180:
            # For 180° rotation: (x,y) → (-x,-y)
            return (-vx, -vy, vz)
        elif angle == 270:
            # For 270° rotation: (x,y) → (-y,x)
            return (-vy, vx, vz)
        
        return (vx, vy, vz)  # Default case
        
    def determine_edge_from_vector(self, vector: Tuple[float, float, float]) -> str:
        """
        Determine edge type from a direction vector.
        
        Args:
            vector: (vx, vy, vz) direction vector
            
        Returns:
            Edge type (LEFT, RIGHT, FRONT, BACK, VERTICAL, or UNKNOWN)
        """
        vx, vy, vz = vector
        
        # Simple classification based on dominant direction
        # This is a simplified version; real implementation might need more complex logic
        if abs(vz) > 0.9:  # Tolerance for numerical imprecision
            return "VERTICAL"
        elif abs(vx) > 0.9:
            return "RIGHT" if vx > 0 else "LEFT"
        elif abs(vy) > 0.9:
            return "FRONT" if vy > 0 else "BACK"
        else:
            return "UNKNOWN"
    
    def rotate_points(self, points: List[Any], position_attr: str = 'machine_position', 
                       update_edges: bool = True) -> Tuple[bool, str, Dict]:
        """
        Rotate a list of drilling points by the current rotation angle.
        
        Args:
            points: List of point objects with position attribute
            position_attr: Name of the position attribute to rotate (default: 'machine_position')
            update_edges: Whether to update edge attributes based on rotated direction vectors (default: True)
            
        Returns:
            Tuple of (success, message, details)
        """
        if not points:
            warning_msg = "No points to rotate"
            logger.warning(warning_msg)
            return ErrorHandler.create_success_response(
                message=warning_msg,
                data={
                    "points": [],
                    "angle": self.get_rotation_angle(),
                    "count": 0
                }
            )
        
        try:
            angle = self.get_rotation_angle()
            
            # Skip if no rotation needed
            if angle == 0:
                return ErrorHandler.create_success_response(
                    message="No rotation needed (current angle: 0°)",
                    data={
                        "points": points,
                        "angle": 0,
                        "count": len(points)
                    }
                )
            
            # Track rotation statistics
            stats = {
                "angle": angle,
                "count": len(points),
                "successful_rotations": 0,
                "edge_updates": 0,
                "errors": 0
            }
            
            # Rotate each point
            for point in points:
                try:
                    # Get position attribute (can be machine_position, position, etc.)
                    if hasattr(point, position_attr) and getattr(point, position_attr):
                        original_pos = getattr(point, position_attr)
                        
                        # Apply rotation to position
                        rotated_pos = self.rotate_point(original_pos)
                        
                        # Update position
                        setattr(point, position_attr, rotated_pos)
                        
                        # Update edge classification if requested and possible
                        if update_edges:
                            # Check if point has direction vector (extrusion_vector)
                            if hasattr(point, 'extrusion_vector') and getattr(point, 'extrusion_vector'):
                                original_vector = getattr(point, 'extrusion_vector')
                                
                                # Rotate the direction vector
                                rotated_vector = self.rotate_direction_vector(original_vector)
                                
                                # Update the direction vector
                                setattr(point, 'extrusion_vector', rotated_vector)
                                
                                # Determine new edge based on rotated vector
                                new_edge = self.determine_edge_from_vector(rotated_vector)
                                
                                # Store original edge if not already stored
                                if not hasattr(point, 'original_edge'):
                                    setattr(point, 'original_edge', getattr(point, 'edge', 'UNKNOWN'))
                                
                                # Update edge attribute
                                setattr(point, 'edge', new_edge)
                                
                                # Track statistics
                                stats["edge_updates"] += 1
                        
                        # Add flags to indicate rotation was applied
                        point.rotated = True
                        point.rotation_angle = angle
                        
                        # Update stats
                        stats["successful_rotations"] += 1
                    else:
                        stats["errors"] += 1
                except Exception as e:
                    logger.warning(f"Error rotating point: {str(e)}")
                    stats["errors"] += 1
                    continue
            
            success_msg = f"Rotated {stats['successful_rotations']} points by {angle}°"
            if update_edges:
                success_msg += f", updated {stats['edge_updates']} edge classifications"
            if stats["errors"] > 0:
                success_msg += f" ({stats['errors']} errors)"
                
            logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "points": points,
                    "stats": stats
                }
            )
            
        except Exception as e:
            error_msg = f"Error rotating points: {str(e)}"
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
    
    def reset_to_original(self) -> Tuple[bool, str, Dict]:
        """
        Reset to original position and dimensions.
        
        Returns:
            Tuple of (success, message, details)
        """
        try:
            # Reset dimensions to original
            self.current_width = self.original_width
            self.current_height = self.original_height
            
            # Reset rotation counter
            self.rotation_count = 0
            
            # Reset point C to initial position (top-right corner)
            self.point_c = (self.original_width, self.original_height)
            
            success_msg = "Reset to original position"
            logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "width": self.current_width,
                    "height": self.current_height,
                    "thickness": self.current_thickness,
                    "rotation_count": 0,
                    "rotation_angle": 0,
                    "point_c": self.point_c,
                    "orientation": self.get_orientation()
                }
            )
            
        except Exception as e:
            error_msg = f"Error during reset: {str(e)}"
            log_exception(logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def get_rotation_angle(self) -> int:
        """
        Get the current rotation angle in degrees.
        
        Returns:
            Rotation angle (0°, 90°, 180°, 270°)
        """
        return (self.rotation_count % 4) * 90
    
    def check_auto_rotation_needed(self) -> bool:
        """
        Check if automatic rotation is needed based on height threshold.
        
        Returns:
            bool: True if automatic rotation is needed, False otherwise
        """
        return self.current_height > self.max_height_threshold
    
    def apply_auto_rotation_if_needed(self) -> Tuple[bool, str, Dict]:
        """
        Apply automatic 90° rotation if height exceeds threshold.
        
        Returns:
            Tuple of (success, message, details)
        """
        if self.check_auto_rotation_needed():
            logger.info(f"Automatic rotation needed: Height {self.current_height}mm exceeds {self.max_height_threshold}mm threshold")
            logger.info(f"Before rotation: {self.current_width}mm x {self.current_height}mm")
            
            # Apply a 90° rotation to bring height below threshold
            rotation_result = self.rotate_90_clockwise()
            
            # Log the result
            if rotation_result[0]:  # If success
                logger.info(f"After rotation: {self.current_width}mm x {self.current_height}mm")
                
                # Add rotation_needed flag to the result data
                if isinstance(rotation_result[2], dict):
                    rotation_result[2]["rotation_needed"] = True
                
                return rotation_result
            else:
                return rotation_result
        else:
            logger.info(f"No automatic rotation needed. Height {self.current_height}mm below threshold {self.max_height_threshold}mm")
            return ErrorHandler.create_success_response(
                message="No automatic rotation needed",
                data={
                    "width": self.current_width,
                    "height": self.current_height,
                    "thickness": self.current_thickness,
                    "threshold": self.max_height_threshold,
                    "rotation_needed": False
                }
            )
    
    def get_current_dimensions(self) -> Dict:
        """
        Get current workpiece dimensions after rotation.
        
        Returns:
            Dict with current width, height, thickness
        """
        return {
            "width": self.current_width,
            "height": self.current_height,
            "thickness": self.current_thickness,
            "rotation_angle": self.get_rotation_angle()
        }


# Example usage if run directly
if __name__ == "__main__":
    rotator = WorkpieceRotator()
    
    # Set test dimensions
    success, message, details = rotator.set_dimensions(500, 900, 20)
    print(f"Set dimensions: {'Success' if success else 'Failed'}")
    print(f"Initial dimensions: {rotator.current_width}x{rotator.current_height}mm")
    
    # Check if auto rotation is needed
    if rotator.check_auto_rotation_needed():
        print(f"Auto rotation needed: Height {rotator.current_height}mm exceeds {rotator.max_height_threshold}mm threshold")
        
        # Apply auto rotation
        success, message, details = rotator.apply_auto_rotation_if_needed()
        print(f"Auto rotation: {message}")
        print(f"Rotated dimensions: {rotator.current_width}x{rotator.current_height}mm")
    
    # Test point rotation
    test_point = (100, 200, 10)
    rotated_point = rotator.rotate_point(test_point)
    print(f"Original point: {test_point}")
    print(f"Rotated point: {rotated_point}")
    
    # Reset to original
    success, message, details = rotator.reset_to_original()
    print(f"Reset: {message}")
    print(f"Final dimensions: {rotator.current_width}x{rotator.current_height}mm")