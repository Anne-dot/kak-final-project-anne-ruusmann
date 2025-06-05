#!/usr/bin/env python3
"""
Module for G-code normalization.

This module implements the G-code normalizer functionality that standardizes
G-code format, removes redundant coordinates, and makes implicit commands
explicit before they are processed for safety checks.

Classes:
    GCodeNormalizer: Normalizes G-code to standard format with explicit commands
"""

import datetime
import os
import re
from pathlib import Path

from Utils.config import AppConfig
from Utils.error_utils import (
    BaseError,
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    FileError,
)

# Import from Utils package - centralized utility functions
from Utils.logging_utils import log_exception, setup_logger
from Utils.path_utils import PathUtils


class GCodeNormalizer:
    """
    Normalizes G-code by standardizing commands and removing redundant data.

    This class performs preprocessing on G-code to:
    1. Normalize G-code format (G0 -> G00, G1 -> G01, etc.)
    2. Remove X/Y/Z coordinates when they don't change from previous position
    3. Add explicit G01 commands where they're implied (respecting modal behavior)

    Attributes:
        current_position: Dictionary tracking the current XYZ position
        current_modal_state: Dictionary tracking the current modal G-code state
    """

    def __init__(self):
        """Initialize the GCodeNormalizer with state tracking."""
        # Set up logger for this class
        self.logger = setup_logger(__name__)
        self._reset_state()
        self.current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info("GCodeNormalizer initialized")

    def _reset_state(self):
        """Reset the internal state tracking."""
        # Position tracking
        self.current_position = {"X": None, "Y": None, "Z": None}

        # Modal state tracking (G-codes are modal and remain active until changed)
        self.current_modal_state = {
            "motion": None,  # G00, G01, G02, G03
            "plane": AppConfig.gcode.DEFAULT_PLANE,  # Default XY plane
            "units": AppConfig.gcode.DEFAULT_UNITS,  # Default mm
            "distance": AppConfig.gcode.DEFAULT_POSITIONING,  # Default absolute positioning
            "feedrate": AppConfig.gcode.DEFAULT_FEEDRATE_MODE,  # Default units per minute
        }

    def normalize_file(self, input_file, output_file=None):
        """
        Process a G-code file with normalization.

        Args:
            input_file: Path to input G-code file
            output_file: Path to output file. If None,
                         generates output filename.

        Returns:
            Tuple: (success, message, details)
        """
        try:
            # Normalize and validate paths
            input_path = PathUtils.normalize_path(input_file)
            self.logger.info(f"Processing file: {input_path}")

            # Generate output filename if not provided
            if output_file is None:
                input_path_obj = Path(input_path)
                # Preserve the original file extension
                output_path = str(
                    input_path_obj.with_stem(f"{input_path_obj.stem}_normalized").with_suffix(
                        input_path_obj.suffix
                    )
                )
            else:
                output_path = PathUtils.normalize_path(output_file)

            self.logger.info(f"Output will be written to: {output_path}")

            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)

            # Read input file
            self.logger.info("Reading input file...")
            try:
                with open(input_path) as f:
                    content = f.read()
                self.logger.info(f"Successfully read file: {len(content)} characters")
            except FileNotFoundError:
                self.logger.error(f"Input file not found: {input_path}")
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"Input file not found: {input_path}",
                        file_path=input_path,
                        severity=ErrorSeverity.ERROR,
                    )
                )
            except PermissionError:
                self.logger.error(f"Permission denied reading input file: {input_path}")
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"Permission denied reading input file: {input_path}",
                        file_path=input_path,
                        severity=ErrorSeverity.ERROR,
                        details={"error": "permission_denied"},
                    )
                )
            except Exception as e:
                self.logger.error(f"Failed to read input file: {e!s}")
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"Failed to read input file: {e!s}",
                        file_path=input_path,
                        severity=ErrorSeverity.ERROR,
                        details={"error_type": type(e).__name__},
                    )
                )

            # Process content
            self.logger.info("Normalizing G-code content...")
            filename = os.path.basename(input_path)
            result = self._normalize_content(content, filename)
            self.logger.info("Normalization complete.")
            self.logger.info(
                f"Statistics: {result['g_codes_normalized']} G-codes normalized, "
                f"{result['coordinates_removed']} coordinates removed, "
                f"{result['g01_commands_added']} G01 commands added"
            )

            # Write output file
            self.logger.info(f"Writing output file: {output_path}")
            try:
                with open(output_path, "w") as f:
                    f.write(result["processed_content"])
                self.logger.info(
                    f"Successfully wrote output file: {len(result['processed_content'])} characters"
                )
            except PermissionError:
                self.logger.error(f"Permission denied writing output file: {output_path}")
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"Permission denied writing output file: {output_path}",
                        file_path=output_path,
                        severity=ErrorSeverity.ERROR,
                        details={"error": "permission_denied"},
                    )
                )
            except Exception as e:
                self.logger.error(f"Failed to write output file: {e!s}")
                return ErrorHandler.from_exception(
                    FileError(
                        message=f"Failed to write output file: {e!s}",
                        file_path=output_path,
                        severity=ErrorSeverity.ERROR,
                        details={"error_type": type(e).__name__},
                    )
                )

            self.logger.info(f"Successfully processed {result['line_count']} lines")
            return ErrorHandler.create_success_response(
                message="G-code normalization completed successfully",
                data={
                    "input_file": input_path,
                    "output_file": output_path,
                    "lines_processed": result["line_count"],
                    "g_codes_normalized": result["g_codes_normalized"],
                    "coordinates_removed": result["coordinates_removed"],
                    "g01_commands_added": result["g01_commands_added"],
                },
            )

        except Exception as e:
            log_exception(self.logger, f"Error normalizing G-code: {e!s}")
            return ErrorHandler.from_exception(
                BaseError(
                    message=f"Error normalizing G-code: {e!s}",
                    category=ErrorCategory.PROCESSING,
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": type(e).__name__},
                )
            )

    def _normalize_content(self, content, filename):
        """
        Process G-code content with normalization.

        Args:
            content: G-code content to normalize
            filename: Original filename for reference

        Returns:
            dict: Result with processed content and statistics
        """
        lines = content.splitlines(True)  # Keep the newlines
        result_lines = []

        # Add header with metadata
        result_lines.append("(Normalized G-code generated by GCodeNormalizer)\n")
        result_lines.append(f"(Original file: {filename})\n")
        result_lines.append(f"(Generated on: {self.current_timestamp})\n")
        result_lines.append("\n")

        # Reset the state for new content
        self._reset_state()

        # Statistics
        line_count = 0
        g_codes_normalized = 0
        coordinates_removed = 0
        g01_commands_added = 0

        # Process each line
        for line in lines:
            line_count += 1

            # Skip blank lines
            if not line.strip():
                result_lines.append(line)
                continue

            # Store original for comparison
            original_line = line

            # Normalize the line
            normalized_line = self._normalize_line(line)

            # Update statistics by checking what changes were made
            if normalized_line != original_line:
                # Check for G-code normalization (G0 -> G00)
                if (
                    (re.search(r"G0(?![0-9])", original_line) and "G00" in normalized_line)
                    or (re.search(r"G1(?![0-9])", original_line) and "G01" in normalized_line)
                    or (re.search(r"G2(?![0-9])", original_line) and "G02" in normalized_line)
                    or (re.search(r"G3(?![0-9])", original_line) and "G03" in normalized_line)
                ):
                    g_codes_normalized += 1

                # Check for coordinates removal
                if len(re.findall(r"[XYZ][+-]?[0-9]*\.?[0-9]+", original_line)) > len(
                    re.findall(r"[XYZ][+-]?[0-9]*\.?[0-9]+", normalized_line)
                ):
                    coordinates_removed += 1

                # Check for G01 addition
                if not re.search(r"G0*1", original_line) and re.search(r"G0*1", normalized_line):
                    g01_commands_added += 1

            # Add normalized line to result
            result_lines.append(normalized_line)

            # Log progress for large files
            if line_count % 1000 == 0:
                self.logger.info(f"Processed {line_count} lines")

        # Add footer with statistics
        result_lines.append("\n")
        result_lines.append("(End of normalized G-code)\n")
        result_lines.append(f"(Processed {line_count} lines)\n")
        result_lines.append(f"(Normalized {g_codes_normalized} G-codes)\n")
        result_lines.append(f"(Removed {coordinates_removed} redundant coordinates)\n")
        result_lines.append(f"(Added {g01_commands_added} explicit G01 commands)\n")

        # Compile result
        return {
            "processed_content": "".join(result_lines),
            "line_count": line_count,
            "g_codes_normalized": g_codes_normalized,
            "coordinates_removed": coordinates_removed,
            "g01_commands_added": g01_commands_added,
        }

    def _normalize_line(self, line):
        """
        Normalize a single line of G-code.

        Args:
            line: G-code line to normalize

        Returns:
            str: Normalized G-code line
        """
        stripped_line = line.strip()

        # Skip empty lines and comments
        if not stripped_line or stripped_line.startswith("(") or stripped_line.startswith(";"):
            return line

        # Track whether the original line ends with a newline
        has_newline = line.endswith("\n")

        # 1. Normalize G-code format
        normalized_line = self._normalize_g_format(stripped_line)

        # 2. Update modal state based on commands in the line
        modal_updated = self._update_modal_state(normalized_line)

        # 3. Extract coordinates from the line
        coordinates = self._extract_coordinates(normalized_line)

        # 4. Handle coordinate removal and G01 addition
        if coordinates:
            normalized_line = self._handle_coordinates(normalized_line, coordinates, modal_updated)

        # Ensure the original line ending is preserved
        if has_newline and not normalized_line.endswith("\n"):
            normalized_line += "\n"

        # Check if any changes were made
        if normalized_line != line:
            self.logger.debug(f"Normalized line: '{line.strip()}' -> '{normalized_line.strip()}'")

        return normalized_line

    def _normalize_g_format(self, line):
        """
        Normalize G-code format (G0 -> G00, G1 -> G01, etc.)

        Args:
            line: G-code line to normalize

        Returns:
            str: Line with normalized G-code format
        """
        # Define patterns for G-code normalization
        g_replacements = [
            (r"G0(?![0-9])", r"G00"),  # G0 -> G00
            (r"G1(?![0-9])", r"G01"),  # G1 -> G01
            (r"G2(?![0-9])", r"G02"),  # G2 -> G02
            (r"G3(?![0-9])", r"G03"),  # G3 -> G03
        ]

        # Apply each replacement pattern
        result = line
        for pattern, replacement in g_replacements:
            result = re.sub(pattern, replacement, result)

        # Log if changes were made
        if result != line:
            self.logger.debug(f"Normalized G-code format: '{line}' -> '{result}'")

        return result

    def _extract_coordinates(self, line):
        """
        Extract X, Y, Z coordinates from a line.

        Args:
            line: G-code line to extract coordinates from

        Returns:
            dict: Dictionary with X, Y, Z coordinates if present
        """
        coordinates = {}

        # Define patterns for coordinate extraction
        # Match X, Y, or Z followed by an optional sign and decimal number
        x_pattern = re.compile(r"X([+-]?[0-9]*\.?[0-9]+)", re.IGNORECASE)
        y_pattern = re.compile(r"Y([+-]?[0-9]*\.?[0-9]+)", re.IGNORECASE)
        z_pattern = re.compile(r"Z([+-]?[0-9]*\.?[0-9]+)", re.IGNORECASE)

        # Extract coordinates
        x_match = x_pattern.search(line)
        if x_match:
            coordinates["X"] = float(x_match.group(1))

        y_match = y_pattern.search(line)
        if y_match:
            coordinates["Y"] = float(y_match.group(1))

        z_match = z_pattern.search(line)
        if z_match:
            coordinates["Z"] = float(z_match.group(1))

        # Log found coordinates for debugging
        if coordinates:
            coord_str = ", ".join([f"{k}={v}" for k, v in coordinates.items()])
            self.logger.debug(f"Extracted coordinates: {coord_str}")

        return coordinates

    def _update_modal_state(self, line):
        """
        Update the current G-code modal state based on the line.

        Args:
            line: G-code line to analyze

        Returns:
            bool: True if modal state was updated, False otherwise
        """
        modal_updated = False

        # Check for motion commands (G00, G01, G02, G03)
        motion_commands = {
            "G00": re.compile(r"G0+(?![0-9])"),
            "G01": re.compile(r"G0*1(?![0-9])"),
            "G02": re.compile(r"G0*2(?![0-9])"),
            "G03": re.compile(r"G0*3(?![0-9])"),
        }

        for command, pattern in motion_commands.items():
            if pattern.search(line):
                prev_motion = self.current_modal_state["motion"]
                self.current_modal_state["motion"] = command
                modal_updated = True
                self.logger.debug(f"Modal motion update: {prev_motion} -> {command}")
                break

        # Check for plane selection (G17, G18, G19)
        plane_commands = {
            "G17": re.compile(r"G0*17(?![0-9])"),  # XY plane
            "G18": re.compile(r"G0*18(?![0-9])"),  # ZX plane
            "G19": re.compile(r"G0*19(?![0-9])"),  # YZ plane
        }

        for command, pattern in plane_commands.items():
            if pattern.search(line):
                self.current_modal_state["plane"] = command
                modal_updated = True
                break

        # Check for units (G20, G21)
        units_commands = {
            "G20": re.compile(r"G0*20(?![0-9])"),  # Inches
            "G21": re.compile(r"G0*21(?![0-9])"),  # Millimeters
        }

        for command, pattern in units_commands.items():
            if pattern.search(line):
                self.current_modal_state["units"] = command
                modal_updated = True
                break

        # Check for distance mode (G90, G91)
        distance_commands = {
            "G90": re.compile(r"G0*90(?![0-9])"),  # Absolute
            "G91": re.compile(r"G0*91(?![0-9])"),  # Incremental
        }

        for command, pattern in distance_commands.items():
            if pattern.search(line):
                self.current_modal_state["distance"] = command
                modal_updated = True
                break

        # Check for feed rate mode (G93, G94)
        feedrate_commands = {
            "G93": re.compile(r"G0*93(?![0-9])"),  # Inverse time
            "G94": re.compile(r"G0*94(?![0-9])"),  # Units per minute
        }

        for command, pattern in feedrate_commands.items():
            if pattern.search(line):
                self.current_modal_state["feedrate"] = command
                modal_updated = True
                break

        # Check for tool changes (TxxM6 or TxxM06)
        tool_change = re.search(r"T\d+M0*6", line)
        if tool_change:
            # Reset position tracking after tool change
            self.current_position = {"X": None, "Y": None, "Z": None}
            self.logger.debug("Tool change detected, position tracking reset")

        return modal_updated

    def _handle_coordinates(self, line, coordinates, modal_updated):
        """
        Handle coordinate updates and remove redundant coordinates.

        Args:
            line: G-code line to process
            coordinates: Dictionary of coordinates found in the line
            modal_updated: Whether modal state was updated in this line

        Returns:
            str: Line with redundant coordinates removed and explicit G command added if needed
        """
        # If no coordinates, return the line unchanged
        if not coordinates:
            return line

        modified_line = line
        coordinates_removed = []

        # Only process redundant coordinates if position is already known
        if any(self.current_position[axis] is not None for axis in ["X", "Y", "Z"]):
            for axis in ["X", "Y", "Z"]:
                if axis in coordinates:
                    # Check if coordinate is redundant (hasn't changed from previous position)
                    if (
                        self.current_position[axis] is not None
                        and abs(coordinates[axis] - self.current_position[axis])
                        < AppConfig.limits.COORDINATE_TOLERANCE
                    ):
                        # Remove the axis and value from the line
                        old_str = modified_line
                        modified_line = re.sub(rf"{axis}[+-]?[0-9]*\.?[0-9]+", "", modified_line)

                        if old_str != modified_line:
                            coordinates_removed.append(axis)
                            self.logger.debug(
                                f"Removed redundant {axis} coordinate: {self.current_position[axis]}"
                            )

        # Add explicit G command if needed
        if not modal_updated and coordinates:
            # Check if this is a movement command without an explicit G-code
            has_g_code = re.search(r"G\d+", modified_line)

            if not has_g_code:
                # Add the current modal motion command (G00, G01, G02, G03)
                # Default to G01 if no motion command is set yet
                motion_command = self.current_modal_state["motion"] or "G01"

                # Look for line number at the beginning
                line_num_match = re.match(r"(N\d+)", modified_line)

                if line_num_match:
                    # Add motion command after the line number
                    prefix = line_num_match.group(1)
                    rest = modified_line[len(prefix) :].lstrip()
                    modified_line = f"{prefix}{motion_command}{rest}"
                else:
                    # Add motion command at the beginning
                    modified_line = f"{motion_command}{modified_line}"

                self.logger.debug(
                    f"Added explicit {motion_command} command: '{line}' -> '{modified_line}'"
                )

        # Update current position with all valid coordinates
        for axis, value in coordinates.items():
            self.current_position[axis] = value

        # Log the overall changes
        if coordinates_removed:
            axes_str = ", ".join(coordinates_removed)
            self.logger.debug(f"Removed redundant coordinates: {axes_str}")

        return modified_line
