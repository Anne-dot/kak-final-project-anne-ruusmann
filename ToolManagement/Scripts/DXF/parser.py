"""
DXF Parser module for loading and validating DXF files.

This module provides a DXFParser class that handles loading DXF files
and parsing them into structured document objects using ezdxf library.
"""

import glob
import os
import sys
from pathlib import Path
from typing import Any

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ezdxf

# Import utilities
from Utils.error_utils import ErrorHandler, ErrorSeverity, FileError, ValidationError
from Utils.file_loader import BaseFileLoader
from Utils.logging_utils import log_exception, setup_logger
from Utils.path_utils import PathUtils


class DXFParser(BaseFileLoader):
    """Class for parsing DXF files into structured document objects."""

    def __init__(self):
        """Initialize the DXF parser."""
        # Initialize base class with DXF-specific settings
        super().__init__(allowed_extensions=[".dxf"], description="DXF")

        self.logger = setup_logger(__name__)
        self.dxf_doc = None
        self.file_path = None

    def load_file(self, file_path: str | Path | None = None) -> tuple[bool, str, dict[str, Any]]:
        """
        Loads and validates a DXF file.

        Implements the abstract method from BaseFileLoader.

        Args:
            file_path: Path to the DXF file. If not provided, will prompt for selection.

        Returns:
            tuple: (success, message, details) with load result
        """
        # If no file path provided, prompt user to select one
        if file_path is None:
            file_path = self.select_file()
            if file_path is None:
                return ErrorHandler.from_exception(
                    FileError(message="No file selected", severity=ErrorSeverity.ERROR)
                )

        # Store the file path and parse the file
        self.file_path = file_path
        return self.parse(file_path)

    def get_file_info(self, file_content: Any = None) -> tuple[bool, str, dict[str, Any]]:
        """
        Returns basic information about the loaded DXF file.

        Implements the abstract method from BaseFileLoader.

        Args:
            file_content: Optional DXF document. If None, uses previously loaded document.

        Returns:
            tuple: (success, message, details) with file information
        """
        # Use provided content or previously loaded document
        dxf_doc = file_content or self.dxf_doc

        # Check if we have a document to extract information from
        if dxf_doc is None:
            return ErrorHandler.from_exception(
                ValidationError(message="No DXF document loaded", severity=ErrorSeverity.ERROR)
            )

        try:
            # Extract basic information
            modelspace = dxf_doc.modelspace()
            entity_count = len(list(modelspace))

            # Count entity types
            entity_types = {}
            for entity in modelspace:
                entity_type = entity.dxftype()
                if entity_type not in entity_types:
                    entity_types[entity_type] = 0
                entity_types[entity_type] += 1

            # Get layers
            layers = [layer.dxf.name for layer in dxf_doc.layers]

            # Return file information
            return ErrorHandler.create_success_response(
                message=f"DXF file contains {entity_count} entities in {len(layers)} layers",
                data={
                    "file_path": str(self.file_path) if self.file_path else None,
                    "entity_count": entity_count,
                    "entity_types": entity_types,
                    "layers": layers,
                },
            )
        except Exception as e:
            log_exception(self.logger, f"Error extracting DXF file information: {e!s}")
            return ErrorHandler.from_exception(
                FileError(
                    message=f"Error extracting DXF file information: {e!s}",
                    file_path=str(self.file_path) if self.file_path else None,
                    severity=ErrorSeverity.ERROR,
                )
            )

    def parse(self, file_path: str | Path) -> tuple[bool, str, dict[str, Any]]:
        """
        Parse a DXF file into a structured document.

        Args:
            file_path: Path to the DXF file

        Returns:
            tuple: (success, message, details) where:
                - success is a boolean indicating if parsing was successful
                - message contains success details or error message
                - details contains the document or error information
        """
        # Convert to Path object for consistency
        file_path = Path(file_path) if not isinstance(file_path, Path) else file_path

        # Validate file exists and has correct extension
        success, message, result = self.validate_file(file_path)
        if not success:
            return success, message, result

        try:
            # Parse with ezdxf
            self.logger.info(f"Parsing DXF file: {file_path}")
            self.dxf_doc = ezdxf.readfile(file_path)

            # Check if modelspace contains at least one entity
            modelspace = self.dxf_doc.modelspace()
            entity_count = len(list(modelspace))

            if entity_count == 0:
                self.logger.error("DXF file contains no entities in modelspace")
                return ErrorHandler.from_exception(
                    ValidationError(
                        message="DXF file contains no entities in modelspace",
                        severity=ErrorSeverity.ERROR,
                        details={"file_path": str(file_path)},
                    )
                )

            # Return success with document
            self.logger.info(f"Successfully parsed DXF file with {entity_count} entities")

            return ErrorHandler.create_success_response(
                message=f"DXF parsed successfully with {entity_count} entities",
                data={
                    "document": self.dxf_doc,
                    "entity_count": entity_count,
                    "file_path": str(file_path),
                },
            )

        except ezdxf.DXFError as e:
            log_exception(self.logger, f"DXF parsing error: {e!s}")
            return ErrorHandler.from_exception(
                FileError(
                    message=f"Invalid DXF file format: {e!s}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                )
            )
        except Exception as e:
            log_exception(self.logger, f"Unexpected error parsing DXF: {e!s}")
            return ErrorHandler.from_exception(
                FileError(
                    message=f"Error parsing DXF file: {e!s}",
                    file_path=str(file_path),
                    severity=ErrorSeverity.ERROR,
                )
            )


# Example usage if run directly
if __name__ == "__main__":
    # If a file path is provided, use it directly
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        parser = DXFParser()
        success, message, result = parser.load_file(file_path)

        if success:
            print(f"Success: {message}")
            print(f"Entity count: {result['entity_count']}")
        else:
            print(f"Error: {message}")
    else:
        # No file path provided, show a selection menu
        print("DXF Parser Test Utility")
        print("=======================")

        # Get path to test DXF files with cross-platform compatibility
        scripts_dir = Path(__file__).parent.parent
        dxf_test_dir = scripts_dir / "Tests" / "TestData" / "DXF"
        test_path = PathUtils.normalize_path(str(dxf_test_dir / "*.dxf"))

        test_paths = [test_path]

        # Find all DXF files in the test paths
        dxf_files = []
        for path in test_paths:
            found_files = glob.glob(path)
            if found_files:
                dxf_files.extend(found_files)

        if not dxf_files:
            # Use ErrorHandler for structured error handling
            logger = setup_logger("DXFParserCLI")
            error = FileError(
                message="No DXF test files found",
                file_path=str(dxf_test_dir),
                severity=ErrorSeverity.ERROR,
                details={"search_pattern": test_path},
            )
            # Log the error properly
            logger.error(str(error))
            # Show error to user
            print(f"Error: {error}")
            print("Usage: python parser.py <dxf_file_path>")
            sys.exit(1)

        # Display file selection menu
        print("\nAvailable DXF files:")
        for i, file_path in enumerate(dxf_files, 1):
            print(f"{i}. {os.path.basename(file_path)}")

        # Get user selection
        while True:
            try:
                choice = input("\nEnter file number to parse (or 'q' to quit): ")

                if choice.lower() == "q":
                    print("Exiting.")
                    sys.exit(0)

                index = int(choice) - 1
                if 0 <= index < len(dxf_files):
                    selected_file = dxf_files[index]
                    break
                else:
                    print(f"Invalid choice. Please enter 1-{len(dxf_files)}.")
            except ValueError:
                print("Please enter a valid number or 'q' to quit.")

        # Load and parse the selected file
        print(f"\nLoading: {selected_file}")
        parser = DXFParser()
        success, message, result = parser.load_file(selected_file)

        if success:
            print(f"Success: {message}")
            print(f"Entity count: {result['entity_count']}")

            # Show additional info for successful parse
            print("\nEntity types:")
            modelspace = result["document"].modelspace()
            entity_types = {}
            for entity in modelspace:
                entity_type = entity.dxftype()
                if entity_type not in entity_types:
                    entity_types[entity_type] = 0
                entity_types[entity_type] += 1

            for entity_type, count in entity_types.items():
                print(f"  - {entity_type}: {count}")

            # Test the get_file_info method
            print("\nFile Information:")
            info_success, info_message, info_data = parser.get_file_info()
            if info_success:
                print(f"- {info_message}")
                if "layers" in info_data:
                    print(f"- Layers: {', '.join(info_data['layers'])}")
            else:
                print(f"Error getting file info: {info_message}")
        else:
            print(f"Error: {message}")
