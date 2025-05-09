"""
Module for generating safe tool paths for CNC operations.

This module focuses on creating safe and efficient tool paths for
different CNC operations, particularly drilling. It generates the
complete sequence of movements needed for each operation type.

Functions:
    calculate_safe_heights: Calculates safe Z heights for different operations
    calculate_drilling_paths: Generates complete drilling approach paths
    calculate_approach_point: Determines safe approach positions

References:
    - MRFP-80: DXF to G-code Generation Epic
"""

import math
import logging
from typing import Tuple, List, Dict, Any, Optional, Union

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception
from Utils.error_utils import ErrorHandler, BaseError, ValidationError, ErrorSeverity, ErrorCategory


class ToolPathGenerator:
    """
    Generates safe tool paths for CNC operations.
    
    This class provides methods for calculating safe approach paths,
    appropriate heights, and complete operation sequences for different
    types of CNC operations.
    """
    
    def __init__(self):
        """Initialize the tool path generator."""
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        
        # Default clearance for operations
        self.clearance_height = 10.0  # mm above workpiece for safe travel
        
        # Default workpiece thickness if not specified
        self.default_thickness = 22.5  # mm
        
        # Safe approach distance for horizontal drilling
        self.approach_distance = 30.0  # mm from edge for safe positioning
        
        # Initialize workpiece parameters
        self.workpiece_width = 0.0
        self.workpiece_height = 0.0
        self.workpiece_thickness = self.default_thickness
        
        self.logger.info("ToolPathGenerator initialized")
    
    def set_workpiece_parameters(
        self, 
        width: float, 
        height: float, 
        thickness: Optional[float] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Set workpiece parameters for path generation.
        
        Args:
            width: Workpiece width in mm (X dimension)
            height: Workpiece height in mm (Y dimension)
            thickness: Workpiece thickness in mm (Z dimension, default is 22.5mm)
            
        Returns:
            Tuple of (success, message, details)
        """
        try:
            # Validate parameters
            if width <= 0 or height <= 0:
                error_msg = f"Invalid workpiece dimensions: width={width}, height={height}"
                self.logger.error(error_msg)
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=error_msg,
                        severity=ErrorSeverity.ERROR,
                        details={
                            "error": "invalid_dimensions",
                            "width": width,
                            "height": height
                        }
                    )
                )
            
            # Set parameters
            self.workpiece_width = float(width)
            self.workpiece_height = float(height)
            
            # Set thickness with default if not provided
            thickness_value = thickness or self.default_thickness
            if thickness_value <= 0:
                warning_msg = f"Invalid thickness ({thickness_value}), using default: {self.default_thickness}mm"
                self.logger.warning(warning_msg)
                self.workpiece_thickness = self.default_thickness
            else:
                self.workpiece_thickness = float(thickness_value)
                
            success_msg = (
                f"Workpiece parameters set: {self.workpiece_width}mm x "
                f"{self.workpiece_height}mm x {self.workpiece_thickness}mm"
            )
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "width": self.workpiece_width,
                    "height": self.workpiece_height,
                    "thickness": self.workpiece_thickness
                }
            )
        except Exception as e:
            error_msg = f"Error setting workpiece parameters: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "width": width,
                        "height": height,
                        "thickness": thickness
                    }
                )
            )
    
    def set_from_workpiece_info(self, workpiece_info: Dict[str, Any]) -> Tuple[bool, str, Dict]:
        """
        Set parameters from workpiece_info dictionary from workpiece_extractor.
        
        Args:
            workpiece_info: Dictionary with workpiece information
            
        Returns:
            Tuple of (success, message, details)
        """
        if not workpiece_info:
            error_msg = "No workpiece information provided"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={"error": "missing_workpiece_info"}
                )
            )
            
        try:
            if 'dimensions' in workpiece_info:
                dims = workpiece_info['dimensions']
                success, message, details = self.set_workpiece_parameters(
                    width=dims.get('width', 0),
                    height=dims.get('height', 0),
                    thickness=dims.get('depth', self.default_thickness)
                )
                
                if not success:
                    return ErrorHandler.from_exception(
                        BaseError(
                            message=f"Failed to set workpiece parameters: {message}",
                            severity=ErrorSeverity.ERROR,
                            category=ErrorCategory.PROCESSING,
                            details={
                                "error_source": "set_workpiece_parameters",
                                "original_message": message,
                                "original_details": details
                            }
                        )
                    )
                
                success_msg = "Parameters set from workpiece_info"
                self.logger.info(success_msg)
                
                return ErrorHandler.create_success_response(
                    message=success_msg,
                    data={
                        "parameters": details,
                        "source": "workpiece_info"
                    }
                )
            else:
                warning_msg = "No dimensions found in workpiece_info"
                self.logger.warning(warning_msg)
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=warning_msg,
                        severity=ErrorSeverity.WARNING,
                        details={"error": "missing_dimensions"}
                    )
                )
                
        except Exception as e:
            error_msg = f"Error setting parameters from workpiece_info: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={
                        "error_type": "Exception", 
                        "error": str(e),
                        "workpiece_info_type": str(type(workpiece_info))
                    }
                )
            )
    
    def set_clearance_height(self, clearance: float) -> Tuple[bool, str, Dict]:
        """
        Set the clearance height for safe travel moves.
        
        Args:
            clearance: Clearance height in mm above workpiece surface
            
        Returns:
            Tuple of (success, message, details)
        """
        try:
            # Validate clearance
            if clearance <= 0:
                error_msg = f"Invalid clearance height: {clearance}mm (must be positive)"
                self.logger.error(error_msg)
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=error_msg,
                        severity=ErrorSeverity.ERROR,
                        details={
                            "error": "invalid_clearance",
                            "value": clearance
                        }
                    )
                )
                
            # Set clearance height
            previous_clearance = self.clearance_height
            self.clearance_height = float(clearance)
            
            success_msg = f"Clearance height set to {self.clearance_height}mm"
            self.logger.info(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "clearance_height": self.clearance_height,
                    "previous_clearance": previous_clearance
                }
            )
            
        except Exception as e:
            error_msg = f"Error setting clearance height: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "clearance": clearance
                    }
                )
            )
    
    def calculate_safe_heights(
        self, 
        operation_type: str,
        point: Tuple[float, float, float],
        drill_depth: Optional[float] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Calculate safe Z heights for different operations.
        
        Args:
            operation_type: Type of operation ('vertical_drill', 'horizontal_drill')
            point: Machine coordinates of the operation point
            drill_depth: Depth of drilling operation (if applicable)
            
        Returns:
            Tuple of (success, message, details) where details contains heights
        """
        # Validate operation type
        valid_operation_types = ["vertical_drill", "horizontal_drill"]
        if operation_type not in valid_operation_types:
            error_msg = f"Invalid operation type: {operation_type}"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={
                        "error": "invalid_operation_type",
                        "value": operation_type,
                        "valid_types": valid_operation_types
                    }
                )
            )
            
        # Validate point
        if not point or len(point) != 3:
            error_msg = "Invalid point coordinates"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={"error": "invalid_point", "point": point}
                )
            )
            
        try:
            # Extract coordinates
            x, y, z = point
            
            # Common heights
            safe_travel_z = self.workpiece_thickness + self.clearance_height
            
            # Operation-specific heights
            heights = {}
            
            if operation_type == "vertical_drill":
                safe_rapid_z = self.workpiece_thickness + 2.0  # 2mm above workpiece
                
                # Calculate drill depth if provided
                if drill_depth is not None:
                    if drill_depth <= 0:
                        warning_msg = f"Invalid drill depth: {drill_depth}mm, using 5mm as default"
                        self.logger.warning(warning_msg)
                        drill_depth = 5.0
                        
                    drill_to_z = self.workpiece_thickness - drill_depth
                else:
                    drill_to_z = None
                    
                heights = {
                    "safe_travel": safe_travel_z,
                    "safe_rapid": safe_rapid_z,
                    "start_position": self.workpiece_thickness,
                    "drill_to": drill_to_z
                }
                
            elif operation_type == "horizontal_drill":
                # For horizontal drilling, Z is already set correctly
                # Just need to provide safe travel height
                heights = {
                    "safe_travel": safe_travel_z,
                    "operation_z": z
                }
            
            success_msg = f"Calculated safe heights for {operation_type}"
            self.logger.debug(f"{success_msg}: {heights}")
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "heights": heights,
                    "operation_type": operation_type,
                    "point": point,
                    "drill_depth": drill_depth
                }
            )
            
        except Exception as e:
            error_msg = f"Error calculating safe heights: {str(e)}"
            log_exception(self.logger, error_msg)
            
            # Create basic safe height as fallback
            basic_heights = {"safe_travel": self.workpiece_thickness + self.clearance_height}
            
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "operation_type": operation_type,
                        "point": point,
                        "fallback_heights": basic_heights
                    }
                )
            )
    
    def calculate_drilling_paths(
        self,
        operation_type: str,
        point: Tuple[float, float, float],
        direction: Optional[Tuple[float, float, float]] = None,
        drill_depth: Optional[float] = None,
        feed_rate: Optional[float] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Calculate complete drilling paths including approach, operation, and retract.
        
        Args:
            operation_type: Type of operation ('vertical_drill', 'horizontal_drill')
            point: Machine coordinates of the operation point
            direction: Drilling direction vector (for horizontal drilling)
            drill_depth: Depth of drilling operation
            feed_rate: Feed rate for drilling operations (mm/min)
            
        Returns:
            Tuple of (success, message, details) with path segments in details
        """
        # Validate operation type
        valid_operation_types = ["vertical_drill", "horizontal_drill"]
        if operation_type not in valid_operation_types:
            error_msg = f"Invalid operation type: {operation_type}"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={
                        "error": "invalid_operation_type",
                        "value": operation_type,
                        "valid_types": valid_operation_types
                    }
                )
            )
            
        # Validate point
        if not point or len(point) != 3:
            error_msg = "Invalid point coordinates"
            self.logger.error(error_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={"error": "invalid_point", "point": point}
                )
            )
            
        # For horizontal drilling, direction is required
        if operation_type == "horizontal_drill" and not direction:
            direction = (1, 0, 0)  # Default to X+ direction
            self.logger.warning(f"No direction provided for horizontal drilling, using default: {direction}")
        
        try:
            # Extract coordinates
            x, y, z = point
            
            # Get safe heights
            heights_success, heights_message, heights_details = self.calculate_safe_heights(
                operation_type, point, drill_depth
            )
            
            if not heights_success:
                return ErrorHandler.from_exception(
                    BaseError(
                        message=f"Failed to calculate safe heights: {heights_message}",
                        severity=ErrorSeverity.ERROR,
                        category=ErrorCategory.PROCESSING,
                        details={
                            "error_source": "calculate_safe_heights",
                            "original_message": heights_message,
                            "original_details": heights_details
                        }
                    )
                )
                
            # Extract heights from details
            heights = heights_details.get('heights', {})
            
            # Default feed rate if not specified
            if feed_rate is None or feed_rate <= 0:
                feed_rate = 300  # mm/min
                self.logger.debug(f"Using default feed rate: {feed_rate} mm/min")
            
            # Build path segments based on operation type
            path_segments = []
            
            if operation_type == "vertical_drill":
                # Follow vertical drilling path pattern:
                # 1. Rapid to position at safe height
                path_segments.append({
                    "type": "rapid",
                    "command": "G0",
                    "coordinates": (x, y, heights["safe_travel"]),
                    "comment": "Rapid to position at safe height"
                })
                
                # 2. Rapid to position 2mm above surface
                path_segments.append({
                    "type": "rapid",
                    "command": "G0",
                    "coordinates": (x, y, heights["safe_rapid"]),
                    "comment": "Rapid to safe height above workpiece"
                })
                
                # 3. Move to surface
                path_segments.append({
                    "type": "positioning",
                    "command": "G0",
                    "coordinates": (x, y, heights["start_position"]),
                    "comment": "Position at top of workpiece"
                })
                
                # 4. Drill to depth
                if heights.get("drill_to") is not None:
                    path_segments.append({
                        "type": "drilling",
                        "command": "G1",
                        "coordinates": (x, y, heights["drill_to"]),
                        "feed_rate": feed_rate,
                        "comment": f"Drill to depth ({drill_depth}mm)"
                    })
                
                # 5. Retract to safe height
                path_segments.append({
                    "type": "retract",
                    "command": "G0",
                    "coordinates": (x, y, heights["safe_travel"]),
                    "comment": "Retract to safe height"
                })
                
            elif operation_type == "horizontal_drill":
                # Determine approach direction
                approach_x, approach_y = self._calculate_approach_point(x, y, direction)
                
                # Follow horizontal drilling path pattern:
                # 1. Rapid to approach position at safe height
                path_segments.append({
                    "type": "rapid",
                    "command": "G0",
                    "coordinates": (approach_x, approach_y, heights["safe_travel"]),
                    "comment": "Rapid to safe approach position"
                })
                
                # 2. Rapid down to drilling height
                path_segments.append({
                    "type": "rapid",
                    "command": "G0",
                    "coordinates": (approach_x, approach_y, heights["operation_z"]),
                    "comment": "Rapid to drilling height"
                })
                
                # 3. Feed to drilling position
                path_segments.append({
                    "type": "approach",
                    "command": "G1",
                    "coordinates": (x, y, heights["operation_z"]),
                    "feed_rate": feed_rate,
                    "comment": "Approach drilling position"
                })
                
                # 4. Drill to depth
                if drill_depth is not None and direction is not None:
                    # Calculate end point
                    end_x = x + direction[0] * drill_depth
                    end_y = y + direction[1] * drill_depth
                    
                    path_segments.append({
                        "type": "drilling",
                        "command": "G1",
                        "coordinates": (end_x, end_y, heights["operation_z"]),
                        "feed_rate": feed_rate,
                        "comment": f"Drill to depth ({drill_depth}mm)"
                    })
                    
                    # 5. Retract to drilling position
                    path_segments.append({
                        "type": "retract",
                        "command": "G1",
                        "coordinates": (x, y, heights["operation_z"]),
                        "feed_rate": feed_rate * 2,  # Faster retract
                        "comment": "Retract to drilling position"
                    })
                
                # 6. Retract to approach position
                path_segments.append({
                    "type": "retract",
                    "command": "G0",
                    "coordinates": (approach_x, approach_y, heights["operation_z"]),
                    "comment": "Retract to approach position"
                })
                
                # Retract to safe height
                path_segments.append({
                    "type": "retract",
                    "command": "G0",
                    "coordinates": (approach_x, approach_y, heights["safe_travel"]),
                    "comment": "Retract to safe height"
                })
            
            success_msg = f"Calculated {len(path_segments)} path segments for {operation_type}"
            self.logger.debug(success_msg)
            
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "path_segments": path_segments,
                    "operation_type": operation_type,
                    "point": point,
                    "direction": direction,
                    "drill_depth": drill_depth,
                    "feed_rate": feed_rate,
                    "segment_count": len(path_segments),
                    "heights": heights
                }
            )
            
        except Exception as e:
            error_msg = f"Error calculating drilling paths: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "operation_type": operation_type,
                        "point": point
                    }
                )
            )
    
    def _calculate_approach_point(
        self, 
        x: float, 
        y: float, 
        direction: Tuple[float, float, float]
    ) -> Tuple[float, float]:
        """
        Calculate a safe approach point for horizontal drilling.
        
        Args:
            x: X coordinate of drilling point
            y: Y coordinate of drilling point
            direction: Direction vector of drilling
            
        Returns:
            Tuple: (X, Y) coordinates of approach point
        """
        try:
            # Extract direction components
            dx, dy, dz = direction
            
            # Normalize direction vector (ensure unit length)
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            if length > 0.0001:  # Avoid division by zero
                dx, dy, dz = dx/length, dy/length, dz/length
            
            # Calculate approach point by moving in the opposite direction of drilling
            approach_x = x - dx * self.approach_distance
            approach_y = y - dy * self.approach_distance
            
            # Check if approach point is inside workpiece bounds
            if 0 <= approach_x <= self.workpiece_width and 0 <= approach_y <= self.workpiece_height:
                # Approach is inside workpiece, try to find an approach from outside
                if abs(dx) > abs(dy):  # X-dominant direction
                    if dx > 0:  # Drilling from left
                        approach_x = 0
                    else:  # Drilling from right
                        approach_x = self.workpiece_width
                else:  # Y-dominant direction
                    if dy > 0:  # Drilling from bottom
                        approach_y = 0
                    else:  # Drilling from top
                        approach_y = self.workpiece_height
            
            # Round to 0.1mm accuracy
            approach_x = round(approach_x, 1)
            approach_y = round(approach_y, 1)
            
            return (approach_x, approach_y)
            
        except Exception as e:
            self.logger.error(f"Error calculating approach point: {str(e)}")
            # Default to original point if calculation fails
            return (round(x, 1), round(y, 1))
    
    def generate_operation_gcode(
        self,
        path_segments: List[Dict[str, Any]]
    ) -> Tuple[bool, str, Dict]:
        """
        Generate actual G-code lines from path segments.
        
        Args:
            path_segments: List of path segment dictionaries
            
        Returns:
            Tuple of (success, message, details) with gcode_lines in details
        """
        if not path_segments:
            warning_msg = "No path segments provided to generate G-code"
            self.logger.warning(warning_msg)
            return ErrorHandler.from_exception(
                ValidationError(
                    message=warning_msg,
                    severity=ErrorSeverity.WARNING,
                    details={"error": "empty_path_segments"}
                )
            )
            
        try:
            gcode_lines = []
            
            # Add header comment
            gcode_lines.append("(Generated toolpath)")
            
            segment_errors = []
            
            # Process each segment
            for i, segment in enumerate(path_segments):
                try:
                    # Validate segment data
                    if "coordinates" not in segment or "command" not in segment or "type" not in segment:
                        segment_errors.append({
                            "index": i,
                            "error": "Missing required fields in segment",
                            "segment": segment
                        })
                        continue
                        
                    # Extract coordinates and command
                    x, y, z = segment["coordinates"]
                    command = segment["command"]
                    comment = segment.get("comment", "")
                    
                    # Format command based on type
                    if segment["type"] in ["rapid", "retract", "positioning"]:
                        # No feed rate for rapid movements
                        code_line = f"{command} X{x:.1f} Y{y:.1f} Z{z:.1f}"
                    else:
                        # Include feed rate for cutting/drilling movements
                        feed_rate = segment.get("feed_rate", 300)
                        code_line = f"{command} X{x:.1f} Y{y:.1f} Z{z:.1f} F{feed_rate}"
                    
                    # Add comment if available
                    if comment:
                        code_line += f" ({comment})"
                    
                    gcode_lines.append(code_line)
                except Exception as seg_e:
                    # Log segment-specific error but continue processing
                    segment_errors.append({
                        "index": i,
                        "error": str(seg_e),
                        "segment": segment
                    })
                    self.logger.warning(f"Error processing segment {i}: {str(seg_e)}")
            
            success_msg = f"Generated {len(gcode_lines)} lines of G-code"
            self.logger.debug(success_msg)
            
            # If there were errors but we generated some output, report as a warning
            if segment_errors and gcode_lines:
                warning_msg = f"Generated {len(gcode_lines)} G-code lines with {len(segment_errors)} errors"
                self.logger.warning(warning_msg)
                
                return ErrorHandler.create_success_response(
                    message=warning_msg,
                    data={
                        "gcode_lines": gcode_lines,
                        "segment_errors": segment_errors,
                        "segment_count": len(path_segments),
                        "success_count": len(gcode_lines) - 1,  # Subtract header line
                        "has_errors": True
                    }
                )
                
            # If everything went well
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "gcode_lines": gcode_lines,
                    "segment_count": len(path_segments),
                    "success_count": len(gcode_lines) - 1,  # Subtract header line
                    "has_errors": False
                }
            )
            
        except Exception as e:
            error_msg = f"Error generating G-code: {str(e)}"
            log_exception(self.logger, error_msg)
            return ErrorHandler.from_exception(
                BaseError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING,
                    details={
                        "error_type": "Exception",
                        "error": str(e),
                        "segment_count": len(path_segments) if path_segments else 0
                    }
                )
            )


# Only initialize if run directly
if __name__ == "__main__":
    # Simple test
    path_generator = ToolPathGenerator()
    success, message, details = path_generator.set_workpiece_parameters(545.5, 555.0, 22.5)
    
    if success:
        print(f"Setup success: {message}")
        
        # Test drilling paths for vertical drilling
        success, message, paths_details = path_generator.calculate_drilling_paths(
            operation_type="vertical_drill",
            point=(35.5, 34.0, 22.5),
            drill_depth=14.0
        )
        
        if success:
            drill_paths = paths_details.get('path_segments', [])
            print(f"\nVertical drilling paths: {len(drill_paths)} segments")
            for i, segment in enumerate(drill_paths):
                coord = segment['coordinates']
                print(f"  {i+1}: {segment['command']} to ({coord[0]}, {coord[1]}, {coord[2]}) - {segment['comment']}")
            
            # Generate G-code for vertical drilling
            gcode_success, gcode_message, gcode_details = path_generator.generate_operation_gcode(drill_paths)
            
            if gcode_success:
                gcode_lines = gcode_details.get('gcode_lines', [])
                print("\nG-code for vertical drilling:")
                for line in gcode_lines:
                    print(f"  {line}")
            else:
                print(f"Error generating G-code: {gcode_message}")
        else:
            print(f"Error calculating drilling paths: {message}")
            if 'details' in paths_details:
                print(f"Details: {paths_details.get('details')}")
        
        # Test drilling paths for horizontal drilling
        success, message, paths_details = path_generator.calculate_drilling_paths(
            operation_type="horizontal_drill",
            point=(510.0, 0, 13.0),
            direction=(1, 0, 0),
            drill_depth=21.5
        )
        
        if success:
            drill_paths = paths_details.get('path_segments', [])
            print(f"\nHorizontal drilling paths: {len(drill_paths)} segments")
            for i, segment in enumerate(drill_paths):
                coord = segment['coordinates']
                print(f"  {i+1}: {segment['command']} to ({coord[0]}, {coord[1]}, {coord[2]}) - {segment['comment']}")
            
            # Generate G-code for horizontal drilling
            gcode_success, gcode_message, gcode_details = path_generator.generate_operation_gcode(drill_paths)
            
            if gcode_success:
                gcode_lines = gcode_details.get('gcode_lines', [])
                print("\nG-code for horizontal drilling:")
                for line in gcode_lines:
                    print(f"  {line}")
            else:
                print(f"Error generating G-code: {gcode_message}")
        else:
            print(f"Error calculating drilling paths: {message}")
            if 'details' in paths_details:
                print(f"Details: {paths_details.get('details')}")
    else:
        print(f"Setup failed: {message}")
        if 'details' in details:
            print(f"Details: {details.get('details')}")