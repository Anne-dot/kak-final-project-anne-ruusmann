"""
Module for loading and validating G-code files.

This module handles the initial loading of G-code files, validation of file
format, and provides the basic file object that other modules will use
for data processing. It isolates file I/O operations from data processing.

References:
    - MRFP-80: DXF to G-code Generation Epic
"""

import os
import sys
import re
import platform
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, Union, List

# Import from Utils package
from Utils.logging_utils import setup_logger, log_exception
from Utils.error_utils import ErrorHandler, FileError, ErrorSeverity, ErrorCategory
from Utils.file_loader import BaseFileLoader
from Utils.config import AppConfig


class GCodeLoader(BaseFileLoader):
    """Class for loading and validating G-code files."""
    
    def __init__(self):
        """Initialize the G-code loader."""
        # Initialize base class with G-code-specific settings
        super().__init__(
            allowed_extensions=['.nc', '.txt', '.gcode', '.ngc'],
            description="G-code"
        )
        
        self.gcode_content = None
        self.gcode_lines = []
        self.logger.info("GCodeLoader initialized")
    
    def load_file(self, file_path=None):
        """
        Loads and validates a G-code file.
        
        Args:
            file_path: Optional path to G-code file. If not provided, will prompt for selection.
            
        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if loading was successful
                - message contains success details or error message
                - details contains the file content or error information
        """
        # If no path provided, prompt for file selection
        if file_path is None:
            self.logger.info("No file path provided, prompting for selection")
            file_path = self.select_file()
            
            # Check if user canceled file selection
            if not file_path:
                self.logger.warning("File selection canceled by user")
                return ErrorHandler.from_exception(
                    FileError(
                        message="File selection canceled by user",
                        severity=ErrorSeverity.WARNING
                    )
                )
        
        # Convert to Path object for consistent handling
        file_path = Path(file_path) if not isinstance(file_path, Path) else file_path
        self.file_path = file_path
        self.logger.info(f"Attempting to load G-code file: {file_path}")
        
        try:
            # Validate the file using the base class method
            success, message, details = self.validate_file(file_path)
            if not success:
                return success, message, details
            
            # Load the G-code file
            with open(file_path, 'r', errors='replace') as f:
                self.gcode_content = f.read()
                self.gcode_lines = self.gcode_content.splitlines()
            
            # Basic validation: Check if file contains G-code commands
            gcode_count = 0
            for line in self.gcode_lines:
                # Skip comments and empty lines
                if not line.strip() or line.strip().startswith(('(', ';', '%')):
                    continue
                
                # Check for G-code commands
                if re.search(r'[GM]\d+', line):
                    gcode_count += 1
            
            if gcode_count == 0:
                self.logger.error("File does not contain any G-code commands")
                return ErrorHandler.from_exception(
                    FileError(
                        message="File does not contain any G-code commands",
                        file_path=str(file_path),
                        severity=ErrorSeverity.ERROR,
                        details={"gcode_count": 0}
                    )
                )
            
            success_msg = f"Successfully loaded G-code file: {file_path.name}"
            self.logger.info(success_msg)
            
            # Return success with content and details
            return ErrorHandler.create_success_response(
                message=success_msg,
                data={
                    "content": self.gcode_content,
                    "lines": self.gcode_lines,
                    "line_count": len(self.gcode_lines),
                    "gcode_count": gcode_count,
                    "file_path": str(file_path)
                }
            )
            
        except UnicodeDecodeError as e:
            error_msg = f"Error decoding G-code file: {str(e)}"
            self.error_message = error_msg
            log_exception(self.logger, error_msg)
            
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "UnicodeDecodeError", "error": str(e)}
                )
            )
        except Exception as e:
            error_msg = f"Unexpected error loading G-code file: {str(e)}"
            self.error_message = error_msg
            log_exception(self.logger, error_msg)
            
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def get_file_info(self, file_content=None):
        """
        Returns basic information about the G-code file.
        
        Args:
            file_content: Optional G-code content. If None, uses previously loaded content.
            
        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if info extraction was successful
                - message contains success or error message
                - details contains the G-code information
        """
        content = file_content if file_content is not None else self.gcode_content
        
        if content is None:
            self.logger.warning("Attempted to get G-code info with no content loaded")
            return ErrorHandler.from_exception(
                FileError(
                    message="No G-code content loaded",
                    severity=ErrorSeverity.WARNING,
                    details={"reason": "no_content"}
                )
            )
            
        try:
            self.logger.info("Extracting G-code file information")
            
            # Split content into lines if it's a string
            if isinstance(content, str):
                lines = content.splitlines()
            else:
                lines = content
            
            # Count different types of commands
            gcode_count = 0
            mcode_count = 0
            tool_changes = 0
            
            # Track coordinates
            has_x = False
            has_y = False
            has_z = False
            
            # Track G-code types
            rapid_moves = 0  # G0/G00
            linear_moves = 0  # G1/G01
            arc_moves = 0     # G2/G02, G3/G03
            
            # Track units
            units = "unknown"  # G20 (inches) or G21 (mm)
            
            # Track coordinate system
            coordinate_mode = "unknown"  # G90 (absolute) or G91 (incremental)
            
            # Analyze each line
            for line in lines:
                # Skip comments and empty lines
                if not line.strip() or line.strip().startswith(('(', ';', '%')):
                    continue
                
                # Check for G-codes
                if re.search(r'G\d+', line):
                    gcode_count += 1
                    
                    # Check for specific G-codes
                    if re.search(r'G0+', line):
                        rapid_moves += 1
                    elif re.search(r'G0*1', line):
                        linear_moves += 1
                    elif re.search(r'G0*[23]', line):
                        arc_moves += 1
                    
                    # Check for units
                    if re.search(r'G20', line):
                        units = "inches"
                    elif re.search(r'G21', line):
                        units = "mm"
                    
                    # Check for coordinate mode
                    if re.search(r'G90', line):
                        coordinate_mode = "absolute"
                    elif re.search(r'G91', line):
                        coordinate_mode = "incremental"
                
                # Check for M-codes
                if re.search(r'M\d+', line):
                    mcode_count += 1
                
                # Check for tool changes (T.. M6)
                if re.search(r'T\d+.*M0*6', line) or re.search(r'M0*6.*T\d+', line):
                    tool_changes += 1
                
                # Check for coordinates
                if re.search(r'X[+-]?[\d.]+', line):
                    has_x = True
                if re.search(r'Y[+-]?[\d.]+', line):
                    has_y = True
                if re.search(r'Z[+-]?[\d.]+', line):
                    has_z = True
            
            # Get filename as string if we have a Path object
            filename = self.file_path.name if isinstance(self.file_path, Path) else \
                      os.path.basename(self.file_path) if self.file_path else "Unknown"
            
            # Compile information
            info = {
                'filename': filename,
                'line_count': len(lines),
                'gcode_count': gcode_count,
                'mcode_count': mcode_count,
                'tool_changes': tool_changes,
                'move_types': {
                    'rapid_moves': rapid_moves,
                    'linear_moves': linear_moves,
                    'arc_moves': arc_moves
                },
                'coordinates': {
                    'has_x': has_x,
                    'has_y': has_y, 
                    'has_z': has_z
                },
                'units': units,
                'coordinate_mode': coordinate_mode
            }
            
            self.logger.info(f"Extracted information from G-code file with {len(lines)} lines")
            
            return ErrorHandler.create_success_response(
                message=f"Successfully extracted G-code information with {len(lines)} lines",
                data=info
            )
            
        except Exception as e:
            error_msg = f"Error extracting G-code information: {str(e)}"
            log_exception(self.logger, error_msg)
            
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )
    
    def is_valid_gcode(self, file_path):
        """
        Validates that a file is readable, valid G-code.
        
        Required elements:
        - Contains at least one G-code command
        
        Args:
            file_path: Path to G-code file
            
        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if validation was successful
                - message contains success or error message
                - details contains information about the validation
        """
        # Convert to Path object for consistent handling
        file_path = Path(file_path) if not isinstance(file_path, Path) else file_path
        self.logger.info(f"Validating G-code file: {file_path}")
        
        # Start with the base validation
        success, message, details = self.validate_file(file_path)
        if not success:
            return success, message, details
            
        try:
            # Read the file
            with open(file_path, 'r', errors='replace') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Check for G-code commands
            gcode_count = 0
            for line in lines:
                # Skip comments and empty lines
                if not line.strip() or line.strip().startswith(('(', ';', '%')):
                    continue
                
                # Check for G-code commands
                if re.search(r'[GM]\d+', line):
                    gcode_count += 1
            
            if gcode_count == 0:
                self.logger.error("File does not contain any G-code commands")
                return ErrorHandler.from_exception(
                    FileError(
                        message="File does not contain any G-code commands",
                        file_path=str(file_path),
                        severity=ErrorSeverity.ERROR,
                        details={"gcode_count": 0}
                    )
                )
            
            valid_msg = f"G-code file is valid with {gcode_count} G/M-code commands"
            self.logger.info(valid_msg)
            
            return ErrorHandler.create_success_response(
                message=valid_msg,
                data={
                    "file_path": str(file_path),
                    "line_count": len(lines),
                    "gcode_count": gcode_count,
                    "is_valid": True
                }
            )
            
        except UnicodeDecodeError as e:
            error_msg = f"Error decoding G-code file: {str(e)}"
            log_exception(self.logger, error_msg)
            
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "UnicodeDecodeError", "error": str(e)}
                )
            )
        except Exception as e:
            error_msg = f"Error validating G-code file: {str(e)}"
            log_exception(self.logger, error_msg)
            
            return ErrorHandler.from_exception(
                FileError(
                    message=error_msg,
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                    details={"error_type": "Exception", "error": str(e)}
                )
            )


# Example usage if run directly
if __name__ == "__main__":
    loader = GCodeLoader()
    success, message, details = loader.load_file()
    
    if success:
        print(f"Success: {message}")
        
        # Get file information
        info_success, info_message, info_details = loader.get_file_info()
        
        if info_success:
            info = info_details
            print("\nG-code Information:")
            print(f"File: {info['filename']}")
            print(f"Line count: {info['line_count']}")
            print(f"G-code commands: {info['gcode_count']}")
            print(f"M-code commands: {info['mcode_count']}")
            print(f"Units: {info['units']}")
            print(f"Coordinate mode: {info['coordinate_mode']}")
            print("\nMove types:")
            for move_type, count in info['move_types'].items():
                print(f"  - {move_type}: {count}")
        else:
            print(f"Error getting G-code info: {info_message}")
    else:
        print(f"Error: {message}")
        if "details" in details:
            print(f"Details: {details['details']}")