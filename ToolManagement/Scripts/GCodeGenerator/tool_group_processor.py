"""
Tool group processor for handling tool matching and operations.

This module processes groups of drill points, matches them to tools,
and generates the complete G-code for each tool group.
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
from GCodeGenerator.approach_calculator import ApproachCalculator
from GCodeGenerator.gcode_section_builder import GCodeSectionBuilder
from GCodeGenerator.tool_matcher import ToolMatcher


class ToolGroupProcessor:
    """
    Processor for tool groups and drilling operations.
    
    Handles matching tools to drill groups and generating
    all operations for each tool.
    """

    def __init__(
        self, 
        tool_matcher: ToolMatcher | None = None,
        section_builder: GCodeSectionBuilder | None = None,
        approach_calculator: ApproachCalculator | None = None
    ):
        """
        Initialize the tool group processor.
        
        Args:
            tool_matcher: Optional ToolMatcher instance
            section_builder: Optional GCodeSectionBuilder instance
            approach_calculator: Optional ApproachCalculator instance
        """
        self.logger = setup_logger(__name__)
        self.tool_matcher = tool_matcher or ToolMatcher()
        self.section_builder = section_builder or GCodeSectionBuilder()
        self.approach_calculator = approach_calculator or ApproachCalculator()
        
        self.logger.info("ToolGroupProcessor initialized")

    def match_tools_to_groups(
        self, 
        grouped_points: dict[tuple, list]
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Match tools to all drill groups.
        
        Fails immediately if any group cannot be matched to a tool.
        
        Args:
            grouped_points: Dictionary with (diameter, direction) keys and drill point lists
            
        Returns:
            tuple: (success, message, details) where details contains:
                   - tool_groups: List of dicts with 'tool' and 'drill_points'
                   - On error: failed_group and partial results for debugging
        """
        tool_groups = []
        
        # Validate we have groups to process
        if not grouped_points:
            return ErrorHandler.from_exception(
                ValidationError(
                    "No drill groups to process",
                    severity=ErrorSeverity.ERROR
                )
            )
        
        # Process each group
        for group_key, drill_points in grouped_points.items():
            # Validate drill points not empty
            if not drill_points:
                self.logger.warning(f"Empty drill points list for group {group_key}, skipping")
                continue
                
            # Log what we're matching
            self.logger.info(f"Matching tool for group: {group_key} with {len(drill_points)} points")
            
            # Call tool matcher
            success, message, result = self.tool_matcher.match_tool_to_group(group_key)
            
            if not success:
                # Fail immediately - program cannot continue without proper tool
                self.logger.error(f"Tool matching failed: {message}")
                return ErrorHandler.from_exception(
                    ValidationError(
                        message,  # Use the matcher's error message
                        severity=ErrorSeverity.ERROR,
                        details={
                            "failed_group": group_key,
                            "processed_groups": len(tool_groups),
                            "partial_results": tool_groups  # For debugging
                        }
                    )
                )
            
            # Store matched tool with its drill points
            # Note: result contains the tool data directly when successful
            tool_groups.append({
                "tool": result,  # Tool info from matcher
                "drill_points": drill_points,
                "group_key": group_key  # Keep for debugging
            })
            
            self.logger.debug(f"Matched tool #{result.get('tool_number')} for {len(drill_points)} points")
        
        self.logger.info(f"Successfully matched {len(tool_groups)} tool groups")
        
        return ErrorHandler.create_success_response(
            f"Matched {len(tool_groups)} tool groups",
            {"tool_groups": tool_groups}
        )

    def process_tool_group(self, tool_info: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """
        Process a single tool group to generate all its operations.
        
        Combines:
        1. Tool change commands
        2. All drilling operations for this tool
        
        Args:
            tool_info: Dict with 'tool', 'drill_points', 'group_key'
            
        Returns:
            tuple: (success, message, {"lines": [complete tool section]})
        """
        try:
            lines = []
            tool = tool_info["tool"]
            drill_points = tool_info["drill_points"]
            
            # Add tool change commands
            lines.extend(self.section_builder.build_tool_change_commands(tool))
            
            # Process each drill point
            for i, point in enumerate(drill_points):
                # Calculate approach position
                success, msg, approach_data = self.approach_calculator.calculate_approach_position(
                    point["machine_position"],
                    point["extrusion_vector"]
                )
                if not success:
                    return ErrorHandler.from_exception(
                        ValidationError(
                            f"Failed to calculate approach for point {i + 1}: {msg}",
                            severity=ErrorSeverity.ERROR,
                            details={
                                "tool": tool["tool_number"],
                                "point_index": i,
                                "point": point
                            }
                        )
                    )
                
                # Build drilling operation
                approach_pos = approach_data["position"]
                success, msg, drill_lines = self.section_builder.build_drilling_operation(
                    point, approach_pos
                )
                if not success:
                    return ErrorHandler.from_exception(
                        ValidationError(
                            f"Failed to build drilling operation for point {i + 1}: {msg}",
                            severity=ErrorSeverity.ERROR,
                            details={
                                "tool": tool["tool_number"],
                                "point_index": i,
                                "partial_lines": lines
                            }
                        )
                    )
                
                lines.extend(drill_lines["lines"])
            
            self.logger.info(
                f"Processed tool group for tool #{tool['tool_number']} "
                f"with {len(drill_points)} drilling operations"
            )
            
            return ErrorHandler.create_success_response(
                f"Tool group processed for tool #{tool['tool_number']}",
                {"lines": lines}
            )
            
        except Exception as e:
            return ErrorHandler.from_exception(e)


# Example usage if run directly
if __name__ == "__main__":
    processor = ToolGroupProcessor()
    
    # Test data - grouped points
    test_grouped_points = {
        (8.0, (1.0, 0.0, 0.0)): [  # 8mm X+ drilling
            {
                "machine_position": (0, -200, 9),
                "diameter": 8.0,
                "depth": 15.0,
                "extrusion_vector": (1.0, 0.0, 0.0)
            },
            {
                "machine_position": (0, -300, 9),
                "diameter": 8.0,
                "depth": 15.0,
                "extrusion_vector": (1.0, 0.0, 0.0)
            }
        ]
    }
    
    print("Testing Tool Group Processor")
    print("=" * 50)
    
    # Test tool matching
    print("\nMatching tools to groups:")
    success, msg, result = processor.match_tools_to_groups(test_grouped_points)
    
    if success:
        print(f"Success: {msg}")
        tool_groups = result["tool_groups"]
        
        # Test processing first group
        if tool_groups:
            print("\nProcessing first tool group:")
            success, msg, lines_result = processor.process_tool_group(tool_groups[0])
            
            if success:
                print("Generated G-code:")
                for line in lines_result["lines"]:
                    print(f"  {line}")
    else:
        print(f"Error: {msg}")