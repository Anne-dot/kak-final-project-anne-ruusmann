"""
DXF Extractor module for identifying and extracting specific entities.

This module provides functionality to extract drilling operations and workpiece
boundaries from DXF documents.
"""

import os
import sys
import re
from typing import Tuple, Dict, Any, List, Optional

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import utilities
from Utils.error_utils import ErrorHandler, ValidationError, ErrorSeverity
from Utils.logging_utils import setup_logger


class DrillPointExtractor:
    """Extracts drilling operation information from DXF documents."""
    
    def __init__(self):
        """Initialize the drill point extractor."""
        self.logger = setup_logger(__name__)
    
    def extract(self, document) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Extract drilling operations from a DXF document.
        
        Args:
            document: An ezdxf document object from the parser
            
        Returns:
            tuple: (success, message, data) where:
                - success is a boolean indicating if extraction was successful
                - message contains success details or error message
                - data contains a dictionary with 'drill_points' list
        """
        self.logger.info("Starting drilling operation extraction")
        
        try:
            # Get the modelspace which contains all entities
            modelspace = document.modelspace()
            
            # This will be populated with drilling information
            drill_points = []
            
            # Track skipped points for reporting
            skipped_points = 0
            issues = []
            
            # Process each entity in modelspace
            entity_count = 0
            for entity in modelspace:
                entity_count += 1
                
                # Is this a potential drilling entity?
                is_potential_drill = (
                    hasattr(entity, 'dxftype') and 
                    hasattr(entity.dxf, 'layer') and
                    ('DRILL' in entity.dxf.layer or 'DRILLING' in entity.dxf.layer)
                )
                
                # Extract drill point data if applicable
                drill_data = self._extract_from_entity(entity)
                
                if drill_data:
                    # Successfully extracted
                    drill_points.append(drill_data)
                elif is_potential_drill:
                    # This looks like a drill point but extraction failed
                    skipped_points += 1
                    
                    # Get position info for better error reporting
                    position = "Unknown"
                    if hasattr(entity.dxf, 'center'):
                        pos = entity.dxf.center
                        position = f"({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})"
                    elif hasattr(entity.dxf, 'location'):
                        pos = entity.dxf.location
                        position = f"({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})"
                    elif hasattr(entity.dxf, 'insert'):
                        pos = entity.dxf.insert
                        position = f"({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})"
                    
                    # Add to issues list for reporting
                    issues.append({
                        "entity_type": entity.dxftype(),
                        "layer": entity.dxf.layer,
                        "position": position
                    })
            
            # Prepare status message with details on skipped points
            if skipped_points > 0:
                message = (f"Extracted {len(drill_points)} drill points. "
                          f"WARNING: {skipped_points} potential drilling entities were skipped "
                          f"due to missing or invalid parameters.")
            else:
                message = f"Successfully extracted {len(drill_points)} drill points from {entity_count} entities"
            
            # Return success with extracted drill points and ALL issues
            return ErrorHandler.create_success_response(
                message=message,
                data={
                    "drill_points": drill_points,
                    "skipped_count": skipped_points,
                    "issues": issues  # Include ALL issues
                }
            )
            
        except Exception as e:
            # Log and return error
            self.logger.error(f"Error in drilling extraction: {str(e)}")
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Failed to extract drilling operations: {str(e)}",
                    severity=ErrorSeverity.ERROR
                )
            )
    
    def _extract_from_entity(self, entity) -> Optional[Dict[str, Any]]:
        """
        Extract drill point data from a single DXF entity.
        
        Args:
            entity: An ezdxf entity object
            
        Returns:
            dict or None: Dictionary with drill point properties if entity
                        represents a drill point, None otherwise
        """
        try:
            # Get entity type and layer
            entity_type = entity.dxftype()
            layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else "unknown"
            
            self.logger.debug(f"Analyzing entity type: {entity_type} on layer: {layer}")
            
            # Extract based on entity type
            if entity_type == "CIRCLE":
                # Circles often represent drilling operations
                return self._extract_from_circle(entity, layer)
                
            elif entity_type == "POINT":
                # Points can also represent drilling operations
                return self._extract_from_point(entity, layer)
                
            elif entity_type == "INSERT":
                # Block inserts sometimes represent drilling symbols
                return self._extract_from_insert(entity, layer)
                
            # Not a drilling entity
            return None
            
        except Exception as e:
            self.logger.warning(f"Error extracting from entity: {str(e)}")
            return None
    
    def _extract_depth_from_layer(self, layer_name: str) -> Optional[float]:
        """
        Extract drilling depth from layer name.
        
        Parses layer names with pattern like "EDGE.DRILL_D8.0_P21.5" 
        where D is diameter and P is depth.
        
        Args:
            layer_name: Name of the layer to parse
            
        Returns:
            float or None: Extracted depth in mm, or None if not found
        """
        try:
            # Pattern for _P{depth} format
            p_pattern = r'_P(\d+(\.\d+)?)'
            p_match = re.search(p_pattern, layer_name)
            if p_match:
                return float(p_match.group(1))
            
            # If we can't find the pattern, return None
            self.logger.debug(f"No depth pattern found in layer '{layer_name}'")
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not extract depth from layer '{layer_name}': {str(e)}")
            return None
    
    def _extract_diameter_from_layer(self, layer_name: str) -> Optional[float]:
        """
        Extract drilling diameter from layer name.
        
        Parses layer names with pattern like "EDGE.DRILL_D8.0_P21.5" 
        where D is diameter and P is depth.
        
        Args:
            layer_name: Name of the layer to parse
            
        Returns:
            float or None: Extracted diameter in mm, or None if not found
        """
        try:
            # Pattern for _D{diameter} format
            d_pattern = r'_D(\d+(\.\d+)?)'
            d_match = re.search(d_pattern, layer_name)
            if d_match:
                return float(d_match.group(1))
            
            # If we can't find the pattern, return None
            self.logger.debug(f"No diameter pattern found in layer '{layer_name}'")
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not extract diameter from layer '{layer_name}': {str(e)}")
            return None
    
    def _extract_from_circle(self, circle, layer) -> Optional[Dict[str, Any]]:
        """
        Extract drilling data from a circle entity.
        
        Args:
            circle: An ezdxf CIRCLE entity
            layer: Layer name of the entity
            
        Returns:
            dict or None: Dictionary with drill point properties
        """
        try:
            # Get circle properties
            center = circle.dxf.center
            radius = circle.dxf.radius
            diameter_from_entity = radius * 2
            position_str = f"({center.x:.2f}, {center.y:.2f}, {center.z:.2f})"
            
            # Verify if this looks like a drilling operation by layer name
            if not ('DRILL' in layer or 'DRILLING' in layer):
                return None
                
            # Extract depth from layer - REQUIRED
            depth = self._extract_depth_from_layer(layer)
            if depth is None:
                self.logger.warning(
                    f"MISSING DEPTH PARAMETER: Circle at {position_str} on layer '{layer}' "
                    f"has no depth information in layer name. Drilling extraction failed for this point."
                )
                return None
                
            # Extract diameter from layer
            diameter_from_layer = self._extract_diameter_from_layer(layer)
            
            # Check for mismatches between layer and entity diameters
            diameter_mismatch = None
            if diameter_from_layer is not None and diameter_from_entity > 0:
                # Calculate difference as percentage
                diff_percent = abs(diameter_from_entity - diameter_from_layer) / diameter_from_layer * 100
                
                # Store mismatch info
                diameter_mismatch = {
                    "percent": diff_percent,
                    "is_significant": diff_percent > 2
                }
                
                # Log warning if difference exceeds threshold
                if diameter_mismatch["is_significant"]:
                    self.logger.warning(
                        f"DIAMETER MISMATCH for circle at {position_str} on layer '{layer}': "
                        f"Circle geometry: {diameter_from_entity:.3f}mm, "
                        f"Layer specification: {diameter_from_layer:.3f}mm, "
                        f"Difference: {diff_percent:.2f}%"
                    )
                
                # Use layer specification as primary diameter
                primary_diameter = diameter_from_layer
            elif diameter_from_layer is not None:
                # Circle has zero radius - use layer name
                primary_diameter = diameter_from_layer
                self.logger.warning(
                    f"Circle at {position_str} has zero radius, "
                    f"using diameter from layer: {primary_diameter}mm"
                )
            elif diameter_from_entity > 0:
                # Only entity diameter available
                primary_diameter = diameter_from_entity
                self.logger.debug(
                    f"No diameter in layer name for circle at {position_str}, "
                    f"using circle geometry: {primary_diameter}mm"
                )
            else:
                # No valid diameter found
                self.logger.warning(
                    f"INVALID DIAMETER: Circle at {position_str} on layer '{layer}' "
                    f"has zero radius and no diameter in layer name. "
                    f"Drilling extraction failed for this point."
                )
                return None
            
            # Default drilling direction is vertical (down)
            direction = (0, 0, 1)
            
            # Check if extrusion vector is specified
            if hasattr(circle.dxf, "extrusion"):
                extrusion = circle.dxf.extrusion
                # Only use non-zero vectors
                if extrusion != (0, 0, 0):
                    direction = extrusion
                    
            # Final validation of parameters
            if primary_diameter <= 0:
                self.logger.warning(
                    f"INVALID DIAMETER: Circle at {position_str} on layer '{layer}' "
                    f"has diameter <= 0. Drilling extraction failed for this point."
                )
                return None
                
            if depth <= 0:
                self.logger.warning(
                    f"INVALID DEPTH: Circle at {position_str} on layer '{layer}' "
                    f"has depth <= 0. Drilling extraction failed for this point."
                )
                return None
            
            # Create the drill point data
            drill_data = {
                "position": (center.x, center.y, center.z),
                "diameter": primary_diameter,  # Main diameter (from layer if available)
                "diameter_geometry": diameter_from_entity,  # Actual geometry
                "diameter_specification": diameter_from_layer,  # From layer spec
                "diameter_mismatch": diameter_mismatch,  # Mismatch info
                "depth": depth,
                "direction": direction,
                "layer": layer,
                "entity_type": "CIRCLE"
            }
            
            self.logger.debug(f"Extracted drill point: {drill_data}")
            return drill_data
            
        except Exception as e:
            self.logger.warning(f"Error extracting from circle: {str(e)}")
            return None
            
    def _extract_from_point(self, entity, layer) -> Optional[Dict[str, Any]]:
        """
        Extract drilling data from a point entity.
        
        NOTE: This method is not yet implemented and will return None.
        POINT entities will be ignored until implementation is complete.
        
        Args:
            entity: An ezdxf POINT entity
            layer: Layer name of the entity
            
        Returns:
            dict or None: Dictionary with drill point properties (currently None)
        """
        self.logger.debug(f"POINT entity extraction not yet implemented - skipping")
        return None
        
    def _extract_from_insert(self, entity, layer) -> Optional[Dict[str, Any]]:
        """
        Extract drilling data from an insert entity.
        
        NOTE: This method is not yet implemented and will return None.
        INSERT entities will be ignored until implementation is complete.
        
        Args:
            entity: An ezdxf INSERT entity
            layer: Layer name of the entity
            
        Returns:
            dict or None: Dictionary with drill point properties (currently None)
        """
        self.logger.debug(f"INSERT entity extraction not yet implemented - skipping")
        return None


class WorkpieceExtractor:
    """Extracts workpiece boundaries from DXF documents."""
    
    def __init__(self):
        """Initialize the workpiece extractor."""
        self.logger = setup_logger(__name__)
    
    def extract(self, document) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Extract workpiece data from a DXF document.
        
        Args:
            document: An ezdxf document object from the parser
            
        Returns:
            tuple: (success, message, data) where:
                - success is a boolean indicating if extraction was successful
                - message contains success details or error message
                - data contains workpiece information
        """
        self.logger.info("Starting workpiece extraction")
        
        try:
            # Get the modelspace
            modelspace = document.modelspace()
            
            # First, try to find polylines on typical workpiece layers
            workpiece_data = self._extract_from_polylines(modelspace)
            
            if not workpiece_data:
                # No workpiece boundary found
                self.logger.info("No workpiece boundary found in the document")
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=f"No workpiece boundary found. Workpiece extraction requires a closed polyline on a 'PANEL_*' or 'OUTLINE_*' layer.",
                        severity=ErrorSeverity.ERROR
                    )
                )
            
            # Return the workpiece data
            return ErrorHandler.create_success_response(
                message=f"Successfully extracted workpiece boundary with {len(workpiece_data['corner_points'])} points",
                data={"workpiece": workpiece_data}
            )
            
        except Exception as e:
            # Log and return error
            self.logger.error(f"Error extracting workpiece: {str(e)}")
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Failed to extract workpiece boundary: {str(e)}",
                    severity=ErrorSeverity.ERROR
                )
            )
    
    def _extract_from_polylines(self, modelspace) -> Optional[Dict[str, Any]]:
        """
        Extract workpiece from POLYLINE entities in the modelspace.
        
        Specifically targets layers named 'PANEL_*' or 'OUTLINE_*' as identified
        in the test DXF files.
        
        Args:
            modelspace: The modelspace of the DXF document
            
        Returns:
            dict or None: Workpiece data if found, None otherwise
        """
        # Look for all polylines
        polylines = []
        
        # Try first for new-style LWPOLYLINE
        for entity in modelspace:
            if entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                if hasattr(entity.dxf, 'layer'):
                    layer = entity.dxf.layer
                    # Check if it's on a workpiece layer
                    if 'PANEL_' in layer or 'OUTLINE_' in layer:
                        polylines.append(entity)
        
        if not polylines:
            self.logger.warning("No workpiece polylines found on PANEL_* or OUTLINE_* layers")
            return None
        
        # Use the first workpiece polyline found (typically there's only one)
        workpiece_polyline = polylines[0]
        layer = workpiece_polyline.dxf.layer
        
        # Extract corner points
        corner_points = []
        if workpiece_polyline.dxftype() == 'LWPOLYLINE':
            # For LWPOLYLINE
            corner_points = [(point[0], point[1], 0) for point in workpiece_polyline.vertices()]
        else:
            # For old-style POLYLINE
            corner_points = [(vertex.dxf.location[0], vertex.dxf.location[1], 0) 
                            for vertex in workpiece_polyline.vertices]
        
        # Validate corner points
        if len(corner_points) < 3:
            self.logger.error(f"Invalid workpiece: Polyline on layer '{layer}' has fewer than 3 corner points")
            return None
        
        # Calculate dimensions
        min_x = min(p[0] for p in corner_points)
        max_x = max(p[0] for p in corner_points)
        min_y = min(p[1] for p in corner_points)
        max_y = max(p[1] for p in corner_points)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Validate dimensions
        if width <= 0 or height <= 0:
            self.logger.error(f"Invalid workpiece dimensions: width={width}, height={height}")
            return None
        
        # Extract thickness from layer name - REQUIRED
        thickness = self._extract_thickness_from_layer(layer)
        
        # Strict validation: Thickness is required
        if thickness is None:
            self.logger.error(
                f"MISSING THICKNESS: Workpiece on layer '{layer}' has no thickness "
                f"information in layer name. Workpiece extraction failed."
            )
            return None
            
        # Validate thickness
        if thickness <= 0:
            self.logger.error(f"Invalid workpiece thickness: {thickness}mm")
            return None
        
        # Create workpiece data
        workpiece_data = {
            "corner_points": corner_points,
            "width": width,
            "height": height,
            "thickness": thickness,
            "layer": layer,
            "entity_type": workpiece_polyline.dxftype()
        }
        
        self.logger.info(f"Extracted workpiece: {width:.2f}mm x {height:.2f}mm x {thickness:.2f}mm")
        return workpiece_data
    
    def _extract_thickness_from_layer(self, layer_name: str) -> Optional[float]:
        """
        Extract thickness information from layer name.
        
        Based on patterns seen in test files like "OUTLINE_T22.5_F1" or "PANEL_Egger22mm".
        
        Args:
            layer_name: Name of the layer
            
        Returns:
            float or None: Extracted thickness in mm, None if not found
        """
        try:
            # Pattern 1: T22.5 format (as in OUTLINE_T22.5_F1)
            t_pattern = r'T(\d+(\.\d+)?)'
            t_match = re.search(t_pattern, layer_name)
            if t_match:
                return float(t_match.group(1))
            
            # Pattern 2: 22mm format (as in PANEL_Egger22mm)
            mm_pattern = r'(\d+)mm'
            mm_match = re.search(mm_pattern, layer_name)
            if mm_match:
                return float(mm_match.group(1))
            
            # No thickness pattern found
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not extract thickness from layer '{layer_name}': {str(e)}")
            return None


class DXFExtractor:
    """
    Main extraction coordinator using specialized extractors.

    This class orchestrates the extraction process, delegating to specialized
    extractors and combining their results. Both workpiece and drill points
    must be successfully extracted for the process to succeed.
    """

    def __init__(self):
        """Initialize the DXF extractor with specialized extractors."""
        self.drill_extractor = DrillPointExtractor()
        self.workpiece_extractor = WorkpieceExtractor()
        self.logger = setup_logger(__name__)

    def process(self, document) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process a DXF document to extract all relevant entities.

        NOTE: This implementation requires BOTH workpiece and drill points
        to be successfully extracted for the process to succeed.

        Args:
            document: An ezdxf document object from the parser

        Returns:
            tuple: (success, message, data) where:
                - success is a boolean indicating if extraction was successful
                - message contains success details or error message
                - data contains 'drill_points' and 'workpiece' information
        """
        self.logger.info("Processing DXF document for complete extraction")

        try:
            # Extract workpiece first (typically one per document)
            wp_success, wp_message, wp_result = self.workpiece_extractor.extract(document)

            # If workpiece extraction failed, fail the entire process
            if not wp_success:
                self.logger.error(f"Workpiece extraction failed: {wp_message}")
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=f"Failed to extract workpiece. {wp_message}",
                        severity=ErrorSeverity.ERROR
                    )
                )

            # Extract drill points
            drill_success, drill_message, drill_result = self.drill_extractor.extract(document)

            # If drill point extraction failed or no points found, fail the entire process
            if not drill_success or not drill_result.get("drill_points", []):
                self.logger.error(f"Drill point extraction failed or no points found: {drill_message}")
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=f"Failed to extract drill points or none found. {drill_message}",
                        severity=ErrorSeverity.ERROR
                    )
                )

            # Both succeeded - prepare combined result
            combined_data = {
                "workpiece": wp_result["workpiece"],
                "drill_points": drill_result["drill_points"],
                "skipped_drill_points": drill_result.get("skipped_count", 0),
                "issues": drill_result.get("issues", [])
            }

            # Success message with details
            wp = combined_data["workpiece"]
            message = (
                f"Extraction complete. "
                f"Workpiece: {wp['width']:.1f}x{wp['height']:.1f}x{wp['thickness']:.1f}mm, "
                f"Drill points: {len(combined_data['drill_points'])}"
            )

            if combined_data["skipped_drill_points"] > 0:
                message += f", {combined_data['skipped_drill_points']} points skipped"

            return ErrorHandler.create_success_response(message=message, data=combined_data)

        except Exception as e:
            # Log and return error
            self.logger.error(f"Error in DXF extraction: {str(e)}")
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Failed to process DXF document: {str(e)}",
                    severity=ErrorSeverity.ERROR
                )
            )