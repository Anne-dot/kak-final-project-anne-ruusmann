"""
G-code program generator module for orchestrating the complete G-code generation process.

This module coordinates the various components to generate complete G-code programs
from processed drilling data.
"""

import os
import sys
from datetime import datetime
from typing import Any

# Add parent directory to Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import utilities
from Utils.error_utils import ErrorHandler, ErrorSeverity, ValidationError
from Utils.logging_utils import log_exception, setup_logger

# Import local modules
from GCodeGenerator.gcode_section_builder import GCodeSectionBuilder
from GCodeGenerator.tool_group_processor import ToolGroupProcessor


class GCodeProgramGenerator:
    """
    Main orchestrator for generating complete G-code programs.

    This class coordinates the various components to generate
    complete G-code programs from processed drilling data.
    """

    def __init__(self):
        """Initialize the G-code program generator."""
        self.logger = setup_logger(__name__)
        self.section_builder = GCodeSectionBuilder()
        self.tool_processor = ToolGroupProcessor()

        self.logger.info("GCodeProgramGenerator initialized")

    def generate_program(
        self, processing_data: dict[str, Any], program_name: str | None = None
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Generate a complete G-code program from processed data.

        Args:
            processing_data: Data from ProcessingEngine with workpiece and drill points
            program_name: Optional program name

        Returns:
            tuple: (success, message, details with 'gcode_lines')
        """
        try:
            # ===== SECTION 1: VALIDATE INPUT =====
            valid, message, validated_data = self.validate_minimal_data(processing_data)
            if not valid:
                return valid, message, validated_data

            # ===== SECTION 2: EXTRACT DATA =====
            workpiece = validated_data["workpiece"]
            grouped_points = validated_data["grouped_points"]
            
            # Set default program name if not provided
            if not program_name:
                program_name = f"program_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # ===== SECTION 3: MATCH TOOLS TO GROUPS =====
            matched, msg, tool_data = self.tool_processor.match_tools_to_groups(grouped_points)
            if not matched:
                return matched, msg, tool_data

            tool_groups = tool_data["tool_groups"]

            # ===== SECTION 4: BUILD G-CODE PROGRAM =====
            all_lines = []
            
            # Generate header section
            success, msg, header_data = self.section_builder.build_header_section(workpiece, program_name)
            if not success:
                return success, msg, header_data
            all_lines.extend(header_data["lines"])
            
            # Generate tool sections
            for tool_info in tool_groups:
                success, msg, tool_lines = self.tool_processor.process_tool_group(tool_info)
                if not success:
                    # Return error with partial program for debugging
                    return ErrorHandler.from_exception(
                        ValidationError(
                            msg,
                            severity=ErrorSeverity.ERROR,
                            details={"partial_gcode": all_lines}
                        )
                    )
                all_lines.extend(tool_lines["lines"])
            
            # Generate footer section
            success, msg, footer_data = self.section_builder.build_footer_section()
            if not success:
                return success, msg, footer_data
            all_lines.extend(footer_data["lines"])

            # ===== SECTION 5: FINAL SUMMARY =====
            self.logger.info(
                f"Successfully generated G-code program with {len(tool_groups)} tools "
                f"and {len(all_lines)} lines"
            )

            return ErrorHandler.create_success_response(
                "G-code program generated successfully", 
                {
                    "gcode_lines": all_lines,
                    "tool_count": len(tool_groups),
                    "line_count": len(all_lines),
                    "program_name": program_name
                }
            )

        except Exception as e:
            log_exception(self.logger, e, "Error generating G-code program")
            return ErrorHandler.from_exception(e)

    def validate_minimal_data(self, processing_data: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """
        Minimal validation - just verify structure exists.
        If data made it here, it should be valid.

        Args:
            processing_data: Input data from ProcessingEngine

        Returns:
            tuple: (success, message, data) where data is the validated processing_data
        """
        if not processing_data:
            return ErrorHandler.from_exception(
                ValidationError("No processing data provided", severity=ErrorSeverity.ERROR)
            )
        
        # Just verify the expected keys exist
        if "workpiece" in processing_data and "grouped_points" in processing_data:
            return ErrorHandler.create_success_response(
                "Data structure verified", 
                processing_data
            )
        else:
            return ErrorHandler.from_exception(
                ValidationError("Missing expected data structure", severity=ErrorSeverity.ERROR)
            )


# Example usage if run directly
if __name__ == "__main__":
    # Create generator
    generator = GCodeProgramGenerator()
    
    # Test data
    test_data = {
        "workpiece": {
            "width_after_rotation": 400.0,
            "height_after_rotation": 600.0,
            "thickness": 18.0
        },
        "grouped_points": {
            (8.0, (1.0, 0.0, 0.0)): [  # 8mm X+ drilling
                {
                    "machine_position": (0, -200, 9),
                    "diameter": 8.0,
                    "depth": 15.0,
                    "extrusion_vector": (1.0, 0.0, 0.0)
                }
            ]
        }
    }
    
    print("Testing G-code Program Generator")
    print("=" * 50)
    
    # Generate program
    success, message, result = generator.generate_program(test_data, "test_program")
    
    if success:
        print(f"\nSuccess: {message}")
        print(f"Generated {result['line_count']} lines for {result['tool_count']} tools")
        print("\nFirst 10 lines:")
        for line in result["gcode_lines"][:10]:
            print(f"  {line}")
    else:
        print(f"\nError: {message}")