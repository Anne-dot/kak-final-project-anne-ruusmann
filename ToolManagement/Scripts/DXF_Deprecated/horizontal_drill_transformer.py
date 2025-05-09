"""
Module for transforming horizontal drilling points from DXF to machine coordinates.

This module provides specialized functionality for transforming horizontal drilling
points from DXF file coordinates to CNC machine coordinates, focusing exclusively on
horizontal drilling operations.

Key features:
- Filters out vertical drilling points
- Transforms horizontal drilling points based on edge direction
- Provides detailed statistics on transformation results
"""

from typing import List, Dict, Tuple, Optional, Any, Union
import math

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception
from Utils.error_utils import ErrorHandler, BaseError, ValidationError, ErrorSeverity, ErrorCategory

# Import workpiece rotator and positioner
from DXF.workpiece_rotator import WorkpieceRotator
from DXF.workpiece_positioner import create_positioner

# Set up logger
logger = setup_logger(__name__)


class HorizontalDrillTransformer:
    """
    Class for transforming horizontal drilling points from DXF to machine coordinates.
    
    This class focuses exclusively on horizontal drilling operations, filtering out
    vertical drilling points and transforming horizontal points based on their edge.
    It also supports rotation of the workpiece and transformed coordinates.
    """
    
    def __init__(self, auto_rotation_enabled=True, target_position="top-left"):
        """
        Initialize the horizontal drill transformer.
        
        Args:
            auto_rotation_enabled: Whether automatic rotation is enabled (default: True)
            target_position: Target position for the workpiece (default: "top-left")
        """
        # Workpiece dimensions
        self.width = 0.0
        self.height = 0.0
        self.thickness = 0.0
        
        # Workpiece boundaries for reference
        self.min_x = 0.0
        self.min_y = 0.0
        self.max_x = 0.0
        self.max_y = 0.0
        
        # Rounding precision for output coordinates
        self.precision = 1  # Round to 1 decimal place
        
        # Edge to direction code mapping
        self.edge_to_direction = {
            "FRONT": 3,  # Y+
            "BACK": 4,   # Y-
            "LEFT": 2,   # X-
            "RIGHT": 1   # X+
        }
        
        # Initialize workpiece rotator
        self.rotator = WorkpieceRotator()
        
        # Rotation flag (enable/disable automatic rotation)
        self.auto_rotation_enabled = auto_rotation_enabled
        
        # Target position for workpiece
        self.target_position = target_position
        
        logger.info(f"HorizontalDrillTransformer initialized (auto_rotation_enabled={auto_rotation_enabled}, "
                   f"target_position={target_position})")
    
    def set_workpiece_parameters(self, width: float, height: float, thickness: float,
                                min_x: float = 0.0, min_y: float = 0.0) -> Tuple[bool, str, Dict]:
        """
        Set workpiece parameters for coordinate transformation.
        
        Args:
            width: Workpiece width in mm
            height: Workpiece height in mm
            thickness: Workpiece thickness in mm
            min_x: Minimum X coordinate of workpiece (default: 0.0)
            min_y: Minimum Y coordinate of workpiece (default: 0.0)
            
        Returns:
            Tuple of (success, message, details)
        """
        # Validate parameters
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
        
        # Set workpiece parameters
        self.width = width
        self.height = height
        self.thickness = thickness
        
        # Set bounding box
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = min_x + width
        self.max_y = min_y + height
        
        # Set dimensions in the rotator as well
        rotator_success, rotator_message, rotator_details = self.rotator.set_dimensions(width, height, thickness)
        if not rotator_success:
            logger.warning(f"Warning setting rotator dimensions: {rotator_message}")
        
        success_msg = f"Workpiece parameters set: {width}x{height}x{thickness}mm"
        logger.info(success_msg)
        
        return ErrorHandler.create_success_response(
            message=success_msg,
            data={
                "width": width,
                "height": height,
                "thickness": thickness,
                "boundaries": {
                    "min_x": min_x,
                    "min_y": min_y,
                    "max_x": self.max_x,
                    "max_y": self.max_y
                }
            }
        )
    
    def set_from_workpiece_info(self, workpiece_info: Dict) -> Tuple[bool, str, Dict]:
        """
        Set parameters from workpiece info dictionary.
        
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
                logger.warning(error_msg)
                dimensions = {}  # Use empty dict with defaults
            
            width = dimensions.get('width', 0.0)
            height = dimensions.get('height', 0.0)
            thickness = dimensions.get('depth', 0.0)
            
            # Get origin information if available
            min_x = dimensions.get('min_x', 0.0)
            min_y = dimensions.get('min_y', 0.0)
            
            # Set up workpiece rotator with the same workpiece info
            rotator_success, rotator_message, rotator_details = self.rotator.set_from_workpiece_info(workpiece_info)
            if not rotator_success:
                logger.warning(f"Warning setting up workpiece rotator: {rotator_message}")
            
            return self.set_workpiece_parameters(
                width, height, thickness, min_x, min_y
            )
        except Exception as e:
            error_msg = f"Error setting parameters from workpiece info: {str(e)}"
            log_exception(logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.TRANSFORMATION,
                    details={
                        "error_type": "Exception", 
                        "error": str(e),
                        "workpiece_info_type": str(type(workpiece_info))
                    }
                )
            )
            
    def position_workpiece(self, transformed_points: List[Any], target_position: Optional[str] = None) -> Tuple[bool, str, Dict]:
        """
        Position the workpiece and its points at the desired location in machine space.
        
        Args:
            transformed_points: List of points with machine_position attribute
            target_position: Desired position ("top-left", "top-right", etc.). If None, use default
            
        Returns:
            Tuple of (success, message, details)
        """
        if not transformed_points:
            warning_msg = "No points to position"
            logger.warning(warning_msg)
            return ErrorHandler.create_success_response(
                message=warning_msg,
                data={
                    "transformed_points": [],
                    "positioned_points": [],
                    "stats": {
                        "total_points": 0,
                        "positioned": 0,
                        "errors": 0
                    }
                }
            )
        
        try:
            # Use specified target position or default
            target_pos = target_position if target_position else self.target_position
            
            # Get current orientation based on point C
            current_orientation = self.rotator.get_orientation()
            
            # Create appropriate positioner
            positioner = create_positioner(
                target_pos, 
                self.width, 
                self.height, 
                current_orientation
            )
            
            # Apply positioning
            success, message, details = positioner.apply_offset(transformed_points)
            
            if success:
                logger.info(f"Positioned workpiece to {target_pos}: {message}")
                return ErrorHandler.create_success_response(
                    message=f"Positioned workpiece to {target_pos}: {message}",
                    data={
                        "positioned_points": transformed_points,
                        "offset": details.get('offset', (0.0, 0.0)),
                        "target_position": target_pos,
                        "original_orientation": current_orientation,
                        "stats": details.get('stats', {})
                    }
                )
            else:
                logger.error(f"Error positioning workpiece: {message}")
                return ErrorHandler.from_exception(
                    BaseError(
                        message=f"Error positioning workpiece: {message}",
                        severity=ErrorSeverity.ERROR,
                        category=ErrorCategory.TRANSFORMATION,
                        details=details
                    )
                )
                
        except Exception as e:
            error_msg = f"Error positioning workpiece: {str(e)}"
            log_exception(logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.TRANSFORMATION,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "points_count": len(transformed_points)
                    }
                )
            )
    
    def apply_manual_rotation(self, transformed_points: List[Any], rotations: int = 1) -> Tuple[bool, str, Dict]:
        """
        Apply a specific number of 90-degree clockwise rotations to transformed points.
        
        Args:
            transformed_points: List of points with machine_position attribute
            rotations: Number of 90-degree clockwise rotations to apply (1-3)
            
        Returns:
            Tuple of (success, message, details)
        """
        if not transformed_points:
            warning_msg = "No points to rotate"
            logger.warning(warning_msg)
            return ErrorHandler.create_success_response(
                message=warning_msg,
                data={
                    "points": [],
                    "rotations": rotations,
                    "angle": 0
                }
            )
        
        # Validate rotation count
        rotations = max(0, min(3, rotations))  # Clamp to 0-3 range
        
        if rotations == 0:
            return ErrorHandler.create_success_response(
                message="No rotation requested (0 rotations)",
                data={
                    "points": transformed_points,
                    "rotations": 0,
                    "angle": 0
                }
            )
        
        try:
            # Reset rotator first to ensure we start from original state
            self.rotator.reset_to_original()
            
            # Apply the requested number of rotations
            for _ in range(rotations):
                self.rotator.rotate_90_clockwise()
            
            # Get current rotation angle
            rotation_angle = self.rotator.get_rotation_angle()
            
            # Apply rotation to points
            rotation_success, rotation_msg, rotation_details = self.rotator.rotate_points(transformed_points)
            
            if rotation_success:
                # Update dimensions based on rotator
                rotated_dimensions = self.rotator.get_current_dimensions()
                self.width = rotated_dimensions["width"]
                self.height = rotated_dimensions["height"]
                
                success_msg = f"Applied {rotations} manual rotation(s) ({rotation_angle}°)"
                logger.info(success_msg)
                
                return ErrorHandler.create_success_response(
                    message=success_msg,
                    data={
                        "points": transformed_points,
                        "rotations": rotations,
                        "angle": rotation_angle,
                        "dimensions": {
                            "width": self.width,
                            "height": self.height,
                            "thickness": self.thickness
                        }
                    }
                )
            else:
                error_msg = f"Error rotating points: {rotation_msg}"
                logger.error(error_msg)
                return ErrorHandler.from_exception(
                    BaseError(
                        message=error_msg,
                        severity=ErrorSeverity.ERROR,
                        category=ErrorCategory.TRANSFORMATION,
                        details=rotation_details
                    )
                )
                
        except Exception as e:
            error_msg = f"Error during manual rotation: {str(e)}"
            log_exception(logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.TRANSFORMATION,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "rotations": rotations
                    }
                )
            )
    
    
    def filter_horizontal_points(self, drilling_points: List[Any]) -> Tuple[List[Any], List[Any]]:
        """
        Filter drilling points to get only horizontal drilling points.
        
        Args:
            drilling_points: List of drilling point objects
            
        Returns:
            Tuple[List[Any], List[Any]]: (horizontal_points, vertical_points)
        """
        horizontal_points = []
        vertical_points = []
        
        for point in drilling_points:
            # Check if point has an edge attribute
            edge = getattr(point, 'edge', None)
            
            # If no edge attribute, try to determine from extrusion vector
            if edge is None and hasattr(point, 'extrusion_vector'):
                extrusion = point.extrusion_vector
                # Vertical drilling typically has (0,0,1) extrusion
                if extrusion[2] == 1.0:
                    edge = "VERTICAL"
                # Horizontal drilling has other extrusion directions
                else:
                    # This is a simplified check; real implementation would be more sophisticated
                    if extrusion[0] == 1.0:
                        edge = "RIGHT"
                    elif extrusion[0] == -1.0:
                        edge = "LEFT"
                    elif extrusion[1] == 1.0:
                        edge = "FRONT"
                    elif extrusion[1] == -1.0:
                        edge = "BACK"
                    else:
                        edge = "UNKNOWN"
            
            # Categorize based on edge
            if edge == "VERTICAL":
                vertical_points.append(point)
            elif edge in ["LEFT", "RIGHT", "FRONT", "BACK"]:
                horizontal_points.append(point)
            else:
                # Log warning for points with unknown edge
                logger.warning(f"Unknown edge type for point: {getattr(point, 'position', 'unknown position')}")
        
        return horizontal_points, vertical_points
    
    def transform_horizontal_point(self, point: Any) -> Tuple[bool, Dict]:
        """
        Transform a horizontal drilling point from DXF to machine coordinates.
        
        Args:
            point: Drilling point object with position and edge attributes
            
        Returns:
            Tuple[bool, Dict]: (success, result_dict)
        """
        try:
            # Extract position and edge
            position = getattr(point, 'position', None)
            edge = getattr(point, 'edge', None)
            
            if position is None or edge is None:
                return False, {
                    "success": False,
                    "error": "Missing position or edge attribute",
                    "point": point
                }
            
            # Extract coordinates
            x_dxf, y_dxf, z_dxf = position
            
            # Apply edge-specific transformations
            if edge == "LEFT":
                x_machine = 0.0  # Left edge is at X=0
                y_machine = self.height - abs(x_dxf)
                z_machine = self.thickness + y_dxf
            elif edge == "RIGHT":
                x_machine = self.width  # Right edge is at X=width
                y_machine = self.height - abs(x_dxf)
                z_machine = self.thickness + y_dxf
            elif edge == "FRONT":
                x_machine = self.width - abs(x_dxf)
                y_machine = self.height  # Front edge is at Y=height
                z_machine = self.thickness + y_dxf
            elif edge == "BACK":
                x_machine = self.width - abs(x_dxf)
                y_machine = 0.0  # Back edge is at Y=0
                z_machine = self.thickness + y_dxf
            else:
                return False, {
                    "success": False,
                    "error": f"Unsupported edge type: {edge}",
                    "point": point
                }
            
            # Round coordinates
            x_machine = round(x_machine, self.precision)
            y_machine = round(y_machine, self.precision)
            z_machine = round(z_machine, self.precision)
            
            transformed_position = (x_machine, y_machine, z_machine)
            
            return True, {
                "success": True,
                "original_position": position,
                "transformed_position": transformed_position,
                "edge": edge
            }
                
        except Exception as e:
            error_msg = f"Error transforming point: {str(e)}"
            logger.error(error_msg)
            return False, {
                "success": False,
                "error": error_msg,
                "point": point
            }
    
    def transform_points(self, drilling_points: List[Any], apply_rotation: bool = True, 
                      apply_positioning: bool = True) -> Tuple[bool, str, Dict]:
        """
        Transform drilling points from DXF to machine coordinates.
        
        This method handles:
        1. Filtering to get only horizontal drilling points
        2. Transforming each point based on its edge
        3. Rotating transformed points if needed (when height > 800mm)
        4. Positioning the workpiece in the target location (default: top-left)
        
        Args:
            drilling_points: List of drilling point objects
            apply_rotation: Whether to apply rotation if needed (default: True)
            apply_positioning: Whether to position the workpiece (default: True)
            
        Returns:
            Tuple of (success, message, details)
        """
        if not drilling_points:
            warning_msg = "No drilling points provided"
            logger.warning(warning_msg)
            return ErrorHandler.create_success_response(
                message=warning_msg,
                data={
                    "transformed_points": [],
                    "stats": {
                        "total_points": 0,
                        "horizontal_points": 0,
                        "vertical_points": 0,
                        "successfully_transformed": 0,
                        "errors": 0
                    }
                }
            )
        
        try:
            # Filter to get only horizontal drilling points
            horizontal_points, vertical_points = self.filter_horizontal_points(drilling_points)
            
            # Statistics tracking
            stats = {
                "total_points": len(drilling_points),
                "horizontal_points": len(horizontal_points),
                "vertical_points": len(vertical_points),
                "successfully_transformed": 0,
                "errors": 0,
                "rotation_applied": False,
                "rotation_angle": 0,
                "by_edge": {}
            }
            
            # Track edge statistics
            for edge in ["LEFT", "RIGHT", "FRONT", "BACK"]:
                stats["by_edge"][edge] = {
                    "total": sum(1 for p in horizontal_points if getattr(p, 'edge', None) == edge),
                    "transformed": 0,
                    "errors": 0
                }
            
            # Transform each horizontal point
            transformed_points = []
            error_points = []
            
            for point in horizontal_points:
                success, result = self.transform_horizontal_point(point)
                
                if success:
                    # Update point with transformed coordinates
                    edge = result["edge"]
                    point.machine_position = result["transformed_position"]
                    point.transformation_result = result
                    
                    # Update statistics
                    stats["successfully_transformed"] += 1
                    stats["by_edge"][edge]["transformed"] += 1
                    
                    transformed_points.append(point)
                else:
                    # Handle error
                    point.transformation_error = result.get("error", "Unknown error")
                    stats["errors"] += 1
                    
                    edge = getattr(point, 'edge', 'UNKNOWN')
                    if edge in stats["by_edge"]:
                        stats["by_edge"][edge]["errors"] += 1
                    
                    error_points.append(point)
            
            # Apply rotation if needed and enabled
            rotation_message = "No rotation applied"
            if apply_rotation and self.auto_rotation_enabled:
                # Check if auto rotation is needed
                auto_rotation_needed = self.rotator.check_auto_rotation_needed()
                
                if auto_rotation_needed:
                    logger.info(f"Automatic rotation needed: Height {self.height}mm exceeds threshold")
                    
                    # First apply auto rotation to the workpiece to update dimensions
                    auto_rotation_success, auto_rotation_msg, auto_rotation_details = self.rotator.apply_auto_rotation_if_needed()
                    
                    if auto_rotation_success:
                        # Now apply rotation to the points
                        rotation_success, rotation_msg, rotation_details = self.rotator.rotate_points(transformed_points)
                        
                        if rotation_success:
                            # Update dimensions based on rotator
                            rotated_dimensions = self.rotator.get_current_dimensions()
                            self.width = rotated_dimensions["width"]
                            self.height = rotated_dimensions["height"]
                            
                            # Update stats with rotation info
                            stats["rotation_applied"] = True
                            stats["rotation_angle"] = rotated_dimensions["rotation_angle"]
                            rotation_message = f"Applied automatic rotation: {stats['rotation_angle']}°"
                        else:
                            logger.warning(f"Error applying rotation to points: {rotation_msg}")
                            rotation_message = f"Rotation failed: {rotation_msg}"
                    else:
                        logger.warning(f"Error applying auto rotation: {auto_rotation_msg}")
                        rotation_message = f"Auto rotation failed: {auto_rotation_msg}"
            
            # Create success message
            # Apply positioning if requested
            positioning_message = "No positioning applied"
            
            if apply_positioning and transformed_points:
                # Position the workpiece at the target location
                pos_success, pos_msg, pos_details = self.position_workpiece(transformed_points)
                
                if pos_success:
                    positioning_message = pos_msg
                    # Add positioning stats
                    stats["positioning_applied"] = True
                    stats["positioning_offset"] = pos_details.get('offset', (0.0, 0.0))
                    stats["positioning_target"] = pos_details.get('target_position', self.target_position)
                else:
                    positioning_message = f"Positioning failed: {pos_msg}"
                    stats["positioning_applied"] = False
            else:
                stats["positioning_applied"] = False
            
            # Create success message combining all steps
            success_msg = (f"Transformed {stats['successfully_transformed']} of {stats['horizontal_points']} "
                           f"horizontal drilling points. Skipped {stats['vertical_points']} vertical points. "
                           f"{rotation_message}. {positioning_message}")
                
            if stats["errors"] > 0:
                success_msg += f" {stats['errors']} points had transformation errors."
                
            logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "transformed_points": transformed_points,
                    "vertical_points": vertical_points,
                    "error_points": error_points,
                    "rotation_applied": stats["rotation_applied"],
                    "rotation_angle": stats["rotation_angle"], 
                    "positioning_applied": stats["positioning_applied"],
                    "dimensions": {
                        "width": self.width,
                        "height": self.height,
                        "thickness": self.thickness
                    },
                    "stats": stats
                }
            )
            
        except Exception as e:
            error_msg = f"Error transforming drilling points: {str(e)}"
            log_exception(logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.TRANSFORMATION,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "points_count": len(drilling_points)
                    }
                )
            )


# Example usage if run directly
if __name__ == "__main__":
    import sys
    
    # Test data structure for drilling points
    class DrillPoint:
        def __init__(self, position, edge=None, extrusion_vector=None, diameter=None, depth=None):
            self.position = position
            self.edge = edge
            self.extrusion_vector = extrusion_vector if extrusion_vector else (0, 0, 1)
            self.diameter = diameter if diameter else 8.0
            self.depth = depth if depth else 20.0
            
        def __str__(self):
            return f"DrillPoint(position={self.position}, edge={self.edge}, diameter={self.diameter}mm)"
    
    # Create test transformer
    transformer = HorizontalDrillTransformer()
    
    # Set workpiece parameters
    success, message, details = transformer.set_workpiece_parameters(500, 500, 20)
    print(f"Set parameters: {'Success' if success else 'Failed'} - {message}")
    
    # Create test drilling points
    test_points = [
        # Vertical points
        DrillPoint((50, 50, 0), edge="VERTICAL", extrusion_vector=(0, 0, 1)),
        DrillPoint((450, 50, 0), edge="VERTICAL", extrusion_vector=(0, 0, 1)),
        DrillPoint((50, 450, 0), edge="VERTICAL", extrusion_vector=(0, 0, 1)),
        DrillPoint((450, 450, 0), edge="VERTICAL", extrusion_vector=(0, 0, 1)),
        
        # Horizontal points - LEFT edge
        DrillPoint((-50, -10, -500), edge="LEFT", extrusion_vector=(-1, 0, 0)),
        DrillPoint((-250, -10, -500), edge="LEFT", extrusion_vector=(-1, 0, 0)),
        
        # Horizontal points - RIGHT edge
        DrillPoint((50, -10, 0), edge="RIGHT", extrusion_vector=(1, 0, 0)),
        DrillPoint((250, -10, 0), edge="RIGHT", extrusion_vector=(1, 0, 0)),
        
        # Other horizontal points
        DrillPoint((-600, -10, -500), edge="LEFT", extrusion_vector=(-1, 0, 0)),
        DrillPoint((600, -10, 0), edge="RIGHT", extrusion_vector=(1, 0, 0)),
    ]
    
    # Transform points
    success, message, details = transformer.transform_points(test_points)
    
    print("\n=== TRANSFORMATION RESULTS ===")
    print(message)
    
    print("\n=== STATISTICS ===")
    stats = details["stats"]
    print(f"Total points: {stats['total_points']}")
    print(f"Horizontal points: {stats['horizontal_points']}")
    print(f"Vertical points: {stats['vertical_points']}")
    print(f"Successfully transformed: {stats['successfully_transformed']}")
    print(f"Errors: {stats['errors']}")
    
    print("\n=== TRANSFORMED POINTS ===")
    for i, point in enumerate(details["transformed_points"]):
        result = getattr(point, 'transformation_result', {})
        original = result.get('original_position', 'unknown')
        transformed = result.get('transformed_position', 'unknown')
        
        print(f"Point {i+1}:")
        print(f"  Original: {original}")
        print(f"  Transformed: {transformed}")
        print(f"  Edge: {result.get('edge', 'unknown')}")
        print("---")