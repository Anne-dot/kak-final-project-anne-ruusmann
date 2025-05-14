"""
Tool matcher module for selecting appropriate tools for drilling operations.

This module provides functionality for matching drill operations to appropriate
tools in the tool database, ensuring exact diameter matches for drills.
"""

import os
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional, Union

# Add parent directory to Python path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import utilities
from Utils.config import AppConfig
from Utils.error_utils import ErrorHandler, ValidationError, ErrorSeverity
from Utils.logging_utils import setup_logger
from Utils.file_utils import FileUtils


class ToolMatcher:
    """
    Class for matching drilling operations to appropriate tools.
    
    This class provides functionality for finding exact tool matches
    for drilling operations based on diameter and direction.
    """
    
    def __init__(self, tool_data_path: Optional[str] = None):
        """
        Initialize the tool matcher.
        
        Args:
            tool_data_path: Optional custom path to tool data CSV file.
                           If not provided, uses the default path from config.
        """
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        
        # Use provided tool data path or get from config
        self.tool_data_path = tool_data_path or str(AppConfig.paths.get_tool_data_path())
        
        self.logger.info(f"ToolMatcher initialized with tool data: {self.tool_data_path}")
    
    def match_tool_to_group(
        self, 
        group_key: Tuple[float, Tuple[float, float, float]]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Match a drilling group to a tool.
        
        Args:
            group_key: Tuple of (diameter, direction_vector) from ProcessingEngine
            
        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if matching was successful
                - message contains success details or error message
                - details contains the matched tool information or error details
        """
        try:
            # Validate group key format
            if not isinstance(group_key, tuple) or len(group_key) != 2:
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=f"Invalid group key format: {group_key}",
                        severity=ErrorSeverity.ERROR
                    )
                )
                
            # Extract diameter and direction
            diameter, direction_vector = group_key
            self.logger.info(f"Looking for tool with diameter {diameter} and direction {direction_vector}")
            
            # Step 1: Convert direction vector to code
            direction_code = self._convert_vector_to_direction_code(direction_vector)
            if direction_code is None:
                return ErrorHandler.from_exception(
                    ValidationError(
                        message=f"Unsupported direction vector: {direction_vector}",
                        severity=ErrorSeverity.ERROR
                    )
                )
                
            # Step 2: Search for matching tool
            success, message, result = self._search_for_matching_tool(
                diameter, direction_code
            )
            if not success:
                return success, message, result
                
            # Step 3: Format the matched tool data
            selected_tool = result["tool"]
            formatted_tool = self._prepare_tool_data_for_response(selected_tool)
            
            # Return the formatted result
            return ErrorHandler.create_success_response(
                message=f"Found matching tool #{formatted_tool['tool_number']} for {diameter}mm drilling",
                data=formatted_tool
            )
            
        except Exception as e:
            # Log and return any unexpected errors
            self.logger.error(f"Error matching tool: {str(e)}")
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Failed to match tool: {str(e)}",
                    severity=ErrorSeverity.ERROR
                )
            )
    
    def _convert_vector_to_direction_code(
        self, 
        vector: Tuple[float, float, float]
    ) -> Optional[int]:
        """
        Convert a direction vector to a numeric direction code.
        
        Args:
            vector: 3D direction vector (x, y, z)
            
        Returns:
            int: Direction code (1-5) or None if no match
        """
        # Use mapping directly from config
        return AppConfig.tool.DIRECTION_VECTOR_MAPPING.get(vector)
    
    def _search_for_matching_tool(
        self, 
        diameter: float,
        direction_code: int
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Search for a tool matching the given criteria.
        
        Args:
            diameter: Required tool diameter
            direction_code: Direction code (1-5)
            
        Returns:
            tuple: (success, message, details) with matching tool
        """
        # Read the tool data CSV
        success, message, data = FileUtils.read_csv(self.tool_data_path)
        if not success:
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"Failed to read tool data: {message}",
                    severity=ErrorSeverity.ERROR
                )
            )
        
        # Find tools matching criteria
        matching_tools = []
        for row in data.get("rows", []):
            try:
                # Skip if missing required fields
                if not all(key in row for key in ["tool_number", "diameter", "tool_direction"]):
                    continue
                
                # Convert numeric fields
                row_diameter = float(row["diameter"])
                row_direction = int(row["tool_direction"])
                
                # Check for exact diameter and matching direction
                if (abs(row_diameter - diameter) < 0.01 and
                    row_direction == direction_code):
                    matching_tools.append(row)
            except (ValueError, KeyError, TypeError):
                # Skip rows with invalid data
                continue
        
        # Return error if no matches found
        if not matching_tools:
            return ErrorHandler.from_exception(
                ValidationError(
                    message=f"No exact diameter match found for {diameter}mm tool with direction {direction_code}",
                    severity=ErrorSeverity.ERROR,
                    details={
                        "diameter": diameter,
                        "direction_code": direction_code
                    }
                )
            )
        
        # Return first matching tool
        return ErrorHandler.create_success_response(
            message=f"Found {len(matching_tools)} matching tools",
            data={"tool": matching_tools[0]}
        )
    
    def _prepare_tool_data_for_response(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format tool data for the API response.
        
        Args:
            tool: Raw tool data from CSV
            
        Returns:
            dict: Formatted tool data with all available fields
        """
        # Start with a dictionary for required fields
        formatted_tool = {
            "tool_number": int(tool["tool_number"]),
            "diameter": float(tool["diameter"]),
            "direction": int(tool["tool_direction"])
        }
        
        # Convert numeric fields if present
        numeric_fields = [
            "tool_length",
            "max_working_length", 
            "tool_holder_z_offset"
        ]
        
        for field in numeric_fields:
            if field in tool and tool[field]:
                try:
                    formatted_tool[field] = float(tool[field])
                except (ValueError, TypeError):
                    formatted_tool[field] = 0.0
        
        # Convert boolean fields
        if "in_spindle" in tool:
            formatted_tool["in_spindle"] = tool["in_spindle"] == "1"
        
        # Copy all other fields directly
        for key, value in tool.items():
            if key not in formatted_tool and value:
                formatted_tool[key] = value
        
        return formatted_tool


# Example usage if run directly
if __name__ == "__main__":
    # Create a tool matcher
    matcher = ToolMatcher()
    
    # Example group keys to test
    test_groups = [
        (8.0, (0.0, 0.0, 1.0)),   # 8mm vertical drill (direction 5)
        (8.0, (1.0, 0.0, 0.0)),   # 8mm horizontal drill, X+ (direction 1)
        (10.0, (0.0, 1.0, 0.0)),  # 10mm horizontal drill, Y+ (direction 3)
        (12.0, (-1.0, 0.0, 0.0)), # 12mm horizontal drill, X- (direction 2)
    ]
    
    # Test each group
    print("Testing Tool Matcher:")
    print("---------------------")
    for group in test_groups:
        diameter, direction = group
        print(f"\nLooking for: {diameter}mm drill with direction {direction}")
        
        success, message, result = matcher.match_tool_to_group(group)
        if success:
            print(f"  SUCCESS: {message}")
            print(f"  Tool #{result['tool_number']} - {result.get('description', '')}")
            print(f"  Diameter: {result['diameter']}mm, Direction: {result['direction']}")
        else:
            print(f"  ERROR: {message}")