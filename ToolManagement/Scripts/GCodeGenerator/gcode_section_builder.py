"""
G-code section builder for constructing program sections.

This module handles building individual sections of G-code programs
including headers, tool changes, drilling operations, and footers.
"""

import os
import sys
from datetime import datetime
from typing import Any

# Add parent directory to Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import utilities
from Utils.error_utils import ErrorHandler, ErrorSeverity, ValidationError
from Utils.logging_utils import setup_logger

# Import local modules
from GCodeGenerator.drilling_operations import generate_drilling_sequence
from GCodeGenerator.machine_settings import MachineSettings


class GCodeSectionBuilder:
    """
    Builder for G-code program sections.
    
    Handles creation of individual G-code sections like headers,
    tool changes, drilling operations, and footers.
    """

    def __init__(self, machine_settings: MachineSettings | None = None):
        """
        Initialize the section builder.
        
        Args:
            machine_settings: Optional MachineSettings instance
        """
        self.logger = setup_logger(__name__)
        self.machine_settings = machine_settings or MachineSettings()
        
        self.logger.info("GCodeSectionBuilder initialized")

    def build_header_section(
        self, 
        workpiece: dict[str, Any], 
        program_name: str
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Build G-code header section using machine settings.
        
        Args:
            workpiece: Workpiece data with dimensions
            program_name: Name for the program
            
        Returns:
            tuple: (success, message, details) with header lines
        """
        try:
            # Get rotated dimensions - these are what the operator needs
            width = workpiece.get("width_after_rotation")
            height = workpiece.get("height_after_rotation")
            thickness = workpiece.get("thickness")
            
            # Validate all dimensions exist - no defaults!
            if width is None or height is None or thickness is None:
                return ErrorHandler.from_exception(
                    ValidationError(
                        "Missing required workpiece dimensions",
                        severity=ErrorSeverity.ERROR,
                        details={
                            "width_after_rotation": width,
                            "height_after_rotation": height,
                            "thickness": thickness
                        }
                    )
                )
            
            # Get complete header from machine_settings (includes attribution)
            header_commands = self.machine_settings.get_default_gcode_header(
                {"width": width, "height": height, "thickness": thickness},
                program_name
            )
            
            # Convert command/comment dicts to G-code lines
            lines = []
            for cmd in header_commands:
                if cmd["command"] == "(":
                    # Pure comment line - wrap in parentheses
                    lines.append(f"({cmd['comment']})")
                else:
                    # Command with comment
                    lines.append(f"{cmd['command']} ({cmd['comment']})")
            
            return ErrorHandler.create_success_response(
                "Header section built",
                {"lines": lines}
            )
            
        except Exception as e:
            return ErrorHandler.from_exception(e)

    def build_tool_change_commands(self, tool: dict[str, Any]) -> list[str]:
        """
        Build tool change and spindle start commands.
        
        Simple method that creates two lines:
        - Tool change command (M6 handles spindle stop internally)
        - Spindle start command
        
        Args:
            tool: Tool data with tool_number, diameter, and tool_direction
            
        Returns:
            list: Two G-code lines for tool change
        """
        lines = []
        
        # Get direction description for the comment
        direction_desc = ""
        if "direction" in tool:
            direction_map = {
                1: "X+",  # Left to Right
                2: "X-",  # Right to Left  
                3: "Y+",  # Front to Back
                4: "Y-",  # Back to Front
                5: "Z+"   # Vertical
            }
            direction_desc = f" dir:{direction_map.get(tool['direction'], '?')}"
        
        lines.append(f"T{tool['tool_number']}M6 (Load {tool['diameter']}mm horizontal drill{direction_desc})")
        lines.append(f"M03 S{self.machine_settings.get_spindle_speed()} (Start spindle)")
        return lines

    def build_drilling_operation(
        self,
        drill_point: dict[str, Any],
        approach_position: tuple[float, float]
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Build G-code for a single drilling operation.
        
        Creates positioning command and drilling sequence.
        
        Args:
            drill_point: Drill point data
            approach_position: Pre-calculated approach position
            
        Returns:
            tuple: (success, message, {"lines": [...]})
        """
        try:
            lines = []
            
            # Position at approach location
            approach_x, approach_y = approach_position
            lines.append(
                f"G00 X{self.machine_settings.format_coordinate(approach_x)} "
                f"Y{self.machine_settings.format_coordinate(approach_y)} "
                f"(Position at approach location)"
            )
            
            # Generate drilling sequence
            success, msg, drill_data = generate_drilling_sequence(drill_point, self.machine_settings)
            if not success:
                return success, msg, drill_data
            
            lines.extend(drill_data["gcode_lines"])
            
            return ErrorHandler.create_success_response(
                "Drilling operation built",
                {"lines": lines}
            )
            
        except Exception as e:
            return ErrorHandler.from_exception(e)

    def build_footer_section(self) -> tuple[bool, str, dict[str, Any]]:
        """
        Build G-code footer section.
        
        Uses machine_settings.get_default_gcode_footer() which includes:
        - M09 (Coolant off)
        - M05 (Spindle off)
        - T0 (No tool)
        - M30 (Program end)
        
        Returns:
            tuple: (success, message, {"lines": [...]})
        """
        try:
            # Get footer commands from machine_settings
            footer_commands = self.machine_settings.get_default_gcode_footer()
            
            # Convert to G-code lines
            lines = []
            for cmd in footer_commands:
                if cmd["command"] == "(":
                    # Pure comment line
                    lines.append(cmd["comment"])
                else:
                    # Command with comment
                    lines.append(f"{cmd['command']} ({cmd['comment']})")
            
            return ErrorHandler.create_success_response(
                "Footer section built",
                {"lines": lines}
            )
            
        except Exception as e:
            return ErrorHandler.from_exception(e)


# Example usage if run directly
if __name__ == "__main__":
    builder = GCodeSectionBuilder()
    
    # Test workpiece data
    workpiece = {
        "width_after_rotation": 400.0,
        "height_after_rotation": 600.0,
        "thickness": 18.0
    }
    
    print("Testing G-code Section Builder")
    print("=" * 50)
    
    # Test header
    print("\nBuilding header section:")
    success, msg, result = builder.build_header_section(workpiece, "test_program")
    if success:
        for line in result["lines"]:
            print(f"  {line}")
    
    # Test tool change
    print("\nBuilding tool change commands:")
    tool = {"tool_number": 22, "diameter": 8.0}
    lines = builder.build_tool_change_commands(tool)
    for line in lines:
        print(f"  {line}")
    
    # Test footer
    print("\nBuilding footer section:")
    success, msg, result = builder.build_footer_section()
    if success:
        for line in result["lines"]:
            print(f"  {line}")