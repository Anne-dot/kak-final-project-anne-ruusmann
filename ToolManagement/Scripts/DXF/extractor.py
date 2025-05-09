"""
DXF Extractor module for identifying and extracting drilling operations.

This module provides functionality to extract drilling operation information
from DXF documents.
"""

import os
import sys
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

            # Process each entity in modelspace
            entity_count = 0
            for entity in modelspace:
                entity_count += 1
                # Extract drill point data if applicable
                drill_data = self._extract_from_entity(entity)
                if drill_data:
                    drill_points.append(drill_data)

            # Return success with extracted drill points
            return ErrorHandler.create_success_response(
                message=f"Successfully extracted {len(drill_points)} drill points from {entity_count} entities",
                data={"drill_points": drill_points}
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
            import re
            
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
            import re
            
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
            
            # Extract diameter from layer name
            diameter_from_layer = self._extract_diameter_from_layer(layer)
            
            # Determine which diameter to use
            if diameter_from_layer is not None:
                # Both diameters available - compare them
                if diameter_from_entity > 0:
                    # Calculate difference as percentage
                    diff_percent = abs(diameter_from_entity - diameter_from_layer) / diameter_from_layer * 100
                    
                    # Log warning if difference exceeds threshold
                    if diff_percent > 2:
                        self.logger.warning(
                            f"DIAMETER MISMATCH for circle on layer '{layer}': "
                            f"Circle geometry: {diameter_from_entity:.3f}mm, "
                            f"Layer specification: {diameter_from_layer:.3f}mm, "
                            f"Difference: {diff_percent:.2f}%"
                        )
                    
                    # Always use layer name value if available
                    diameter = diameter_from_layer
                else:
                    # Circle has zero radius - use layer name
                    diameter = diameter_from_layer
                    self.logger.warning(f"Circle has zero radius, using diameter from layer: {diameter}mm")
            else:
                # Only entity diameter available
                diameter = diameter_from_entity
                self.logger.debug(f"No diameter in layer name, using circle geometry: {diameter}mm")
            
            # Default drilling direction is vertical (down)
            direction = (0, 0, 1)
            
            # Check if extrusion vector is specified
            if hasattr(circle.dxf, "extrusion"):
                extrusion = circle.dxf.extrusion
                # Only use non-zero vectors
                if extrusion != (0, 0, 0):
                    direction = extrusion
            
            # Try to get depth from layer name
            depth = self._extract_depth_from_layer(layer)
            
            # If depth not found in layer name, use default
            if depth is None:
                depth = 10.0  # Default depth in mm
                self.logger.debug(f"Using default depth for circle on layer '{layer}'")
            
            # Create the drill point data
            drill_data = {
                "position": (center.x, center.y, center.z),
                "diameter": diameter,
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