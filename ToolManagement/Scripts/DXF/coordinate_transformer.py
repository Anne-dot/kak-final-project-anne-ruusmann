"""
Module for transforming coordinates from DXF to machine coordinates.

This module handles the transformation of coordinates from DXF file format to CNC machine 
coordinates, including horizontal drilling points and workpiece rotation operations.
It also provides functionality to offset coordinates to match machine origin.
"""

from typing import Tuple, Dict, Any, Optional, List, Union
import math

# Import from Utils package
from Utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger(__name__)


class WorkpieceRotator:
    """Handles workpiece rotation operations with standardized interface."""
    
    def __init__(self):
        """Initialize the workpiece rotator."""
        self.original_corners = {}
        self.current_corners = {}
        self.rotation_count = 0
        logger.info("WorkpieceRotator initialized")
    
    def set_original_corners(self, corners: Dict[str, Tuple[float, float]]) -> Tuple[bool, str, Dict]:
        """
        Set the original corner points of the workpiece.
        
        Args:
            corners: Dictionary of corner points with keys like 'corner_point_a'
            
        Returns:
            Tuple of (success, message, details)
        """
        if not corners:
            error_msg = "No corner points provided"
            logger.error(error_msg)
            return False, error_msg, {}
        
        self.original_corners = corners
        self.current_corners = corners.copy()
        self.rotation_count = 0
        
        success_msg = "Original corner points set"
        logger.info(success_msg)
        return True, success_msg, {"corners": corners}
    
    def set_from_workpiece_info(self, workpiece_info: Dict) -> Tuple[bool, str, Dict]:
        """
        Set corner points from workpiece info dictionary.
        
        Args:
            workpiece_info: Dictionary with workpiece information
            
        Returns:
            Tuple of (success, message, details)
        """
        try:
            reference_points = workpiece_info.get('reference_points', {})
            
            # Extract corner points with neutral names
            corners = {
                'corner_point_a': reference_points.get('corner_bl', (0, 0)),
                'corner_point_b': reference_points.get('corner_br', (100, 0)),
                'corner_point_c': reference_points.get('corner_tr', (100, 100)),
                'corner_point_d': reference_points.get('corner_tl', (0, 100))
            }
            
            return self.set_original_corners(corners)
        except Exception as e:
            error_msg = f"Error setting parameters from workpiece info: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def rotate_90_clockwise(self) -> Tuple[bool, Dict[str, Tuple[float, float]], Dict]:
        """
        Rotate the workpiece 90 degrees clockwise.
        
        Returns:
            Tuple of (success, rotated_corners, details)
        """
        try:
            rotated_corners = {}
            for key, point in self.current_corners.items():
                # Apply rotation formula (x,y) -> (y,-x)
                x, y = point
                rotated_corners[key] = (y, -x)
            
            self.current_corners = rotated_corners
            self.rotation_count += 1
            
            success_msg = f"Rotated 90° clockwise (total: {self.get_rotation_angle()}°)"
            logger.info(success_msg)
            return True, self.current_corners, {
                "rotation_count": self.rotation_count,
                "rotation_angle": self.get_rotation_angle(),
                "orientation": self.get_orientation()
            }
        except Exception as e:
            error_msg = f"Error during rotation: {str(e)}"
            logger.error(error_msg)
            return False, self.current_corners, {"error": error_msg}
    
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
    
    def rotate_drilling_points(self, drilling_points: List[Any]) -> Tuple[bool, List[Any], Dict]:
        """
        Rotate a list of drilling points by the current rotation angle.
        
        Args:
            drilling_points: List of drilling point objects with position property
            
        Returns:
            Tuple of (success, rotated_points, details)
        """
        try:
            angle = self.get_rotation_angle()
            
            # Skip if no rotation needed
            if angle == 0:
                return True, drilling_points, {"angle": 0, "count": len(drilling_points)}
            
            # Track rotation statistics
            stats = {
                "angle": angle,
                "count": len(drilling_points),
                "successful_rotations": 0
            }
            
            # Rotate each point
            for point in drilling_points:
                try:
                    # Get original position
                    if hasattr(point, 'position') and point.position:
                        original_pos = point.position
                        
                        # Apply rotation
                        rotated_pos = self.rotate_point(original_pos)
                        
                        # Update position
                        point.position = rotated_pos
                        
                        # Update stats
                        stats["successful_rotations"] += 1
                except Exception as e:
                    logger.warning(f"Error rotating drilling point: {str(e)}")
                    continue
            
            success_msg = f"Rotated {stats['successful_rotations']} drilling points by {angle}°"
            logger.info(success_msg)
            return True, drilling_points, stats
        except Exception as e:
            error_msg = f"Error rotating drilling points: {str(e)}"
            logger.error(error_msg)
            return False, drilling_points, {"error": error_msg}
    
    def reset_to_original(self) -> Tuple[bool, Dict[str, Tuple[float, float]], Dict]:
        """
        Reset to original position.
        
        Returns:
            Tuple of (success, original_corners, details)
        """
        try:
            self.current_corners = self.original_corners.copy()
            self.rotation_count = 0
            
            success_msg = "Reset to original position"
            logger.info(success_msg)
            return True, self.current_corners, {
                "rotation_count": 0,
                "rotation_angle": 0,
                "orientation": self.get_orientation()
            }
        except Exception as e:
            error_msg = f"Error during reset: {str(e)}"
            logger.error(error_msg)
            return False, self.current_corners, {"error": error_msg}
    
    def get_rotation_angle(self) -> int:
        """
        Get the current rotation angle in degrees.
        
        Returns:
            Rotation angle (0°, 90°, 180°, 270°)
        """
        return (self.rotation_count % 4) * 90
    
    def get_orientation(self) -> str:
        """
        Determine workpiece orientation based on point C coordinates.
        
        Returns:
            String indicating orientation
        """
        if not self.current_corners or 'corner_point_c' not in self.current_corners:
            return "Unknown"
            
        x_c, y_c = self.current_corners['corner_point_c']
        
        if x_c > 0 and y_c > 0:
            return "Bottom-Left"
        elif x_c > 0 and y_c < 0:
            return "Top-Left"
        elif x_c < 0 and y_c < 0:
            return "Top-Right"
        elif x_c < 0 and y_c > 0:
            return "Bottom-Right"
        else:
            return "Unknown orientation"
    
    def calculate_dimensions(self) -> Tuple[bool, Tuple[float, float], Dict]:
        """
        Calculate workpiece dimensions based on corner coordinates.
        
        Returns:
            Tuple of (success, (width, height), details)
        """
        try:
            # Get all coordinates
            x_values = [abs(point[0]) for point in self.current_corners.values()]
            y_values = [abs(point[1]) for point in self.current_corners.values()]
            
            # Width and height are the maximum values
            width = max(x_values)
            height = max(y_values)
            
            return True, (width, height), {
                "width": width,
                "height": height
            }
        except Exception as e:
            error_msg = f"Error calculating dimensions: {str(e)}"
            logger.error(error_msg)
            return False, (0, 0), {"error": error_msg}
    
    def get_current_corners(self) -> Tuple[bool, Dict[str, Tuple[float, float]], Dict]:
        """
        Get the current corner points.
        
        Returns:
            Tuple of (success, corners, details)
        """
        if not self.current_corners:
            return False, {}, {"error": "No corners available"}
        
        return True, self.current_corners, {
            "rotation_count": self.rotation_count,
            "rotation_angle": self.get_rotation_angle(),
            "orientation": self.get_orientation()
        }


class DrillPointTransformer:
    """
    Class for transforming drilling points based on type and edge.
    
    This class processes drilling points that have been classified by the 
    DrillPointClassifier, applying appropriate coordinate transformations
    based on the drilling operation type and edge.
    """
    
    def __init__(self):
        """Initialize the drill point transformer."""
        # Workpiece dimensions
        self.width = 0.0
        self.height = 0.0
        self.thickness = 0.0
        
        # Bounding box
        self.min_x = 0.0
        self.min_y = 0.0
        self.max_x = 0.0
        self.max_y = 0.0
        
        # Rounding precision for output coordinates
        self.precision = 1
        
        # Classifier reference for edge grouping
        self.classifier = None
        
        logger.info("DrillPointTransformer initialized")
    
    def set_workpiece_parameters(self, width: float, height: float, thickness: float,
                                min_x: float, min_y: float, max_x: float, max_y: float) -> Tuple[bool, str, Dict]:
        """
        Set workpiece parameters for coordinate transformation.
        
        Args:
            width: Workpiece width in mm
            height: Workpiece height in mm
            thickness: Workpiece thickness in mm
            min_x: Minimum X coordinate of workpiece
            min_y: Minimum Y coordinate of workpiece
            max_x: Maximum X coordinate of workpiece
            max_y: Maximum Y coordinate of workpiece
            
        Returns:
            Tuple of (success, message, details)
        """
        # Validate parameters
        if width <= 0 or height <= 0 or thickness <= 0:
            error_msg = "Invalid workpiece dimensions (must be positive)"
            logger.error(error_msg)
            return False, error_msg, {}
        
        # Set workpiece parameters
        self.width = width
        self.height = height
        self.thickness = thickness
        
        # Set bounding box
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        
        success_msg = f"Workpiece parameters set: {width}x{height}x{thickness}mm"
        logger.info(success_msg)
        return True, success_msg, {
            "width": width,
            "height": height,
            "thickness": thickness
        }
    
    def set_from_workpiece_info(self, workpiece_info: Dict, classifier=None) -> Tuple[bool, str, Dict]:
        """
        Set parameters from workpiece info dictionary.
        
        Args:
            workpiece_info: Dictionary with workpiece information
            classifier: Classifier for organizing points by edge
            
        Returns:
            Tuple of (success, message, details)
        """
        try:
            # Store classifier for later use
            self.classifier = classifier
            
            # Extract dimensions
            dimensions = workpiece_info.get('dimensions', {})
            
            width = dimensions.get('width', 0.0)
            height = dimensions.get('height', 0.0)
            thickness = dimensions.get('depth', 0.0)
            
            min_x = dimensions.get('min_x', 0.0)
            min_y = dimensions.get('min_y', 0.0)
            max_x = dimensions.get('max_x', 0.0)
            max_y = dimensions.get('max_y', 0.0)
            
            return self.set_workpiece_parameters(
                width, height, thickness, min_x, min_y, max_x, max_y
            )
        except Exception as e:
            error_msg = f"Error setting parameters from workpiece info: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def transform_z_coordinate(self, y_dxf: float) -> float:
        """
        Transform the Z coordinate for horizontal drilling.
        
        Formula: Z_machine = workpiece_thickness + Y_dxf
        
        Args:
            y_dxf: Y coordinate from DXF
            
        Returns:
            Z coordinate in machine coordinates
        """
        z_machine = self.thickness + y_dxf
        return round(z_machine, self.precision)
    
    def transform_horizontal_drilling_point(self, point_position: Tuple[float, float, float], 
                                           edge: str) -> Tuple[bool, Tuple[float, float, float], Dict]:
        """
        Transform a horizontal drilling point's coordinates based on its edge.
        
        Args:
            point_position: (x, y, z) coordinates from DXF
            edge: Edge type (LEFT, RIGHT, FRONT, BACK)
            
        Returns:
            Tuple of (success, transformed_position, details)
        """
        if edge not in ["LEFT", "RIGHT", "FRONT", "BACK"]:
            error_msg = f"Unsupported edge: {edge}"
            logger.error(error_msg)
            return False, None, {"error": error_msg}
            
        # Extract coordinates
        x_dxf, y_dxf, z_dxf = point_position
        
        # Transform Z coordinate (same for all horizontal drilling)
        z_machine = self.transform_z_coordinate(y_dxf)
        
        # Apply edge-specific transformations for X and Y
        if edge == "LEFT":
            x_machine = 0.0  # Left edge is at X=0
            y_machine = self.height - abs(x_dxf)
        elif edge == "RIGHT":
            x_machine = self.width  # Right edge is at X=width
            y_machine = self.height - abs(x_dxf)
        elif edge == "FRONT":
            x_machine = self.width - abs(x_dxf)
            y_machine = self.height  # Front edge is at Y=height
        else:  # BACK edge
            x_machine = self.width - abs(x_dxf)
            y_machine = 0.0  # Back edge is at Y=0
        
        # Round coordinates
        x_machine = round(x_machine, self.precision)
        y_machine = round(y_machine, self.precision)
        
        return True, (x_machine, y_machine, z_machine), {
            "edge": edge,
            "original_position": point_position
        }
    
    
    def transform_drilling_points(self, drilling_points: List[Any]) -> Tuple[bool, List[Any], Dict]:
        """
        Transform drilling points from DXF to machine coordinates.
        
        This method leverages the classifier to separate points by drill type,
        processes only horizontal drilling points, and applies the appropriate
        transformation based on edge.
        
        Args:
            drilling_points: List of classified drilling points
            
        Returns:
            Tuple of (success, transformed_points, details)
        """
        if not drilling_points:
            warning_msg = "No drilling points to transform"
            logger.warning(warning_msg)
            return True, [], {"message": warning_msg, "count": 0}
        
        try:
            # Get horizontal points by type using classifier if available
            horizontal_points = []
            vertical_points = []
            
            if self.classifier:
                # Use classifier to group points by edge
                points_by_edge = self.classifier.get_points_by_edge(drilling_points)
                
                # Add all points except vertical ones to horizontal_points
                for edge, points in points_by_edge.items():
                    if edge == "VERTICAL":
                        vertical_points.extend(points)
                    elif edge in ["LEFT", "RIGHT", "FRONT", "BACK"]:
                        horizontal_points.extend(points)
            else:
                # Manual classification if no classifier provided
                for point in drilling_points:
                    if getattr(point, 'drill_type', None) == "vertical" or getattr(point, 'edge', None) == "VERTICAL":
                        vertical_points.append(point)
                    else:
                        horizontal_points.append(point)
            
            # Skip vertical drilling transformation - not part of MVP
            for point in vertical_points:
                point.transformation_skipped = True
                point.transformation_note = "Vertical drilling transformation not implemented in MVP"
            
            # Transform horizontal drilling points
            transformed_count = 0
            
            for point in horizontal_points:
                edge = getattr(point, 'edge', None)
                position = getattr(point, 'position', None)
                
                if edge and position:
                    success, transformed_position, details = self.transform_horizontal_drilling_point(position, edge)
                    
                    if success and transformed_position:
                        point.machine_position = transformed_position
                        point.transformation_skipped = False
                        transformed_count += 1
                    else:
                        point.transformation_skipped = True
                        point.transformation_note = details.get('error', 'Unknown error during transformation')
                else:
                    point.transformation_skipped = True
                    point.transformation_note = "Missing edge or position data"
            
            # Apply origin offset
            success, points_with_offset, offset_details = self.apply_origin_offset(horizontal_points)
            
            # Combine results
            all_points = vertical_points + horizontal_points
            
            # Log results
            message = (f"Transformed {transformed_count} of {len(horizontal_points)} horizontal points. "
                       f"Skipped {len(vertical_points)} vertical points.")
            logger.info(message)
            
            # Return statistics
            stats = {
                "total_points": len(drilling_points),
                "horizontal_points": len(horizontal_points),
                "vertical_points": len(vertical_points),
                "transformed_points": transformed_count,
                "offset_applied": offset_details.get('stats', {}).get('offset_applied', 0) if success else 0
            }
            
            return True, all_points, {
                "message": message,
                "stats": stats
            }
            
        except Exception as e:
            error_msg = f"Error transforming drilling points: {str(e)}"
            logger.error(error_msg)
            return False, drilling_points, {"error": error_msg}


class CoordinateTransformer:
    """
    Main coordinate transformer class that combines all transformation steps.
    
    This class orchestrates the complete transformation pipeline from DXF coordinates
    to machine coordinates, handling workpiece rotation, edge-based transformation,
    and origin offset in a single workflow.
    """
    
    def __init__(self):
        """Initialize the coordinate transformer."""
        self.rotator = WorkpieceRotator()
        self.drill_transformer = DrillPointTransformer()
        
        self.workpiece_info = None
        self.classifier = None  # Optional classifier for point organization
        
        logger.info("CoordinateTransformer initialized")
    
    def set_from_workpiece_info(self, workpiece_info: Dict, classifier=None) -> Tuple[bool, str, Dict]:
        """
        Set parameters from workpiece info dictionary.
        
        Args:
            workpiece_info: Dictionary with workpiece information
            classifier: Optional classifier to organize points by edge
            
        Returns:
            Tuple of (success, message, details)
        """
        try:
            # Store workpiece info and classifier
            self.workpiece_info = workpiece_info
            self.classifier = classifier
            
            # Set up rotator
            rot_success, rot_message, _ = self.rotator.set_from_workpiece_info(workpiece_info)
            if not rot_success:
                logger.warning(f"Rotator setup warning: {rot_message}")
            
            # Set up drill transformer
            drill_success, drill_message, _ = self.drill_transformer.set_from_workpiece_info(workpiece_info, classifier)
            if not drill_success:
                logger.warning(f"Drill transformer setup warning: {drill_message}")
            
            success_msg = "Coordinate transformer configured successfully"
            logger.info(success_msg)
            return True, success_msg, {
                "workpiece_info": workpiece_info
            }
            
        except Exception as e:
            error_msg = f"Error setting coordinate transformer parameters: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {"error": str(e)}
    
    def transform_drilling_points(self, points: List[Any], rotation=False, edge=True, 
                                offset=True) -> Tuple[bool, List[Any], Dict]:
        """
        Apply full transformation pipeline to drilling points.
        
        Args:
            points: List of drilling point objects
            rotation: Whether to apply rotation (default: False)
            edge: Whether to apply edge-based transformation (default: True)
            offset: Whether to apply origin offset (default: True)
            
        Returns:
            Tuple of (success, transformed_points, details)
        """
        if not points:
            warning_msg = "No drilling points to transform"
            logger.warning(warning_msg)
            return True, [], {"message": warning_msg, "count": 0}
        
        try:
            # Track transformation statistics
            stats = {
                "total_points": len(points),
                "horizontal_points": sum(1 for p in points if getattr(p, 'drill_type', None) == "horizontal"),
                "vertical_points": sum(1 for p in points if getattr(p, 'drill_type', None) == "vertical"),
                "stages": {}
            }
            
            # Start with the original points
            current_points = points
            
            # Stage 1: Rotation (if requested)
            if rotation and self.rotator:
                logger.info("Applying rotation transformation")
                rot_success, current_points, rot_details = self.rotator.rotate_drilling_points(current_points)
                stats["stages"]["rotation"] = {
                    "success": rot_success,
                    "details": rot_details
                }
                
                if not rot_success:
                    logger.warning(f"Rotation transformation failed: {rot_details.get('error', 'Unknown error')}")
            
            # Stage 2: Apply drill point transformation (if requested)
            # This handles both edge-based transformation and origin offset
            if edge:
                logger.info("Applying drilling point transformation")
                transform_success, current_points, transform_details = self.drill_transformer.transform_drilling_points(current_points)
                stats["stages"]["drilling_transformation"] = {
                    "success": transform_success,
                    "details": transform_details
                }
                
                if not transform_success:
                    logger.warning(f"Drilling transformation failed: {transform_details.get('error', 'Unknown error')}")
            
            # Calculate final statistics
            transformed_count = sum(1 for p in current_points 
                                   if hasattr(p, 'machine_position') and p.machine_position 
                                   and not getattr(p, 'transformation_skipped', False))
            
            stats["transformed_count"] = transformed_count
            stats["success_rate"] = transformed_count / stats["horizontal_points"] if stats["horizontal_points"] > 0 else 0
            
            success_msg = (f"Transformed {transformed_count} of {stats['horizontal_points']} horizontal "
                          f"drilling points. Skipped {stats['vertical_points']} vertical points.")
            logger.info(success_msg)
            return True, current_points, {
                "message": success_msg,
                "stats": stats
            }
            
        except Exception as e:
            error_msg = f"Error during coordinate transformation: {str(e)}"
            logger.error(error_msg)
            return False, points, {"error": error_msg}