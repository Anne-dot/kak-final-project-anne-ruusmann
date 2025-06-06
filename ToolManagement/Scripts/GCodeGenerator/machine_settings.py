"""
Machine settings module for G-code generation.

This module provides machine-specific settings and parameters for
generating G-code, particularly for horizontal drilling operations.
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to Python path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import utilities
from Utils.config import AppConfig
from Utils.logging_utils import setup_logger


class MachineSettings:
    """
    Class for managing machine-specific settings for G-code generation.

    This class provides settings and parameters for generating machine-specific
    G-code, with a focus on horizontal drilling operations.
    """

    def __init__(self, custom_settings: dict[str, Any] | None = None):
        """
        Initialize machine settings.

        Args:
            custom_settings: Optional dictionary of custom settings to override defaults
        """
        # Set up logger for this class
        self.logger = setup_logger(__name__)

        # Initialize with default settings
        self.settings = {
            # Feed rates
            "drilling_feed_rate": AppConfig.gcode.DRILLING_FEED_RATE,
            "rapid_feed_rate": AppConfig.gcode.RAPID_POSITIONING_FEED_RATE,
            "retraction_feed_rate": AppConfig.gcode.RETRACTION_FEED_RATE,
            # Spindle settings
            "spindle_speed": AppConfig.gcode.DEFAULT_SPINDLE_SPEED,
            # Safety parameters
            "approach_distance": AppConfig.gcode.SAFE_APPROACH_DISTANCE,
            "clearance_distance": AppConfig.gcode.SAFE_CLEARANCE_DISTANCE,
            "z_height_margin": AppConfig.gcode.SAFE_Z_HEIGHT_MARGIN,
            # Coordinate system thresholds
            "workpiece_height_threshold": AppConfig.gcode.WORKPIECE_HEIGHT_THRESHOLD,
            # G-code formatting
            "decimal_precision": AppConfig.gcode.DECIMAL_PRECISION,
            "use_line_numbers": AppConfig.gcode.USE_LINE_NUMBERS,
            "line_number_increment": AppConfig.gcode.LINE_NUMBER_INCREMENT,
        }

        # Override with custom settings if provided
        if custom_settings:
            for key, value in custom_settings.items():
                if key in self.settings:
                    self.settings[key] = value
                    self.logger.info(f"Overriding setting {key} with value {value}")

        # Load tool change height from m6start macro
        self._tool_change_height = self._read_tool_change_height_from_macro()

        self.logger.info("MachineSettings initialized")

    def get_feed_rate(self, operation_type: str) -> float:
        """
        Get the appropriate feed rate for a specific operation.

        Args:
            operation_type: Type of operation ('drilling', 'rapid', 'retraction')

        Returns:
            float: Feed rate in mm/min
        """
        if operation_type == "drilling":
            return self.settings["drilling_feed_rate"]
        if operation_type == "rapid":
            return self.settings["rapid_feed_rate"]
        if operation_type == "retraction":
            return self.settings["retraction_feed_rate"]
        # Default to drilling feed rate if unknown
        self.logger.warning(f"Unknown operation type: {operation_type}, using drilling feed rate")
        return self.settings["drilling_feed_rate"]

    def get_approach_distance(self) -> float:
        """
        Get the safe approach distance before drilling.

        Returns:
            float: Approach distance in mm
        """
        return self.settings["approach_distance"]

    def get_clearance_distance(self) -> float:
        """
        Get the clearance distance after drilling.

        Returns:
            float: Clearance distance in mm
        """
        return self.settings["clearance_distance"]

    def get_safe_z_height(self) -> float:
        """
        Get the safe Z height for tool changes and movements.

        This value is read from the m6start.m1s macro to maintain
        a single source of truth.

        Returns:
            float: Safe Z height in mm
            
        Raises:
            RuntimeError: If the safe Z height cannot be determined from macro
        """
        if self._tool_change_height is None:
            raise RuntimeError(
                "CRITICAL: Could not read TOOL_CHANGE_HEIGHT from m6start.m1s macro. "
                "This is a safety-critical value and must be properly configured."
            )
        return self._tool_change_height

    def get_spindle_speed(self) -> int:
        """
        Get the spindle speed for drilling operations.

        Returns:
            int: Spindle speed in RPM
        """
        return int(self.settings["spindle_speed"])

    def _read_tool_change_height_from_macro(self) -> float | None:
        """
        Extract TOOL_CHANGE_HEIGHT value from m6start.m1s macro file.

        This ensures Python uses the same value as the VBScript macro,
        maintaining a single source of truth for the MVP.

        Returns:
            float: Tool change height value if found
            None: If value cannot be read (triggers safety error)
        """
        # Try multiple possible macro paths
        mach3_root = AppConfig.paths.DEFAULT_MACH3_ROOT
        macro_paths = [
            mach3_root / "macros" / "Mach3Development" / "m6Start.m1s",
            mach3_root / "macros" / "Mach3Mill" / "m6start.m1s",
            Path("C:/Mach3/macros/Mach3Mill/m6start.m1s"),
        ]
        
        for macro_path in macro_paths:
            if macro_path.exists():
                try:
                    with open(macro_path, 'r') as f:
                        content = f.read()
                    
                    # Look for: Const TOOL_CHANGE_HEIGHT = 50
                    match = re.search(r'Const\s+TOOL_CHANGE_HEIGHT\s*=\s*(\d+(?:\.\d+)?)', content)
                    if match:
                        height = float(match.group(1))
                        self.logger.info(f"Read TOOL_CHANGE_HEIGHT={height} from {macro_path}")
                        return height
                    
                except Exception as e:
                    self.logger.error(f"Error reading macro file {macro_path}: {e}")
                    continue
        
        # Log all paths tried for debugging
        self.logger.error(
            f"CRITICAL: Could not find TOOL_CHANGE_HEIGHT in any macro file. Tried: {[str(p) for p in macro_paths]}"
        )
        return None

    def get_positioning_commands(self) -> dict[str, str]:
        """
        Get the M-code commands for horizontal drill positioning.

        Returns:
            dict: Dictionary with positioning command keys and M-codes
        """
        # Map of positioning commands to M-codes
        commands = {
            "safe_z_positioning": "M151",  # Safe Z height positioning
            "tooltip_positioning": "M152",  # Tooltip Z positioning
        }

        self.logger.info("Retrieved horizontal drill positioning commands")
        return commands

    def get_vector_axis_info(self, direction_vector: tuple[float, float, float]) -> dict[str, Any]:
        """
        Extract axis information from a direction vector.

        Args:
            direction_vector: 3D direction vector (x, y, z)

        Returns:
            dict: Axis information with keys 'axis', 'direction', 'description'
        """
        # Map vectors to axis information with minimal descriptions
        vector_map = {
            (1.0, 0.0, 0.0): {"axis": "X", "direction": 1, "description": "X+"},
            (-1.0, 0.0, 0.0): {"axis": "X", "direction": -1, "description": "X-"},
            (0.0, 1.0, 0.0): {"axis": "Y", "direction": 1, "description": "Y+"},
            (0.0, -1.0, 0.0): {"axis": "Y", "direction": -1, "description": "Y-"},
        }

        # Return the mapped info or a default if not found
        if direction_vector in vector_map:
            return vector_map[direction_vector]
        self.logger.warning(f"Unsupported direction vector: {direction_vector}")
        return {"axis": "?", "direction": 0, "description": "Unknown"}

    def get_coordinate_system(self, workpiece_dimensions: dict[str, float]) -> dict[str, str]:
        """
        Determine the appropriate coordinate system based on workpiece dimensions.

        Args:
            workpiece_dimensions: Dictionary with 'width', 'height', etc. keys

        Returns:
            dict: Dictionary with 'command' and 'comment' keys
        """
        # Get workpiece height (Y dimension)
        workpiece_height = workpiece_dimensions.get("height", 0.0)

        # Get threshold from config
        threshold = self.settings.get(
            "workpiece_height_threshold", AppConfig.gcode.WORKPIECE_HEIGHT_THRESHOLD
        )

        # Select coordinate system based on workpiece height
        if workpiece_height > threshold:
            coordinate_system = AppConfig.gcode.COORDINATE_SYSTEM_LARGE
            comment = f"Use fixture offset 2 for workpiece height > {threshold}mm"
        else:
            coordinate_system = AppConfig.gcode.COORDINATE_SYSTEM_SMALL
            comment = f"Use fixture offset 3 for workpiece height <= {threshold}mm"

        self.logger.info(
            f"Selected coordinate system {coordinate_system} for workpiece height {workpiece_height}mm"
        )

        return {"command": coordinate_system, "comment": comment}

    def format_coordinate(self, value: float) -> str:
        """
        Format a coordinate value according to the decimal precision setting.

        Args:
            value: Coordinate value to format

        Returns:
            str: Formatted coordinate string
        """
        # Format with the specified decimal precision
        format_str = f"{{:.{self.settings['decimal_precision']}f}}"
        return format_str.format(value)

    def format_comment(self, comment: str) -> str:
        """
        Format a comment according to the comment style setting.

        Args:
            comment: Comment text

        Returns:
            str: Formatted comment
        """
        # Currently only supports parentheses style
        return f"({comment})"

    def get_line_number(self, index: int) -> str:
        """
        Generate a line number based on the index and settings.

        Args:
            index: Sequential index (0-based)

        Returns:
            str: Formatted line number (e.g., "N1")
        """
        if not self.settings["use_line_numbers"]:
            return ""

        line_num = 1 + (index * self.settings["line_number_increment"])
        return f"N{line_num}"

    def get_default_gcode_header(
        self, workpiece_dimensions: dict[str, float], program_name: str = "program"
    ) -> list[dict[str, str]]:
        """
        Get the default G-code header commands.
        
        Includes:
        - Attribution comment (DXF to G-code Generator - Anne Ruusmann)
        - Generation timestamp
        - Program name
        - Workpiece dimensions
        - Machine setup commands (units, positioning, plane, feed mode)
        - Coordinate system selection based on workpiece height
        - Operator confirmation prompt (M00)

        Args:
            workpiece_dimensions: Dictionary with workpiece dimensions
                                 Must contain 'width', 'height', and 'thickness' keys
            program_name: Name of the program or file (default: "program")

        Returns:
            list: List of dictionaries with 'command' and 'comment' keys

        Raises:
            ValueError: If workpiece dimensions are missing required keys
        """
        # Validate required workpiece dimensions
        required_dimensions = ["width", "height", "thickness"]
        for dim in required_dimensions:
            if dim not in workpiece_dimensions:
                raise ValueError(f"Missing required workpiece dimension: {dim}")

        # Get the appropriate coordinate system based on workpiece dimensions
        coordinate_system = self.get_coordinate_system(workpiece_dimensions)

        # Format workpiece dimensions for display (rounded to 1 decimal place for woodworking)
        width = round(workpiece_dimensions["width"], 1)
        height = round(workpiece_dimensions["height"], 1)
        thickness = round(workpiece_dimensions["thickness"], 1)

        # Create workpiece dimensions strings
        dimensions_str_compact = f"{width:.1f}x{height:.1f}x{thickness:.1f}"
        dimensions_str_readable = f"{width:.1f} x {height:.1f} x {thickness:.1f} mm"

        # Create a clear message about workpiece placement with specific G-code offset
        coordinate_code = coordinate_system["command"]  # G55 or G56
        if coordinate_code == AppConfig.gcode.COORDINATE_SYSTEM_LARGE:
            placement_message = f"LARGE WORKPIECE {dimensions_str_compact}mm - Confirm in {coordinate_code} position"
        else:
            placement_message = (
                f"WORKPIECE {dimensions_str_compact}mm - Confirm in {coordinate_code} position"
            )

        # Return the complete header with attribution, timestamp, and machine setup
        return [
            {"command": "(", "comment": "Generated by DXF to G-code Generator - Anne Ruusmann"},
            {"command": "(", "comment": f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
            # TODO: Program name should include original DXF filename instead of timestamp
            {"command": "(", "comment": f"Program name: {program_name}"},
            {"command": "(", "comment": f"Workpiece dimensions: {dimensions_str_readable}"},
            {"command": AppConfig.gcode.DEFAULT_UNITS, "comment": "Set units to mm"},
            {"command": AppConfig.gcode.DEFAULT_POSITIONING, "comment": "Set absolute positioning"},
            {"command": AppConfig.gcode.DEFAULT_PLANE, "comment": "Set XY plane"},
            {
                "command": AppConfig.gcode.DEFAULT_FEEDRATE_MODE,
                "comment": "Set feed rate mode to units/min",
            },
            coordinate_system,  # This is a dict with 'command' and 'comment' keys
            {"command": "M00", "comment": placement_message},
        ]

    def get_default_gcode_footer(self) -> list[dict[str, str]]:
        """
        Get the default G-code footer commands.

        Returns:
            list: List of dictionaries with 'command' and 'comment' keys
        """
        return [
            {"command": "M09", "comment": "Coolant off"},
            {"command": "M05", "comment": "Spindle off"},
            {"command": "T0", "comment": "Select tool 0 (no tool)"},
            {"command": "M30", "comment": "Program end"},
        ]


# Example usage if run directly
if __name__ == "__main__":
    # Create machine settings
    settings = MachineSettings()

    # Test workpiece dimensions
    test_dimensions = {
        "small": {"width": 400.0, "height": 500.0, "thickness": 18.0},
        "large": {"width": 400.0, "height": 700.0, "thickness": 18.0},
    }

    # Test direction vector to axis mapping
    test_vectors = [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)]

    print("Testing Machine Settings")
    print("-----------------------")

    print("\nDirection Vector Mapping:")
    for vector in test_vectors:
        info = settings.get_vector_axis_info(vector)
        print(
            f"Vector {vector} -> Axis: {info['axis']}, Direction: {info['direction']}, Description: {info['description']}"
        )

    print("\nFeed Rates:")
    print(f"Drilling: {settings.get_feed_rate('drilling')} mm/min")
    print(f"Rapid: {settings.get_feed_rate('rapid')} mm/min")
    print(f"Retraction: {settings.get_feed_rate('retraction')} mm/min")

    print("\nSafety Parameters:")
    print(f"Approach Distance: {settings.get_approach_distance()} mm")
    print(f"Clearance Distance: {settings.get_clearance_distance()} mm")

    print("\nPositioning Commands:")
    commands = settings.get_positioning_commands()
    for key, command in commands.items():
        print(f"{key}: {command}")

    print("\nCoordinate Systems:")
    for name, dimensions in test_dimensions.items():
        coordinate_system = settings.get_coordinate_system(dimensions)
        print(
            f"{name.capitalize()} workpiece ({dimensions['height']}mm height): {coordinate_system['command']} - {coordinate_system['comment']}"
        )

    print("\nFormatting Examples:")
    print(f"Coordinate: {settings.format_coordinate(10.1234567)}")
    print(f"Comment: {settings.format_comment('Test comment')}")
    print(
        f"Line Numbers: {settings.get_line_number(0)}, {settings.get_line_number(1)}, {settings.get_line_number(2)}"
    )

    print("\nG-code Header Example (Small Workpiece):")
    header = settings.get_default_gcode_header(test_dimensions["small"])
    for i, item in enumerate(header):
        line_num = settings.get_line_number(i)
        comment = settings.format_comment(item["comment"])
        print(f"{line_num} {item['command']} {comment}")

    print("\nG-code Footer Example:")
    footer = settings.get_default_gcode_footer()
    for i, item in enumerate(footer):
        line_num = settings.get_line_number(i)
        comment = settings.format_comment(item["comment"])
        print(f"{line_num} {item['command']} {comment}")
